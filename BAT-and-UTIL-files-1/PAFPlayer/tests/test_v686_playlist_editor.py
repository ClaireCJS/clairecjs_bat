import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('playlist_v686', ROOT / 'src' / 'PAFPlayer_playlist_window.py')
view = importlib.util.module_from_spec(spec); spec.loader.exec_module(view)

class PlaylistEditorTests(unittest.TestCase):
    def test_reorder_keeps_duplicates_and_other_slots(self):
        self.assertEqual(['a', 'b', 'a', 'c'], view.move_row(['a', 'a', 'b', 'c'], 1, 2))
        self.assertEqual(['c', 'a', 'b'], view.move_row(['a', 'b', 'c'], 2, 0))
        with self.assertRaises(ValueError): view.move_row(['a'], 0, 1)

    def test_metadata_prefers_artist_and_title_and_falls_back(self):
        class Media:
            tags = {'artist': ['Band'], 'title': ['Song']}
            info = type('Info', (), {'length': 125.5})()
            def get(self, key, default=None): return self.tags.get(key, default)
        with mock.patch.dict(sys.modules, {'mutagen': type('Mutagen', (), {'File': staticmethod(lambda *a, **k: Media())})()}):
            self.assertEqual(('Band - Song', '2:05'), view.metadata_display('track.mp3'))
        with mock.patch.dict(sys.modules, {'mutagen': type('Mutagen', (), {'File': staticmethod(lambda *a, **k: None)})()}):
            self.assertEqual(('track.mp3', '--:--'), view.metadata_display('track.mp3'))

    @unittest.skipUnless(os.name == 'nt', 'Windows Tk interaction')
    def test_drag_and_jump_in_real_tk_window(self):
        code = r'''
import sys,time,threading,tkinter as tk
sys.path.insert(0,'src')
import PAFPlayer_playlist_window as m
m.metadata_display=lambda path: ('Artist' + path[-5] + ' - Song', '1:00')
paths=['track1.mp3','track2.mp3','track3.mp3']; errors=[]
w=m.PlaylistWindow(lambda: (paths, paths[0]), {'.mp3'})
original=tk.Tk

def factory():
 root=original()
 def check():
  try:
   def descendants(widget):
    for child in widget.winfo_children():
     yield child
     yield from descendants(child)
   rows=next(x for x in descendants(root) if isinstance(x,tk.Listbox))
   root.update(); a=rows.bbox(0); b=rows.bbox(2)
   assert a and b,(a,b)
   rows.event_generate('<ButtonPress-1>',x=20,y=a[1]+4)
   rows.event_generate('<B1-Motion>',x=20,y=b[1]+4)
   rows.event_generate('<ButtonRelease-1>',x=20,y=b[1]+4)
   move=w.events.get_nowait(); assert move[0]=='move' and move[1][1:]==(0,2),move
   rows.focus_force();root.update();rows.event_generate('<KeyPress-j>');root.update()
   dialog=next(x for x in root.winfo_children() if isinstance(x,tk.Toplevel))
   entry=next(x for x in dialog.winfo_children() if isinstance(x,tk.Entry))
   box=next(x for x in dialog.winfo_children() if isinstance(x,tk.Listbox))
   entry.insert(0,'artist2');root.update(); assert box.size()==1,box.get(0,'end')
   entry.focus_force();root.update();entry.event_generate('<Return>');root.update()
   play=w.events.get_nowait();assert play==('play','track2.mp3'),play
  except BaseException as e: errors.append(repr(e))
  finally: w.close()
 root.after(1300,check);return root
tk.Tk=factory
w.toggle();w.thread.join(10)
assert not w.thread.is_alive(), 'window did not close'
assert not errors,errors
'''
        run = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(0, run.returncode, run.stdout + run.stderr)

if __name__ == '__main__': unittest.main()
