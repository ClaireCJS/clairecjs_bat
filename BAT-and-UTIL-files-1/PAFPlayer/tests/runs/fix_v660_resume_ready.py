from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def replace(path,data):
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=path.with_name(name);i=0
    while backup.exists():i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data,encoding='utf8',newline='');dst=root/'releases'/backup.name;i=0
    while dst.exists():i+=1;dst=root/'releases'/(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(dst))
player=root/'PAFPlayer.py';text=player.read_text(encoding='utf8')
old='''                        if paused_action in ({STOP, QUIT_Q, PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, WEB_STOP} | NAVIGATION_ACTIONS) or (paused_action is not None and seek_seconds_for_action(paused_action) is not None):
                            dj_controller.cancel_request()
                            dj_owned_pause = False
                            dj_started = False
'''
new='''                        if paused_action in ({STOP, QUIT_Q, PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, WEB_STOP} | NAVIGATION_ACTIONS) or (paused_action is not None and seek_seconds_for_action(paused_action) is not None):
                            # Resuming a user's pause must not discard an automatic
                            # segment that became ready while music was paused.
                            preserve_ready_dj = (paused_action in {PAUSE_TOGGLE, WEB_PLAY}
                                and not dj_started and not dj_controller.forced and dj_controller.due())
                            if not preserve_ready_dj:
                                dj_controller.cancel_request()
                                dj_owned_pause = False
                                dj_started = False
'''
assert text.count(old)==1;text=text.replace(old,new,1);compile(text,str(player),'exec')
replace(player,text);replace(root/'releases/PAFPlayer_v660_dj_diagnostics.py',text)
print('Preserved prepared automatic commentary on user resume.')
