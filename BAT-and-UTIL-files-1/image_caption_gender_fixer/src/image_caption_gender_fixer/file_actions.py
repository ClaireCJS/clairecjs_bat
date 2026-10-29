"""Explicit artwork-window actions on the queued source, never preview crops."""
from pathlib import Path, PureWindowsPath
from .errors import IntegrityError
from .fs import available,folder_lock,identity,move,recycle,relative_file,sha256,source_lease,validate_path


def rename_target(source,name):
    source=Path(source)
    if not isinstance(name,str) or not name or any(c in name for c in '<>:"/\\|?*') or PureWindowsPath(name).is_reserved():
        raise IntegrityError('Enter a valid filename without a folder or Windows reserved characters.')
    destination=relative_file(source.parent,name)
    if destination.suffix.casefold()!=source.suffix.casefold():
        raise IntegrityError('Keep the existing image extension; Rename does not convert the image format.')
    from .cli import product_name
    if product_name(destination):raise IntegrityError('That name is reserved for ICGF output or backups.')
    return destination


def _verify(source,item,expected_identity=None):
    if sha256(source)!=item['hash'] or (expected_identity is not None and identity(source)!=expected_identity):
        raise IntegrityError('Source changed since review; file action was refused.')


def reconcile(app,item,session):
    """Finish bookkeeping after interruption between a file move and job save."""
    action=item.get('source_file_action')
    if not action:return
    source=validate_path(Path(action['from']),app.root)
    if action['kind']=='rename':
        destination=validate_path(Path(action['to']),app.root)
        if destination.parent!=source.parent:raise IntegrityError('Invalid rename recovery destination.')
        if source.exists():
            _verify(source,item,action['identity']) # No move happened; retain source.
        else:
            _verify(destination,item,action['identity'])
            item['path']=str(destination)
    elif action['kind']=='recycle':
        if source.exists():_verify(source,item,action['identity'])
        else:item.update(state='skipped',disposition='recycled')
    else:raise IntegrityError('Unknown image file action; retained for inspection.')
    item.pop('source_file_action',None);app.sessions.save(session)


def apply(app,source,item,session,payload,expected_identity):
    """Journal before mutation, use non-overwriting moves and verified recycling."""
    source=validate_path(source,app.root)
    if payload.get('source')!=str(source):raise IntegrityError('Stale artwork file action was refused.')
    kind=payload['action']
    if kind not in ('rename_image','recycle_image'):raise IntegrityError('Unknown image file action.')
    if kind=='recycle_image' and payload.get('confirmed') is not True:
        raise IntegrityError('Recycle requires explicit confirmation in the artwork window.')
    with folder_lock(source.parent),source_lease(source):
        _verify(source,item,expected_identity)
        destination=rename_target(source,payload.get('name')) if kind=='rename_image' else None
        if destination==source:return source
        if destination is not None:destination=available(destination)
        journal={'kind':'rename' if destination is not None else 'recycle','from':str(source),'identity':expected_identity}
        if destination is not None:journal['to']=str(destination)
        item['source_file_action']=journal;app.sessions.save(session)
        if destination is not None:
            move(source,destination);item['path']=str(destination)
            item.setdefault('renamed_from',[]).append(str(source))
        else:
            recycle(source);item.update(state='skipped',disposition='recycled')
        item.pop('source_file_action',None);app.sessions.save(session)
        return destination
