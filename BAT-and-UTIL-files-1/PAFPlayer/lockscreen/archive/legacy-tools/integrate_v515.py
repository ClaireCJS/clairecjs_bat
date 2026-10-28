"""One-time V515 source integration; replacements must already be backed up."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'PAFPlayer.py'
source = path.read_text(encoding='utf-8')
assert 'PAFPlayer_lockscreen' not in source
marker = '_PAF_BUNDLED_SOURCES["PAFPlayer_screensaver"]'
lines = source.splitlines(keepends=True)
index = next(i for i, line in enumerate(lines) if line.startswith(marker))
module = (ROOT / 'lockscreen/src/PAFPlayer_lockscreen.py').read_text(encoding='utf-8')
lines.insert(index + 1, '_PAF_BUNDLED_SOURCES["PAFPlayer_lockscreen"] = ' + repr(module) + '\n')
source = ''.join(lines)

def replace_once(old, new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old, new, 1)

replace_once('2026-10-07-v514-lockscreen-background-registration', '2026-10-08-v515-managed-lockscreen')
source = re.sub(r'(?m)^(PROGRAM_(?:VERSION|RELEASE_LABEL)\s*=\s*)"V514"', r'\1"V515"', source)
replace_once('    html = screensaver_ui(html)\n', '    html = screensaver_ui(html)\n    from PAFPlayer_lockscreen import augment as lockscreen_ui\n    html = lockscreen_ui(html)\n')
for verb in ('GET', 'POST'):
    old = '            def do_' + verb + '(self):\n'
    replace_once(old, old + '                from PAFPlayer_lockscreen import handle as lockscreen_handle\n                if lockscreen_handle(self, owner, self.path.partition("?")[0]): return\n')
replace_once('        self._playlist_job_thread.start()\n        return True',
             '        self._playlist_job_thread.start()\n        from PAFPlayer_lockscreen import controller as lockscreen_controller\n        lockscreen_controller(self).start()\n        return True')
replace_once('        """Stop HTTP threads; Ctrl+Break may request a nonblocking hard-abort path."""\n',
             '        """Stop HTTP threads; Ctrl+Break may request a nonblocking hard-abort path."""\n        lockscreen = getattr(self, "_lock_screen_controller", None)\n        if lockscreen is not None: lockscreen.close()\n')
assert re.search(r'PROGRAM_VERSION\s*=\s*"V515"', source)
path.write_text(source, encoding='utf-8')
for name in ('DesktopHost.cs', 'DesktopHost.manifest', 'DesktopPackage.appxmanifest',
             'build_desktop.ps1', 'lockscreen_installer.py', 'run_regression_checks.py', 'test_desktop.ps1'):
    target = ROOT / 'lockscreen' / name
    value = target.read_text(encoding='utf-8').replace('V514', 'V515').replace('v514', 'v515')
    value = value.replace('514.0.0.2', '515.0.0.0').replace('514.0.0.1', '515.0.0.0')
    target.write_text(value, encoding='utf-8')
