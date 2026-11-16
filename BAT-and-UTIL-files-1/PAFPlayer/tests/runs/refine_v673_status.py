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
s=once(s,'    choices={}\n    for key,item in CATALOG.items():', '    choices={}; availability={}\n    for key,item in CATALOG.items():')
s=once(s,"        ttk.Checkbutton(row,text=item['name'],variable=value).pack(side='left')\n        ttk.Label(row,text=item['detail'],wraplength=580).pack(side='left',padx=10)","        ttk.Checkbutton(row,text=item['name'],variable=value).pack(side='left')\n        label=ttk.Label(row,text='Installed' if installed(key) else 'Not installed');label.pack(side='left',padx=8);availability[key]=label\n        ttk.Label(row,text=item['detail'],wraplength=500).pack(side='left',padx=10)")
s=once(s,"                    for button in buttons:button.state(['!disabled'])\n                    status.set(value)","                    for button in buttons:button.state(['!disabled'])\n                    for key,label in availability.items():label.config(text='Installed' if installed(key) else 'Not installed')\n                    status.set(value)")
compile(s,str(src),'exec');p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_voice_models'] = ")];assert len(idx)==1;lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_voice_models'] = "+repr(s)+'\n';text=''.join(lines);compile(text,str(p),'exec')
replace(src,s,root/'backups');replace(p,text,root/'releases');replace(root/'releases/PAFPlayer_v673_voice_models.py',text,root/'releases')
print('Added installed-model indicators.')
