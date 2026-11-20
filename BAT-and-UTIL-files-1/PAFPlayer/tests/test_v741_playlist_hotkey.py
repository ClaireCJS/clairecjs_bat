import os
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
import PAFPlayer as app

class PlaylistHotkeyTests(unittest.TestCase):
    def test_decoded_ctrl_alt_p_and_existing_shortcuts(self):
        for first,extended in [('p',None),('P',None),('\x10',None),('\x00','\x19'),('\xe0','\x19')]:
            with self.subTest(first=first,extended=extended):
                self.assertEqual(app.PLAYLIST_WINDOW_TOGGLE, app.interpret_console_key(first,extended=extended,ctrl=True,alt=True))
        self.assertEqual(app.PLAYLIST_WINDOW_TOGGLE,app.interpret_console_key('p',alt=True))
        self.assertEqual(app.PROGRESS_STYLE_NEXT,app.interpret_console_key('p'))
        self.assertEqual(app.PROGRESS_STYLE_PREVIOUS,app.interpret_console_key('P',shift=True))
        self.assertNotEqual(app.PLAYLIST_WINDOW_TOGGLE,app.interpret_console_key('\x10',ctrl=True))

    def test_focus_gate_and_modifier_loss_on_buffered_control_byte(self):
        held={0x11,0x12,0x50};chars=['\x10']
        def getwch():
            held.discard(0x11);held.discard(0x12)
            return chars.pop(0)
        console=types.SimpleNamespace(kbhit=lambda:bool(chars),getwch=getwch)
        with mock.patch.dict(sys.modules,{'msvcrt':console}), \
             mock.patch.object(app,'_windows_key_down',side_effect=lambda code:code in held), \
             mock.patch.object(app,'control_hotkeys_enabled',return_value=False), \
             mock.patch.object(app,'test_tone_enabled',return_value=False), \
             mock.patch.object(app,'_GLOBAL_SEEK_CAPTURE',None):
            self.assertEqual(app.PLAYLIST_WINDOW_TOGGLE,app.read_windows_key_action())
            held.update((0x11,0x12,0x50))
            self.assertIsNone(app.read_windows_key_action())

    @unittest.skipUnless(os.name=='nt','Windows Tk interaction')
    def test_ctrl_alt_p_closes_focused_playlist(self):
        code=r'''
import sys,tkinter as tk
sys.path.insert(0,'src')
from PAFPlayer_playlist_window import PlaylistWindow
seen=[];errors=[]
w=PlaylistWindow(lambda:(['one.mp3'], 'one.mp3'),{'.mp3'},trace=lambda event,**fields:seen.append((event,fields)))
orig=tk.Tk
def factory():
 root=orig()
 def exercise():
  try:
   root.focus_force();root.update();root.event_generate('<Control-Alt-KeyPress-p>')
  except BaseException as e:errors.append(repr(e));w.close()
 root.after(900,exercise);return root
tk.Tk=factory
w.toggle();w.thread.join(7)
assert not w.thread.is_alive(),'shortcut did not close window'
assert not errors,errors
assert ('playlist-window.close',{'reason':'ctrl-alt-p'}) in seen,seen
'''
        result=subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,capture_output=True,text=True,timeout=15)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
