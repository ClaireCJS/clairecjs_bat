from pathlib import Path
import ast,hashlib,shutil,unittest,io,inspect
import PAFPlayer as app
root=Path.cwd()
notes=root/'releases/PAFPlayer_v756_speed_credit_release_notes.md'
assert not notes.exists();notes.write_text('# PAFPlayer V756 — clear speed confirmation and minor credit warnings\n\nThe X menu distinguishes the active Playing speed from the typed Pending value until Enter. Applying a custom multiplier clears the stale menu in both normal and simple mode; simple mode repaints only its reserved rows without a full-screen clear. Exact custom speed continues through decoder restarts and across tracks.\n\nHistorical OpenAI credit exhaustion remains in Web Warnings and DJ diagnostic logs. The HUD/help list escalates it only when DJs are enabled, OpenAI participates in the configured text/speech chain, and the latest generation has failed without a ready fallback. Severity checks use local job state and perform no network requests or key-file reads.\n\nValidation covers 1.333 reaching the decoder, menu dismissal without clearing the screen, warning severity combinations, Web Warnings retention, nonblocking warnings, and existing simple-mode, interrupt, speed and preview-focus regressions. No live provider calls or user playback interruption were needed.\n',encoding='utf-8')
release=root/'releases/PAFPlayer_v756_speed_credit.py';assert not release.exists();shutil.copy2(root/'PAFPlayer.py',release)
assert hashlib.sha256(release.read_bytes()).digest()==hashlib.sha256((root/'PAFPlayer.py').read_bytes()).digest()
for raw in ('PAFPlayer.py','src/PAFPlayer_dj.py','releases/PAFPlayer_v756_speed_credit.py'):
 ast.parse((root/raw).read_text(encoding='utf-8-sig'))
suite=unittest.TestSuite()
for name in ('test_v756_speed_credit','test_v751_speed_entry','test_v694_nonblocking_warnings','test_v742_simple_splash','test_v749_simple_interrupt','test_v755_preview_focus'):
 suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
app.set_post_playback_output(False)
assert app._PAF_BUNDLED_SOURCES['PAFPlayer_dj']==(root/'src/PAFPlayer_dj.py').read_text(encoding='utf-8-sig')
report=stream.getvalue()+'\nSyntax, embedded DJ source parity and release-copy hash checks passed. Root audit: player root retains active runtime/data files and Qwen shim; lockscreen and screensaver roots retain build inputs and active assets. No C:\\BAT files changed.\n'
path=root/'tests/reports/v756-speed-credit-checks.txt';assert not path.exists();path.write_text(report,encoding='utf-8')
print(report)
raise SystemExit(not result.wasSuccessful())
