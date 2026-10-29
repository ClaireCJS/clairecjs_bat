from PIL import Image
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer.rules import builtins
from dataclasses import asdict

def test_actual_add_substitution_dialog_saves_priority_and_reordered_list(tmp_path):
    from tkinter import ttk
    source=tmp_path/'portrait.png';Image.new('RGB',(200,600),'gray').save(source)
    viewer=AlbumArtReview([{'path':str(source),'title':'Proposal'}],{'detected':'his wife','proposed':'her wife'},floating=True)
    results=[];errors=[]
    def test():
        try:
            if not viewer._has_drawn:viewer.root.after(40,test);return
            viewer.set_review(results.append,[asdict(r) for r in builtins()],False)
            viewer.buttons['add_rule'].invoke();dialog=viewer._dialog
            entries=[w for w in dialog.winfo_children() if isinstance(w,ttk.Entry)]
            for entry,value in zip(entries,['king','queen','75']):entry.delete(0,'end');entry.insert(0,value)
            buttons={w.cget('text'):w for w in dialog.winfo_children() if isinstance(w,ttk.Button)}
            buttons['Preview rule list'].invoke();buttons['↑ Raise'].invoke();buttons['Save and regenerate'].invoke()
            assert len(results)==1 and results[0]['action']=='add_rule'
            payload=results[0]['payload'];assert payload['before']=='king' and payload['priority']==75 and 'new' in payload['order']
        except BaseException as error:errors.append(error)
        finally:viewer.choose('c')
    viewer.root.after(250,test);viewer.show()
    if errors:raise errors[0]

def test_passive_window_keeps_foreground_and_approve_requires_current_render(tmp_path):
    import os,ctypes
    from ctypes import wintypes
    source=tmp_path/'landscape.png';Image.new('RGB',(600,200),'gray').save(source)
    viewer=AlbumArtReview([{'path':str(source),'title':'Proposal'}],{'detected':'old','proposed':'new'},floating=True)
    api=ctypes.windll.user32;api.GetForegroundWindow.restype=wintypes.HWND
    foreground=api.GetForegroundWindow();results=[];errors=[]
    def check():
        try:
            if not viewer._has_drawn:viewer.root.after(40,check);return
            _,own_window,getter,_=viewer._native_window()
            current=api.GetForegroundWindow()
            # A human can switch applications during this desktop test. The
            # preview itself must never be the newly activated window.
            assert current!=own_window or foreground==own_window,(foreground,current,own_window)
            assert getter(own_window,-20)&0x08000000
            viewer.set_review(results.append,[],False);viewer.buttons['a'].invoke()
            viewer.buttons['a'].invoke();assert results==['a']
        except BaseException as error:errors.append(error)
        finally:viewer.choose('c')
    viewer.root.after(250,check);viewer.show()
    if errors:raise errors[0]
