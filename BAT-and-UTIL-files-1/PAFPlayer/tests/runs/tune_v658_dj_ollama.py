from pathlib import Path
import datetime, hashlib, shutil
root=Path(__file__).resolve().parents[2]
src=root/'src/PAFPlayer_dj.py'; player=root/'PAFPlayer.py'; release=root/'releases/PAFPlayer_v658_dj_help_commentary.py'
dj=src.read_text(encoding='utf-8')
old="            model=models[0]['name']"
new="            model=min(models, key=lambda item: item.get('size') or float('inf'))['name']"
assert dj.count(old)==1; dj=dj.replace(old,new,1)
old="        value=post_json('http://127.0.0.1:11434/api/chat',{'model':model,'stream':False,\n              'messages':[{'role':'system','content':prompt},{'role':'user','content':data}]},timeout=120)"
new="        value=post_json('http://127.0.0.1:11434/api/chat',{'model':model,'stream':False,\n              'options':{'num_ctx':4096},\n              'messages':[{'role':'system','content':prompt},{'role':'user','content':data}]},timeout=120)"
assert dj.count(old)==1; dj=dj.replace(old,new,1)
lines=player.read_text(encoding='utf-8').splitlines(keepends=True)
indexes=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")]
assert len(indexes)==1; lines[indexes[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n'; text=''.join(lines)
compile(dj,str(src),'exec'); compile(text,str(player),'exec')
for path,data in ((src,dj),(player,text),(release,text)):
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak'); backup=path.with_name(name); i=0
    while backup.exists():
        i+=1; backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup); assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data,encoding='utf-8',newline='')
    archive=root/('backups' if path==src else 'releases'); dest=archive/backup.name; i=0
    while dest.exists():
        i+=1; dest=archive/(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(dest))
print('Selected smallest installed Ollama model by default and bounded its context.')
