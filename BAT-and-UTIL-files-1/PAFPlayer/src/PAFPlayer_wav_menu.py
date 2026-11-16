"""Optional per-user Explorer action for sending WAV files to PAFPlayer."""
from pathlib import Path
import os
import subprocess
import sys

VERB_ROOT = r'Software\Classes\SystemFileAssociations\.wav\shell'
VERB_NAME = 'PAFPlayer.Enqueue'
LABEL = 'Queue in PAFPlayer'


def command_for(script, python=None):
    python=str(python or sys.executable);script=str(Path(script).resolve())
    return subprocess.list2cmdline([python,'-B',script,'--enqueue-or-play'])+' "%1"'


def register(script, *, registry=None, python=None):
    """Add a new per-user WAV verb; never overwrite a pre-existing verb."""
    if registry is None:
        if os.name!='nt':raise OSError('Windows Explorer integration requires Windows')
        import winreg as registry
    expected=command_for(script,python)
    for number in range(1000):
        name=VERB_NAME+(f' ({number})' if number else '')
        path=VERB_ROOT+'\\'+name
        try:
            with registry.OpenKey(registry.HKEY_CURRENT_USER,path+'\\command') as key:
                current=registry.QueryValueEx(key,'')[0]
            if current==expected:return path,False
            continue
        except FileNotFoundError:
            try:
                with registry.OpenKey(registry.HKEY_CURRENT_USER,path):pass
            except FileNotFoundError:pass
            else:continue
        with registry.CreateKeyEx(registry.HKEY_CURRENT_USER,path,0,registry.KEY_WRITE) as key:
            registry.SetValueEx(key,'',0,registry.REG_SZ,LABEL)
        with registry.CreateKeyEx(registry.HKEY_CURRENT_USER,path+'\\command',0,registry.KEY_WRITE) as key:
            registry.SetValueEx(key,'',0,registry.REG_SZ,expected)
        return path,True
    raise OSError('Could not find an unused Explorer menu name')


def queue_or_play(path, *, runtime, script, instance_factory=None, spawn=None):
    target=Path(path).expanduser().resolve()
    if target.suffix.casefold()!='.wav' or not target.is_file():raise ValueError('Choose an existing WAV file')
    if instance_factory is None:
        from PAFPlayer_instance import Instance
        instance_factory=Instance
    instance=instance_factory(runtime)
    try:
        if not instance.acquire():
            result=instance.forward({'selectors':[{'kind':'path','value':str(target),'size':target.stat().st_size}]})
            if not result.get('ok',True):raise RuntimeError(result.get('error','The player could not queue the file'))
            return 'queued'
    finally:instance.close()
    launch=spawn or subprocess.Popen
    launch([sys.executable,'-B',str(Path(script).resolve()),'--bootstrap-installed',str(target)],
           close_fds=True,creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0))
    return 'launched'
