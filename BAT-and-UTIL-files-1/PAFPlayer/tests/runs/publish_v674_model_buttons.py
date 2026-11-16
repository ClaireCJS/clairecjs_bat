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
anchor="    choices={}; availability={}\n"
s=once(s,anchor,"    action_bar=ttk.Frame(frame);action_bar.pack(fill='x',pady=(4,8))\n"+anchor)
s=once(s,"    row=ttk.Frame(frame);row.pack(fill='x',pady=8)\n    for label,callback in [('Download selected',lambda:run(do_install)),('Compare selected',lambda:run(do_compare))]:\n        button=ttk.Button(row,text=label,command=callback);button.pack(side='left',padx=(0,8));buttons.append(button)\n    ttk.Button(row,text='Close',command=window.destroy).pack(side='right')", "    for label,callback in [('Download selected',lambda:run(do_install)),('Compare selected',lambda:run(do_compare))]:\n        button=ttk.Button(action_bar,text=label,command=callback);button.pack(side='left',padx=(0,8));buttons.append(button)\n    ttk.Button(action_bar,text='Close',command=window.destroy).pack(side='right')")
compile(s,str(src),'exec');p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_voice_models'] = ")];assert len(idx)==1;lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_voice_models'] = "+repr(s)+'\n';text=''.join(lines)
text=once(text,"'2026-11-12-v673-voice-model-manager'","'2026-11-12-v674-visible-model-buttons'")
text=once(text,"PROGRAM_VERSION                = 'V673'","PROGRAM_VERSION                = 'V674'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V673'","PROGRAM_RELEASE_LABEL          = 'V674'");compile(text,str(p),'exec')
release=root/'releases/PAFPlayer_v674_model_buttons.py';notes=root/'releases/PAFPlayer_v674_model_buttons_release_notes.md';assert not release.exists() and not notes.exists()
readme=root/'docs/README.md';docs=readme.read_text(encoding='utf8');docs=once(docs,'Current release: **V673** — local voice model download and comparison window.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v673_voice_models_release_notes.md).','Current release: **V674** — visible voice model action buttons.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v674_model_buttons_release_notes.md).')
docs=once(docs,'then download the selected models or compare installed models.','then use the buttons at the top to download the selected models or compare installed models.')
changelog=root/'docs/PAFPlayer_changelog.md';change=changelog.read_text(encoding='utf8');change=once(change,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V674 — November 12, 2026\n\nKeep voice model download and comparison buttons visible above the model list and output. [Release notes](../releases/PAFPlayer_v674_model_buttons_release_notes.md).\n')
replace(src,s,root/'backups');replace(p,text,root/'releases');release.write_text(text,encoding='utf8',newline='');replace(readme,docs,root/'docs');replace(changelog,change,root/'backups')
notes.write_text('# PAFPlayer V674 — Visible model controls\n\nMove the Download selected, Compare selected and Close buttons above the model list and expandable output, so display scaling and smaller windows do not push the actions below the visible area.\n',encoding='utf8')
print('Published V674 with verified backups.')
