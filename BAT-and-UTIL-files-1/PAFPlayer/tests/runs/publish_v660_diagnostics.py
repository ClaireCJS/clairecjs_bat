from pathlib import Path
import datetime, hashlib, shutil
root=Path(__file__).resolve().parents[2]
def replace(path,data,archive):
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=path.with_name(name);i=0
    while backup.exists():i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data,encoding='utf8',newline='');dest=archive/backup.name;i=0
    while dest.exists():i+=1;dest=archive/(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(dest))
def once(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
dj=(root/'tests/runs/PAFPlayer_dj_v660_candidate.py').read_text(encoding='utf8')
player=root/'PAFPlayer.py';lines=player.read_text(encoding='utf8').splitlines(keepends=True)
indices=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(indices)==1
lines[indices[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines)
text=once(text,"'2026-11-11-v659-piper-auto-setup'","'2026-11-11-v660-dj-diagnostics'")
text=once(text,"PROGRAM_VERSION                = 'V659'","PROGRAM_VERSION                = 'V660'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V659'","PROGRAM_RELEASE_LABEL          = 'V660'")
old="""                if action is None and not startup_pause_transition and dj_controller.due():
                    dj_owned_pause = True
                    action = PAUSE_TOGGLE
"""
assert text.count(old)==1;text=text.replace(old,'',1)
anchor="""                if action is None:
                    fps_hud_rolled = roll_fps_hud(now)"""
replacement="""                # Help is modal: wait until it closes before claiming the
                # music pause for a prepared DJ interruption.
                if action is None and not startup_pause_transition and not help_overlay_until and dj_controller.due():
                    dj_owned_pause = True
                    action = PAUSE_TOGGLE
                if action is None:
                    fps_hud_rolled = roll_fps_hud(now)"""
text=once(text,anchor,replacement)
compile(dj,'dj','exec');compile(text,str(player),'exec')
release=root/'releases/PAFPlayer_v660_dj_diagnostics.py';notes=root/'releases/PAFPlayer_v660_dj_diagnostics_release_notes.md';assert not release.exists() and not notes.exists()
replace(root/'src/PAFPlayer_dj.py',dj,root/'backups');replace(player,text,root/'releases');release.write_text(text,encoding='utf8',newline='')
test=root/'tests/test_v660_dj_diagnostics.py';testtext=test.read_text(encoding='utf8');testtext=once(testtext,"ROOT/'tests/runs/PAFPlayer_dj_v660_candidate.py'","ROOT/'src/PAFPlayer_dj.py'");replace(test,testtext,root/'backups')
readme=root/'docs/README.md';doc=readme.read_text(encoding='utf8')
doc=once(doc,'Current release: **V659** — automatic Piper setup for AI DJ speech.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v659_piper_auto_setup_release_notes.md).','Current release: **V660** — AI DJ diagnostics and Help handoff.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v660_dj_diagnostics_release_notes.md).')
anchor='During playback, `#dj` toggles automatic commentary;'
assert doc.count(anchor)==1
doc=doc.replace(anchor,'''DJ diagnostics are saved as separate append-only JSONL files under `%LOCALAPPDATA%\\PAFPlayer\\workflows\\dj-logs`. Each session records scheduling decisions, provider stages and failure types, HTTP status codes, cancellation, and playback outcomes. It does not record track metadata, generated dialogue, API keys, error bodies, or provider response text. The `?` screen shows the number of qualifying tracks while waiting, and shows progress for automatic as well as forced requests. When Help is open, prepared commentary waits until Help closes before it claims the music pause.

'''+anchor,1)
replace(readme,doc,root/'docs')
change=root/'docs/PAFPlayer_changelog.md';doc=change.read_text(encoding='utf8');doc=once(doc,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V660 — November 11, 2026\n\nLog private, metadata-free DJ scheduling, provider, and playback events; show automatic progress and qualifying-track counts; defer automatic playback until modal Help closes. [Release notes](../releases/PAFPlayer_v660_dj_diagnostics_release_notes.md).\n');replace(change,doc,root/'backups')
notes.write_text('''# PAFPlayer V660 — DJ diagnostics and Help handoff

The DJ writes separate append-only per-session JSONL logs under `%LOCALAPPDATA%\\PAFPlayer\\workflows\\dj-logs`. Scheduling, provider start/fallback, HTTP status, setup stages, cancellation, and playback outcomes are recorded without keys, track metadata, generated dialogue, response bodies, or exception messages. Help shows how many qualifying tracks have been counted and automatic job progress; the web DJ status also exposes automatic stages.

Prepared commentary now waits for the modal Help screen to close before the player claims its music pause. Previously Help could swallow the synthetic pause action while the DJ claimed ownership. Explicit user pause remains respected.

The V659 live session showed a ready segment from local Ollama and Piper, with OpenAI text and speech failing over. The precise cause of the earlier lack of a job was not recorded by V659. No literal C:\\BAT paths were changed.
''',encoding='utf8')
print('Published V660 diagnostics, Help handoff, release and documentation.')
