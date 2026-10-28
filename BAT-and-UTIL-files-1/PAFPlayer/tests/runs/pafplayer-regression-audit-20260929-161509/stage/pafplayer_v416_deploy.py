"""Install the reviewed release; preserve and verify every replaced C:\BAT byte."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import shutil

from pafplayer_v416_edit import unique

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'pafplayer_v416_release_manifest.json').read_text())
source = Path(manifest['source'])
snapshot = Path(manifest['versioned_source'])
data = source.read_bytes()
assert hashlib.sha256(data).hexdigest() == manifest['sha256'], 'Source changed since validation/package'
assert snapshot.read_bytes() == data, 'Versioned snapshot mismatch'
compile(data, str(source), 'exec')
destination = Path(r'C:\BAT\play_audio_file.py')
assert destination.parent.resolve() == Path(r'C:\BAT').resolve()
old = destination.read_bytes()
assert hashlib.sha256(old).hexdigest() == manifest['installed_before_sha256'], 'Installed player changed; review before replacing'
backup = unique(destination.with_name(destination.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')))
shutil.copy2(destination, backup)
assert backup.read_bytes() == old, 'Backup verification failed'
print('CREATED ' + str(backup), flush=True)
release_copy = unique(destination.parent / snapshot.name)
release_copy.write_bytes(data)
assert release_copy.read_bytes() == data
print('CREATED ' + str(release_copy), flush=True)
destination.write_bytes(data)
assert destination.read_bytes() == data
print('MODIFIED ' + str(destination), flush=True)
record = {'installed_at': datetime.now().isoformat(), 'sha256': manifest['sha256'],
          'changes': [{'path': str(backup), 'operation': 'created'},
                      {'path': str(release_copy), 'operation': 'created'},
                      {'path': str(destination), 'operation': 'modified'}]}
log = unique(root / 'pafplayer_v416_deployment.json')
log.write_text(json.dumps(record, indent=2), encoding='utf-8')
print('Verified identical canonical and versioned copies; deployment log: ' + str(log))
