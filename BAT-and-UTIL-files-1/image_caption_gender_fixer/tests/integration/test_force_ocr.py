"""Force mode refreshes all selected image OCR without entering correction."""
import json
from pathlib import Path
import pytest
from PIL import Image
from image_caption_gender_fixer import cli,imaging,ocr_cache
from image_caption_gender_fixer.fs import sha256,hide
from test_images import app_for,make_image

def refreshed(*args,**kwargs):
    text='REFRESHED'
    return [{'text':text,'words':[imaging.Word(text,(1,1,100,30),99,0,len(text))]}]

@pytest.mark.parametrize('arguments',[['-of'],['--ocr-force'],['-o','-of'],['.','-of']])
def test_force_flag_selects_ocr_only_mode(arguments):
    args=cli.parser().parse_intermixed_args(arguments)
    assert args.ocr_only and args.ocr_force

def test_end_of_options_retains_literal_force_filename():
    args=cli.parser().parse_intermixed_args(['--','-of'])
    assert args.items==['-of'] and not args.ocr_force and not args.ocr_only

def test_force_reruns_cached_ocr_and_preserves_old_records_for_future_reuse(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source,text='hello friend');before=sha256(source)
    assert app_for(tmp_path,['-o','--json']).process([str(source)])[1]==0
    cache=tmp_path/'.ocr';old=cache.read_bytes();calls=[]
    def scan(*args,**kwargs):calls.append(True);return refreshed()
    monkeypatch.setattr(ocr_cache,'recognize',scan)
    result,code=app_for(tmp_path,['-of','--json']).process([str(source)])
    assert code==0 and calls==[True] and not result['results'][0]['reused']
    assert result['results'][0]['caption']=='REFRESHED'
    saved=cache.read_bytes();assert saved.startswith(old) and len(saved.splitlines())==3
    def forbidden(*args,**kwargs):raise AssertionError('Refreshed OCR was not reused')
    monkeypatch.setattr(ocr_cache,'recognize',forbidden)
    result,code=app_for(tmp_path,['-o','--json']).process([str(source)])
    assert code==0 and result['results'][0]['reused'] and result['results'][0]['caption']=='REFRESHED'
    assert cache.read_bytes()==saved and sha256(source)==before

def test_force_includes_processed_images_and_preserved_originals_without_jobs_or_edits(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source)
    result,code=app_for(tmp_path,answers=iter(['y'])).process([str(source)])
    assert code==0
    corrected=Path(result['results'][0]['corrected'])
    from image_caption_gender_fixer.history import History
    event=History(tmp_path).resolve(corrected.name)[0];backup=tmp_path/event['backup']
    history=tmp_path/'.history.icgf';snapshots={p:p.read_bytes() for p in (corrected,backup,history)}
    artifact=tmp_path/'.icgf-uncommitted-proposal.png';Image.new('RGB',(100,100),'red').save(artifact)
    ordinary,code=app_for(tmp_path,['-o','--json']).process([str(tmp_path)])
    assert code==11 and not ordinary['results']
    app=app_for(tmp_path,['-of','--json'])
    pending=app.sessions.create([corrected],'default');journal=app.sessions.directory/(pending['id']+'.json');job_bytes=journal.read_bytes()
    def forbidden(*args,**kwargs):raise AssertionError('Force OCR entered correction or job handling')
    monkeypatch.setattr(app,'select_session',forbidden);monkeypatch.setattr(app,'preview',forbidden)
    monkeypatch.setattr(app.transactions,'recover',forbidden);monkeypatch.setattr(imaging,'proposal',forbidden)
    monkeypatch.setattr(ocr_cache,'recognize',refreshed)
    result,code=app.process([str(tmp_path)])
    assert code==0 and {Path(r['file']) for r in result['results']}=={corrected,backup}
    assert all(not r['reused'] for r in result['results'])
    assert all(p.read_bytes()==data for p,data in snapshots.items()) and journal.read_bytes()==job_bytes
    assert artifact.exists() and (tmp_path/'.ocr').stat().st_file_attributes&2

