from pathlib import Path
import ast, datetime, hashlib, shutil
root=Path.cwd()
paths=['PAFPlayer.py','docs/README.md','docs/PAFPlayer_changelog.md']
backups=[]
for raw in paths:
 p=root/raw; b=p.with_name(p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt.bak'); n=0
 while b.exists():
  n+=1;b=p.with_name(p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+f'.replaced-by-chatgpt ({n}).bak')
 shutil.copy2(p,b)
 assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 backups.append((p,b))
p=root/'PAFPlayer.py';text=p.read_text(encoding='utf-8-sig')
text=text.replace("2026-11-25-v754-arbitrary-speed-multipliers","2026-11-25-v755-preview-focus-bottom-row").replace("= 'V754'","= 'V755'")
text=text.replace('TERMINAL_BOTTOM_RESERVE_TRIM_ROWS = 2  # Keep spectrum paints away from the viewport edge; a stray row advance must not scroll the UI.', 'TERMINAL_BOTTOM_RESERVE_TRIM_ROWS = 1  # One safety row prevents a trailing advance from scrolling the live display.')
text=text.replace('self.assertGreaterEqual(TERMINAL_BOTTOM_RESERVE_TRIM_ROWS, 2)', 'self.assertEqual(TERMINAL_BOTTOM_RESERVE_TRIM_ROWS, 1)')
text=text.replace('    simple_mode: bool = False,\n    shuffle_state:', '    simple_mode: bool = False,\n    playback_focus=None,\n    shuffle_state:',1)
needle='        while True:\n            speed = current_speed()'
assert text.count(needle)==1
text=text.replace(needle,'        if playback_focus is not None:\n            playback_focus.claim()\n'+needle,1)
needle='    web_server: PAFWebServer | None = None\n    error_alerts = ErrorAlerts()'
assert needle in text
text=text.replace(needle,'    web_server: PAFWebServer | None = None\n    playback_focus = None\n    error_alerts = ErrorAlerts()',1)
needle="        playback_paused_state = [bool(persisted_settings.get('PlaybackPaused', 0))]"
assert needle in text
text=text.replace(needle,needle+"\n        from PAFPlayer_playback_focus import PlaybackFocus\n        playback_focus = PlaybackFocus(paf_workflows().root, playback_paused_state,\n            web_server.enqueue_action, preview=simple_instance, pause=WEB_PAUSE, resume=WEB_PLAY)",1)
needle='                simple_mode=simple_instance,\n                shuffle_state='
assert needle in text
text=text.replace(needle,'                simple_mode=simple_instance,\n                playback_focus=playback_focus,\n                shuffle_state=',1)
needle='    finally:\n        set_post_playback_output(True)\n        if playlist_window is not None:'
assert needle in text
text=text.replace(needle,'    finally:\n        set_post_playback_output(True)\n        if playback_focus is not None:\n            playback_focus.close()\n        if playlist_window is not None:',1)
lines=text.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  sources=ast.literal_eval(line.split(' = ',1)[1]);sources['PAFPlayer_playback_focus']=(root/'src/PAFPlayer_playback_focus.py').read_text(encoding='utf-8-sig');lines[i]='_PAF_BUNDLED_SOURCES = '+repr(sources)+'\n';break
text=''.join(lines);compile(text,str(p),'exec');p.write_text(text,encoding='utf-8')
p=root/'docs/README.md';text=p.read_text(encoding='utf-8-sig');text+='\n\n### V755: preview audio focus and console space\n\n`--simple` pauses the main player and other simple previews immediately before starting its first decoder. A local authenticated loopback listener coordinates players even when their web servers are disabled. Closing a preview releases its pause requests; players that were already paused stay paused. Nested previews resume the preceding preview first and keep the main player paused until all preview requests have ended. Crash recovery expires abandoned requests after approximately 12 seconds. Restart running players once to enable this coordination. The console visualizer now reserves one bottom safety row instead of two.\n';p.write_text(text,encoding='utf-8')
p=root/'docs/PAFPlayer_changelog.md';text=p.read_text(encoding='utf-8-sig');text=text.replace('# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V755 — November 25, 2026\n\nUse one bottom safety row and coordinate simple-preview pauses with the main player and other previews, preserving prior pause state and nested preview ownership. [Release notes](../releases/PAFPlayer_v755_preview_focus_release_notes.md).\n',1);p.write_text(text,encoding='utf-8')
for p,b in backups:
 target=root/('releases' if p.name=='PAFPlayer.py' else 'docs/backups')/b.name;target.parent.mkdir(exist_ok=True)
 assert not target.exists();b.rename(target)
print('Updated V755 with verified backups archived.')
