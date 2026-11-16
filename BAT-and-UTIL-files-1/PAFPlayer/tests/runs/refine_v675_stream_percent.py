from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
def replace(p,data,archive):
 name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
 while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 if dest!=b:shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_voice_models.py';s=src.read_text(encoding='utf8')
s=once(s,"environment=os.environ.copy();environment['PYTHONUNBUFFERED']='1'", "environment=os.environ.copy();environment['PYTHONUNBUFFERED']='1';environment['HF_HUB_DISABLE_PROGRESS_BARS']='0'")
a="""                elif kind=='output':
                    log.insert('end',value+'\\n');log.see('end')
                elif kind=='bytes':"""
b="""                elif kind=='output':
                    log.insert('end',value+'\\n');log.see('end')
                    match=re.search(r'(?<![0-9])(100|[0-9]{1,2})%',value)
                    if match:
                        current_bar.stop();current_bar.config(mode='determinate',value=int(match.group(1)))
                        activity['status']=value[:200]
                elif kind=='bytes':"""
s=once(s,a,b);compile(s,str(src),'exec');p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_voice_models'] = ")];assert len(idx)==1;lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_voice_models'] = "+repr(s)+'\n';text=''.join(lines);compile(text,str(p),'exec')
replace(src,s,root/'backups');replace(p,text,root/'releases');replace(root/'releases/PAFPlayer_v675_model_progress.py',text,root/'releases')
print('Mapped installer-reported percentages to the current progress bar.')
