"""Install the tested sidecar release, with exact backups and path disclosure."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

PROJECT = Path(__file__).resolve().parent.parent
VERIFIED = PROJECT / 'screensaver/verification-20260929-161816'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(path):
    candidate, index = path, 1
    while candidate.exists():
        candidate = path.with_name(path.stem + f' ({index})' + path.suffix); index += 1
    return candidate


def main():
    summary = json.loads((VERIFIED / 'summary.json').read_text())
    assert summary['successful']
    assert digest(PROJECT / 'PAFPlayer.py') == summary['player_sha256']
    assert digest(VERIFIED / 'PAFPlayer.scr') == summary['screensaver_sha256']
    plan = json.loads((PROJECT / 'releases/pafplayer_v474_deployment_plan.json').read_text())
    for item in plan:
        target = Path(item['target'])
        assert target.parent.resolve() in (Path('C:/BAT').resolve(), (PROJECT / 'screensaver').resolve())
        assert digest(Path(item['source'])) == item['sha256']
        assert (digest(target) if target.exists() else None) == item['prior_sha256'], 'Target changed since preflight'

    # The obsolete preview executable is in use. Stop only this project's
    # preview instances; never stop a Python player/audio process or /s session.
    import psutil
    target_exe = (PROJECT / 'screensaver/PAFPlayer.scr').resolve()
    for process in psutil.process_iter(['name']):
        try:
            if str(process.info['name']).casefold() != 'pafplayer.scr': continue
            args = process.cmdline()
            if args and Path(args[0]).resolve() == target_exe and any(arg.lower() == '/p' or arg.lower().startswith('/p:') for arg in args[1:]):
                process.terminate(); process.wait(timeout=3)
                print('Closed obsolete screensaver preview PID', process.pid, flush=True)
        except psutil.NoSuchProcess: pass

    changes = []
    try:
        for item in plan:
            source, target = Path(item['source']), Path(item['target'])
            operation = 'modified' if target.exists() else 'created'
            if target.exists():
                backup = unique(target.with_name(target.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')))
                shutil.copy2(target, backup)
                assert digest(backup) == digest(target), 'Backup verification failed'
                changes.append({'path': str(backup), 'operation': 'created', 'sha256': digest(backup)})
            shutil.copy2(source, target)
            changes.append({'path': str(target), 'operation': operation, 'sha256': digest(target)})
            assert digest(target) == item['sha256'], 'Installation checksum failed'
    finally:
        report = unique(PROJECT / 'releases/PAFPlayer-v474-installed-files.json')
        with report.open('x', encoding='utf-8') as output:
            json.dump({'version': 'V474', 'changes': changes}, output, indent=2)
        print(json.dumps({'report': str(report), 'changes': changes}, indent=2), flush=True)


if __name__ == '__main__': main()
