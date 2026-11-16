from pathlib import Path
root=Path(__file__).resolve().parents[2]
def once(s,a,b):assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
s=(root/'src/PAFPlayer_dj.py').read_text(encoding='utf8')
start=s.index('def _piper_setup_command(');end=s.index('\n\n_PIPER_SETUP_LOCK',start)
new='''_PIPER_SETUP_PROGRESS = threading.local()


def _piper_setup_command(args, cwd, valid, timeout=600):
    if not valid():raise InterruptedError()
    from PAFPlayer_voice_models import run_command
    try:
        run_command(args,cwd=cwd,timeout=timeout,valid=valid,
                    progress=getattr(_PIPER_SETUP_PROGRESS,'output',None))
    except InterruptedError:raise
    except subprocess.TimeoutExpired as exc:raise PiperSetupError('Piper setup timed out; check the network and try again') from exc
    except (OSError,RuntimeError) as exc:raise PiperSetupError('Piper setup failed; check Python, network access, and free space: '+str(exc)[-3000:]) from exc
'''
s=s[:start]+new+s[end:]
s=once(s,'''def ensure_piper(stage, valid, root=None):
    with _PIPER_SETUP_LOCK:
        return _ensure_piper_unlocked(stage, valid, root)''','''def ensure_piper(stage, valid, root=None):
    with _PIPER_SETUP_LOCK:
        _PIPER_SETUP_PROGRESS.output=getattr(stage,'output',None)
        try:return _ensure_piper_unlocked(stage, valid, root)
        finally:_PIPER_SETUP_PROGRESS.output=None''')
s=once(s,'''def ensure_piper_male(auto_exe, stage, valid, root=None):
    with _PIPER_SETUP_LOCK:
        return _ensure_piper_male_unlocked(auto_exe, stage, valid, root)''','''def ensure_piper_male(auto_exe, stage, valid, root=None):
    with _PIPER_SETUP_LOCK:
        _PIPER_SETUP_PROGRESS.output=getattr(stage,'output',None)
        try:return _ensure_piper_male_unlocked(auto_exe, stage, valid, root)
        finally:_PIPER_SETUP_PROGRESS.output=None''')
compile(s,'dj candidate','exec');target=root/'tests/runs/PAFPlayer_dj_v675_candidate.py'
with target.open('x',encoding='utf8',newline='') as f:f.write(s)
print('Staged Piper installer output streaming.')
