import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PlaylistLifetimeTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'nt', 'Windows Tk lifecycle')
    def test_existing_tk_root_and_close_reason(self):
        code = r'''
import sys,time,tkinter as tk
sys.path.insert(0,'src')
from PAFPlayer_playlist_window import PlaylistWindow
other=tk.Tk();other.withdraw(); events=[]
w=PlaylistWindow(lambda: ([],None),{'.mp3'},trace=lambda event,**fields:events.append((event,fields)))
w.toggle();limit=time.monotonic()+2
while time.monotonic()<limit: other.update();time.sleep(.02)
assert w.opening,events
w.close();limit=time.monotonic()+5
while w.thread.is_alive() and time.monotonic()<limit: other.update();time.sleep(.02)
assert not w.thread.is_alive(),events
assert ('playlist-window.close',{'reason':'player-shutdown'}) in events,events
assert not [e for e in events if e[0] in ('playlist-window.failure','playlist-window.callback-error')],events
other.destroy()
'''
        run = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)

if __name__ == '__main__': unittest.main()
