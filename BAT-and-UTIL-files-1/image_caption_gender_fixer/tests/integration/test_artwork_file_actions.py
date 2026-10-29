from pathlib import Path
import pytest
from PIL import Image
from test_images import ROOT,app_for,make_image
from image_caption_gender_fixer import file_actions
from image_caption_gender_fixer.fs import identity,sha256
from image_caption_gender_fixer.errors import IntegrityError,UnsafeFilesystem
from image_caption_gender_fixer.paf_album_art import AlbumArtReview


def fixture(tmp_path):
    source=tmp_path/'source.png';make_image(source);app=app_for(tmp_path,answers=iter([]))
    session=app.sessions.create([source],'default');return app,session,session['items'][0],source


def test_rename_preserves_source_bytes_and_collision_and_updates_queue(tmp_path):
    app,session,item,source=fixture(tmp_path);digest=sha256(source)
    occupied=tmp_path/'renamed.png';occupied.write_bytes(b'preserve collision')
    target=file_actions.apply(app,source,item,session,{'action':'rename_image','source':str(source),'name':'renamed.png'},identity(source))
    assert target.name=='renamed (1).png' and sha256(target)==digest and not source.exists()
    assert occupied.read_bytes()==b'preserve collision'
    assert app.sessions.load(session['id'])['items'][0]['path']==str(target)
    assert not item.get('source_file_action')


def test_rename_recovery_after_move_before_final_job_save(tmp_path,monkeypatch):
    app,session,item,source=fixture(tmp_path);digest=sha256(source);save=app.sessions.save;calls=[]
    def interrupted(value):
        calls.append(None)
        if len(calls)==2:raise OSError('simulated interruption after move')
        save(value)
    monkeypatch.setattr(app.sessions,'save',interrupted)
    with pytest.raises(OSError,match='simulated'):
        file_actions.apply(app,source,item,session,{'action':'rename_image','source':str(source),'name':'new.png'},identity(source))
    monkeypatch.setattr(app.sessions,'save',save)
    durable=app.sessions.load(session['id']);queued=durable['items'][0]
    assert queued['path']==str(source) and queued.get('source_file_action')
    file_actions.reconcile(app,queued,durable)
    assert queued['path']==str(tmp_path/'new.png') and sha256(Path(queued['path']))==digest


@pytest.mark.parametrize('name',['../escape.png','other.jpg','CON.png','bad?.png','trailing.png ','.icgf-preview.png','source-genderfixed.png'])
def test_rename_rejects_unsafe_format_or_reserved_names(tmp_path,name):
    with pytest.raises(IntegrityError):file_actions.rename_target(tmp_path/'source.png',name)


def test_recycle_failure_never_falls_back_and_unconfirmed_request_does_nothing(tmp_path,monkeypatch):
    app,session,item,source=fixture(tmp_path);digest=sha256(source);stamp=identity(source)
    payload={'action':'recycle_image','source':str(source)}
    with pytest.raises(IntegrityError,match='confirmation'):file_actions.apply(app,source,item,session,payload,stamp)
    def unavailable(path):raise UnsafeFilesystem('Recycle Bin unavailable; retained')
    monkeypatch.setattr(file_actions,'recycle',unavailable);payload['confirmed']=True
    with pytest.raises(UnsafeFilesystem):file_actions.apply(app,source,item,session,payload,stamp)
    assert source.exists() and sha256(source)==digest
    file_actions.reconcile(app,item,session);assert 'source_file_action' not in item


def test_rename_from_review_regenerates_with_new_name_and_needs_approval(tmp_path,monkeypatch):
    source=tmp_path/'source.png';make_image(source);digest=sha256(source)
    app=app_for(tmp_path,answers=iter([]));seen=[]
    def review(path,proposal,regions):
        seen.append((path,proposal['transaction']))
        return {'action':'rename_image','source':str(path),'name':'new.png'} if len(seen)==1 else 'a'
    monkeypatch.setattr(app,'review',review);result,code=app.process([str(source)])
    assert code==0 and len(seen)==2 and seen[1][0].name=='new.png' and seen[0][1]!=seen[1][1]
    corrected=Path(result['results'][0]['corrected']);assert corrected.name=='new-genderfixed.png'
    assert any(sha256(p)==digest for p in tmp_path.glob('new.png.bak.*.bak'))


def test_confirmed_recycle_from_review_uses_real_recycle_bin_without_commit(tmp_path,monkeypatch):
    source=tmp_path/'source.png';make_image(source);app=app_for(tmp_path,answers=iter([]))
    monkeypatch.setattr(app,'review',lambda path,*args:{'action':'recycle_image','source':str(path),'confirmed':True})
    result,code=app.process([str(source)])
    assert code==10 and result['results']==[{'file':str(source),'state':'recycled'}]
    assert not source.exists() and not (tmp_path/'.history.icgf').exists()
    assert not list(tmp_path.glob('*-genderfixed.png'))


def test_artwork_file_buttons_target_original_prefill_name_and_confirm_recycle(tmp_path,monkeypatch):
    from tkinter import simpledialog,messagebox
    source=tmp_path/'original.png';preview=tmp_path/'.icgf-proposal.png';Image.new('RGB',(100,200),'navy').save(preview)
    viewer=AlbumArtReview([{'path':str(preview),'title':'Proposal'}],floating=True);actions=[];questions=[]
    try:
        viewer.set_review(actions.append,[],False,changes=[],source=str(source))
        def ask(*args,**kwargs):questions.append(kwargs);return 'renamed.png'
        monkeypatch.setattr(simpledialog,'askstring',ask);viewer.buttons['rename_image'].invoke()
        assert questions[0]['initialvalue']=='original.png'
        assert actions==[{'action':'rename_image','source':str(source),'name':'renamed.png'}]
        viewer.set_review(actions.append,[],False,changes=[],source=str(source))
        monkeypatch.setattr(messagebox,'askyesno',lambda *args,**kwargs:False)
        viewer.buttons['recycle_image'].invoke();assert len(actions)==1
        monkeypatch.setattr(messagebox,'askyesno',lambda *args,**kwargs:True)
        viewer.buttons['recycle_image'].invoke()
        assert actions[-1]=={'action':'recycle_image','source':str(source),'confirmed':True}
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
