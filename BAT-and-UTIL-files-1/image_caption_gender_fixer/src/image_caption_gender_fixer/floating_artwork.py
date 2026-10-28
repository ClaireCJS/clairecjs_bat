r"""ICGF adaptation of PAFPlayer's floating artwork thread/queue ownership.

Origin: C:\BAT\PAFPlayer\PAFPlayer.py, ExternalAlbumArtWindow._ensure_started,
_gui_thread_entry, and _gui_main (V567). This is an explicitly marked copy/
adaptation of its non-daemon GUI-thread, queue, shutdown, and owner-thread garbage
collection pattern. Pixel fitting/photo routines bind to the installed sibling
PAFPlayer first; attributed internal copies are the fallback.
No Tk object crosses back to the console thread. Program shutdown joins this
worker, so the calling shell cannot return while its floating window still lives.
"""
import gc
from pathlib import Path
import queue
import threading
import uuid
from dataclasses import asdict

from .errors import DependencyUnavailable
from .paf_backend import get_backend


class FloatingArtwork:
    def __init__(self,root):
        self.root=Path(root);self.backend=get_backend(root)
        self.commands=queue.Queue();self.thread=None
        self.ready=threading.Event();self.stopped=threading.Event()
        self.error=None;self.last_path=None
        self.actions=queue.Queue();self.review_token=None

    def update(self,path,title,captions=None):
        view={'path':str(path),'title':str(title)};ack=threading.Event()
        if self.thread is None:
            self.thread=threading.Thread(target=self._gui_main,args=(view,captions),
                                         name='icgf-floating-artwork',daemon=False)
            self.thread.start()
        if not self.ready.wait(15) or self.error or self.stopped.is_set():
            raise DependencyUnavailable('Floating artwork window could not start: '+str(self.error or 'startup timeout'))
        self.commands.put(('image',view,captions,ack))
        if not ack.wait(15) or self.error or self.stopped.is_set():
            raise DependencyUnavailable('Floating artwork window could not display the latest image: '+str(self.error or 'render timeout'))
        self.last_path=str(path)

    def begin_review(self,blocked,rules,notes=()):
        token=uuid.uuid4().hex;self.review_token=token
        self.commands.put(('review',token,bool(blocked),[asdict(r) for r in rules],list(notes)))
        return token

    def review_action(self,token):
        while True:
            try:current,action=self.actions.get_nowait()
            except queue.Empty:return None
            if current==token and token==self.review_token:return action

    def end_review(self,token):
        if self.review_token==token:
            self.review_token=None;self.commands.put(('review',None,False,[],[]))

    def _gui_main(self,initial,captions):
        from .paf_album_art import AlbumArtReview
        viewer=None
        try:
            viewer=AlbumArtReview([initial],captions,inspect_only=True,floating=True,backend=self.backend)
            def poll():
                try:
                    while True:
                        command=self.commands.get_nowait()
                        if command[0]=='stop': viewer.choose('c');return
                        if command[0]=='review':
                            _,token,blocked,rules,notes=command
                            callback=(lambda action,token=token:self.actions.put((token,action))) if token else None
                            viewer.set_review(callback,rules,blocked,notes);continue
                        _,view,text,ack=command
                        viewer.update_image(view,text)
                        def acknowledge(ack=ack):
                            if viewer.blocked:
                                self.error='Image preview did not render'
                            elif not viewer._has_drawn:
                                # A busy desktop may delay the debounced draw.
                                # Acknowledge the completed image, not a timer.
                                viewer.root.after(25,acknowledge);return
                            ack.set()
                        viewer.root.after(140,acknowledge)
                except queue.Empty: pass
                viewer.root.after(50,poll)
            viewer.root.after(0,poll);self.ready.set()
            viewer.show()
        except BaseException as error:
            self.error=type(error).__name__
            self.ready.set()
        finally:
            # PAFPlayer's owner-thread cleanup pattern prevents Tcl_AsyncDelete
            # when Tk/ImageTk cycles would otherwise be finalized elsewhere.
            viewer=None
            gc.collect()
            self.stopped.set()

    def close(self):
        if self.thread is None: return
        if self.thread.is_alive():
            self.commands.put(('stop',))
            self.thread.join(15)
        if self.thread.is_alive():
            raise DependencyUnavailable('Floating artwork shutdown has not completed; renderer remains alive.')
