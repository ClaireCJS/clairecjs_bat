"""Real close protocol, fresh image, and clean worker restart."""
import gc
import threading
from PIL import Image
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer.floating_artwork import FloatingArtwork
from test_images import ROOT


def test_close_reopens_on_next_image_without_restarting_worker(tmp_path,monkeypatch):
    gc.collect() # Dispose main-thread Tk cycles before starting another owner.
    paths=[tmp_path/f'{i}.png' for i in range(3)]
    for i,path in enumerate(paths):Image.new('RGB',(120+i*10,200),'navy').save(path)
    states=[];closed=threading.Event();original=AlbumArtReview.update_image
    def update(viewer,view,captions):
        if view['path']==str(paths[1]):
            # Run the actual window-manager close protocol, rather than destroy.
            viewer.root.tk.call(viewer.root.protocol('WM_DELETE_WINDOW'))
            states.append(viewer.root.state());closed.set()
        original(viewer,view,captions)
        states.append(viewer.root.state())
    monkeypatch.setattr(AlbumArtReview,'update_image',update)
    art=FloatingArtwork(ROOT)
    try:
        art.update(paths[0],'First');thread=art.thread
        art.update(paths[1],'After close')
        assert closed.is_set() and states[-2:] == ['withdrawn','normal']
        assert art.thread is thread and art.last_path==str(paths[1])
        art.close();assert art.stopped.is_set()
        stale=art.begin_review(False,[]);art.actions.put((stale,'a'))
        art.update(paths[2],'Reopened after worker shutdown')
        assert art.thread is not thread and art.thread.is_alive()
        assert art.review_token is None and art.review_action(stale) is None
        assert art.last_path==str(paths[2])
    finally:art.close()


def test_fit_button_requests_new_render_and_cannot_approve_blocked(tmp_path):
    gc.collect();path=tmp_path/'preview.png';Image.new('RGB',(120,200),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Blocked'}],floating=True)
    actions=[]
    try:
        viewer.set_review(actions.append,[],True,changes=[{'index':0,'before':'old','after':'new'}])
        assert str(viewer.buttons['m']['state'])=='normal'
        viewer.buttons['m'].invoke();assert actions==[{'action':'fit_all'}]
        viewer.choose('a');assert actions==[{'action':'fit_all'}]
        viewer.set_review(actions.append,[],False)
        assert str(viewer.buttons['m']['state'])=='normal'
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
