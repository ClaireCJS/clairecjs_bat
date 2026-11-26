"""Safe model-store relocation with verified copies and Windows junctions."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import time


def sources():
    base=Path(os.environ.get('LOCALAPPDATA') or (Path.home()/'AppData'/'Local'))/'PAFPlayer'/'support'
    return [('voice-models',base/'voice-models','.'),('piper',base/'piper','Piper'),('ollama',Path.home()/'.ollama'/'models','Ollama')]


def scan(root):
    root=Path(root);files=[];dirs=[]
    for directory,subdirs,names in os.walk(root,followlinks=False):
        directory=Path(directory);subdirs.sort();names.sort();relative=directory.relative_to(root);dirs.append(relative)
        for name in subdirs:
            item=directory/name
            if item.is_symlink() or (hasattr(item,'is_junction') and item.is_junction()):raise ValueError('Nested link requires manual review: '+str(item))
        for name in names:
            item=directory/name
            if item.is_symlink():raise ValueError('Nested link requires manual review: '+str(item))
            stat=item.stat();files.append((relative/name,stat.st_size,stat.st_mtime_ns))
    return dirs,files


def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):value.update(block)
    return value.digest()


def backup_name(path):
    path=Path(path);stamp=time.strftime('%Y%m%d%H%M');base=path.with_name(path.name+'.bak.'+stamp+'.replaced-by-chatgpt.bak');candidate=base;index=0
    while candidate.exists():
        index+=1;candidate=base.with_name(base.name[:-4]+f' ({index}).bak')
    return candidate




def preference_path():
    base=Path(os.environ.get('LOCALAPPDATA') or (Path.home()/'AppData'/'Local'))/'PAFPlayer'/'support'
    return base/'model-storage.json'


def preferred_root():
    configured=os.environ.get('PAFPLAYER_MODEL_ROOT','').strip()
    if configured:return Path(configured).expanduser()
    try:
        import json
        value=json.loads(preference_path().read_text(encoding='utf-8'))
        if isinstance(value,dict) and isinstance(value.get('root'),str) and value['root'].strip():return Path(value['root']).expanduser()
    except (OSError,ValueError):pass
    from PAFPlayer_runtime_paths import runtime_root
    return runtime_root()/'models'


def save_preferred_root(root):
    """Persist a model path using a verified backup before replacing settings."""
    import json
    path=preference_path();path.parent.mkdir(parents=True,exist_ok=True)
    value=Path(root).expanduser().resolve()
    data=(json.dumps({'root':str(value)},indent=2)+'\n').encode('utf-8')
    if path.exists():
        backup=backup_name(path);shutil.copy2(path,backup)
        if digest(path)!=digest(backup):raise OSError('Model location backup verification failed')
    stage=path.with_name(path.name+'.tmp')
    suffix=0
    while stage.exists():suffix+=1;stage=path.with_name(path.name+f'. ({suffix}).tmp')
    with stage.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    os.replace(stage,path)
    workflow=path.parent.parent/'workflows'/'settings.json'
    if workflow.is_file():
        try:settings=json.loads(workflow.read_text(encoding='utf-8'))
        except (OSError,ValueError):settings={}
        if not isinstance(settings,dict):settings={}
        dj=settings.get('ai_dj')
        if not isinstance(dj,dict):dj={}
        dj['model_storage_path']=str(value);settings['ai_dj']=dj
        payload=(json.dumps(settings,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        backup=backup_name(workflow);shutil.copy2(workflow,backup)
        if digest(workflow)!=digest(backup):raise OSError('AI DJ settings backup verification failed')
        temp=workflow.with_name(workflow.name+'.tmp')
        suffix=0
        while temp.exists():suffix+=1;temp=workflow.with_name(workflow.name+f' ({suffix}).tmp')
        with temp.open('xb') as stream:stream.write(payload);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,workflow)
    return value


def create_junction(link,target):
    if os.name!='nt':raise OSError('Automatic model relocation currently requires Windows junctions')
    env=os.environ.copy();env['PAF_MODEL_JUNCTION_LINK']=str(link);env['PAF_MODEL_JUNCTION_TARGET']=str(target)
    command="New-Item -ItemType Junction -Path $env:PAF_MODEL_JUNCTION_LINK -Target $env:PAF_MODEL_JUNCTION_TARGET -ErrorAction Stop | Out-Null"
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],env=env,check=True,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,startupinfo=startup,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    if not Path(link).is_dir() or not os.path.samefile(link,target):
        raise OSError('Junction creation did not link to the verified model store')


def relocate(target, progress=lambda text:None, source_list=None, link=create_junction):
    """Copy and hash-verify, then preserve original directories and switch paths.

    Originals are renamed to sibling backups and retained. Failed copies and
    backups are never deleted automatically. Existing destination files are
    never overwritten. Callers can retry using a different empty destination.
    """
    target=Path(target).expanduser().resolve()
    specs=list(sources() if source_list is None else source_list)
    existing=[(name,Path(src),rel) for name,src,rel in specs if Path(src).is_dir()]
    if not existing:raise ValueError('No model stores were found')
    if target.exists() and (not target.is_dir() or any(target.iterdir())):raise FileExistsError('Choose an empty destination directory; existing files will not be overwritten')
    for name,src,rel in existing:
        resolved=src.resolve();dest=(target/rel).resolve()
        if dest==resolved or dest.is_relative_to(resolved) or resolved.is_relative_to(dest):raise ValueError('Destination overlaps a source: '+name)
    # On subsequent moves the voice root already contains Piper/Ollama; copy
    # that physical tree once and retain the separate compatibility junctions.
    voice=next((src for name,src,rel in existing if name=='voice-models' and rel=='.'),None)
    aliases=[];copy_specs=[]
    for name,src,rel in existing:
        if name in ('piper','ollama') and voice is not None and src.resolve()==(voice/rel).resolve():
            aliases.append((name,src,target/rel));continue
        if name=='voice-models' and voice is not None:
            for other,sub in (('piper','Piper'),('ollama','Ollama')):
                if (voice/sub).exists() and not any(n==other and q.resolve()==(voice/sub).resolve() for n,q,_ in existing):
                    raise FileExistsError('Voice model folder conflicts with '+sub+' destination')
        copy_specs.append((name,src,rel))
    progress('Inventorying model files; original data will be retained as backups.')
    inventory=[];total=0
    for name,src,rel in copy_specs:
        dirs,files=scan(src);inventory.append((name,src,target/rel,dirs,files));total+=sum(size for _,size,_ in files)
    probe=target
    while not probe.exists() and probe!=probe.parent:probe=probe.parent
    if shutil.disk_usage(probe).free<total:raise OSError('Not enough destination free space for a verified copy')
    target.mkdir(parents=True,exist_ok=True);copied=0;last=0;started=time.monotonic()
    for name,src,dest,dirs,files in inventory:
        progress('Copying '+name)
        for rel in dirs:(dest/rel).mkdir(parents=True,exist_ok=True)
        for rel,size,mtime in files:
            source=src/rel;output=dest/rel;hash_source=hashlib.sha256()
            with source.open('rb') as a,output.open('xb') as b:
                while True:
                    block=a.read(8*1024*1024)
                    if not block:break
                    b.write(block);hash_source.update(block);copied+=len(block)
                    now=time.monotonic()
                    if now-last>=5:
                        if hasattr(progress,'bytes'):progress.bytes('Copying model stores',copied,total,copied/max(.001,now-started))
                        progress(f'Copied {copied/1073741824:.1f} / {total/1073741824:.1f} GiB; verifying each file');last=now
            stat=source.stat()
            if stat.st_size!=size or stat.st_mtime_ns!=mtime or digest(output)!=hash_source.digest():raise OSError('Source changed or verification failed: '+str(source))
            shutil.copystat(source,output)
        if scan(src)[1]!=files:raise OSError('Model store changed during copy: '+str(src))
        progress('Verified '+name)
    moved=[]
    for name,src,dest,dirs,files in inventory:
        if scan(src)[1]!=files:raise OSError('Model store changed before switch: '+str(src))
    switches=[(name,src,dest) for name,src,dest,_,_ in inventory]+aliases
    for name,src,dest in sorted(switches,key=lambda item:item[0]!='ollama'):
        backup=backup_name(src);src.rename(backup)
        try:link(src,dest)
        except Exception:
            if not src.exists():backup.rename(src)
            raise
        moved.append({'name':name,'old_path':str(src),'new_path':str(dest),'backup':str(backup)})
        progress('Using '+str(dest)+'; original preserved at '+str(backup))
    return moved
