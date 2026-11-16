"""Separate render-facing locks and remove no-action undo I/O from each frame."""
import ast
import hashlib
from prepare_v642_artwork_chrome import ROOT, write, unique

path=ROOT/'PAFPlayer.py'
assert hashlib.sha256(path.read_bytes()).hexdigest()=='0f3cfeb92523216db34f27ce36af3e4bbbc10da9dc890c87d2e97833deae1476'
source=path.read_text(encoding='utf-8')
def change(before,after):
    global source
    assert source.count(before)==1,before[:100]
    source=source.replace(before,after,1)
change("PROGRAM_VERSION                = 'V648'","PROGRAM_VERSION                = 'V649'")
change("PROGRAM_RELEASE_LABEL          = 'V648'","PROGRAM_RELEASE_LABEL          = 'V649'")
change("'2026-11-09-v648-local-stack-diagnostics'","'2026-11-09-v649-render-blocking'")
change('''        if workflow is not None:
            with workflow.lock:
                workflow.sequence += 1''','''        if workflow is not None:
            # A library scan can hold workflow.lock across slow filesystem I/O.
            # Neither playback nor lyric presentation may wait for that work.
            with workflow.presentation_lock:
                workflow.sequence += 1''')
change('''                else:
                    observe_runtime_settings_for_undo()
                    action = next_owner_action()''','''                else:
                    action = next_owner_action()
                    if action is not None:
                        observe_runtime_settings_for_undo()''')
change('''                        else:
                            observe_runtime_settings_for_undo()
                            paused_action = next_owner_action()''','''                        else:
                            paused_action = next_owner_action()
                            if paused_action is not None:
                                observe_runtime_settings_for_undo()''')
change('''        last_bass_filter_signature = None

        def current_loudness_key():''','''        last_bass_filter_signature = None
        # Establish undo's baseline once; later snapshots precede actual input.
        # Empty input polls must not read four registry values on every frame.
        observe_runtime_settings_for_undo()

        def current_loudness_key():''')

for name in ('PAFPlayer_workflows','PAFPlayer_web_workflows'):
    module=ROOT/'src'/(name+'.py');old=module.read_text(encoding='utf-8');new=old
    if name=='PAFPlayer_workflows':
        before='        self.lock=threading.RLock(); self.token=secrets.token_urlsafe(32); self.events=deque(maxlen=1000); self.sequence=0'
        assert new.count(before)==1
        new=new.replace(before,before+'\n        # Tiny render-facing state must never share the library/filesystem lock.\n        self.presentation_lock=threading.RLock()',1)
        new=new.replace('''        with self.lock:
            self._hud_activity=(label,time.monotonic()+max(.1,min(float(seconds),15)))''','''        with self.presentation_lock:
            self._hud_activity=(label,time.monotonic()+max(.1,min(float(seconds),15)))''',1)
        new=new.replace('''    def hud_activity(self):
        with self.lock:''','''    def hud_activity(self):
        with self.presentation_lock:''',1)
    else:
        before='''                records=list(runtime.events)
                data={'cursor':runtime.sequence,'''
        after='''                with runtime.presentation_lock:
                    records=list(runtime.events)
                    cursor=runtime.sequence
                data={'cursor':cursor,'''
        assert new.count(before)==1
        new=new.replace(before,after,1)
    assert new!=old
    compile(new,str(module),'exec')
    tree=ast.parse(source)
    bundle=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_PAF_BUNDLED_SOURCES' for t in n.targets))
    literal=next(v for k,v in zip(bundle.keys,bundle.values) if ast.literal_eval(k)==name)
    assert ast.literal_eval(literal)==old
    change(ast.get_source_segment(source,literal),repr(new))
    prior=set(module.parent.glob(module.name+'.bak.*'))
    write(module.relative_to(ROOT),new)
    archive=module.parent/'backups';archive.mkdir(exist_ok=True)
    for backup in set(module.parent.glob(module.name+'.bak.*'))-prior:
        target=unique(archive/backup.name)
        assert ROOT in backup.resolve().parents and ROOT in target.resolve().parents
        backup.rename(target)
        print('ARCHIVED',target)
compile(source,str(path),'exec')
write('PAFPlayer.py',source)
