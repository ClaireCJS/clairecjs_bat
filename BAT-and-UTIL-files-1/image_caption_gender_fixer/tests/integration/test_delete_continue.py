"""Recycling from artwork must advance without a second user decision."""
import threading
from pathlib import Path

from test_images import app_for,make_image
from image_caption_gender_fixer import adjustment_menu,file_actions
from image_caption_gender_fixer.errors import UnsafeFilesystem
from image_caption_gender_fixer.fs import sha256


class ArtworkDecisions:
    """Exercise the real popup/console review handoff without foreground input."""
    def __init__(self,decide):
        self.decide=decide;self.stopped=threading.Event();self.sources=[];self.ended=[]

    def begin_review(self,blocked,rules,notes,changes,source):
        self.sources.append(source);return len(self.sources)

    def review_action(self,token):
        return self.decide(Path(self.sources[-1]),token)

    def end_review(self,token):self.ended.append(token)


def popup_app(tmp_path,monkeypatch,decide):
    app=app_for(tmp_path);app.interactive=True
    artwork=ArtworkDecisions(decide);app.floating_artwork=artwork
    previews=[]
    monkeypatch.setattr(app,'preview',lambda path,title,detail=False:previews.append(
        (Path(path),title,dict(app.preview_captions))))
    def no_console():raise AssertionError('Artwork decision must not require console input')
    monkeypatch.setattr(adjustment_menu,'console_key',no_console)
    return app,artwork,previews


def test_confirmed_delete_shows_next_image_before_ocr_and_needs_no_continue(tmp_path,monkeypatch):
    first=tmp_path/'first.png';second=tmp_path/'second.png'
    make_image(first,'good boi');make_image(second,'kind boi');second_hash=sha256(second)
    def decide(source,token):
        if source==first:return {'action':'recycle_image','source':str(source),'confirmed':True}
        return 's'
    app,artwork,previews=popup_app(tmp_path,monkeypatch,decide)
    recognize=app.ocr_lines;ocr_order=[]
    def recognize_checked(source,*args,**kwargs):
        ocr_order.append(source)
        if source==second:
            assert not first.exists()
            assert previews[-1][0]==second,'Next source should replace deleted artwork before slow OCR'
            assert previews[-1][2]=={},'Previous image captions must not appear beside the next source'
        return recognize(source,*args,**kwargs)
    monkeypatch.setattr(app,'ocr_lines',recognize_checked)
    result,code=app.process([str(first),str(second)])
    assert code==10 and result['results']==[
        {'file':str(first),'state':'recycled'},{'file':str(second),'state':'skipped'}]
    assert artwork.sources==[str(first),str(second)] and artwork.ended==[1,2]
    assert ocr_order==[first,second]
    assert not first.exists() and sha256(second)==second_hash
    assert result['summary']['remaining']==0
    assert not list(tmp_path.glob('.icgf-*.png'))
    assert not list(tmp_path.glob('*-genderfixed.png'))


def test_failed_delete_stays_on_current_image_until_another_decision(tmp_path,monkeypatch):
    first=tmp_path/'first.png';second=tmp_path/'second.png'
    make_image(first,'good boi');make_image(second,'kind boi')
    first_hash=sha256(first);second_hash=sha256(second)
    def decide(source,token):
        if token==1:return {'action':'recycle_image','source':str(source),'confirmed':True}
        return 's'
    app,artwork,previews=popup_app(tmp_path,monkeypatch,decide)
    def unavailable(source):raise UnsafeFilesystem('Recycle Bin unavailable; retained')
    monkeypatch.setattr(file_actions,'recycle',unavailable)
    result,code=app.process([str(first),str(second)])
    assert code==10 and all(r['state']=='skipped' for r in result['results'])
    assert artwork.sources==[str(first),str(first),str(second)]
    assert sha256(first)==first_hash and sha256(second)==second_hash
    assert not list(tmp_path.glob('*-genderfixed.png'))


def test_delete_final_image_finishes_queue_without_an_extra_prompt(tmp_path,monkeypatch):
    source=tmp_path/'last.png';make_image(source)
    app,artwork,previews=popup_app(tmp_path,monkeypatch,lambda path,token:{
        'action':'recycle_image','source':str(path),'confirmed':True})
    result,code=app.process([str(source)])
    assert code==10 and result['results']==[{'file':str(source),'state':'recycled'}]
    assert result['summary']['remaining']==0 and artwork.sources==[str(source)]
    assert not source.exists()
