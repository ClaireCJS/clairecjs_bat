from pathlib import Path
import ast,inspect,io,contextlib,threading,unittest,hashlib,shutil
from unittest.mock import Mock
import PAFPlayer as app
root=Path.cwd()
# Execute the real main Ctrl+C handler body with cleanup side effects mocked.
tree=ast.parse(inspect.getsource(app.main))
handler=next(n for n in ast.walk(tree) if isinstance(n,ast.ExceptHandler) and isinstance(n.type,ast.Name) and n.type.id=='KeyboardInterrupt' and any(isinstance(v,ast.Constant) and isinstance(v.value,str) and 'Playback stopped.' in v.value for v in ast.walk(n)))
module=ast.fix_missing_locations(ast.Module(body=handler.body,type_ignores=[]))
env={'set_post_playback_output':Mock(),'_FAST_CONSOLE_ABORT_REQUESTED':threading.Event(),'restore_terminal_after_interrupt':Mock(),'arm_fast_console_abort_watchdog':Mock(),'append_pafplayer_trace':Mock()}
out=io.StringIO()
with contextlib.redirect_stdout(out):exec(compile(module,'<real-ctrl-c-handler>','exec'),env)
payload=out.getvalue();assert 'Playback stopped.\033[J\n' in payload
for forbidden in ('\033[2J','\033[H','\033c'):assert forbidden not in payload
suite=unittest.TestSuite()
for name in ('test_v749_simple_interrupt','test_v742_simple_splash'):
 suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);app.set_post_playback_output(False)
assert result.wasSuccessful(),stream.getvalue()
notes=root/'releases/PAFPlayer_v760_erase_after_interrupt_release_notes.md';assert not notes.exists()
notes.write_text('# PAFPlayer V760 — erase leftover display after Ctrl+C\n\nThe main Ctrl+C handler now prints ANSI erase-to-end-of-screen (`ESC[J`) immediately after `Playback stopped.` and flushes the message. Remaining karaoke/progress content beneath it is erased without adding a full-screen clear, cursor-home or terminal-reset sequence.\n\nVerified by executing the actual interrupt handler body with cleanup side effects mocked and capturing the output order. Seven existing simple-interrupt/startup-splash regressions also pass. No live player was interrupted for testing.\n',encoding='utf-8')
release=root/'releases/PAFPlayer_v760_erase_after_interrupt.py';assert not release.exists();shutil.copy2(root/'PAFPlayer.py',release)
assert hashlib.sha256(release.read_bytes()).digest()==hashlib.sha256((root/'PAFPlayer.py').read_bytes()).digest()
for p in (root/'PAFPlayer.py',release):ast.parse(p.read_text(encoding='utf-8-sig'))
report=root/'tests/reports/v760-interrupt-erase-checks.txt';assert not report.exists();report.write_text('Actual main Ctrl+C handler capture: erase-to-end follows stop message before newline; no full-screen clear/home/reset introduced.\n\n'+stream.getvalue()+'\nSyntax and standalone release hash checks passed. Root audit: active player/data files retained; lockscreen/screensaver roots retain build/runtime assets. No C:\\BAT changes.\n',encoding='utf-8')
print('Actual Ctrl+C output capture passed. '+stream.getvalue())
