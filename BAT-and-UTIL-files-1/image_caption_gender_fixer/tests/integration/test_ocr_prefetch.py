import json
from pathlib import Path
import pytest
from image_caption_gender_fixer import cli,imaging,ocr_cache
from image_caption_gender_fixer.cli import ArgumentsError
from image_caption_gender_fixer.fs import sha256
from test_images import app_for,make_image


@pytest.mark.parametrize('alias',['--ocr','--ocr-only','-o'])
def test_ocr_aliases_cache_in_hidden_folder_file_without_jobs_or_image_edits(tmp_path,monkeypatch,alias):
    source=tmp_path/'caption.png';make_image(source)
    before=sha256(source);app=app_for(tmp_path,[alias,'--json'])
    # OCR-only must not recover/choose jobs, stage a proposal, or open a window.
    def forbidden(*args,**kwargs): raise AssertionError('OCR-only entered correction workflow')
    for name in ('select_session','preview'): monkeypatch.setattr(app,name,forbidden)
    monkeypatch.setattr(app.transactions,'recover',forbidden)
    monkeypatch.setattr(imaging,'proposal',forbidden)
    existing=app.sessions.create([source],'default')
    journal=app.sessions.directory/(existing['id']+'.json');journal_before=journal.read_bytes()
    result,code=app.process([str(source)])
    assert code==0 and result['state']=='ocr_only'
    assert result['results'][0]['caption']=='good boi' and not result['results'][0]['reused']
    cache=tmp_path/'.ocr'
    assert cache.is_file() and cache.stat().st_file_attributes&2
    assert result['results'][0]['cache']==str(cache)
    assert not(tmp_path/'.history.icgf').exists() and not list(tmp_path.glob('.icgf-*.png'))
    assert sha256(source)==before and journal.read_bytes()==journal_before
    assert len(app.sessions.list())==1


def test_repeated_ocr_only_reuses_cache_without_rewriting_it(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source)
    first=app_for(tmp_path,['-o','--json']);assert first.process([str(source)])[1]==0
    cached=(tmp_path/'.ocr').read_bytes()
    def forbidden(*args,**kwargs): raise AssertionError('A cache hit re-ran Tesseract')
    monkeypatch.setattr(imaging,'ocr',forbidden)
    second=app_for(tmp_path,['--ocr-only','--json'])
    result,code=second.process([str(source)])
    assert code==0 and result['results'][0]['reused']
    assert cached==(tmp_path/'.ocr').read_bytes()


def test_normal_run_uses_prefetched_initial_ocr_after_folder_and_image_rename(tmp_path,monkeypatch):
    folder=tmp_path/'before';folder.mkdir()
    source=folder/'caption.png';make_image(source)
    assert app_for(tmp_path,['-o','--json']).process([str(source)])[1]==0
    source.rename(folder/'renamed.png');folder.rename(tmp_path/'after')
    source=tmp_path/'after/renamed.png';cached=(source.parent/'.ocr').read_bytes()
    real=imaging.ocr;calls=[]
    def only_verification(image,exe,data,eco=False,full=False,psm=11):
        calls.append(psm)
        assert psm==6,'Normal processing repeated the initial page OCR'
        return real(image,exe,data,eco,full,psm)
    monkeypatch.setattr(imaging,'ocr',only_verification)
    app=app_for(tmp_path,answers=iter(['s']))
    result,code=app.process([str(source)])
    assert code==10 and result['results'][0]['state']=='skipped' and calls
    assert (source.parent/'.ocr').read_bytes()==cached
    assert not(source.parent/'.history.icgf').exists()


def test_changed_image_and_quality_get_fresh_entries_without_overwriting_old_ocr(tmp_path):
    source=tmp_path/'caption.png';make_image(source)
    first=app_for(tmp_path,['-o','--json']);assert first.process([str(source)])[1]==0
    initial=(tmp_path/'.ocr').read_bytes()
    make_image(source,text='hello friend')
    changed=app_for(tmp_path,['-o','--json']);result,code=changed.process([str(source)])
    assert code==0 and not result['results'][0]['reused'] and result['results'][0]['caption']=='hello friend'
    assert (tmp_path/'.ocr').read_bytes().startswith(initial)
    eco=app_for(tmp_path,['-o','--eco','--json']);result,code=eco.process([str(source)])
    assert code==0 and not result['results'][0]['reused']
    assert len((tmp_path/'.ocr').read_bytes().splitlines())==4


def test_partial_cache_write_preserves_completed_results_and_all_original_bytes(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source,text='hello friend')
    assert app_for(tmp_path,['-o','--json']).process([str(source)])[1]==0
    cache=tmp_path/'.ocr'
    with cache.open('ab') as stream: stream.write(b'{partial interrupted record')
    damaged=cache.read_bytes()
    second=tmp_path/'second.png';make_image(second)
    result,code=app_for(tmp_path,['-o','--json']).process([str(tmp_path)])
    assert code==0 and [r['reused'] for r in result['results']]==[True,False]
    assert cache.read_bytes().startswith(damaged+b'\n')
    def forbidden(*args,**kwargs): raise AssertionError('Completed OCR was lost after a partial append')
    monkeypatch.setattr(imaging,'ocr',forbidden)
    result,code=app_for(tmp_path,['-o','--json']).process([str(tmp_path)])
    assert code==0 and all(r['reused'] for r in result['results'])
    result,code=app_for(tmp_path,['--json']).process([str(source)])
    assert code==10 and result['results'][0]['reason']=='no_substitution'
    assert cache.read_bytes().startswith(damaged+b'\n')


