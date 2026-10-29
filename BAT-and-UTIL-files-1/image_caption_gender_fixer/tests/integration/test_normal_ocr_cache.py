"""Normal review persists initial OCR independently of edit approval."""
import json
from pathlib import Path
import pytest
from image_caption_gender_fixer import imaging,ocr_cache
from image_caption_gender_fixer.fs import sha256
from test_images import app_for,make_image

def no_recognition(*args,**kwargs):raise AssertionError('Saved initial OCR was recognized again')

def test_skipped_review_saves_hidden_cache_and_next_normal_run_reuses_it(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source);original=sha256(source)
    first=app_for(tmp_path,answers=iter(['s']));result,code=first.process([str(source)])
    assert code==10 and result['results'][0]['state']=='skipped'
    cache=tmp_path/'.ocr';saved=cache.read_bytes()
    assert cache.stat().st_file_attributes&2
    record=json.loads(saved.splitlines()[1]);assert record['image_hash']==original and record['lines'][0]['text']=='good boi'
    monkeypatch.setattr(ocr_cache,'recognize',no_recognition)
    second=app_for(tmp_path,answers=iter(['s']));result,code=second.process([str(source)])
    assert code==10 and result['results'][0]['state']=='skipped'
    assert cache.read_bytes()==saved and sha256(source)==original and not(tmp_path/'.history.icgf').exists()

@pytest.mark.parametrize('text,action',[('hello friend',None),('good boi','c')])
def test_no_match_and_canceled_review_results_are_reused_by_ocr_only(tmp_path,monkeypatch,text,action):
    source=tmp_path/'caption.png';make_image(source,text);original=sha256(source)
    app=app_for(tmp_path,answers=iter([action] if action else []));result,code=app.process([str(source)])
    assert code==20 if action else code==10
    saved=(tmp_path/'.ocr').read_bytes();monkeypatch.setattr(ocr_cache,'recognize',no_recognition)
    result,code=app_for(tmp_path,['-o','--json']).process([str(source)])
    assert code==0 and result['results'][0]['reused']
    assert (tmp_path/'.ocr').read_bytes()==saved and sha256(source)==original

def test_dry_run_does_not_populate_cache(tmp_path):
    source=tmp_path/'caption.png';make_image(source)
    result,code=app_for(tmp_path,['--dry-run','--json']).process([str(source)])
    assert code==0 and not(tmp_path/'.ocr').exists()

def test_unrelated_cache_is_preserved_and_normal_review_still_works(tmp_path,capsys):
    source=tmp_path/'caption.png';make_image(source)
    cache=tmp_path/'.ocr';cache.write_bytes(b'unrelated user data\n');before=cache.read_bytes()
    result,code=app_for(tmp_path,answers=iter(['s'])).process([str(source)])
    assert code==10 and result['results'][0]['state']=='skipped'
    assert cache.read_bytes()==before and 'continuing review' in capsys.readouterr().err

def test_cache_write_error_is_nonfatal_in_normal_review(tmp_path,monkeypatch,capsys):
    source=tmp_path/'caption.png';make_image(source)
    def denied(*a,**k):raise PermissionError('generated cache-write failure')
    monkeypatch.setattr(ocr_cache.OCRCache,'put',denied)
    result,code=app_for(tmp_path,answers=iter(['s'])).process([str(source)])
    assert code==10 and result['results'][0]['state']=='skipped'
    assert 'continuing review' in capsys.readouterr().err and not(tmp_path/'.ocr').exists()

def test_image_changed_during_recognition_is_not_cached_or_committed(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source)
    real=ocr_cache.recognize
    def changed(*args,**kwargs):
        lines=real(*args,**kwargs)
        with source.open('ab') as stream:stream.write(b'changed while recognizing')
        return lines
    monkeypatch.setattr(ocr_cache,'recognize',changed)
    result,code=app_for(tmp_path,answers=iter([])).process([str(source)])
    assert code==50 and result['results'][0]['state']=='failed'
    assert 'changed during OCR' in result['results'][0]['error']
    assert not(tmp_path/'.ocr').exists() and not(tmp_path/'.history.icgf').exists()
