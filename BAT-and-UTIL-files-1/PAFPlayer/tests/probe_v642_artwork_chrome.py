"""Isolated real popup for visual checks; never starts audio or commands the owner."""
from datetime import datetime
import ctypes
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from run_PAFPlayer_tests import install_guards, unique
stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
stage=unique(ROOT/'tests/runs'/('artwork-v642-'+stamp));stage.mkdir(parents=True)
with (stage/'PAFPlayer.py').open('xb') as f:f.write((ROOT/'PAFPlayer.py').read_bytes())
for key in ('APPDATA','LOCALAPPDATA','TEMP','TMP'): os.environ[key]=str(stage)
tempfile.tempdir=str(stage)
sys.path.insert(0,str(stage));sys.argv=['PAFPlayer.py','--unit-tests'];os.chdir(stage)
blocks=install_guards(ROOT/'tests')
import PAFPlayer as app
import PAFPlayer_remote_tray as remote
prefs=remote.RemoteTrayAppSettings('fixture-v642',stage/'preferences')
prefs.install_player_preference_backend(app)
prefs.save_player_settings({'RendererPreferences':{k:{'type':1 if isinstance(v,str) else 4,'value':v} for k,v in {
    'ExternalAlbumArtGeometry':'900x620+200+180', 'ExternalAlbumArtManualSizeV237':1,
    'ExternalAlbumArtLyricsModeV180':0,'ExternalAlbumArtKaraokeEnabledV336':1,
    'ExternalAlbumArtPopupEmojimaxV295':0,'ExternalAlbumArtTopmost':0,
}.items()}})
app.load_external_album_art_geometry=lambda:'900x620+200+180'
app.load_external_album_art_placement=lambda:None
app.load_external_album_art_manual_size=lambda:True
app.windows_restore_foreground_window=lambda *a,**k:True
errors=[]
app.append_pafplayer_trace=lambda *a,**k:None
app.append_pafplayer_error=lambda *a,**k:errors.append(str(a))
app.record_pafplayer_runtime_warning=lambda *a,**k:errors.append(str(a))
app.record_pafplayer_callback_exception=lambda *a,**k:errors.append(str(a))
app.append_pafplayer_exception=lambda *a,**k:errors.append(str(a))
events=unique(ROOT/'tests/reports'/('v642-ui-'+stamp+'.jsonl'))
stream=events.open('x',encoding='utf-8')
app.webbrowser.open_new_tab=lambda url: (stream.write(json.dumps({'web_url':url})+'\n'),stream.flush(),True)[-1]
class Probe(app.ExternalAlbumArtWindow):
    def _gui_main(self):
        def observe(frame,event,arg):
            if event!='return' or frame.f_code.co_name!='process_commands':return
            state=frame.f_locals.get('state');root=frame.f_locals.get('root')
            if not state or root is None:return
            sys.setprofile(None)
            import tkinter as tk
            other=tk.Toplevel(root);other.title('PAFPlayer V642 focus test')
            other.geometry('450x160+1140+200');other.configure(background='#223a50')
            tk.Label(other,text='Click here to unfocus the artwork popup',bg='#223a50',fg='white',font=('Segoe UI',14)).pack(expand=True)
            # Disable the legacy "acknowledge caption" synthetic click for this
            # fixture. UI actions are performed by the computer-use tool.
            state['attention_acknowledged']=True
            def record():
                try:
                    label=state.get('identity_label');button=state.get('artwork_web_button')
                    u=ctypes.WinDLL('user32');get=u.GetWindowLongPtrW
                    get.argtypes=[ctypes.c_void_p,ctypes.c_int];get.restype=ctypes.c_ssize_t
                    hwnd=state['native_hwnd']
                    data=dict(time=time.monotonic(),hwnd=hwnd,active=state.get('window_active'),
                        background=root.cget('background'),border=state['art_border_frame'].cget('background'),
                        style=get(hwnd,-16),exstyle=get(hwnd,-20),geometry=root.geometry(),
                        title=label.cget('text') if label else None,
                        title_box=[label.winfo_x(),label.winfo_y(),label.winfo_width(),label.winfo_height()] if label else None,
                        button_box=[button.winfo_x(),button.winfo_y(),button.winfo_width(),button.winfo_height()] if button else None,
                        controls=[w.winfo_class() for w in button.master.winfo_children()] if button else [],errors=list(errors))
                    stream.write(json.dumps(data)+'\n');stream.flush();root.after(500,record)
                except Exception as exc:errors.append(repr(exc))
            root.after(200,record)
        sys.setprofile(observe)
        try:super()._gui_main()
        finally:sys.setprofile(None)

from PIL import Image,ImageDraw
image=Image.new('RGB',(720,720),'#132c3c');draw=ImageDraw.Draw(image)
for i,color in enumerate(('#357a89','#89b6a5','#e0c89a')):draw.rectangle((80+i*60,80+i*60,640-i*60,640-i*60),outline=color,width=25)
bio=io.BytesIO();image.save(bio,format='PNG')
p=Probe(enabled=True,idle_foreground_seconds=0)
p._player_window_hwnd=0
p.update_title('PAFPlayer V642 artwork test')
p.update_track_identity('Necros','Count Me Out')
p.set_web_interface_url('http://127.0.0.1:666/?fixture=v642#old')
p.update_remote_artwork([bio.getvalue()])
print(json.dumps({'stage':str(stage),'events':str(events)}),flush=True)
deadline=time.monotonic()+float(os.environ.get('PAF_V642_PROBE_SECONDS','480'))
try:
    while time.monotonic()<deadline and not (stage/'stop').exists():time.sleep(.2)
finally:
    p.close();stream.close()
    print(json.dumps({'errors':errors,'blocks':blocks}),flush=True)
