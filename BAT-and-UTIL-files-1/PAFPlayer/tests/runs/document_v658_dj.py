from pathlib import Path
import datetime, hashlib, shutil
root = Path(__file__).resolve().parents[2]

def replace(path, data, archive):
    name = path.name + datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')
    backup=path.with_name(name); i=0
    while backup.exists():
        i+=1; backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup)
    assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data,encoding='utf-8',newline='')
    dst=archive/backup.name; i=0
    while dst.exists():
        i+=1; dst=archive/(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(dst))

p=root/'PAFPlayer.py'; text=p.read_text(encoding='utf-8')
old='''                        if help_overlay_until:
                            modifier_down = any(_windows_key_down(key) for key in (0x10, 0x11, 0x12))'''
new='''                        if help_overlay_until:
                            current_dj_snapshot = getattr(dj_controller, 'help_snapshot', lambda: None)()
                            if current_dj_snapshot != help_dj_snapshot:
                                help_dj_snapshot = current_dj_snapshot
                                render_help_overlay()
                            modifier_down = any(_windows_key_down(key) for key in (0x10, 0x11, 0x12))'''
assert text.count(old)==1
text=text.replace(old,new,1);compile(text,str(p),'exec')
replace(p,text,root/'releases')
replace(root/'releases/PAFPlayer_v658_dj_help_commentary.py',text,root/'releases')
readme=root/'docs/README.md'; text=readme.read_text(encoding='utf-8')
text=text.replace('Current release: **V657** — experimental AI Podcaster / DJ.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v657_experimental_ai_dj_release_notes.md).', 'Current release: **V658** — AI DJ commentary in Help.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v658_dj_help_commentary_release_notes.md).',1)
anchor='## Experimental AI Podcaster / DJ\n'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+'''
During playback, `#dj` toggles automatic commentary; `#djforce` requests it now after at least three seconds of the current track. Open `?` or F1 to see DJ status and generated dialogue below the track diagnostics and above the shortcut list. The text appears as soon as it is written, even if voice synthesis fails. Long dialogue uses Help's PgUp/PgDn pages. Help updates while open, including when playback is paused. A failed request retains the last successfully generated text; the status identifies the current failure.

''',1)
replace(readme,text,root/'docs')
change=root/'docs/PAFPlayer_changelog.md'; text=change.read_text(encoding='utf-8')
assert text.startswith('# PAFPlayer changelog\n')
text=text.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V658 — November 11, 2026\n\nShow AI DJ generation status and dialogue in Help as soon as text is ready, even if speech fails; refresh during playback and pause, and preserve the last dialogue on failure. Restore the editable DJ implementation and bundle parity. [Release notes](../releases/PAFPlayer_v658_dj_help_commentary_release_notes.md).\n',1)
replace(change,text,root/'backups')
notes=root/'releases/PAFPlayer_v658_dj_help_commentary_release_notes.md'
assert not notes.exists()
notes.write_text('''# PAFPlayer V658 — DJ commentary in Help

`?` / F1 shows AI DJ status and the most recent generated dialogue between track diagnostics and keyboard shortcuts. Dialogue appears before speech synthesis and stays visible if synthesis fails. Help paginates long dialogue and refreshes while open during playback or pause. Cancelled generations cannot publish stale text. Control characters are stripped before display.

The editable DJ implementation now matches the bundled implementation and retains the separate presentation helpers. Text and speech still require working providers; this release does not install Piper or configure credentials. Use `#djforce` after three seconds of playback to request a segment, or `#dj` for automatic intervals.

The configured OpenAI key tested on this machine was rejected with HTTP 401. Ollama and local models were detected, but a live text result and real speech are not guaranteed by the automated tests. No literal C:\\BAT files were changed.
''',encoding='utf-8')
print('Updated player, release copy, manual, changelog and release notes.')
