"""Exercise the actual Tk header and browser anchor without playback or preferences."""
import ast
import contextlib
import ctypes
import inspect
import json
import os
from pathlib import Path
import subprocess
import tkinter as tk
import tkinter.font as tkfont
from types import SimpleNamespace as NS
import unittest
from unittest import mock

import PAFPlayer as app

GUI=ast.parse(inspect.getsource(app.ExternalAlbumArtWindow)).body[0]
GUI=next(n for n in GUI.body if isinstance(n,ast.FunctionDef) and n.name=='_gui_main')
def functions(ns,*names):
    for name in names:
        n=next(n for n in GUI.body if isinstance(n,ast.FunctionDef) and n.name==name)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[n],type_ignores=[])),'<production artwork chrome>','exec'),ns)

class HeaderTests(unittest.TestCase):
    def setUp(self):
        self.root=tk.Tk();self.root.withdraw();self.root.overrideredirect(True)
        self.root.geometry('700x300+100+100')
        self.root.configure(bg='#010203');self.root.attributes('-transparentcolor','#010203')
        self.strip=tk.Frame(self.root,height=60);self.strip.pack(fill='x');self.strip.pack_propagate(False);self.strip.grid_propagate(False)
        self.border=tk.Frame(self.root);self.border.pack(fill='both',expand=True)
        self.state={'track_identity':'Necros - Count Me Out','native_hwnd':1,'border_pixels':5,'web_url':'http://127.0.0.1:666/?q=1#old'}
        self.ns=dict(tk=tk,root=self.root,control_strip=self.strip,art_border_frame=self.border,state=self.state,
            contextlib=contextlib,os=os,ctypes=ctypes,webbrowser=mock.Mock(),
            EXTERNAL_ALBUM_ART_TRANSPARENT_KEY='#010203',EXTERNAL_ALBUM_ART_MIN_SIZE=160,
            window_is_active=lambda:True,set_native_focus_chrome=mock.Mock(),
            install_tooltip=mock.Mock(),windows_window_rect=lambda _: (100,100,800,400),
            windows_set_window_rect=mock.Mock(return_value=True),ctrl_is_down=lambda:False,
            apply_art_topmost_setting=mock.Mock(),user_closed_window=mock.Mock(),schedule_focus_chrome_update=mock.Mock())
        functions(self.ns,'open_web_interface','apply_focus_chrome','hide_focus_chrome_immediately','ensure_titlebar_lyrics_button')
        self.ns['ensure_titlebar_lyrics_button']();self.root.deiconify();self.root.update()
        self.state['fit_identity_label']();self.root.update_idletasks()
    def tearDown(self):
        self.root.destroy()
    def test_one_button_next_to_title_with_nearly_full_row_font(self):
        children=self.strip.winfo_children()
        self.assertEqual(['Label','Button'],[w.winfo_class() for w in children])
        label,button=children
        self.assertEqual(label.winfo_y(),0)
        self.assertEqual(label.winfo_height(),self.strip.winfo_height())
        self.assertLessEqual(label.winfo_x()+label.winfo_width(),button.winfo_x())
        font=tkfont.nametofont(label.cget('font'),root=self.root)
        self.assertGreaterEqual(font.metrics('linespace'),self.strip.winfo_height()-6)
        self.assertLessEqual(font.metrics('linespace'),self.strip.winfo_height())
        button.invoke()
        self.ns['webbrowser'].open_new_tab.assert_called_once_with('http://127.0.0.1:666/?q=1#artworkPopupSection')
    def test_long_title_stays_large_ellipsizes_and_cannot_displace_web_button(self):
        label=self.state['identity_label'];before=tkfont.nametofont(label.cget('font'),root=self.root).metrics('linespace')
        self.state['track_identity']='A very long artist and song title '*20
        self.state['fit_identity_label']();self.root.update_idletasks()
        self.assertTrue(label.cget('text').endswith('…'))
        font=tkfont.nametofont(label.cget('font'),root=self.root)
        self.assertEqual(before,font.metrics('linespace'))
        self.assertLessEqual(font.measure(label.cget('text')),label.winfo_width()-14)
        self.assertTrue(self.state['artwork_web_button'].winfo_ismapped())
    def test_focus_roundtrip_hides_only_border_and_preserves_hwnd_geometry(self):
        hwnd=self.root.winfo_id();geometry=self.root.geometry()
        for active in (False,True,False,True):
            self.ns['window_is_active']=lambda value=active:value
            self.ns['apply_focus_chrome']();self.root.update_idletasks()
            self.assertEqual('#909090' if active else '#010203',self.root.cget('background'))
            self.assertEqual(self.root.cget('background'),self.border.cget('background'))
            self.assertTrue(self.strip.winfo_ismapped())
            self.assertEqual((hwnd,geometry),(self.root.winfo_id(),self.root.geometry()))
        self.ns['hide_focus_chrome_immediately']()
        self.assertEqual('#010203',self.root.cget('background'))
        self.assertTrue(self.strip.winfo_ismapped())
    def test_header_drag_and_corner_resize_keep_anchor_and_minimum_size(self):
        # Tk dispatches the installed production handlers; coordinates describe
        # this test's known starting rectangle, never a user's window.
        label=self.state['identity_label']
        label.event_generate('<ButtonPress-1>',x=20,y=20,rootx=130,rooty=130)
        self.root.event_generate('<B1-Motion>',x=40,y=40,rootx=160,rooty=170)
        self.root.event_generate('<ButtonRelease-1>',x=40,y=40,rootx=160,rooty=170)
        self.ns['windows_set_window_rect'].assert_called_with(1,(130,140,830,440))
        self.root.event_generate('<ButtonPress-1>',x=699,y=299,rootx=799,rooty=399)
        self.root.event_generate('<B1-Motion>',x=699,y=299,rootx=200,rooty=200)
        self.root.event_generate('<ButtonRelease-1>',x=699,y=299,rootx=200,rooty=200)
        self.ns['windows_set_window_rect'].assert_called_with(1,(100,100,260,260))

