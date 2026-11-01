"""Approval delivery, visible progress, and advancement through real GUI reviews."""
import time
from pathlib import Path
import pytest
from PIL import Image
from test_images import ROOT,app_for,make_image
from test_delete_continue import popup_app
from image_caption_gender_fixer import adjustment_menu,paf_album_art
from image_caption_gender_fixer.fs import sha256
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.paf_album_art import AlbumArtReview


def test_approval_is_delivered_before_controls_refresh_and_only_once(tmp_path,monkeypatch):
    source=tmp_path/'neutral.png';Image.new('RGB',(150,250),'navy').save(source)
    viewer=AlbumArtReview([{'path':str(source),'title':'Proposal'}],floating=True);actions=[]
    try:
        viewer.set_review(actions.append,[],False,source=str(source))
        def stalled_controls(*args,**kwargs):raise RuntimeError('simulated GUI refresh failure')
        monkeypatch.setattr(viewer,'set_review',stalled_controls)
        with pytest.raises(RuntimeError,match='simulated GUI refresh failure'):viewer.emit('a')
        assert actions==['a'],'Refreshing GUI controls must not prevent delivery of approval'
        assert viewer._review_callback is None
        viewer.emit('a');assert actions==['a']
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_approve_shows_the_next_source_before_ocr_without_a_continue_prompt(tmp_path,monkeypatch):
    first=tmp_path/'first.png';second=tmp_path/'second.png'
    make_image(first,'good boi');make_image(second,'kind boi')
    first_hash=sha256(first);second_hash=sha256(second)
    app,artwork,previews=popup_app(tmp_path,monkeypatch,lambda path,token:'a' if path==first else 's')
    recognize=app.ocr_lines
    def recognize_checked(source,*args,**kwargs):
        if source==second:
            assert not first.exists() and (tmp_path/'first-genderfixed.png').exists()
            assert previews[-1][0]==second,'A saved correction must immediately advance the artwork'
            assert previews[-1][2]=={}
        return recognize(source,*args,**kwargs)
    monkeypatch.setattr(app,'ocr_lines',recognize_checked)
    result,code=app.process([str(first),str(second)])
    assert code==10 and [r['state'] for r in result['results']]==['committed','skipped']
    assert artwork.sources==[str(first),str(second)] and artwork.ended==[1,2]
    event=next(iter(History(tmp_path).transactions().values()))
    assert sha256(tmp_path/event['backup'])==first_hash and sha256(second)==second_hash
    assert result['summary']['remaining']==0 and not list(tmp_path.glob('.icgf-*.png'))


def test_busy_status_survives_redraw_counts_seconds_and_clears_on_review(tmp_path,monkeypatch):
    source=tmp_path/'neutral.png';Image.new('RGB',(150,250),'navy').save(source)
    viewer=AlbumArtReview([{'path':str(source),'title':'Proposal'}],floating=True)
    clock=[10.0];monkeypatch.setattr(paf_album_art.time,'monotonic',lambda:clock[0])
    try:
        viewer.work_status('Saving approved correction')
        viewer.set_review(None,[],False);viewer.draw()
        assert 'Saving approved correction' in viewer.notice.cget('text')
        clock[0]=22.0;viewer.refresh_work_status()
        assert '12s' in viewer.notice.cget('text')
        viewer.set_review(lambda action:None,[],False)
        ready=viewer.notice.cget('text')
        assert viewer._work_message is None and 'Saving approved correction' not in ready
        clock[0]=50.0;viewer.refresh_work_status();assert viewer.notice.cget('text')==ready
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_real_artwork_approval_saves_and_advances_with_visible_stages(tmp_path,monkeypatch):
    first=tmp_path/'first.png';second=tmp_path/'second.png'
    make_image(first,'good boi');make_image(second,'kind boi');digest=sha256(first)
    app=app_for(tmp_path);app.interactive=True;app.args.no_preview=False
    choices=[];stages=[];deadline=time.monotonic()+30
    original_review=AlbumArtReview.set_review;original_status=AlbumArtReview.work_status
    def review(viewer,*args,**kwargs):
        original_review(viewer,*args,**kwargs)
        callback=args[0] if args else kwargs.get('callback')
        source=viewer._review_source
        if callback and source==str(first) and not choices:
            choices.append('approve');viewer.root.after(20,lambda:viewer.buttons['a'].invoke())
        elif callback and source==str(second) and choices==['approve']:
            choices.append('skip');viewer.root.after(20,lambda:viewer.buttons['s'].invoke())
    def status(viewer,message):
        if message:stages.append(message)
        original_status(viewer,message)
    monkeypatch.setattr(AlbumArtReview,'set_review',review)
    monkeypatch.setattr(AlbumArtReview,'work_status',status)
    monkeypatch.setattr(adjustment_menu,'console_key',lambda:'c' if time.monotonic()>deadline else None)
    try:
        result,code=app.process([str(first),str(second)])
        assert code==10 and [r['state'] for r in result['results']]==['committed','skipped']
        assert choices==['approve','skip']
        assert any('Saving approved' in text for text in stages)
        assert any('Recycling temporary preview' in text for text in stages)
        assert any('Loading next image' in text for text in stages)
        assert app.floating_artwork.error is None
        event=next(iter(History(tmp_path).transactions().values()))
        assert sha256(tmp_path/event['backup'])==digest
    finally:app.close_previews()
