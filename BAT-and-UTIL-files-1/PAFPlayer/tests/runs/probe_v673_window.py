import importlib.util,sys,tkinter
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v673_window_player',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_voice_models as models
real=tkinter.Tk
def closing_window():
 window=real();window.after(1200,window.destroy);return window
tkinter.Tk=closing_window
assert models.launch_window()==0
print('Real model manager window opened and closed successfully.')
