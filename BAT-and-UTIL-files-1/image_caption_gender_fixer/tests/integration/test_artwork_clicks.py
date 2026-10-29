"""Real Tk gesture dispatch, comparison state and two-second tooltip timing."""
from types import SimpleNamespace
from PIL import Image
import pytest
from image_caption_gender_fixer.paf_album_art import AlbumArtReview


def pump(viewer,milliseconds):
    viewer.root.after(milliseconds,viewer.root.quit)
    viewer.root.mainloop()
    assert viewer._callback_error is None


@pytest.fixture
def review(tmp_path):
    before=tmp_path/'before.png';after=tmp_path/'after.png'
    Image.new('RGB',(500,500),'navy').save(before)
    Image.new('RGB',(500,500),'teal').save(after)
    viewer=AlbumArtReview([{'path':str(after),'title':'Complete proposed corrected image'}],
                          {'detected':'old caption','proposed':'new caption'},floating=True)
    try:
        viewer.root.geometry('1000x700+16+16');viewer.passive_show()
        pump(viewer,180)
        viewer.set_review(lambda _:None,[],False,changes=[{'index':0,'before':'old','after':'new'}],source=str(before))
        yield viewer,before,after
    finally:
        viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def selected(viewer):return viewer.views[viewer.selector.current()]['path']


def test_single_click_toggles_complete_versions_and_keeps_caption_draft(review):
    viewer,before,after=review;art=viewer.artwork_clicks
    viewer.proposed_caption.insert('end',' edited');viewer.caption_modified()
    assert selected(viewer)==str(after)
    art.click();pump(viewer,art.click_ms+100)
    assert selected(viewer)==str(before)
    art.click();pump(viewer,art.click_ms+100)
    assert selected(viewer)==str(after)
    assert viewer.proposed_caption.get('1.0','end-1c')=='new caption edited'
    assert viewer._dirty and viewer.buttons['a'].instate(['disabled'])


@pytest.mark.parametrize('initial',[0,1])
def test_actual_triple_click_opens_displayed_version_once_without_toggling(review,monkeypatch,initial):
    from image_caption_gender_fixer import paf_album_art
    viewer,before,after=review;viewer.selector.current(initial);opened=[]
    monkeypatch.setattr(viewer,'activate_on_click',lambda event:None)
    monkeypatch.setattr(paf_album_art.os,'startfile',lambda path,operation:opened.append((path,operation)))
    expected=selected(viewer)
    for stamp in (1000,1100,1200):
        viewer.canvas.event_generate('<ButtonPress-1>',x=20,y=20,time=stamp)
        viewer.canvas.event_generate('<ButtonRelease-1>',x=20,y=20,time=stamp+1)
        viewer.root.update()
    assert opened==[(expected,'open')]
    pump(viewer,viewer.artwork_clicks.click_ms+100)
    assert selected(viewer)==expected and len(opened)==1


def test_double_click_does_not_open_viewer(review,monkeypatch):
    viewer,before,after=review;opened=[]
    monkeypatch.setattr(viewer,'activate_on_click',lambda event:None)
    monkeypatch.setattr(viewer,'open_default_viewer',lambda event=None:opened.append(True))
    for stamp in (2000,2100):
        viewer.canvas.event_generate('<ButtonPress-1>',x=30,y=30,time=stamp)
        viewer.canvas.event_generate('<ButtonRelease-1>',x=30,y=30,time=stamp+1)
        viewer.root.update()
    assert not opened
    pump(viewer,viewer.artwork_clicks.click_ms+100)
    assert not opened and selected(viewer)==str(before)


def test_tooltip_waits_two_seconds_explains_gestures_and_clears_on_leave(review):
    viewer,_,_=review;art=viewer.artwork_clicks
    event=SimpleNamespace(x_root=viewer.canvas.winfo_rootx()+40,y_root=viewer.canvas.winfo_rooty()+40)
    focused=viewer.root.focus_get()
    art.enter(event);pump(viewer,1800)
    assert art.tooltip is None
    pump(viewer,300)
    assert art.tooltip is not None and art.tooltip.winfo_viewable()
    help_text=art.tooltip.winfo_children()[0].cget('text')
    assert 'Single click: toggle Before / After' in help_text and 'Triple click:' in help_text
    assert viewer.root.focus_get()==focused
    art.leave();assert art.tooltip is None and art.hover_timer is None


def test_new_image_cancels_pending_toggle_and_forgets_previous_pair(review,tmp_path):
    viewer,_,_=review;art=viewer.artwork_clicks
    path=tmp_path/'next.png';Image.new('RGB',(500,500),'gray').save(path)
    art.click()
    viewer.update_image({'path':str(path),'title':'Original — fitting needs review'},{'detected':'next','proposed':'next'})
    viewer.set_review(lambda _:None,[],True,changes=[],source=str(path))
    assert art.click_timer is None and art.pair is None
    art.click();pump(viewer,art.click_ms+100)
    assert selected(viewer)==str(path) and len(viewer.views)==1


def test_hiding_artwork_cancels_click_and_tooltip_timers(review):
    viewer,_,_=review;art=viewer.artwork_clicks
    art.enter(SimpleNamespace(x_root=40,y_root=40));art.click()
    viewer.hide()
    assert art.click_timer is None and art.hover_timer is None and art.tooltip is None
