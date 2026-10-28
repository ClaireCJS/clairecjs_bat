"""Recoverable, byte-preserving correction of the legacy output suffix."""
import json
import os
import re
import uuid
from pathlib import Path
from .fs import available,canonical,folder_lock,identity,move,relative_file,sha256,source_lease,validate_path
from .history import History
from .errors import IntegrityError

def corrected_name(path):
    stem=re.sub(r'-gendeerfixed(?=(?: \(\d+\))*$)','-genderfixed',Path(path).stem,flags=re.I)
    return stem+Path(path).suffix if stem!=Path(path).stem else None

def append(path,data):
    with path.open('ab') as handle:handle.write((canonical(data)+'\n').encode('utf-8'));handle.flush();os.fsync(handle.fileno())

def finish(root,journal,record):
    if record.get('application')!='icgf-name-migration' or str(uuid.UUID(record['migration']))+'.jsonl'!=journal.name:
        raise IntegrityError('Invalid filename migration journal retained.')
    folder=validate_path(Path(record['folder']),root)
    source=relative_file(folder,record['source']);target=relative_file(folder,record['target'])
    validate_path(source,root);validate_path(target,root)
    if corrected_name(source) is None or target==source:raise IntegrityError('Invalid legacy rename intent.')
    with folder_lock(folder):
        history=History(folder);history.validate()
        if record.get('event'):
            active=history.transactions().get(record['event']['transaction'])
            if not active or active['event']=='undone' or active['corrected'] not in (source.name,target.name) or any(active.get(k)!=v for k,v in record['event'].items()):
                raise IntegrityError('Filename migration disagrees with active history; files retained.')
        if source.exists():
            if target.exists() or sha256(source)!=record['hash'] or identity(source)[:2]!=record['identity'][:2]:
                raise IntegrityError('Filename migration collision or changed source; both files retained.')
            with source_lease(source):move(source,target)
        if not target.is_file() or sha256(target)!=record['hash'] or identity(target)[:2]!=record['identity'][:2]:
            raise IntegrityError('Renamed output did not verify; migration evidence retained.')
        if record.get('event'):
            event=dict(record['event']);event.update(corrected=target.name,previous_corrected=source.name,migration=record['migration'])
            history.append('renamed',**event)
        append(journal,{'completed':True,'migration':record['migration']})
    return {'from':str(source),'to':str(target),'state':'renamed'}

def recover(root):
    directory=Path(root)/'runtime/state/name-migrations';results=[]
    if not directory.exists():return results
    for path in directory.glob('*.jsonl'):
        from .fs import reparse
        if reparse(path):raise IntegrityError('Linked filename migration journal refused.')
        lines=path.read_bytes().splitlines();record=json.loads(lines[0])
        if len(lines)>1:
            complete=json.loads(lines[-1])
            if complete.get('completed') and complete.get('migration')==record.get('migration'):continue
        results.append(finish(root,path,record))
    return results

def migrate(root,source):
    source=validate_path(Path(source),root);name=corrected_name(source)
    if name is None:return None
    with folder_lock(source.parent):
        history=History(source.parent);history.validate();digest=sha256(source)
        matches=[e for e in history.transactions().values() if e.get('corrected')==source.name and e['event']!='undone']
        if len(matches)>1:raise IntegrityError('Ambiguous corrected output history; filename retained.')
        event=matches[0] if matches else None
        # Changed corrected images keep the conversion's original expected hash;
        # undo will still flag and preserve their changed content.
        target=available(source.with_name(name));migration=str(uuid.uuid4())
        record={'application':'icgf-name-migration','migration':migration,'folder':str(source.parent),
            'source':source.name,'target':target.name,'hash':digest,'identity':identity(source),
            'event':{key:value for key,value in (event or {}).items() if key in ('transaction','original','backup','original_hash','corrected_hash','profile','program_version','rules_fingerprint','original_size','corrected_size')}}
        directory=Path(root)/'runtime/state/name-migrations';directory.mkdir(parents=True,exist_ok=True)
        journal=directory/(migration+'.jsonl')
        with journal.open('xb') as handle:handle.write((canonical(record)+'\n').encode('utf-8'));handle.flush();os.fsync(handle.fileno())
    return finish(root,journal,record)
