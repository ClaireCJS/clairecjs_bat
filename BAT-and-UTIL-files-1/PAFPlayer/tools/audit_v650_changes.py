"""Retain a combined path audit for V647–V650 without replacing old reports."""
import ast
import hashlib
import json
from pathlib import Path
from prepare_v642_artwork_chrome import ROOT,write

old=json.loads((ROOT/'tests/reports/v648-change-manifest.json').read_text())
paths={Path(item['path']):item['status'] for item in old['paths']}
for rel in ('PAFPlayer.py','src/PAFPlayer_workflows.py','src/PAFPlayer_web_workflows.py',
            'docs/README.md','docs/PAFPlayer_changelog.md','docs/performance-v519.md'):
    paths[ROOT/rel]='modified'
for folder in ('tools','tests','tests/reports','releases','backups','docs','src/backups'):
    for p in (ROOT/folder).iterdir():
        if p.is_file() and any('v'+str(v) in p.name.lower() for v in (647,648,649,650)):
            paths.setdefault(p,'created')
for folder,prefixes in {
    'releases':('PAFPlayer.py.bak.202611091337','PAFPlayer.py.bak.202611100129','PAFPlayer.py.bak.202611100132'),
    'src/backups':('PAFPlayer_workflows.py.bak.202611091337','PAFPlayer_web_workflows.py.bak.202611091337'),
    'docs':('README.md.bak.202611091348','README.md.bak.202611100142',
            'performance-v519.md.bak.202611091348','performance-v519.md.bak.202611091349','performance-v519.md.bak.202611100142'),
    'backups':('PAFPlayer_changelog.md.bak.202611091348','PAFPlayer_changelog.md.bak.202611100142'),
}.items():
    for p in (ROOT/folder).iterdir():
        if p.is_file() and p.name.startswith(prefixes):paths.setdefault(p,'created')
for folder in (ROOT/'tests/runs').iterdir():
    if folder.is_dir() and any('v'+str(v) in folder.name.lower() for v in (647,648,649,650)):
        for p in folder.rglob('*'):
            if p.is_file():
                assert ROOT in p.resolve().parents
                paths.setdefault(p,'created')

manifest=ROOT/'tests/reports/v650-change-manifest.json'
pointer=ROOT/'tests/reports/v649-change-manifest.json'
assert not manifest.exists() and not pointer.exists()
with pointer.open('x',encoding='utf-8') as f:json.dump({
    'version':649,'release_sha256':hashlib.sha256((ROOT/'releases/PAFPlayer_v649_render_blocking.py').read_bytes()).hexdigest(),
    'combined_audit':str(manifest),'user_feedback':'Mostly fluid; remaining large hitch during karaoke/visualizer height transitions.',
    'literal_c_bat_changes':[]},f,indent=2)
paths[pointer]='created'
records=[];moves=[]
for p,status in sorted(paths.items(),key=lambda x:str(x[0]).casefold()):
    assert p.is_file(),p
    if p.parent==ROOT/'releases' and p.suffix=='.py' and p.name.startswith('PAFPlayer_v'):
        status='copied (new immutable release)'
    records.append({'path':str(p),'status':status,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    if '.bak.' in p.name and p.name.endswith('.bak'):
        original=p.name.split('.bak.')[0]
        sibling=None
        if p.parent==ROOT/'releases' and original=='PAFPlayer.py':sibling=ROOT/p.name
        elif p.parent==ROOT/'backups':
            origin=ROOT/'tests' if original.startswith('verify_') else ROOT/'docs'
            sibling=origin/p.name
        elif p.parent==ROOT/'src/backups':sibling=ROOT/'src'/p.name
        elif p.parent==ROOT/'docs' and original.startswith('PAFPlayer_v'):
            sibling=ROOT/'releases'/p.name
        if sibling and sibling!=p:
            moves.append({'from':str(sibling),'to':str(p),'status':'verified sibling backup created, then moved to archive'})
records.append({'path':str(manifest),'status':'created'})
root_audit={str(ROOT/name):[p.name for p in (ROOT/name).iterdir() if p.is_file()]
            for name in ('.','lockscreen','screensaver')}
main=ROOT/'PAFPlayer.py';release=ROOT/'releases/PAFPlayer_v650_karaoke_resize.py'
assert main.read_bytes()==release.read_bytes()
assert 'Current release: **V650**' in (ROOT/'docs/README.md').read_text(encoding='utf-8')
assert (ROOT/'docs/PAFPlayer_changelog.md').read_text(encoding='utf-8').startswith('# PAFPlayer changelog\n\n## V650')
for p in (main,release,*ROOT.glob('tools/*v650*.py'),*ROOT.glob('tests/*v650*.py')):
    compile(p.read_text(encoding='utf-8'),str(p),'exec')
with manifest.open('x',encoding='utf-8') as f:json.dump({
    'versions':[647,648,649,650],'source_sha256':hashlib.sha256(main.read_bytes()).hexdigest(),
    'paths':records,'backup_moves':moves,'root_audit':root_audit,'root_cleanup_needed':False,
    'literal_c_bat_changes':[],'existing_files_deleted':[],
    'live_v649_feedback':'Mostly fluid; large hitch when karaoke appears/disappears and visualizer changes height.',
    'live_v650_verification':'Pending user restart and visual feedback.',
    'overall_freeze_fix_complete':False,
    'tests':{'focused_new':10,'focused_passed':10,'existing':188,'existing_passed':176,
             'baseline_failures':11,'baseline_errors':1,
             'combined_suite_limitation':'Existing five-second silent-playback test times out after new tests; passes alone and in clean existing-test run.'},
},f,indent=2)
print(manifest,len(records),'paths;',len(moves),'backup archive moves')
