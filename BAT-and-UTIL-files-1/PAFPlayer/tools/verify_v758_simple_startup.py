from pathlib import Path
import datetime,hashlib,shutil,ast,unittest,io
root=Path.cwd();p=root/'PAFPlayer.py'
base=p.name+'.bak.'+datetime.datetime.now().strftime('%Y%m%d%H%M')+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
while b.exists():n+=1;b=p.with_name(base+f' ({n}).bak')
shutil.copy2(p,b);assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(p.read_bytes()).digest();dest=root/'releases'/b.name
while dest.exists():n+=1;dest=root/'releases'/(base+f' ({n}).bak')
b.rename(dest)
s=p.read_text(encoding='utf-8-sig')
s=s.replace('self.assertIn("\'PlaybackPaused\': int(playback_paused_state[0] and not external_media_controller.auto_paused)", main_source)', 'self.assertIn("\'PlaybackPaused\': int(persisted_settings.get(\'PlaybackPaused\', 0)) if simple_instance else int(playback_paused_state[0] and not external_media_controller.auto_paused)", main_source)')
compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
notes=root/'releases/PAFPlayer_v758_simple_startup_release_notes.md';assert not notes.exists()
notes.write_text('# PAFPlayer V758 — recover simple-preview startup\n\nObserved logs showed recent V757 simple launches taking approximately 31–33 seconds to start the decoder. The preview registry contained 18 entries, with only the main process still alive at inspection. Requests to exited peers were adding serial refused-connection delays. No fatal exception was present for these launches in the inspected error log.\n\nThe coordinator now verifies process liveness before connecting and archives exited registrations, preserving collisions and avoiding permanent deletion. It traces focus discovery, skipped dead peers, pause requests, acknowledgements and readiness without logging authentication tokens. Only contacted peers receive heartbeat/release requests.\n\nOverlapping preview startups give priority to the newest preview. An older preview can acknowledge being silent before it has a decoder, then wait for the newer preview without both startup threads waiting for queued pause actions. A new simple preview starts unpaused and preserves the main player\'s saved pause preference.\n\nTests cover dead registration batches with zero connection attempts, native process liveness, overlapping startups, original pause restoration, disabled-web transport acknowledgement, preview startup/persistence state, archive collisions, diagnostic redaction and existing simple-mode/interrupt regressions. Live music was not interrupted for testing. Existing main-player endpoints remain compatible; restart a failing preview using the updated active file.\n',encoding='utf-8')
release=root/'releases/PAFPlayer_v758_simple_startup.py';assert not release.exists();shutil.copy2(p,release)
assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(release.read_bytes()).digest()
for file in (p,release,root/'src/PAFPlayer_playback_focus.py'):ast.parse(file.read_text(encoding='utf-8-sig'))
import PAFPlayer as app
assert app._PAF_BUNDLED_SOURCES['PAFPlayer_playback_focus']==(root/'src/PAFPlayer_playback_focus.py').read_text(encoding='utf-8-sig')
suite=unittest.TestSuite()
for name in ('test_v758_simple_startup.StartupTests','test_v755_preview_focus','test_v624_simple_instance','test_v742_simple_splash','test_v749_simple_interrupt'):
 suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
suite.addTest(app.PlayWaveFileTests('test_v174_play_pause_state_persists_and_defaults_to_playing'))
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);app.set_post_playback_output(False)
report=stream.getvalue()+'\nSyntax checks, bundle/module parity and release SHA256 passed. Root audit: active player/data/Qwen shim retained; lockscreen and screensaver build/runtime assets retained. No C:\\BAT changes. Live playback was not interrupted; live startup improvement remains to be confirmed on the next preview launch.\n'
path=root/'tests/reports/v758-simple-startup-checks.txt';assert not path.exists();path.write_text(report,encoding='utf-8');print(report)
raise SystemExit(not result.wasSuccessful())
