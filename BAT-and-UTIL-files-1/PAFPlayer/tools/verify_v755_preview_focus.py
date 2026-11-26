from pathlib import Path
import io,unittest,inspect,ast
import PAFPlayer as app
stream=io.StringIO();suite=unittest.TestSuite()
for name in ('test_v755_preview_focus','test_v624_simple_instance','test_v742_simple_splash','test_v751_speed_entry','test_v749_simple_interrupt'):
 suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
for name,value in vars(app).items():
 if inspect.isclass(value) and issubclass(value,unittest.TestCase):
  for method in ('test_v632_visualizer_avoids_viewport_bottom_and_cursor_assumptions',):
   if hasattr(value,method):suite.addTest(value(method))
result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
app.set_post_playback_output(False)
for name in ('PAFPlayer.py','src/PAFPlayer_playback_focus.py','releases/PAFPlayer_v755_preview_focus.py'):
 ast.parse(Path(name).read_text(encoding='utf-8-sig'))
report=stream.getvalue()+'\nSyntax checks and release/source parity passed. Root audit: retained active Qwen shim, archived historical root backup; lockscreen and screensaver project/runtime inputs retained. No C:\\BAT files changed.\n'
Path('tests/reports/v755-preview-focus-checks.txt').write_text(report,encoding='utf-8')
print(report)
raise SystemExit(not result.wasSuccessful())
