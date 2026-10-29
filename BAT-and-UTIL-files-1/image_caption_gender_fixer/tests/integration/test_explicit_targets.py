"""Explicit targets never enter unfinished-job selection, including no matches."""
from pathlib import Path
import pytest
from PIL import Image
from test_images import app_for,make_image
from image_caption_gender_fixer.fs import sha256

@pytest.mark.parametrize('target',['.','*.*','image.png','literal','missing*.png'])
def test_explicit_targets_do_not_read_or_change_other_jobs(tmp_path,monkeypatch,target):
    folder=tmp_path/'requested';folder.mkdir()
    image=folder/'image.png';make_image(image,text='Hello world')
    other=tmp_path/'other';other.mkdir();old_image=other/'previous.png';Image.new('RGB',(30,30),'blue').save(old_image)
    app=app_for(tmp_path,['--json']);app.args.new_session=False
    first=app.sessions.create([old_image],'default');second=app.sessions.create([old_image],'conservative')
    old={s['id']:(app.sessions.directory/(s['id']+'.json')).read_bytes() for s in (first,second)}
    original=sha256(image)
    def forbidden(*args,**kwargs):raise AssertionError('Explicit targets inspected unrelated job queues')
    monkeypatch.setattr(app.sessions,'unfinished',forbidden)
    monkeypatch.chdir(folder)
    if target=='literal':app.args.literal_path=[str(image)];targets=[]
    else:targets=[target]
    result,code=app.process(targets)
    if target.startswith('missing'):assert result['state']=='nothing_to_process' and code==11
    else:
        assert code==10 and all(Path(r['file']).parent==folder for r in result['results'])
        assert result['session'] not in old
    assert sha256(image)==original
    assert all((app.sessions.directory/(key+'.json')).read_bytes()==value for key,value in old.items())


def test_explicit_dry_run_does_not_inspect_unrelated_queues(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source,text='Hello world')
    app=app_for(tmp_path,['--dry-run','--json']);app.args.new_session=False
    app.sessions.create([source],'default')
    def forbidden():raise AssertionError('Explicit dry run read old jobs')
    monkeypatch.setattr(app.sessions,'unfinished',forbidden)
    result,code=app.process([str(source)])
    assert code==0 and result['state']=='dry_run' and result['resumable_sessions']==[]
