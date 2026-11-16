from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def replace(path,data,archive):
 name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=path.with_name(name);i=0
 while b.exists():i+=1;b=path.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(path,b);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 path.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 shutil.move(str(b),str(dest))
def once(s,a,b):
 assert s.count(a)==1,(a[:110],s.count(a));return s.replace(a,b,1)
dj=(root/'tests/runs/PAFPlayer_dj_v665_candidate.py').read_text(encoding='utf8')
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines)
text=once(text,"'2026-11-12-v664-gemini-native'","'2026-11-12-v665-dj-sleep'")
text=once(text,"PROGRAM_VERSION                = 'V664'","PROGRAM_VERSION                = 'V665'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V664'","PROGRAM_RELEASE_LABEL          = 'V665'")
def hour_label(h):
 return 'midnight' if h==0 else 'noon' if h==12 else f'{h%12 or 12}{"am" if h<12 else "pm"}'
sleep_options='<option value="never">never</option>'+''.join(f'<option value="{h:02}:00">at {hour_label(h)}</option>' for h in range(24))
wake_options='<option value="sunrise">sunrise</option>'+''.join(f'<option value="{h:02}:00">{hour_label(h)}</option>' for h in list(range(6,24))+list(range(0,6)))
anchor='<label><input type="checkbox" id="dj_enabled"> Enable AI DJ</label>'
controls=anchor+f'''\n<label>AI DJs go to sleep <select id="dj_sleep_time">{sleep_options}</select></label>
<div id="djSleepScheduleDetails" hidden><label>and wake up at <select id="dj_wake_time">{wake_options}</select></label>
<div id="djSunriseZipDetails" hidden><label>US ZIP code for sunrise (confirm or change the default for your location) <input id="dj_sunrise_zip" type="text" inputmode="numeric" pattern="[0-9]{{5}}" maxlength="5" value="22312"></label><p>For ZIP codes other than 22312, PAFPlayer sends the ZIP to Zippopotam.us to find approximate coordinates and caches the result. If sunrise is unavailable, 7am is used and a warning is shown.</p></div></div>
<label><input type="checkbox" id="dj_sleep_when_locked"> AI DJs go to sleep when screen is locked</label>'''
text=once(text,anchor,controls)
text=once(text,"    html = lockscreen_ui(html)\n", "    html = lockscreen_ui(html)\n    html = html.replace('<label><input type=\"checkbox\" id=\"lockScreenShowVersion\" disabled>Show PAFPlayer version after album</label>', '<label><input type=\"checkbox\" id=\"lockScreenShowVersion\" disabled>Show PAFPlayer version after album</label><label><input type=\"checkbox\" id=\"djLockScreenSleep\" disabled>AI DJs go to sleep when screen is locked</label>', 1)\n")
text=once(text,"'piper_executable','piper_voices','gemini_free_confirmed'];let loaded=false,local=false,token='';", "'piper_executable','piper_voices','gemini_free_confirmed','sleep_time','wake_time','sunrise_zip','sleep_when_locked'];let loaded=false,local=false,token='',lockSyncBusy=false,lastLockValue=false;")
anchor="function balance(changed){"
new="""function updateSleepVisibility(){const details=document.getElementById('djSleepScheduleDetails'),zip=document.getElementById('djSunriseZipDetails');details.hidden=$('sleep_time').value==='never';zip.hidden=details.hidden||$('wake_time').value!=='sunrise'}
for(const k of ['sleep_time','wake_time'])$(k).addEventListener('change',updateSleepVisibility);
async function saveSharedLock(value){if(!local||lockSyncBusy)return;const mirror=document.getElementById('djLockScreenSleep'),prior=lastLockValue;lockSyncBusy=true;$('sleep_when_locked').disabled=true;if(mirror)mirror.disabled=true;try{const r=await fetch('/api/workflows/dj',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify({sleep_when_locked:!!value})}),d=await r.json();if(!r.ok)throw Error(d.error||'Save failed');lastLockValue=!!d.settings.sleep_when_locked;$('status').textContent='AI DJ lock setting saved'}catch(e){lastLockValue=prior;$('status').textContent=String(e)}finally{$('sleep_when_locked').checked=lastLockValue;if(mirror){mirror.checked=lastLockValue;mirror.disabled=!local}$('sleep_when_locked').disabled=!local;lockSyncBusy=false}}
$('sleep_when_locked').addEventListener('change',e=>saveSharedLock(e.target.checked));const lockMirror=document.getElementById('djLockScreenSleep');if(lockMirror)lockMirror.addEventListener('change',e=>saveSharedLock(e.target.checked));
function balance(changed){"""
text=once(text,anchor,new)
old="for(const k of keys)$(k).disabled=!local;$('save').disabled=!local;$('status').textContent=[d.error,d.notice,d.stage,d.ready?'Commentary ready':''"
new="for(const k of keys)$(k).disabled=!local;if(!lockSyncBusy){lastLockValue=!!d.settings.sleep_when_locked;$('sleep_when_locked').checked=lastLockValue;if(lockMirror)lockMirror.checked=lastLockValue}if(lockMirror)lockMirror.disabled=!local||lockSyncBusy;$('sleep_when_locked').disabled=!local||lockSyncBusy;updateSleepVisibility();$('save').disabled=!local;$('status').textContent=[d.error,d.notice,d.sleeping?'Asleep: '+d.sleep_reason:'',d.stage,d.ready?'Commentary ready':''"
text=once(text,old,new)
text=once(text,"$('status').textContent='AI DJ settings saved'}catch(e)","$('status').textContent='AI DJ settings saved';updateSleepVisibility()}catch(e)")
compile(dj,'dj','exec');compile(text,str(p),'exec')
release=root/'releases/PAFPlayer_v665_dj_sleep.py';notes=root/'releases/PAFPlayer_v665_dj_sleep_release_notes.md';assert not release.exists() and not notes.exists()
replace(root/'src/PAFPlayer_dj.py',dj,root/'backups');replace(p,text,root/'releases');release.write_text(text,encoding='utf8',newline='')
test=root/'tests/test_v665_dj_sleep.py';s=test.read_text(encoding='utf8');s=once(s,"ROOT/'tests/runs/PAFPlayer_dj_v665_candidate.py'","ROOT/'src/PAFPlayer_dj.py'");replace(test,s,root/'backups')
readme=root/'docs/README.md';s=readme.read_text(encoding='utf8');s=once(s,'Current release: **V664** — verified free DJ providers.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v664_gemini_native_release_notes.md).','Current release: **V665** — DJ sleep hours and screen-lock sleep.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v665_dj_sleep_release_notes.md).')
anchor='## Experimental AI Podcaster / DJ\n'
addition='''
The Experimental DJ settings include **AI DJs go to sleep**, defaulting to **never**. Pick an hourly sleep time to reveal a wake selector, which defaults to **sunrise**, or select a fixed hourly wake time. Sunrise reveals a US ZIP field: confirm or change the default **22312** for your location during setup. Sunrise uses approximate local solar calculations; ZIP 22312 works offline. Other US ZIP codes are sent to Zippopotam.us for approximate coordinates, which are cached locally. If the ZIP lookup or sunrise is unavailable (including polar day/night), 7:00 AM is used and a warning is shown. Times use the player computer’s local time zone.

**AI DJs go to sleep when screen is locked** is available both in the DJ controls and under Windows Lock Screen; the two checkboxes immediately save and reflect the same setting. When asleep, new DJ jobs—including `#djforce`—do not start, prepared segments wait, and active DJ speech stops. Music resumes if the DJ owned its pause. Unlocking or the scheduled wake time allows the next eligible segment to play.

'''
s=once(s,anchor,anchor+addition);replace(readme,s,root/'docs')
changelog=root/'docs/PAFPlayer_changelog.md';s=changelog.read_text(encoding='utf8');s=once(s,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V665 — November 12, 2026\n\nAdd scheduled DJ sleep and sunrise/fixed-hour wake with configurable ZIP, plus a shared DJ/lock-screen sleep-on-lock checkbox. [Release notes](../releases/PAFPlayer_v665_dj_sleep_release_notes.md).\n');replace(changelog,s,root/'backups')
notes.write_text('''# PAFPlayer V665 — DJ sleep schedule

DJ settings include an hourly sleep time, sunrise or hourly wake time, default US ZIP 22312, and a sleep-on-screen-lock checkbox mirrored in Windows Lock Screen settings. Sleep blocks new/forced jobs and prepared interruptions; active commentary stops and DJ-owned music pauses resume. Custom ZIP lookups run in the background and are cached; unavailable sunrise uses a visible 7am fallback. Times use the player’s local time zone.

The two free hosted DJ providers and the previous OpenAI credit warning remain available. The default sleep setting is never and the default sleep-on-lock setting is off.
''',encoding='utf8')
print('Published V665 sleep controls and documentation.')
