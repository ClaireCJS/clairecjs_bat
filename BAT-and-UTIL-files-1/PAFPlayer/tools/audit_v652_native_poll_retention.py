"""Record this operation's artifacts without attributing other chats' edits to it."""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
from prepare_v642_artwork_chrome import ROOT

modified=['PAFPlayer.py','src/PAFPlayer_steam.py','docs/README.md',
          'docs/PAFPlayer_changelog.md','docs/performance-v519.md']
created=['tests/probe_pipeline_gc.py','tests/probe_native_poll_soak.py','tests/test_pipeline_native_allocations.py',
         'tests/verify_pipeline_native_allocations.py','tests/verify_pipeline_regressions.py',
         'tools/prepare_pipeline_gc_candidate.py','tools/release_v652_native_poll_retention.py',
         'tools/audit_v652_native_poll_retention.py',
         'releases/PAFPlayer_v652_native_poll_retention.py','releases/PAFPlayer_v652_native_poll_retention_release_notes.md',
         'releases/PAFPlayer.py.bak.202611110624.replaced-by-chatgpt.bak',
         'src/backups/PAFPlayer_steam.py.bak.202611110624.replaced-by-chatgpt.bak',
         'tests/reports/v648-thread-stacks-20261111-005959.json','tests/reports/v652-publication.json']
patterns={
    'backups':['probe_pipeline_gc.py.bak.20261111*.bak','verify_pipeline*.py.bak.20261111*.bak','PAFPlayer_changelog.md.bak.202611110634*.bak'],
    'tools':['prepare_pipeline_gc_candidate.py.bak.20261111*.bak'],
    'docs':['README.md.bak.20261111063*.bak','performance-v519.md.bak.202611110634*.bak'],
    'tests/reports':['pipeline-gc-*20261111*.json','native-checks-*20261111*','native-soak-*20261111*.json',
                     'pipeline-regressions-*20261111*','v650-checks-V651-20261111*.log','v650-checks-V653-20261111*.log']}
paths={ROOT/name:'modified' for name in modified}
paths.update({ROOT/name:'created' for name in created})
for folder,globs in patterns.items():
    for pattern in globs:
        paths.update({p:'created' for p in (ROOT/folder).glob(pattern)})
stages=[]
for prefix in ('pipeline-gc','gc-candidate','native-checks','native-soak','pipeline-regressions','checks-v650'):
    for stage in (ROOT/'tests/runs').glob(prefix+'-20261111-*'):
        stages.append(str(stage));paths[stage]='created'
        paths.update({p:'created' for p in stage.rglob('*')})
publication=json.loads((ROOT/'tests/reports/v652-publication.json').read_text())
moves=publication['moves']
for move in moves:
    target=Path(move['to']);paths[target]='moved'
    if target.is_dir():paths.update({p:'moved' for p in target.rglob('*')})
for path in paths:assert path.exists(),path

# Verify the actual test and benchmark source hashes, even when another chat
# modified the active file during a run. One historical harness report records
# its post-test validation hash separately from its corrected test snapshot hash.
checked_reports=[]
for p in (ROOT/'tests/reports').glob('*.json'):
    if p not in paths or not p.name.startswith(('pipeline-gc-','native-checks-','native-soak-','pipeline-regressions-')):continue
    j=json.loads(p.read_text());stage=Path(j['stage'])/'PAFPlayer.py'
    assert hashlib.sha256(stage.read_bytes()).hexdigest()==j['source_sha256'],p
    checked_reports.append(str(p))
release=ROOT/'releases/PAFPlayer_v652_native_poll_retention.py'
assert hashlib.sha256(release.read_bytes()).hexdigest()=='ae9aaea9f3cc9a95ce9d0e99e7597d49867a2fc702cefc865e922b44417422db'
active=ROOT/'PAFPlayer.py';current_release=ROOT/'releases/PAFPlayer_v653_idle_art_music_dance.py'
assert active.read_bytes()==current_release.read_bytes()
def fs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text(encoding='utf8')).body if isinstance(n,(ast.ClassDef,ast.FunctionDef))}
base,current=fs(release),fs(active)
for name in ('_external_audio_probe_api','probe_external_audio_sessions','_windows_process_memory_api','paf_runtime_diagnostics_snapshot',
             '_console_cursor_info_type','set_console_cursor_visible','_windows_last_input_info_type','windows_last_input_tick'):
    assert base[name]==current[name],name
compile(active.read_text(encoding='utf8'),str(active),'exec')
for p in paths:
    if p.is_file() and p.suffix=='.py' and p.parent in (ROOT/'tests',ROOT/'tools',ROOT/'src'):
        compile(p.read_text(encoding='utf8'),str(p),'exec')

entries=[]
for p,status in sorted(paths.items(),key=lambda pair:str(pair[0]).casefold()):
    entry={'path':str(p),'status':status,'kind':'directory' if p.is_dir() else 'file'}
    if p.is_file():entry['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    entries.append(entry)
manifest=ROOT/'tests/reports/v652-change-manifest.json'
entries.append({'path':str(manifest),'status':'created','kind':'file'})
report=dict(created_at=datetime.now().isoformat(),release='V652',active_release='V653',
    applied_source_sha256='ae9aaea9f3cc9a95ce9d0e99e7597d49867a2fc702cefc865e922b44417422db',
    final_active_sha256=hashlib.sha256(active.read_bytes()).hexdigest(),current_release_matches=True,
    native_fixes_retained_in_current_release=True,live_verification_pending=True,
    no_gc_policy_change=True,literal_cbat_changes=[],deleted_paths=[],
    notes=['Only this operation\'s source changes, publication, probes, tests and retained staging artifacts are attributed here.',
           'The independently published V653 release contains these fixes; its other edits and artifacts belong to the other chat.',
           'Sibling backups were verified before replacement, then archived; no permanent deletion occurred.',
           'All report source hashes were verified against the exact staged snapshots.'],
    moves=moves,checked_report_hashes=checked_reports,paths=entries,
    roots={str(root):sorted(p.name for p in root.iterdir()) for root in (ROOT,ROOT/'lockscreen',ROOT/'screensaver')})
with manifest.open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(json.dumps({'manifest':str(manifest),'paths':len(entries),'checked_reports':len(checked_reports),
                  'current_release_matches':True,'literal_cbat_changes':[]},indent=2))
