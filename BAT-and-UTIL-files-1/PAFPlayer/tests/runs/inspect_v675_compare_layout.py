import importlib.util,sys,tkinter
from pathlib import Path
root=Path(__file__).resolve().parents[2];spec=importlib.util.spec_from_file_location('v675_layout',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_voice_models as models
real=tkinter.Tk
def descend(w):
 for c in w.winfo_children():yield c;yield from descend(c)
def create():
 w=real();w.tk.call('tk','scaling',2.0)
 def inspect():
  w.update_idletasks();print('window',w.winfo_width(),w.winfo_height())
  for c in descend(w):
   if c.winfo_class() in ('Text','TProgressbar','TButton'):
    print(c.winfo_class(),c.cget('text') if c.winfo_class()=='TButton' else '', 'mapped',c.winfo_ismapped(),'x',c.winfo_rootx()-w.winfo_rootx(),'y',c.winfo_rooty()-w.winfo_rooty(),'width',c.winfo_width(),'height',c.winfo_height())
  w.destroy()
 w.after(500,inspect);return w
tkinter.Tk=create;models.launch_window()
