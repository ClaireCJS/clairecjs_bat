import importlib.util,sys,threading,time,tkinter
from pathlib import Path
from unittest import mock
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v675_window',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_voice_models as models
real=tkinter.Tk;started=threading.Event();release=threading.Event();errors=[]
def descendants(widget):
 for child in widget.winfo_children():
  yield child
  yield from descendants(child)
def install(model,progress):
 progress('Downloading example');progress.output('Fetching files: 42%')
 started.set();release.wait(5);return Path('fixture')
def create():
 window=real();window.tk.call('tk','scaling',2.0)
 def begin():
  try:
   window.update_idletasks();widgets=list(descendants(window))
   [w for w in widgets if w.winfo_class()=='TCheckbutton' and w.cget('text')=='Kokoro 82M'][0].invoke()
   [w for w in widgets if w.winfo_class()=='TButton' and w.cget('text')=='Download selected'][0].invoke()
   window.after(400,check)
  except Exception as e:errors.append(e);release.set();window.destroy()
 def check():
  try:
   window.update_idletasks();widgets=list(descendants(window));bars=[w for w in widgets if w.winfo_class()=='TProgressbar'];assert len(bars)==2
   assert started.is_set();assert str(bars[0].cget('mode'))=='determinate';assert float(bars[0].cget('value'))==42
   logs=[w for w in widgets if w.winfo_class()=='Text'];assert 'Fetching files: 42%' in logs[0].get('1.0','end')
   release.set();window.after(400,finish)
  except Exception as e:errors.append(e);release.set();window.destroy()
 def finish():
  try:
   bars=[w for w in descendants(window) if w.winfo_class()=='TProgressbar'];assert float(bars[1].cget('value'))==100
  except Exception as e:errors.append(e)
  window.destroy()
 window.after(300,begin);return window
tkinter.Tk=create
with mock.patch.object(models,'install',side_effect=install):assert models.launch_window()==0
if errors:raise errors[0]
print('Real window displayed streamed output, 42% installer-reported progress, and completed overall progress.')
