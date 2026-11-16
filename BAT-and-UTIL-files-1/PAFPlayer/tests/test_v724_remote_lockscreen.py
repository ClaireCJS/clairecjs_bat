import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
from unittest import mock
from urllib.error import HTTPError
from urllib.request import build_opener, ProxyHandler

ROOT=Path(__file__).resolve().parents[1]
import PAFPlayer as app
import PAFPlayer_remote_lockscreen as lockscreen
import PAFPlayer_lockscreen as local

class Settings:
    def __init__(self): self.values={}
    def load_player_settings(self): return dict(self.values)
    def save_player_settings(self, values): self.values.update(values)

class Remote:
    def __init__(self):
        self._lock=threading.RLock();self.connected=True;self.owner_identity='remote-one';self.clock_offset=0
        self._state={'program':'PAFPlayer','version':'V723','playing':True,'paused':False,'lyric_clock_epoch':100,
                     'lyric_position_seconds':11,'position_seconds':11,'duration_seconds':180,
                     'metadata':{'Artist':'Artist','Song':'Track','Album':'Album'},
                     'lyric_timeline':[[1,'First'],[10,'Second'],[20,'Third']]}

class Process:
    def __init__(self): self.closed=False
    def poll(self): return 0 if self.closed else None
    def close(self): self.closed=True

def wait_for(condition):
    end=time.monotonic()+5
    while time.monotonic()<end:
        if condition(): return True
        time.sleep(.03)
    return False

class RemoteLockTests(unittest.TestCase):
    def test_payload_verifies_owner_advances_lyric_and_rejects_disconnect(self):
        remote=Remote()
        result=lockscreen.status_payload(remote,'local-lease','remote-one',True,now=101)
        self.assertEqual('local-lease',result['identity'])
        self.assertEqual('Second',result['state']['lyric'])
        self.assertEqual('First',result['state']['lyric_previous'])
        self.assertEqual(12,result['state']['position_seconds'])
        self.assertTrue(result['state']['lockscreen_show_version'])
        self.assertIsNone(lockscreen.status_payload(remote,'local-lease','different'))
        remote.connected=False
        self.assertIsNone(lockscreen.status_payload(remote,'local-lease','remote-one'))

    def test_bridge_is_opt_in_loopback_and_recovers_owner_changes(self):
        remote=Remote();settings=Settings(); settings.values[lockscreen.RemoteLockScreen.KEY]=False; launched=[]
        def launch(url, identity):
            proc=Process();launched.append((url,identity,proc));return proc
        controller=lockscreen.RemoteLockScreen(remote,settings,launcher=launch, inspector=lambda: ('530.0.0.0','530.0.0.0',True,None))
        opener=build_opener(ProxyHandler({}))
        with mock.patch.object(local,'installed_version',return_value=local.EMBEDDED_INSTALL_VERSION):
            controller.start()
            try:
                self.assertEqual('127.0.0.1',controller.httpd.server_address[0])
                self.assertFalse(controller.enabled()); self.assertFalse(launched)
                controller.set_option(controller.KEY,True)
                self.assertTrue(wait_for(lambda: bool(launched)))
                url=launched[0][0]+'/api/remote-tray/hello?lockscreen=1'
                self.assertEqual(launched[0][1],json.load(opener.open(url,timeout=3))['identity'])
                remote.connected=False
                with self.assertRaises(HTTPError) as error:opener.open(url,timeout=3)
                self.assertEqual(503,error.exception.code)
                remote.connected=True;remote.owner_identity='remote-two';controller.wake.set()
                self.assertTrue(wait_for(lambda: len(launched)==2))
                self.assertTrue(launched[0][2].closed)
                self.assertNotEqual(launched[0][1],launched[1][1])
                self.assertEqual(launched[1][1],json.load(opener.open(url,timeout=3))['identity'])
                controller.set_option(controller.KEY,False)
                self.assertTrue(wait_for(lambda: launched[1][2].closed))
                with self.assertRaises(HTTPError):opener.open(url,timeout=3)
            finally: controller.close()
        self.assertFalse(controller.thread.is_alive())
        self.assertFalse(controller.http_thread.is_alive())

    def test_embedded_sources_match(self):
        tree=ast.parse((ROOT/'PAFPlayer.py').read_text(encoding='utf-8-sig'))
        for name in ('PAFPlayer_remote_tray','PAFPlayer_remote_lockscreen'):
            values=[]
            for node in tree.body:
                if not isinstance(node,ast.Assign):continue
                for target in node.targets:
                    if isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='_PAF_BUNDLED_SOURCES' and isinstance(target.slice,ast.Constant) and target.slice.value==name:values.append(ast.literal_eval(node.value))
                    if isinstance(target,ast.Name) and target.id=='_PAF_BUNDLED_SOURCES' and isinstance(node.value,ast.Dict):
                        for key,value in zip(node.value.keys,node.value.values):
                            if isinstance(key,ast.Constant) and key.value==name:values.append(ast.literal_eval(value))
            self.assertTrue(values,name)
            self.assertEqual((ROOT/'src'/f'{name}.py').read_text(encoding='utf-8-sig'),values[-1])

    @unittest.skipUnless(os.name=='nt','Windows Tk setup')
    def test_setup_window_explains_steps_without_installing(self):
        code=r'''
import sys,threading,tkinter as tk
sys.path.insert(0,'.');import PAFPlayer
from PAFPlayer_remote_lockscreen import setup_dialog
class C:
 KEY='e';VERSION_KEY='v';status='Off';install_message='';install_busy=False
 def enabled(self):return False
 def show_version(self):return False
 def install_async(self):raise AssertionError('must not install automatically')
 def set_option(self,*args):raise AssertionError('must not change settings automatically')
orig=tk.Tk
class Checked(tk.Tk):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw)
  def check():
   def walk(w):
    for c in w.winfo_children():yield c;yield from walk(c)
   widgets=list(walk(self));texts=[str(w.cget('text')) for w in widgets if 'text' in w.keys()]
   guides=[w.get('1.0','end') for w in widgets if isinstance(w,tk.Text)]
   assert any('Windows+L' in t and 'Windows 10' in t for t in guides),guides
   assert any('Install or repair' in t for t in texts),texts
   assert any('Open Windows settings' in t for t in texts),texts
   self.destroy()
  self.after(500,check)
tk.Tk=Checked
setup_dialog(C(),threading.Event())
'''
        result=subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
