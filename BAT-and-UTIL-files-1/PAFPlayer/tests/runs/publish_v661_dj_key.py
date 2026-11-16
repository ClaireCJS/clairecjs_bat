from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def replace(path,data,archive):
 name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=path.with_name(name);i=0
 while b.exists():i+=1;b=path.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(path,b);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 path.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 shutil.move(str(b),str(dest))
def once(s,a,b):
 assert s.count(a)==1,(a[:80],s.count(a));return s.replace(a,b,1)
dj=(root/'tests/runs/PAFPlayer_dj_v661_candidate.py').read_text(encoding='utf8')
player=root/'PAFPlayer.py';lines=player.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines)
text=once(text,"'2026-11-11-v660-dj-diagnostics'","'2026-11-11-v661-dj-private-key'")
text=once(text,"PROGRAM_VERSION                = 'V660'","PROGRAM_VERSION                = 'V661'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V660'","PROGRAM_RELEASE_LABEL          = 'V661'")
compile(dj,'dj','exec');compile(text,str(player),'exec')
release=root/'releases/PAFPlayer_v661_dj_private_key.py';notes=root/'releases/PAFPlayer_v661_dj_private_key_release_notes.md';assert not release.exists() and not notes.exists()
replace(root/'src/PAFPlayer_dj.py',dj,root/'backups');replace(player,text,root/'releases');release.write_text(text,encoding='utf8',newline='')
test=root/'tests/test_v661_dj_key.py';s=test.read_text(encoding='utf8');s=once(s,"ROOT/'tests/runs/PAFPlayer_dj_v661_candidate.py'","ROOT/'src/PAFPlayer_dj.py'");replace(test,s,root/'backups')
readme=root/'docs/README.md';s=readme.read_text(encoding='utf8');s=once(s,'Current release: **V660** — AI DJ diagnostics and Help handoff.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v660_dj_diagnostics_release_notes.md).','Current release: **V661** — private-file AI DJ key loading.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v661_dj_private_key_release_notes.md).')
s=once(s,'using `OPENAI_API_KEY` from the player’s environment.','using a valid `OPENAI_API_KEY` from `C:\\BAT\\private.env` when present, otherwise from the player’s environment. The private-file key takes precedence so a stale inherited environment value does not override it.')
replace(readme,s,root/'docs')
changelog=root/'docs/PAFPlayer_changelog.md';s=changelog.read_text(encoding='utf8');s=once(s,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V661 — November 11, 2026\n\n+Load the DJ OpenAI key from Claire’s private environment file when present, falling back to the process environment, without putting keys in settings or logs. [Release notes](../releases/PAFPlayer_v661_dj_private_key_release_notes.md).\n'.replace('\n+Load','\nLoad'));replace(changelog,s,root/'backups')
notes.write_text('''# PAFPlayer V661 — DJ private key loading

The DJ reads a valid `OPENAI_API_KEY` from `C:\\BAT\\private.env` when available, with the process environment as a fallback. The private-file value takes priority over stale inherited keys. The key is never written into DJ settings or diagnostics.

The new service-account key authenticated against the models endpoint, but a live text request returned HTTP 429 `credit_balance_exhausted`, so cloud generation was not verified. Ollama and Piper remain the local fallback. A verified backup of the prior private environment file was created before the file was updated.
''',encoding='utf8')
print('Published V661 private-key loading and documentation.')
