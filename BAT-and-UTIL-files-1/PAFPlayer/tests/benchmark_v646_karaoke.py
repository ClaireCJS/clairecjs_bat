"""No-audio karaoke profiling; retained fixtures, timings, and output hashes."""
import ast
import cProfile
import contextlib
from datetime import datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import pstats
import statistics
import sys
import tempfile
import time
import tkinter as tk
from types import SimpleNamespace

from run_PAFPlayer_tests import install_guards, unique

ROOT = Path(__file__).resolve().parents[1]
requested = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT/'PAFPlayer.py'
stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
stage = unique(ROOT/'tests/runs'/('karaoke-v646-'+stamp)); stage.mkdir(parents=True)
with (stage/'PAFPlayer.py').open('xb') as f: f.write(requested.read_bytes())
for key in ('APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP'): os.environ[key] = str(stage)
tempfile.tempdir = str(stage)
os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(stage/'history.sqlite3')
sys.path.insert(0, str(stage)); sys.argv = ['PAFPlayer.py', '--unit-tests']; os.chdir(stage)
blocks = install_guards(ROOT/'tests')
import PAFPlayer as app
from PIL import Image, ImageDraw

root = tk.Tk(); root.withdraw(); root.update_idletasks()
state = dict(border_pixels=5, lyric_font_scale=.7, popup_color_emoji_enabled=True,
             popup_emojimax_enabled=True, artwork_solution_show=True,
             floating_autosize=True, floating_teeny_solutions=True,
             lyric_solutions_artwork=[dict(display='🔥', solution='fire')],
             lyric_solutions_floating=[dict(display='🔥', solution='fire')])
ns = dict(vars(app), root=root, state=state, widget_dpi=lambda _:144,
          karaoke_shadow_size=lambda _: .045, paf_workflows=lambda:SimpleNamespace(benchmark=None))
tree=ast.parse((stage/'PAFPlayer.py').read_text(encoding='utf-8'))
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ExternalAlbumArtWindow')
gui=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_gui_main')
names={'artwork_solutions_active','resolve_artwork_pillow_font','resolve_artwork_pillow_emoji_font',
       'build_artwork_plasma_mask','build_floating_lyric_mask','pattern_rgba_for_mask',
       'reuse_or_create_photoimage','_solution_boxes_for_lines','_pillow_solution_boxes','draw_solution_labels'}
for fn in gui.body:
    if isinstance(fn,ast.FunctionDef) and (fn.name in names or fn.name.startswith('_pillow_')):
        exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])), '<production karaoke>', 'exec'), ns)

results=[]
def measure(name, action, repeat=5):
    elapsed=[];cpu=[];value=None
    for _ in range(repeat):
        start=time.perf_counter(); process=time.process_time()
        value=action()
        cpu.append((time.process_time()-process)*1000)
        elapsed.append((time.perf_counter()-start)*1000)
    entry=dict(name=name,median_ms=statistics.median(elapsed),max_ms=max(elapsed),cpu_median_ms=statistics.median(cpu))
    if isinstance(value,str): entry['value']=value
    if isinstance(value,Image.Image):entry['sha256']=hashlib.sha256(value.tobytes()).hexdigest()
    results.append(entry); print(json.dumps(entry),flush=True)
    return value

profile=cProfile.Profile();profiled=os.environ.get('PAF_PROFILE_KARAOKE')=='1'
if profiled:profile.enable()
for width,height in ((900,540),(1920,1080)):
    lyric='We are 🔥 tonight'
    built=measure(f'artwork_layout_{width}',lambda:ns['build_artwork_plasma_mask'](width,height,lyric),3)
    mask,origin,shadow,wrapped,font,overlay=built
    rgba=measure(f'artwork_color_{width}',lambda:ns['pattern_rgba_for_mask'](mask,shadow,1.25,'lava-lamp',0,brightness=1.8,saturation=.35))
    photo=ns['reuse_or_create_photoimage'](None,rgba,root)
    measure(f'upload_{width}',lambda:ns['reuse_or_create_photoimage'](photo,rgba,root))
    del photo
for size in ((300,160),(900,320)):
    width,height=size
    rgba=Image.new('RGBA',size,(20,140,230,255));mask=Image.new('L',size,0)
    measure(f'inherited_color_empty_mask_{width}',lambda:app.emojimax_solution_label_color('#f4f8ff',True,(0,0,width,height),rgba,(0,0),mask),3)
    ImageDraw.Draw(mask).rectangle((width//3,0,width-1,height-1),fill=255)
    measure(f'inherited_color_left_padding_{width}',lambda:app.emojimax_solution_label_color('#f4f8ff',True,(0,0,width,height),rgba,(0,0),mask),3)
profile.disable()
text=io.StringIO()
if profiled:pstats.Stats(profile,stream=text).strip_dirs().sort_stats('cumulative').print_stats(28)
else:text.write('Profiler disabled for wall-clock measurements.\n')
report=unique(ROOT/'tests/reports'/('v646-profile-'+app.PROGRAM_VERSION+'-'+stamp+'.json'))
with report.with_suffix('.txt').open('x',encoding='utf-8') as f:f.write(text.getvalue())
with report.open('x',encoding='utf-8') as f:json.dump(dict(profiled=profiled,version=app.PROGRAM_VERSION,source=str(requested),source_sha256=hashlib.sha256(requested.read_bytes()).hexdigest(),results=results,blocks=blocks,stage=str(stage)),f,indent=2)
root.update_idletasks();root.destroy();print(report)
