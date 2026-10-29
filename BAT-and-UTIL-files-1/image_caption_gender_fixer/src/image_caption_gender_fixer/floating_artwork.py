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
        self.dialog_actions=queue.Queue();self.dialog_token=None
        self._review_spec=None;self._dialog_spec=None;self.last_view=None;self.last_captions=None

    def update(self,path,title,captions=None):
        view={'path':str(path),'title':str(title)};ack=threading.Event()
        self.last_view=dict(view);self.last_captions=captions
        # A closed/halted worker is restarted only on a new preview request.
        # Do not carry stale review buttons or acknowledgements into that GUI.
        if self.thread is not None and self.stopped.is_set() and not self.error:
            self.thread.join(15)
            if self.thread.is_alive():
                raise DependencyUnavailable('Previous artwork window is still shutting down.')
            self.thread=None;self.commands=queue.Queue();self.actions=queue.Queue()
            self.ready=threading.Event();self.stopped=threading.Event()
            self.review_token=None;self.last_path=None;self.dialog_token=None
            self.dialog_actions=queue.Queue();self._review_spec=None;self._dialog_spec=None
        if self.error and self.thread is not None:
            self.close();self.error=None
            self.thread=None;self.ready=threading.Event();self.stopped=threading.Event()
            self.commands=queue.Queue();self.actions=queue.Queue();self.dialog_actions=queue.Queue()
            self.review_token=None;self.dialog_token=None;self._review_spec=None;self._dialog_spec=None
        if self.thread is None:
            self.thread=threading.Thread(target=self._gui_main,args=(view,captions),
                                         name='icgf-floating-artwork',daemon=False)
            self.thread.start()
        if not self._wait(self.ready) or self.error or self.stopped.is_set():
            raise DependencyUnavailable('Floating artwork window could not start: '+str(self.error or 'startup timeout'))
        self.commands.put(('image',view,captions,ack))
        if not self._wait(ack) or self.error or self.stopped.is_set():
            raise DependencyUnavailable('Floating artwork window could not display the latest image: '+str(self.error or 'render timeout'))
        self.last_path=str(path)

    def _wait(self,event):
        import time
        deadline=time.monotonic()+15
        while not event.wait(min(.05,max(0,deadline-time.monotonic()))):
            if self.error or self.stopped.is_set() or time.monotonic()>=deadline:return False
        return True

    def begin_review(self,blocked,rules,notes=(),changes=(),source=None):
        token=uuid.uuid4().hex;self.review_token=token
        self._review_spec=(bool(blocked),[asdict(r) for r in rules],list(notes),list(changes),source)
        self.commands.put(('review',token,*self._review_spec))
        return token

    def review_action(self,token):
        while True:
            try:current,action=self.actions.get_nowait()
            except queue.Empty:return None
            if current==token and token==self.review_token:return action

    def end_review(self,token):
        if self.review_token==token:
            self.review_token=None;self._review_spec=None;self.commands.put(('review',None,False,[],[],[],None))

    def begin_dialog(self,spec):
        token=uuid.uuid4().hex;self.dialog_token=token;self._dialog_spec=spec
        self.commands.put(('dialog',token,spec));return token

    def dialog_action(self,token):
        while True:
            try:current,value=self.dialog_actions.get_nowait()
            except queue.Empty:return None
            if current==token and token==self.dialog_token:return (value,)

    def end_dialog(self,token):
        if token==self.dialog_token:
            self.dialog_token=None;self._dialog_spec=None;self.commands.put(('dialog',None,None))

    def reopen(self,activate=False):
        if self.last_view is None:raise DependencyUnavailable('No preview image is available yet.')
        if self.thread is None or not self.thread.is_alive() or self.error or self.stopped.is_set():
            if self.thread is not None and self.thread.is_alive():self.close()
            review,review_token=self._review_spec,self.review_token
            dialog,dialog_token=self._dialog_spec,self.dialog_token
            view,captions=dict(self.last_view),self.last_captions
            self.thread=None;self.error=None;self.ready=threading.Event();self.stopped=threading.Event()
            self.commands=queue.Queue();self.actions=queue.Queue();self.dialog_actions=queue.Queue()
            self.update(view['path'],view['title'],captions)
            self._review_spec,self.review_token=review,review_token
            self._dialog_spec,self.dialog_token=dialog,dialog_token
            if review is not None:self.commands.put(('review',review_token,*review))
            if dialog is not None:self.commands.put(('dialog',dialog_token,dialog))
        ack=threading.Event();self.commands.put(('show',bool(activate),ack))
        if not self._wait(ack) or self.error or self.stopped.is_set():
            raise DependencyUnavailable('Artwork could not reopen: '+str(self.error or 'window timeout'))

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
                        if command[0]=='show':
                            _,activate,ack=command;viewer.reopen(activate);ack.set();continue
                        if command[0]=='dialog':
                            _,token,spec=command
                            callback=(lambda value,token=token:self.dialog_actions.put((token,value))) if token else None
                            viewer.set_dialog(spec,callback);continue
                        if command[0]=='review':
                            _,token,blocked,rules,notes,changes,source=command
                            callback=(lambda action,token=token:self.actions.put((token,action))) if token else None
                            viewer.set_review(callback,rules,blocked,notes,changes,source);continue
                        _,view,text,ack=command
                        viewer.update_image(view,text)
                        def acknowledge(ack=ack):
                            if viewer.blocked:
                                self.error='Image preview did not render: '+str(getattr(viewer,'_render_error','unknown image error'))
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
            self.error=type(error).__name__+': '+str(error)
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
