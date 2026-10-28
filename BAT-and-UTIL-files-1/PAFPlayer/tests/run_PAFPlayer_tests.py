"""Run ALL embedded and standalone player tests in isolated, preserved staging.

Uses the real compatibility entry point. Returns nonzero for any failure/error.
Run with python -B -X utf8 tests/run_PAFPlayer_tests.py. JSON and logs are retained.
"""
from __future__ import annotations
import ast
import datetime
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unique(path):
    candidate = path
    index = 1
    while candidate.exists():
        candidate = path.with_name(path.stem + f" ({index})" + path.suffix)
        index += 1
    return candidate


def install_guards(root):
    """Constrain test writes, preserve overwritten fixtures, and reject live mutations."""
    root = str(root.resolve()).casefold() + os.sep
    local = threading.local()
    blocks = []
    real_now = datetime.datetime.now
    used_backups = set()
    def inside(path):
        if isinstance(path, int):
            return True
        if os.fsdecode(path).casefold() in ('nul', 'nul:', r'\\.\nul'):
            return True
        value = os.path.abspath(os.fsdecode(path)).casefold()
        return value == root[:-1] or value.startswith(root)
    def check(path):
        if not inside(path):
            blocks.append(str(path))
            raise PermissionError("Audit blocked write outside staging: " + str(path))
    def backup(path):
        if isinstance(path, int) or not os.path.isfile(path):
            return
        target = Path(os.fsdecode(path))
        # Honor a verified backup just created by the code under test.
        for existing in target.parent.glob(target.name + '.bak.*.replaced-by-chatgpt*.bak'):
            key = str(existing)
            if key not in used_backups and existing.stat().st_mtime_ns >= target.stat().st_mtime_ns and digest(existing) == digest(target):
                used_backups.add(key)
                return
        now = real_now()
        stamp = f'{now.year:04d}{now.month:02d}{now.day:02d}{now.hour:02d}{now.minute:02d}'
        saved = unique(target.with_name(target.name + '.bak.' + stamp + '.replaced-by-chatgpt.bak'))
        local.busy = True
        try:
            # Avoid mocked shutil.copy2 in backup-corruption tests.
            with open(target, 'rb') as src, open(saved, 'xb') as dst:
                shutil.copyfileobj(src, dst)
            if digest(target) != digest(saved):
                raise OSError('Audit fixture backup verification failed')
            used_backups.add(str(saved))
        finally:
            local.busy = False
    def audit(event, args):
        if getattr(local, 'busy', False):
            return
        if event == 'open':
            path, mode, flags = args
            if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                check(path)
                if not flags & os.O_EXCL:
                    backup(path)
        elif event in ('os.rename',):
            check(args[0]); check(args[1]); backup(args[1])
        elif event in ('os.mkdir', 'os.chmod', 'os.utime'):
            check(args[0])
        elif event in ('os.remove', 'os.rmdir'):
            raise PermissionError('Audit disallows permanent deletion: ' + str(args[0]))
        elif event == 'sqlite3.connect' and args[0] != ':memory:':
            check(args[0]); backup(args[0])
        elif event in ('winreg.SetValue', 'winreg.DeleteKey', 'winreg.DeleteValue', 'winreg.CreateKey'):
            blocks.append(event)
            raise PermissionError('Audit disallows live registry writes: ' + event)
        elif event == 'socket.connect':
            address = args[1]
            if isinstance(address, tuple) and address[0] not in ('127.0.0.1', 'localhost', '::1'):
                blocks.append('outbound socket')
                raise PermissionError('Audit permits only loopback networking')
    # Preserve test directories as evidence instead of tempfile's destructive cleanup.
    def retain(self):
        self._finalizer.detach()
    tempfile.TemporaryDirectory.cleanup = retain
    from send2trash import send2trash
    def recycle(path, *args, **kwargs):
        check(path)
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        send2trash(os.path.abspath(path))
    os.unlink = os.remove = recycle
    if hasattr(Path, '_accessor'):
        # Python 3.10 caches nt.unlink before os.unlink can be replaced.
        Path._accessor.unlink = recycle
    sys.addaudithook(audit)
    return blocks


