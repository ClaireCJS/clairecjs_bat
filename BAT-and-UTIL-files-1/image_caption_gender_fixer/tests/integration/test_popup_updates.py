"""Native focus invariants across updates after the user has interacted."""
import ctypes
from ctypes import wintypes
import time
import tkinter as tk
from PIL import Image
import pytest
from image_caption_gender_fixer.paf_album_art import AlbumArtReview

def pump(root):
    end=time.monotonic()+.3
    while time.monotonic()<end:root.update();time.sleep(.01)

@pytest.mark.parametrize('state',['visible','hidden','minimized'])
def test_update_after_popup_interaction_preserves_other_window_focus(tmp_path,state):
    first=tmp_path/'one.png';second=tmp_path/'two.png'
    Image.new('RGB',(640,240),'blue').save(first);Image.new('RGB',(240,640),'green').save(second)
    viewer=AlbumArtReview([{'path':str(first),'title':'First'}],{'detected':'first','proposed':'first'},floating=True)
    anchor=tk.Tk();anchor.title('ICGF test console stand-in');anchor.geometry('400x160+20+20')
    api=ctypes.windll.user32;api.GetForegroundWindow.restype=wintypes.HWND
    try:
        viewer.passive_show();pump(viewer.root)
        viewer.set_review(lambda action:None,[],False)
        viewer.activate_on_click() # A prior deliberate click removed NOACTIVATE.
        viewer.proposed_caption.focus_force();pump(viewer.root)
        if state=='hidden':viewer.hide()
        if state=='minimized':viewer.root.iconify()
        anchor.deiconify();anchor.update()
        api.SetForegroundWindow.argtypes=[wintypes.HWND];api.SetForegroundWindow.restype=wintypes.BOOL
        api.SetForegroundWindow(api.GetAncestor(anchor.winfo_id(),2))
        anchor.focus_force();pump(anchor)
        foreground=api.GetForegroundWindow();mouse_activations=viewer._activation.mouse_activations
        # The desktop may deny activating the test stand-in while the human
        # uses another application. Preserve whichever other window owns focus.
        assert foreground!=viewer._native_window()[1]
        viewer.update_image({'path':str(second),'title':'Second'}, {'detected':'second','proposed':'second'})
        pump(viewer.root)
        after=api.GetForegroundWindow();own=viewer._native_window()[1]
        # Other applications/user input may change focus on this live desktop;
        # this popup must not be the window gaining it during the update.
        assert after==foreground or after!=own or viewer._activation.mouse_activations>mouse_activations,(state,foreground,after,own)
        assert viewer._native_window()[2](own,-20)&0x08000000
        assert viewer._has_drawn
        if state=='minimized':assert viewer.root.state()=='iconic'
    finally:
        anchor.destroy();viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_native_activation_attempt_inside_draw_is_vetoed_before_focus_changes(tmp_path):
    from types import SimpleNamespace
    from image_caption_gender_fixer.paf_album_art import _active_artwork_guards
    path=tmp_path/'test.png';Image.new('RGB',(600,200),'gray').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Proposal'}],floating=True)
    anchor=tk.Tk();anchor.title('ICGF focus test anchor');anchor.geometry('400x160+20+20')
    api,own,_,_=viewer._native_window();api.GetForegroundWindow.restype=wintypes.HWND
    api.SetForegroundWindow.argtypes=[wintypes.HWND];api.SetForegroundWindow.restype=wintypes.BOOL
    guard=viewer._activation
    try:
        viewer.passive_show();pump(viewer.root)
        viewer.activate_on_click();anchor.update()
        api.SetForegroundWindow(api.GetAncestor(anchor.winfo_id(),2));anchor.focus_force();pump(anchor)
        api.SetActiveWindow.argtypes=[wintypes.HWND];api.SetActiveWindow.restype=wintypes.HWND
        api.SetActiveWindow(api.GetAncestor(anchor.winfo_id(),2))
        before=api.GetForegroundWindow();blocked=guard.blocked
        original=viewer.backend
        def fit(*args):
            api.SetActiveWindow.argtypes=[wintypes.HWND];api.SetActiveWindow.restype=wintypes.HWND
            api.SetActiveWindow(viewer._native_window()[1])
            api.SetForegroundWindow(viewer._native_window()[1])
            assert api.GetForegroundWindow()==before
            return original.fit(*args)
        viewer.backend=SimpleNamespace(fit=fit,photo=original.photo)
        viewer.draw();assert viewer._has_drawn and guard.blocked>blocked
        assert api.GetForegroundWindow()==before and guard.depth==0
        blocked=guard.blocked;viewer.activate_on_click()
        current=viewer._native_window()[1];api.SetActiveWindow(current)
        api.GetActiveWindow.restype=wintypes.HWND
        assert api.GetActiveWindow()==current and guard.blocked==blocked
    finally:
        anchor.destroy();viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
    assert guard.handle is None and guard.callback is None and guard not in _active_artwork_guards


def test_activation_guard_is_released_when_tk_initialization_fails(monkeypatch):
    from image_caption_gender_fixer import paf_album_art
    before=set(paf_album_art._active_artwork_guards)
    def fail():raise RuntimeError('simulated Tcl initialization failure')
    monkeypatch.setattr(tk,'Tk',fail)
    with pytest.raises(RuntimeError,match='simulated Tcl'):
        AlbumArtReview([{'path':'unused.png','title':'unused'}],floating=True)
    assert paf_album_art._active_artwork_guards==before

