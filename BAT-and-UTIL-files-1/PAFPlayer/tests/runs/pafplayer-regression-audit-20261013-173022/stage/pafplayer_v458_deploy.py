"""Publish reviewed V458 files with verified sibling backups and exact disclosure."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(path):
    candidate, number = path, 1
    while candidate.exists():
        candidate = path.with_name(f'{path.stem} ({number}){path.suffix}')
        number += 1
    return candidate


def main():
    plan = json.loads((ROOT / 'releases/PAFPlayer-v458-deployment-plan.json').read_text())
    for item in plan:
        source, target = Path(item['source']), Path(item['path'])
        if target.parent.resolve() != Path('C:/BAT').resolve():
            raise ValueError('Unexpected deployment directory')
        if digest(source) != item['source_sha256']:
            raise ValueError('Source changed since release validation: ' + str(source))
        if (digest(target) if target.exists() else None) != item['prior_sha256']:
            raise ValueError('Installed file changed since preflight: ' + str(target))
    changes = []
    try:
        for item in plan:
            source, target = Path(item['source']), Path(item['path'])
            operation = 'modified' if target.exists() else 'created'
            if target.exists():
                backup = unique(target.with_name(target.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')))
                shutil.copy2(target, backup)
                if digest(target) != digest(backup):
                    raise OSError('Replacement backup verification failed: ' + str(target))
                changes.append({'path': str(backup), 'operation': 'created', 'sha256': digest(backup)})
            shutil.copy2(source, target)
            changes.append({'path': str(target), 'operation': operation, 'sha256': digest(target)})
            if digest(target) != item['source_sha256']:
                raise OSError('Installed checksum does not match validated source')
    finally:
        report = unique(ROOT / 'releases/PAFPlayer-v458-installed-files.json')
        with report.open('x', encoding='utf-8') as stream:
            json.dump({'version': 'V458', 'changes': changes}, stream, indent=2)
        print(json.dumps({'report': str(report), 'changes': changes}, indent=2), flush=True)


if __name__ == '__main__':
    main()
