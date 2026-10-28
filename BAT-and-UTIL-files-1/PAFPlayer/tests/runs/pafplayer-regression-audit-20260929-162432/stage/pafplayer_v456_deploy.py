"""Install the verified V456 artifact; preserve and report every replaced file."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parent
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def unique(path):
    candidate=path;number=0
    while candidate.exists():
        number+=1;candidate=path.with_name(f'{path.stem} ({number}){path.suffix}')
    return candidate

def main():
    manifest=json.loads((ROOT/'releases/PAFPlayer-v456-manifest.json').read_text())
    plan=json.loads((ROOT/'releases/PAFPlayer-v456-deployment-plan.json').read_text())
    # Verify every destination before making the first change.
    for item in plan:
        target=Path(item['path']).resolve()
        if target.parent!=Path('C:/BAT').resolve():raise ValueError('Unexpected deployment destination')
        actual=digest(target) if target.exists() else None
        if actual!=item['prior_sha256']:raise ValueError('Destination changed since review: '+str(target))
        if digest(ROOT/target.name)!=manifest['files'][target.name]:raise ValueError('Source changed after verification')
    changes=[]
    def install(source,target):
        operation='modified' if target.exists() else 'created'
        if target.exists():
            backup=unique(target.with_name(target.name+datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')))
            shutil.copy2(target,backup)
            if digest(target)!=digest(backup):raise OSError('Backup verification failed: '+str(target))
            changes.append({'path':str(backup),'operation':'created','purpose':'verified replacement backup'})
        shutil.copy2(source,target)
        if digest(source)!=digest(target):raise OSError('Installed content differs: '+str(target))
        changes.append({'path':str(target),'operation':operation,'sha256':digest(target)})
    # Helpers first, canonical entry point and launcher last.
    ordered=sorted(plan,key=lambda x:2 if Path(x['path']).name=='paf.bat' else 1 if Path(x['path']).name=='PAFPlayer.py' else 0)
    for item in ordered:
        target=Path(item['path']);install(ROOT/target.name,target)
    docs=Path('C:/sandbox/docs/PAFPlayer')
    for name in ('PAFPlayer_v456_release_notes.md','PAFPlayer_TODO.md','PAFPlayer_changelog.md','README.md'):
        install(ROOT/'docs/PAFPlayer'/name,docs/name)
    report=unique(ROOT/'releases/PAFPlayer-v456-installed-files.json')
    report.write_text(json.dumps({'version':'V456','changes':changes},indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(report),'changes':changes},indent=2))

if __name__=='__main__':main()
