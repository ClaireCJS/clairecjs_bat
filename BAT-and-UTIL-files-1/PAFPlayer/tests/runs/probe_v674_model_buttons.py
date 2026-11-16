import importlib.util,sys,tkinter,time
from pathlib import Path
from unittest import mock
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v674_window_player',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_voice_models as models
real=tkinter.Tk

def descendants(widget):
 for child in widget.winfo_children():
  yield child
  yield from descendants(child)

for scale in (1.0,2.0,2.5):
 calls=[];errors=[]
 def create():
  window=real();window.tk.call('tk','scaling',scale)
  def inspect():
   try:
    window.update_idletasks();widgets=list(descendants(window))
    buttons={w.cget('text'):w for w in widgets if w.winfo_class()=='TButton'}
    for name in ('Download selected','Compare selected','Close'):
     button=buttons[name];assert button.winfo_ismapped(),(scale,name,'not mapped')
     assert button.winfo_rooty()+button.winfo_height()<=window.winfo_rooty()+window.winfo_height(),(scale,name,'below window')
     assert button.winfo_rootx()+button.winfo_width()<=window.winfo_rootx()+window.winfo_width(),(scale,name,'outside right edge')
    checks=[w for w in widgets if w.winfo_class()=='TCheckbutton' and w.cget('text')=='Kokoro 82M'];assert len(checks)==1
    checks[0].invoke();buttons['Download selected'].invoke()
    deadline=time.monotonic()+5
    def next_action():
     try:
      if buttons['Compare selected'].instate(['disabled']):
       assert time.monotonic()<deadline,'download callback did not finish';window.after(50,next_action);return
      buttons['Compare selected'].invoke()
      def finish():
       try:
        if buttons['Download selected'].instate(['disabled']):
         assert time.monotonic()<deadline,'compare callback did not finish';window.after(50,finish);return
        assert ('install','kokoro') in calls and ('compare',['kokoro']) in calls,calls
       except Exception as exc:errors.append(exc)
       finally:window.destroy()
      window.after(50,finish)
     except Exception as exc:errors.append(exc);window.destroy()
    window.after(50,next_action)
   except Exception as exc:errors.append(exc);window.destroy()
  window.after(300,inspect);return window
 tkinter.Tk=create
 def install(model,progress):calls.append(('install',model));return Path('fixture')
 def compare(selected,progress):calls.append(('compare',list(selected)));return Path('fixture'),[]
 with mock.patch.object(models,'install',side_effect=install),mock.patch.object(models,'compare',side_effect=compare),mock.patch.object(models.os,'startfile',create=True):
  assert models.launch_window()==0
 if errors:raise errors[0]
 print('Visible and clickable at Tk scale',scale)