def child(stage, module_name, result_path, selected=None):
    root = stage.parent
    work = unique(root / ('work-' + module_name.replace('.', '-')))
    work.mkdir()
    for name in ('TEMP', 'TMP', 'LOCALAPPDATA', 'APPDATA'):
        os.environ[name] = str(work)
    os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(work / 'history.sqlite3')
    for key in tuple(os.environ):
        if key.startswith('LASTFM_') or key == 'PAFPLAYER_DISCORD_WEBHOOK':
            os.environ.pop(key)
    tempfile.tempdir = str(work)
    sys.path.insert(0, str(stage))
    os.chdir(stage)
    sys.argv = [str(stage / 'PAFPlayer.py'), '--unit-tests']
    blocks = install_guards(root)
    # Equality checks remain unchanged; avoid quadratic pretty-diffs of ANSI frames.
    def compact_diff(left, right, *args, **kwargs):
        import itertools
        for index, (a, b) in enumerate(itertools.zip_longest(left, right)):
            if a != b:
                yield f'First differing diagnostic line: {index}'
                yield '- ' + str(a)[:1200]
                yield '+ ' + str(b)[:1200]
                return
    unittest.case.difflib.ndiff = compact_diff
    entries = []
    progress = open(result_path.with_suffix('.progress.jsonl'), 'x', encoding='utf-8')
    class Result(unittest.TestResult):
        def startTest(self, test):
            super().startTest(test)
            self.started = time.monotonic()
            self.current_test = test.id()
            progress.write(json.dumps({'start': test.id()}) + '\n'); progress.flush()
        def record(self, test, outcome, detail=''):
            entries.append({'test': test.id(), 'parent_test': self.current_test, 'outcome': outcome, 'seconds': round(time.monotonic()-self.started, 3), 'detail': detail[:6000] + ('\n... [truncated] ...\n' + detail[-2500:] if len(detail)>6000 else '')})
            progress.write(json.dumps(entries[-1]) + '\n'); progress.flush()
        def addSuccess(self, test):
            super().addSuccess(test); self.record(test, 'pass')
        def addFailure(self, test, err):
            super().addFailure(test, err); self.record(test, 'failure', self._exc_info_to_string(err, test))
        def addError(self, test, err):
            super().addError(test, err); self.record(test, 'error', self._exc_info_to_string(err, test))
        def addSkip(self, test, reason):
            super().addSkip(test, reason); self.record(test, 'skip', reason)
        def addExpectedFailure(self, test, err):
            super().addExpectedFailure(test, err); self.record(test, 'expected-failure', self._exc_info_to_string(err,test))
        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            if err:
                self.record(subtest, 'subtest-failure', self._exc_info_to_string(err,test))
    started = time.monotonic()
    try:
        module = importlib.import_module(module_name)
        if selected:
            suite = unittest.defaultTestLoader.loadTestsFromNames(selected, module)
        else:
            suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        result = Result()
        suite.run(result)
        report = {'module': module_name, 'count': result.testsRun, 'successful': result.wasSuccessful(), 'entries': entries, 'blocks': sorted(set(blocks)), 'seconds': round(time.monotonic()-started, 2)}
    except BaseException:
        import traceback
        report = {'module': module_name, 'count': 0, 'successful': False, 'import_error': traceback.format_exc(), 'entries': entries, 'blocks': sorted(set(blocks))}
    result_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    progress.close()


def prepare():
    source = Path(__file__).resolve().parents[1]
    repository = source.parent
    root = unique(source / 'tests/runs' / ('pafplayer-regression-audit-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')))
    stage = root / 'stage'
    stage.mkdir(parents=True)
    roots = (source, source / 'tests', source / 'screensaver',
             source / 'screensaver' / 'testing', source / 'releases', repository)
    tests = sorted(set().union(*(set(folder.glob(pattern)) for folder in roots[:4]
                                for pattern in ('test*PAFPlayer*.py', 'test*paf*.py', 'test_play_audio_file*.py')))
                   | set(repository.glob('test_paf_nest_exclusion.py')))
    files = set(tests)
    for test in tests:
        for node in ast.walk(ast.parse(test.read_text(encoding='utf-8-sig'))):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str): continue
            if len(node.value) >= 180 or '\n' in node.value: continue
            for folder in roots:
                candidate = folder / node.value
                try:
                    if candidate.is_file() and candidate.parent == folder: files.add(candidate)
                except OSError: pass
    files.update((source / 'src').glob('PAFPlayer_*.py'))
    files.update((source / 'releases').glob('PAFPlayer_v*.py'))
    files.update((source / 'screensaver' / 'src').glob('PAFPlayer_*.py'))
    files.update((source / 'releases').glob('pafplayer_v416_timing_fixture*.wav'))
    files.add(repository / 'winamp-status-from-file.pl')
    files.add(source / 'PAFPlayer.py')
    files.add(repository / 'play_audio_file.py')
    manifest = []
    for path in sorted(files):
        if not path.is_file():
            continue
        destination = stage / path.name
        shutil.copyfile(path, destination)
        before, after = digest(path), digest(destination)
        if before != after:
            raise OSError('Staging checksum mismatch: ' + str(path))
        manifest.append({'source': str(path), 'staged': str(destination), 'sha256': before})
    (root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    return root, stage, ['PAFPlayer'] + [p.stem for p in tests]


def run():
    root, stage, modules = prepare()
    print(str(root), flush=True)
    reports = []
    for module in modules:
        result_path = root / (module + '.json')
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(stage)+os.pathsep+str(Path(__file__).resolve().parent))
        with open(root / (module + '.log'), 'xb') as log:
            command = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()), '--child', str(stage), module, str(result_path)]
            try:
                completed = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env, timeout=360)
            except subprocess.TimeoutExpired:
                print(module + ': TIMEOUT', flush=True)
                reports.append({'module':module, 'timeout':True}); continue
        if result_path.exists():
            report = json.loads(result_path.read_text(encoding='utf-8'))
            reports.append(report)
            counts = {status:sum(e['outcome']==status for e in report['entries']) for status in ('pass','failure','error','skip','subtest-failure')}
            print(module + ': ' + json.dumps({'run':report['count'], **counts, 'import_error':bool(report.get('import_error'))}), flush=True)
        else:
            reports.append({'module': module, 'exit_code':completed.returncode, 'missing_report':True})
            print(module + ': MISSING REPORT', flush=True)
    (root / 'results.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    counts = {}
    for report in reports:
        outcomes = {}
        for entry in report.get('entries', []):
            key = entry.get('parent_test') or entry['test']
            status = entry['outcome']
            if status == 'subtest-failure': status = 'failure'
            if outcomes.get(key) not in ('failure', 'error'): outcomes[key] = status
        for status in outcomes.values(): counts[status] = counts.get(status, 0) + 1
    successful = all(report.get('successful', False) for report in reports)
    summary = {'tests_run':sum(report.get('count',0) for report in reports),
               'outcomes':counts, 'successful':successful}
    (root / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print('COMPLETE ' + str(root) + ' ' + json.dumps(summary), flush=True)
    return 0 if successful else 1


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':
        child(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]), sys.argv[5:] or None)
    else:
        sys.exit(run())
