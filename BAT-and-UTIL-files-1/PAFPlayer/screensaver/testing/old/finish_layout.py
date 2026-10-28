"""Adapt screensaver development to the reorganized PAFPlayer project."""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

SIDE = Path(__file__).resolve().parent
PROJECT = SIDE.parent


def save(path, text):
    raw = path.read_bytes()
    stem = path.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt')
    backup = path.with_name(stem + '.bak'); index = 1
    while backup.exists(): backup = path.with_name(stem + f' ({index}).bak'); index += 1
    shutil.copyfile(path, backup)
    assert hashlib.sha256(raw).digest() == hashlib.sha256(backup.read_bytes()).digest()
    assert path.read_bytes() == raw, 'Concurrent edit refused'
    path.write_text(text, encoding='utf-8')


def edit(path, changes):
    text = path.read_text(encoding='utf-8-sig')
    for old, new in changes:
        assert text.count(old) == 1, (path, old, text.count(old))
        text = text.replace(old, new, 1)
    save(path, text)


runner = PROJECT / 'run_PAFPlayer_tests.py'
text = runner.read_text()
start = text.index('    source = Path(__file__).resolve().parent', text.index('def prepare():'))
end = text.index('    manifest = []', start)
text = text[:start] + '''    source = Path(__file__).resolve().parent
    repository = source.parent
    root = unique(source / 'tests/runs' / ('pafplayer-regression-audit-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))
    stage = root / 'stage'
    stage.mkdir(parents=True)
    roots = (source, source / 'tests', source / 'screensaver', source / 'releases', repository)
    tests = sorted(set().union(*(set(folder.glob(pattern)) for folder in roots[:3]
                                for pattern in ('test*PAFPlayer*.py', 'test*paf*.py', 'test_play_audio_file*.py')))
                   | set(repository.glob('test_paf_nest_exclusion.py')))
    files = set(tests)
    for test in tests:
        for node in ast.walk(ast.parse(test.read_text(encoding='utf-8-sig'))):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str): continue
            if len(node.value) >= 180 or '\\n' in node.value: continue
            for folder in roots:
                candidate = folder / node.value
                try:
                    if candidate.is_file() and candidate.parent == folder: files.add(candidate)
                except OSError: pass
    files.update(source.glob('PAFPlayer_*.py'))
    files.update((source / 'releases').glob('PAFPlayer_v*.py'))
    files.update((source / 'screensaver').glob('PAFPlayer_*.py'))
    files.update((source / 'releases').glob('pafplayer_v416_timing_fixture*.wav'))
    files.add(repository / 'winamp-status-from-file.pl')
    files.add(source / 'PAFPlayer.py')
    files.add(repository / 'play_audio_file.py')
''' + text[end:]
compile(text, str(runner), 'exec'); save(runner, text)
edit(SIDE / 'verify.py', [
    ('ROOT = SIDE.parent.parent', 'ROOT = SIDE.parent'),
    ('executable = build(SIDE)\noutput = SIDE /', 'output = SIDE /'),
    ('output.mkdir(exist_ok=False)', "output.mkdir(exist_ok=False)\nexecutable = build(SIDE, output / 'PAFPlayer.scr')")])
edit(SIDE / 'build_PAFPlayer_screensaver.py', [
    ('def build(root=None):', 'def build(root=None, output=None):'),
    ("    output = root / 'PAFPlayer.scr'", "    output = Path(output) if output is not None else root / 'PAFPlayer.scr'")])
edit(SIDE / 'PAFPlayer_screensaver.py', [
    ("        development = local.parent / 'PAFPlayer/screensaver/PAFPlayer.scr'", "        development = local.parent / 'screensaver/PAFPlayer.scr'"),
    ("        value = dict(protocol=1, session=self.session, close_revision=self.close_revision,", "        value = dict(protocol=1, player_version=self.runtime.app.PROGRAM_VERSION, session=self.session, close_revision=self.close_revision,")])
edit(SIDE / 'PAFPlayer_screensaver.cs', [
    ('public string Title = "", Lyric', 'public string Version = "", Title = "", Lyric'),
    ('Online = true, Enabled = Flag(map, "enabled"),', 'Online = true, Version = Text(map, "player_version", 40), Enabled = Flag(map, "enabled"),'),
    ('string title = content ? state.Title : state.Online ? "Visual screensaver disabled" : "Waiting for PAFPlayer";',
     'string title = content ? state.Title : state.Online ? "PAFPlayer detected — screensaver disabled" : "Waiting for PAFPlayer";'),
    ('            Text(g, state.Status, new RectangleF(',
     '            string status = state.Online && !state.Enabled ? "Enable Visual Screensaver in PAFPlayer controls. " + state.Version : state.Status;\n            Text(g, status, new RectangleF(')])
edit(SIDE / 'test_PAFPlayer_screensaver.cs', [
    ('            using (Bitmap art = new Bitmap(300, 300))', '''            if (args.Length > 1) {
                using (Server server = new Server()) using (Form parent = new Form()) {
                    IntPtr host = parent.Handle;
                    var info = new System.Diagnostics.ProcessStartInfo(args[1], "/p " + host.ToInt64() + " /port:" + server.Port) { UseShellExecute = false, CreateNoWindow = true, WindowStyle = System.Diagnostics.ProcessWindowStyle.Hidden };
                    using (var preview = System.Diagnostics.Process.Start(info)) {
                        try {
                            Thread.Sleep(1000);
                            Check(!preview.HasExited && server.States > 0, "real .scr preview process starts and polls");
                            parent.Dispose();
                            Check(preview.WaitForExit(5000) && preview.ExitCode == 0, "real .scr exits when preview parent closes");
                        } finally { if (!preview.HasExited) preview.Kill(); }
                    }
                }
            }
            using (Bitmap art = new Bitmap(300, 300))''')])
manifest = PROJECT / 'releases/pafplayer_v472_baseline.json'
data = json.loads(manifest.read_text())
data['baseline'] = str(PROJECT / 'releases/PAFPlayer_v471_before_visual_screensaver.py')
save(manifest, json.dumps(data, indent=2))
player = PROJECT / 'PAFPlayer.py'
line = next(line for line in player.read_text(encoding='utf-8-sig').splitlines() if line.startswith('_PAF_BUNDLED_SOURCES["PAFPlayer_screensaver"] = '))
edit(player, [(line, '_PAF_BUNDLED_SOURCES["PAFPlayer_screensaver"] = ' + repr((SIDE / 'PAFPlayer_screensaver.py').read_text(encoding='utf-8')))])
print('New project layout incorporated')
