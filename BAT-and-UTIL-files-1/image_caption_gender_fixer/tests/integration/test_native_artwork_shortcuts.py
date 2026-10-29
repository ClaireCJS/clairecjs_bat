"""Native input records and explicit foreground restoration, isolated from images."""
import ctypes
import json,os,subprocess,sys
from pathlib import Path
import pytest
from PIL import Image
from test_images import ROOT
from image_caption_gender_fixer import console_input
from image_caption_gender_fixer.paf_album_art import AlbumArtReview


def test_real_windows_key_records_distinguish_both_shortcuts_in_hidden_console():
    source_root=Path(console_input.__file__).parents[1]
    code=r'''
import ctypes,sys,json
from ctypes import wintypes as w
sys.path.insert(0,sys.argv[1])
from image_caption_gender_fixer import console_input as keys
api=ctypes.WinDLL('kernel32',use_last_error=True)
api.CreateFileW.argtypes=[w.LPCWSTR,w.DWORD,w.DWORD,ctypes.c_void_p,w.DWORD,w.DWORD,w.HANDLE]
api.CreateFileW.restype=w.HANDLE
handle=api.CreateFileW('CONIN$',0x80000000|0x40000000,3,None,3,0,None)
assert handle and handle!=w.HANDLE(-1).value,ctypes.get_last_error()
api.SetStdHandle.argtypes=[w.DWORD,w.HANDLE];assert api.SetStdHandle(-10,handle)
keys.native_console.cache_clear();native=keys.native_console();assert native is not None
api,handle,Record=native
api.FlushConsoleInputBuffer.argtypes=[w.HANDLE];assert api.FlushConsoleInputBuffer(handle)
api.WriteConsoleInputW.argtypes=[w.HANDLE,ctypes.POINTER(Record),w.DWORD,ctypes.POINTER(w.DWORD)]
records=(Record*2)()
for index,state in enumerate((8,10)):
    records[index].kind=1;event=records[index].event.key
    event.down=1;event.repeat=1;event.key=0x41;event.char.UnicodeChar='\x01';event.modifiers=state
written=w.DWORD();assert api.WriteConsoleInputW(handle,records,2,ctypes.byref(written)) and written.value==2
assert ctypes.sizeof(Record)==20
values=[keys.read_key(),keys.read_key()]
assert values==[keys.SHOW_ART,keys.FRONT_ART],values
print(json.dumps({'record_size':ctypes.sizeof(Record),'keys':values}))
'''
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    result=subprocess.run([sys.executable,'-B','-I','-S','-c',code,str(source_root)],capture_output=True,text=True,
                          creationflags=subprocess.CREATE_NEW_CONSOLE,startupinfo=startup,timeout=20)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['record_size']==20


def test_bring_to_front_is_reserved_for_explicit_active_reopen(tmp_path,monkeypatch):
    path=tmp_path/'image.png';Image.new('RGB',(200,600),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Review'}],floating=True);calls=[]
    api,_,_,_=viewer._native_window()
    def bring(hwnd):calls.append(('front',hwnd));return 1
    def focus(hwnd):calls.append(('focus',hwnd));return 1
    monkeypatch.setattr(api,'BringWindowToTop',bring);monkeypatch.setattr(api,'SetForegroundWindow',focus)
    try:
        viewer.root.withdraw();viewer.reopen(False)
        assert not calls
        viewer.reopen(True)
        assert [call[0] for call in calls]==['front','focus']
        assert not (viewer._native_window()[2](viewer._native_window()[1],-20)&0x08000000)
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
