"""Apply the sidecar folder layout and the preview lifecycle correction once."""
from datetime import datetime
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
SIDE = ROOT / 'PAFPlayer/screensaver'


def replace(path, changes):
    raw = path.read_bytes(); text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    for old, new in changes:
        assert text.count(old) == 1, (path, old, text.count(old))
        text = text.replace(old, new, 1)
    base = path.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt')
    backup = path.with_name(base + '.bak'); index = 1
    while backup.exists(): backup = path.with_name(base + f' ({index}).bak'); index += 1
    shutil.copyfile(path, backup)
    assert hashlib.sha256(raw).digest() == hashlib.sha256(backup.read_bytes()).digest()
    assert path.read_bytes() == raw, 'Concurrent edit refused'
    path.write_bytes(text.replace('\n', '\r\n' if b'\r\n' in raw else '\n').encode('utf-8'))


replace(SIDE / 'PAFPlayer_screensaver.py', [
    ("        return local if local.is_file() else Path('C:/BAT/PAFPlayer.scr')",
     "        development = local.parent / 'PAFPlayer/screensaver/PAFPlayer.scr'\n        for candidate in (development, local):\n            if candidate.is_file(): return candidate\n        return Path('C:/BAT/PAFPlayer.scr')")])
replace(SIDE / 'PAFPlayer_screensaver.cs', [
    ('        bool cursorHidden;', '        bool cursorHidden, resourcesReleased;'),
    ('            TopMost = options.Mode == "s";', '            if (options.Mode == "p") TopLevel = false;\n            TopMost = options.Mode == "s";'),
    ('        protected override void OnHandleCreated(EventArgs e) {', '''        protected override CreateParams CreateParams {
            get {
                CreateParams parameters = base.CreateParams;
                if (options != null && options.Mode == "p") {
                    parameters.Parent = options.Parent;
                    parameters.Style = (parameters.Style | 0x40000000) & ~unchecked((int)0x80000000);
                }
                return parameters;
            }
        }
        protected override void OnHandleCreated(EventArgs e) {'''),
    ('''        protected override void OnFormClosed(FormClosedEventArgs e) {
            timer.Stop(); timer.Dispose(); poller.Dispose(); mailbox.Dispose();
            if (artwork != null) artwork.Dispose(); if (cursorHidden) Cursor.Show();
            base.OnFormClosed(e);
        }''', '''        protected override void Dispose(bool disposing) {
            if (disposing && !resourcesReleased) {
                resourcesReleased = true;
                timer.Stop(); timer.Dispose(); if (poller != null) poller.Dispose(); mailbox.Dispose();
                if (artwork != null) artwork.Dispose(); if (cursorHidden) Cursor.Show();
            }
            base.Dispose(disposing);
        }''')])
replace(ROOT / 'run_PAFPlayer_tests.py', [
    ("root = unique(source / ('pafplayer-regression-audit-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))",
     "root = unique(source / 'PAFPlayer' / ('pafplayer-regression-audit-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))"),
    ("tests = sorted(set(source.glob('test*PAFPlayer*.py')) | set(source.glob('test*paf*.py')) | set(source.glob('test_play_audio_file*.py')))",
     "tests = sorted(set(source.glob('test*PAFPlayer*.py')) | set(source.glob('test*paf*.py')) | set(source.glob('test_play_audio_file*.py')) | set((source / 'PAFPlayer/screensaver').glob('test*PAFPlayer*.py')))"),
    ("    files.update(source.glob('PAFPlayer_*.py'))", "    files.update(source.glob('PAFPlayer_*.py'))\n    files.update((source / 'PAFPlayer').glob('PAFPlayer_v*.py'))\n    files.update((source / 'PAFPlayer/screensaver').glob('PAFPlayer_*.py'))")])
# Refresh only our own embedded module while preserving concurrent unrelated edits.
player = ROOT / 'PAFPlayer.py'
line = next(line for line in player.read_text(encoding='utf-8-sig').splitlines() if line.startswith('_PAF_BUNDLED_SOURCES["PAFPlayer_screensaver"] = '))
replace(player, [(line, '_PAF_BUNDLED_SOURCES["PAFPlayer_screensaver"] = ' + repr((SIDE / 'PAFPlayer_screensaver.py').read_text(encoding='utf-8')))])
print('Updated nested paths, preview lifecycle, full-suite discovery and embedded bridge')