def test_unrelated_dot_ocr_file_is_never_overwritten(tmp_path):
    source=tmp_path/'caption.png';make_image(source)
    cache=tmp_path/'.ocr';cache.write_bytes(b'user-owned unrelated file\n')
    result,code=app_for(tmp_path,['-o','--json']).process([str(source)])
    assert code==50 and 'retained' in result['results'][0]['error']
    assert cache.read_bytes()==b'user-owned unrelated file\n'


def test_interruption_retains_completed_ocr_and_repeat_fills_only_missing_entries(tmp_path,monkeypatch):
    first=tmp_path/'a.png';second=tmp_path/'b.png';make_image(first);make_image(second,text='hello friend')
    real=ocr_cache.recognize;calls=[]
    def interrupted(*args,**kwargs):
        calls.append(True)
        if len(calls)==2: raise KeyboardInterrupt()
        return real(*args,**kwargs)
    monkeypatch.setattr(ocr_cache,'recognize',interrupted)
    with pytest.raises(KeyboardInterrupt): app_for(tmp_path,['-o','--json']).process([str(tmp_path)])
    saved=(tmp_path/'.ocr').read_bytes()
    monkeypatch.setattr(ocr_cache,'recognize',real)
    result,code=app_for(tmp_path,['-o','--json']).process([str(tmp_path)])
    assert code==0 and [r['reused'] for r in result['results']]==[True,False]
    assert (tmp_path/'.ocr').read_bytes().startswith(saved)


def test_ocr_failure_does_not_block_other_images(tmp_path):
    source=tmp_path/'a.png';make_image(source)
    broken=tmp_path/'b.png';broken.write_bytes(b'\x89PNG\r\n\x1a\ngenerated broken fixture')
    result,code=app_for(tmp_path,['-o','--json']).process([str(tmp_path)])
    assert code==50 and [r['state'] for r in result['results']]==['ocr_cached','failed']


@pytest.mark.parametrize('conflict',['--resume','--dry-run'])
def test_ocr_only_rejects_conflicting_modes_without_creating_cache(tmp_path,conflict):
    source=tmp_path/'caption.png';make_image(source)
    with pytest.raises(ArgumentsError): app_for(tmp_path,['-o',conflict]).process([str(source)])
    assert not(tmp_path/'.ocr').exists()


def test_cache_signature_tracks_engine_and_english_data_contents(tmp_path):
    (tmp_path/'environment/tessdata').mkdir(parents=True)
    engine=tmp_path/'engine.exe';engine.write_bytes(b'engine 1')
    model=tmp_path/'environment/tessdata/eng.traineddata';model.write_bytes(b'model 1')
    before=ocr_cache.signature(tmp_path,engine,False)
    with engine.open('ab') as stream: stream.write(b' updated')
    assert ocr_cache.signature(tmp_path,engine,False)!=before
    engine_two=ocr_cache.signature(tmp_path,engine,False)
    with model.open('ab') as stream: stream.write(b' updated')
    assert ocr_cache.signature(tmp_path,engine,False)!=engine_two


def test_prefetch_low_confidence_retry_is_saved_as_final_result(tmp_path,monkeypatch):
    from PIL import Image
    source=tmp_path/'large.png';Image.new('RGB',(2000,100),'white').save(source)
    calls=[]
    def fake(image,exe,data,eco=False,full=False,psm=11):
        calls.append(full)
        return [{'text':'hello','words':[imaging.Word('hello',(1,1,50,30),99 if full else 20,0,5)]}]
    monkeypatch.setattr(imaging,'ocr',fake)
    result,code=app_for(tmp_path,['-o','--json']).process([str(source)])
    assert code==0 and calls==[False,True,True]
    record=json.loads((tmp_path/'.ocr').read_bytes().splitlines()[1])
    assert record['lines'][0]['words'][0]['confidence']==99


def test_two_cache_instances_merge_appends_without_losing_other_images(tmp_path):
    from PIL import Image
    first=tmp_path/'a.png';second=tmp_path/'b.png'
    Image.new('RGB',(100,40),'white').save(first);Image.new('RGB',(100,40),'black').save(second)
    a=ocr_cache.OCRCache(tmp_path);b=ocr_cache.OCRCache(tmp_path);settings={'quality':'test'}
    assert b.get(sha256(second),settings,(100,40)) is None
    lines=[{'text':'hello','words':[imaging.Word('hello',(1,1,50,30),99,0,5)]}]
    a.put(first,sha256(first),settings,(100,40),lines)
    prefix=(tmp_path/'.ocr').read_bytes()
    b.put(second,sha256(second),settings,(100,40),lines)
    assert (tmp_path/'.ocr').read_bytes().startswith(prefix)
    assert a.get(sha256(second),settings,(100,40))[0]['text']=='hello'
    assert b.get(sha256(first),settings,(100,40))[0]['text']=='hello'


def test_ocr_repair_restart_waits_and_retains_ocr_mode_targets_and_quality(tmp_path,monkeypatch):
    import os
    source=tmp_path/'caption with spaces.png';make_image(source)
    app=app_for(tmp_path,['--ocr-only','--eco']);app.interactive=True;app.ask_callback=None
    monkeypatch.setattr(cli,'repair_packages',lambda app:True)
    captured=[]
    def restart(mode,exe,arguments): captured.append((mode,arguments));return 21
    monkeypatch.setattr(cli.os,'spawnv',restart)
    with pytest.raises(SystemExit) as ended: app.process([str(source)])
    mode,arguments=captured[0]
    assert ended.value.code==21 and mode==os.P_WAIT
    assert '--ocr-only' in arguments and '--eco' in arguments and '--resume' not in arguments
    index=arguments.index('--literal-path');assert arguments[index+1]==str(source)
    assert not app.sessions.list() and not(tmp_path/'.ocr').exists()