class NativeStyleTests(unittest.TestCase):
    def test_style_setup_uses_private_pointer_safe_api_and_never_clips_region(self):
        user=NS(GetWindowLongPtrW=mock.Mock(return_value=0x000A0390),SetWindowLongPtrW=mock.Mock(),SetWindowPos=mock.Mock())
        dwm=NS(DwmSetWindowAttribute=mock.Mock())
        ns=dict(os=os,ctypes=ctypes,contextlib=contextlib,root=object(),state={},widget_root_hwnd=lambda _:0x123456789)
        functions(ns,'suppress_native_windows_border')
        with mock.patch.object(ctypes,'WinDLL',side_effect=[user,dwm]):
            ns['suppress_native_windows_border']();ns['suppress_native_windows_border']()
        args=user.SetWindowLongPtrW.call_args.args
        self.assertEqual(0x123456789,args[0]);self.assertTrue(args[2]&0x40000)
        self.assertFalse(args[2]&0x20380)
        self.assertEqual(ctypes.c_ssize_t,user.SetWindowLongPtrW.argtypes[-1])
        user.SetWindowPos.assert_called_once()
        self.assertFalse(hasattr(user,'SetWindowRgn'))
    def test_foreground_pointer_does_not_truncate(self):
        getter=mock.Mock(return_value=0x123456789)
        ns=dict(os=os,ctypes=ctypes,contextlib=contextlib,state={'native_hwnd':0x123456789},root=mock.Mock())
        functions(ns,'window_is_active')
        with mock.patch.object(ctypes,'WinDLL',return_value=NS(GetForegroundWindow=getter)):
            self.assertTrue(ns['window_is_active']())
            getter.return_value=0x23456789
            self.assertFalse(ns['window_is_active']())
        self.assertEqual(ctypes.c_void_p,getter.restype)

class WebAnchorTests(unittest.TestCase):
    def test_anchor_selects_artwork_scroller_initially_and_after_hash_change(self):
        source=Path(app.__file__).read_text(encoding='utf-8')
        a=source.index('function setupConfigTabs(){');b=source.index('\nfunction ',a+15)
        script=r'''
const assert=require('node:assert/strict');let raf=[];global.requestAnimationFrame=fn=>{raf.push(fn);return 1};let configTabScrollRaf=0;
global.location={hash:'#artworkPopupSection'};const listeners={};global.window={addEventListener:(k,f)=>listeners[k]=f,removeEventListener:(k,f)=>delete listeners[k]};
const frame={scrollTop:0,clientHeight:200,scrollHeight:2000,getBoundingClientRect:()=>({top:100}),addEventListener:()=>{}};
const bar={offsetHeight:30,appendChild:()=>{},textContent:''};
const section=(id,y)=>({id,hidden:false,compareDocumentPosition:other=>y<other.y?4:2,y,getBoundingClientRect:()=>({top:100+y-frame.scrollTop})});
const elements={choicesFrame:frame,configTabs:bar,playbackMirrorSection:section('playbackMirrorSection',0),artworkPopupSection:section('artworkPopupSection',500)};
global.Node={DOCUMENT_POSITION_FOLLOWING:4};global.document={getElementById:id=>elements[id],createElement:()=>({dataset:{},classList:{toggle:()=>{}},setAttribute:()=>{},scrollIntoView:()=>{},addEventListener:function(k,f){this.fn=f},click:function(){this.fn({preventDefault(){},stopPropagation(){}})}})};
function drain(){for(let i=0;raf.length&&i<20;i++)raf.shift()()}
'''+source[a:b]+r'''
setupConfigTabs();drain();assert.equal(frame.scrollTop,462);
location.hash='#playbackMirrorSection';listeners.hashchange();drain();assert.equal(frame.scrollTop,0);
location.hash='#%';listeners.hashchange();assert.equal(frame.scrollTop,0);
location.hash='#missing';listeners.hashchange();assert.equal(frame.scrollTop,0);
location.hash='#artworkPopupSection';listeners.hashchange();drain();assert.equal(frame.scrollTop,462);
'''
        result=subprocess.run([r'C:\Program Files\nodejs\node.exe','-'],input=script,text=True,capture_output=True,timeout=15)
        self.assertEqual(0,result.returncode,result.stderr)

if __name__=='__main__':unittest.main()
