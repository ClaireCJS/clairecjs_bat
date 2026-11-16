import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('playlist_v696', ROOT / 'src' / 'PAFPlayer_playlist_window.py')
view = importlib.util.module_from_spec(spec); spec.loader.exec_module(view)

class SelectionTests(unittest.TestCase):
    def test_group_reorder_and_duplicate_remap(self):
        self.assertEqual((['b','d','a','c','e'], (0,1)), view.move_rows(['a','b','c','d','e'], [1,3], 0))
        self.assertEqual((['a','c','e','b','d'], (3,4)), view.move_rows(['a','b','c','d','e'], [1,3], 4))
        self.assertEqual((0,2), view.remap_selection(['x','y','x'], ['x','y','x','z'], [0,2]))
        self.assertEqual((1,), view.remap_selection(['x','x','y'], ['y','x','x'], [0]))

    @unittest.skipUnless(os.name == 'nt', 'Windows Tk interaction')
    def test_modifier_clicks_survive_refresh_and_group_drag(self):
        code = r'''
import sys,time,tkinter as tk
sys.path.insert(0,'src')
import PAFPlayer_playlist_window as m
m.metadata_display=lambda path:(time.sleep(.02) or path,'1:00')
m.metadata_extra=lambda path,last_played=None:{}
paths=['a.mp3','b.mp3','c.mp3','d.mp3','e.mp3','f.mp3'];current=[paths[0]];errors=[]
w=m.PlaylistWindow(lambda:(paths,current[0]),{'.mp3'})
orig=tk.Tk

def factory():
 root=orig()
 def step1():
  try:
   def desc(widget):
    for child in widget.winfo_children():
     yield child;yield from desc(child)
   rows=next(x for x in desc(root) if isinstance(x,tk.Listbox));root.update()
   def click(i,state=0):
    box=rows.bbox(i);assert box,(i,rows.size()); y=box[1]+4
    rows.event_generate('<ButtonPress-1>',x=15,y=y,state=state)
    rows.event_generate('<ButtonRelease-1>',x=15,y=y,state=state)
   click(1);click(4,1);assert rows.curselection()==(1,2,3,4),rows.curselection()
   click(2,4);assert rows.curselection()==(1,3,4),rows.curselection()
   current[0]=paths[1]
   def step2():
    try:
     assert rows.curselection()==(1,3,4),('refresh',rows.curselection())
     click(5,1);assert rows.curselection()==(2,3,4,5),('anchor',rows.curselection())
     start=rows.bbox(3)[1]+4;end=rows.bbox(0)[1]+4
     rows.event_generate('<ButtonPress-1>',x=15,y=start)
     rows.event_generate('<B1-Motion>',x=15,y=end)
     rows.event_generate('<ButtonRelease-1>',x=15,y=end)
     kind,value=w.events.get_nowait();assert kind=='move' and value[1:]==((2,3,4,5),0),(kind,value)
     paths[:],selected=m.move_rows(paths,value[1],value[2])
     def step3():
      try:
       assert rows.curselection()==selected,('after drag',rows.curselection(),selected)
       rows.event_generate('<Return>');assert w.events.empty(),list(w.events.queue)
      except BaseException as e:errors.append(repr(e))
      finally:w.close()
     root.after(800,step3)
    except BaseException as e:errors.append(repr(e));w.close()
   root.after(800,step2)
  except BaseException as e:errors.append(repr(e));w.close()
 root.after(700,step1);return root
tk.Tk=factory
w.toggle();w.thread.join(12)
assert not w.thread.is_alive(),'window did not close'
assert not errors,errors
'''
        result = subprocess.run([sys.executable, '-B', '-c', code], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

if __name__ == '__main__': unittest.main()
