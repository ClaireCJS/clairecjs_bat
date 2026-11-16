from pathlib import Path
root=Path(__file__).resolve().parents[2]
src=(root/'tests/runs/PAFPlayer_dj_v662_candidate.py').read_text(encoding='utf8')
src=src.replace("    elif mode in ('auto','gemini'):\n        _dj_event('text.provider.skipped',provider='gemini',reason='free_tier_not_confirmed')", "    elif mode in ('auto','gemini'):\n        _dj_event('text.provider.skipped',provider='gemini',reason='free_tier_not_confirmed')\n        if mode=='gemini':notices.append('Gemini skipped: free tier not confirmed')",1)
start=src.index('class CreditWarnings:\n');end=src.index('\n\nclass Controller:',start)
replacement='''class CreditWarnings:
    """Append-only account-key-scoped observations; no raw keys or user data."""
    def __init__(self,runtime):
        self.root=Path(runtime.root)/'dj-credit-warnings' if getattr(runtime,'root',None) else None
        self.key_id=None;self.active=False;self.sync()

    def sync(self):
        key=openai_key();current=hashlib.sha256(key.encode('utf8')).hexdigest() if key else ''
        if current==self.key_id:return
        self.key_id=current;self.active=False
        if not self.root or not self.root.is_dir() or not self.key_id:return
        latest=None
        for path in self.root.glob('observation-*.json'):
            try:
                with path.open('r',encoding='utf8') as stream:value=json.load(stream)
                if value.get('key_id')==self.key_id and type(value.get('time_ns')) is int and type(value.get('active')) is bool:
                    if latest is None or value['time_ns']>latest['time_ns']:latest=value
            except (OSError,ValueError,TypeError):pass
        if latest:self.active=latest['active']

    def set(self,active):
        self.sync();active=bool(active)
        if self.active==active:return
        self.active=active
        if not self.root or not self.key_id:return
        try:
            self.root.mkdir(parents=True,exist_ok=True)
            fd,path=tempfile.mkstemp(prefix='observation-',suffix='.json',dir=str(self.root))
            with os.fdopen(fd,'w',encoding='utf8') as stream:
                json.dump({'time_ns':time.time_ns(),'key_id':self.key_id,'active':active},stream)
        except OSError:pass

    def messages(self):
        self.sync();return [OPENAI_CREDIT_WARNING] if self.active else []
'''
src=src[:start]+replacement+src[end:];compile(src,'candidate','exec')
p=root/'tests/runs/PAFPlayer_dj_v662_candidate_v2.py';assert not p.exists();p.write_text(src,encoding='utf8');print(p)