def test_force_reads_legacy_suffix_without_renaming_and_excludes_internal_artifacts(tmp_path,monkeypatch):
    source=tmp_path/'caption-gendeerfixed (2).png';make_image(source)
    original=sha256(source)
    artifact=tmp_path/'.icgf-hidden-genderfixed.png';Image.new('RGB',(200,100),'red').save(artifact)
    app=app_for(tmp_path,['-of','--include-hidden','--json'])
    def forbidden(*args,**kwargs):raise AssertionError('Force mode tried filename migration')
    monkeypatch.setattr(app.transactions,'pending',forbidden)
    monkeypatch.setattr(ocr_cache,'recognize',refreshed)
    result,code=app.process([str(tmp_path)])
    assert code==0 and [r['file'] for r in result['results']]==[str(source)]
    assert sha256(source)==original and not(tmp_path/'caption-genderfixed (2).png').exists()

def test_force_keeps_hidden_file_filter_and_optional_override(tmp_path,monkeypatch):
    source=tmp_path/'hidden-genderfixed.png';make_image(source);hide(source)
    assert app_for(tmp_path,['-of','--json']).process([str(source)])[1]==11
    monkeypatch.setattr(ocr_cache,'recognize',refreshed)
    assert app_for(tmp_path,['-of','--include-hidden','--json']).process([str(source)])[1]==0

@pytest.mark.parametrize('option',['--dry-run','--resume'])
def test_force_rejects_incompatible_modes_without_writes(tmp_path,option):
    source=tmp_path/'caption.png';make_image(source)
    with pytest.raises(cli.ArgumentsError):app_for(tmp_path,['-of',option]).process([str(source)])
    assert not(tmp_path/'.ocr').exists()

def test_force_refuses_unrelated_cache_without_overwriting_it(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source)
    cache=tmp_path/'.ocr';cache.write_bytes(b'unrelated user data\n');old=cache.read_bytes()
    monkeypatch.setattr(ocr_cache,'recognize',refreshed)
    result,code=app_for(tmp_path,['-of','--json']).process([str(source)])
    assert code==50 and result['results'][0]['state']=='failed' and cache.read_bytes()==old

def test_force_retains_partial_record_before_appending_fresh_result(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source)
    assert app_for(tmp_path,['-o','--json']).process([str(source)])[1]==0
    cache=tmp_path/'.ocr'
    with cache.open('ab') as stream:stream.write(b'{incomplete record')
    before=cache.read_bytes();monkeypatch.setattr(ocr_cache,'recognize',refreshed)
    assert app_for(tmp_path,['-of','--json']).process([str(source)])[1]==0
    assert cache.read_bytes().startswith(before+b'\n')
    def forbidden(*args,**kwargs):raise AssertionError('Latest forced record was lost')
    monkeypatch.setattr(ocr_cache,'recognize',forbidden)
    result,code=app_for(tmp_path,['-o','--json']).process([str(source)])
    assert code==0 and result['results'][0]['reused'] and result['results'][0]['caption']=='REFRESHED'

def test_force_repair_restart_preserves_force_flag_and_targets(tmp_path,monkeypatch):
    import os
    source=tmp_path/'caption-genderfixed.png';make_image(source)
    app=app_for(tmp_path,['-of']);app.interactive=True;app.ask_callback=None
    monkeypatch.setattr(cli,'repair_packages',lambda app:True);captured=[]
    def restart(mode,exe,arguments):captured.append((mode,arguments));return 21
    monkeypatch.setattr(cli.os,'spawnv',restart)
    with pytest.raises(SystemExit) as result:app.process([str(source)])
    mode,arguments=captured[0]
    assert result.value.code==21 and mode==os.P_WAIT and '--ocr-force' in arguments
    index=arguments.index('--literal-path');assert arguments[index+1]==str(source)
    assert not(tmp_path/'.ocr').exists() and not app.sessions.list()

def test_force_is_not_an_administrative_command_modifier(tmp_path,capsys):
    assert cli.main(tmp_path,['rules','show','-of','--json'])==64
    assert json.loads(capsys.readouterr().out)['state']=='failed'
    assert list(tmp_path.iterdir())==[]
