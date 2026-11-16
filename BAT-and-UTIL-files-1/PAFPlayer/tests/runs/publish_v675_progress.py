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
voice=(root/'tests/runs/PAFPlayer_voice_models_v675_candidate_v2.py').read_text(encoding='utf8');dj=(root/'tests/runs/PAFPlayer_dj_v675_candidate.py').read_text(encoding='utf8');compile(voice,'voice','exec');compile(dj,'dj','exec')
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True)
for name,value in [('PAFPlayer_voice_models',voice),('PAFPlayer_dj',dj)]:
 idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['"+name+"'] = ")];assert len(idx)==1;lines[idx[0]]="_PAF_BUNDLED_SOURCES['"+name+"'] = "+repr(value)+'\n'
text=''.join(lines)
text=once(text,"'2026-11-12-v674-visible-model-buttons'","'2026-11-12-v675-model-progress'")
text=once(text,"PROGRAM_VERSION                = 'V674'","PROGRAM_VERSION                = 'V675'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V674'","PROGRAM_RELEASE_LABEL          = 'V675'");compile(text,str(p),'exec')
release=root/'releases/PAFPlayer_v675_model_progress.py';notes=root/'releases/PAFPlayer_v675_model_progress_release_notes.md';assert not release.exists() and not notes.exists()
readme=root/'docs/README.md';docs=readme.read_text(encoding='utf8');docs=once(docs,'Current release: **V674** — visible voice model action buttons.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v674_model_buttons_release_notes.md).','Current release: **V675** — live voice-model download and installation progress.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v675_model_progress_release_notes.md).')
anchor='No model is downloaded without selecting it and clicking Download.'
docs=once(docs,anchor,anchor+' The window displays live installer output, a current-step bar, overall model progress, and elapsed time. Direct model downloads show bytes, speed and a percentage when the server supplies a size; other stages use an animated bar rather than an invented percentage.')
changelog=root/'docs/PAFPlayer_changelog.md';change=changelog.read_text(encoding='utf8');change=once(change,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V675 — November 12, 2026\n\nStream model installer output and show current-step and overall progress in the model window. [Release notes](../releases/PAFPlayer_v675_model_progress_release_notes.md).\n')
replace(root/'src/PAFPlayer_voice_models.py',voice,root/'backups');replace(root/'src/PAFPlayer_dj.py',dj,root/'backups');replace(p,text,root/'releases');release.write_text(text,encoding='utf8',newline='');replace(readme,docs,root/'docs');replace(changelog,change,root/'backups')
notes.write_text('# PAFPlayer V675 — Voice model installation progress\n\nThe model window shows streamed installer output, elapsed time, current-step and overall model progress. Direct model downloads display bytes and speed, with a percentage when available. Piper setup also forwards subprocess output. Unknown-duration stages use an animated bar.\n',encoding='utf8')
print('Published V675 with verified backups.')
