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
 assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
dj=(root/'tests/runs/PAFPlayer_dj_v664_candidate.py').read_text(encoding='utf8')
player=root/'PAFPlayer.py';lines=player.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines)
text=once(text,"'2026-11-12-v663-dj-between-tracks'","'2026-11-12-v664-gemini-native'")
text=once(text,"PROGRAM_VERSION                = 'V663'","PROGRAM_VERSION                = 'V664'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V663'","PROGRAM_RELEASE_LABEL          = 'V664'")
compile(dj,'dj','exec');compile(text,str(player),'exec')
release=root/'releases/PAFPlayer_v664_gemini_native.py';notes=root/'releases/PAFPlayer_v664_gemini_native_release_notes.md';assert not release.exists() and not notes.exists()
replace(root/'src/PAFPlayer_dj.py',dj,root/'backups');replace(player,text,root/'releases');release.write_text(text,encoding='utf8',newline='')
test=root/'tests/test_v662_free_providers.py';s=test.read_text(encoding='utf8')
old="with mock.patch.object(dj,'provider_key',return_value='fake-gemini'),mock.patch.object(dj,'post_json',return_value={'choices':[{'message':{'content':'```json\\n'+PAYLOAD+'\\n```'}}]}) as post:"
new="with mock.patch.object(dj,'provider_key',return_value='fake-gemini'),mock.patch.object(dj,'post_json',return_value={'candidates':[{'content':{'parts':[{'text':PAYLOAD}]}}]}) as post:"
s=once(s,old,new)
s=once(s,"self.assertEqual('gemini-2.5-flash-lite',post.call_args.args[1]['model'])", "self.assertIn('gemini-3.5-flash-lite:generateContent',post.call_args.args[0]);self.assertEqual('fake-gemini',post.call_args.args[2]['x-goog-api-key'])")
replace(test,s,root/'backups')
readme=root/'docs/README.md';s=readme.read_text(encoding='utf8')
s=once(s,'Current release: **V663** — automatic DJ commentary between tracks.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v663_dj_between_tracks_release_notes.md).','Current release: **V664** — verified free DJ providers.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v664_gemini_native_release_notes.md).')
s=once(s,"then Gemini only if the user confirms its project is on the free tier, then local Ollama.","then Gemini 3.5 Flash-Lite via Google’s native API only if the user confirms its project is on the free tier, then local Ollama.")
replace(readme,s,root/'docs')
changelog=root/'docs/PAFPlayer_changelog.md';s=changelog.read_text(encoding='utf8');s=once(s,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V664 — November 12, 2026\n\nUse the native Gemini API and current free-tier model, including Google authorization keys; verify real free OpenRouter and Gemini dialogue. [Release notes](../releases/PAFPlayer_v664_gemini_native_release_notes.md).\n');replace(changelog,s,root/'backups')
notes.write_text('''# PAFPlayer V664 — verified free DJ providers

Gemini uses Google’s native `generateContent` API with `x-goog-api-key` and `gemini-3.5-flash-lite`, supporting modern AQ authorization keys. The previous Gemini model was unavailable to this new account. The Gemini free-tier confirmation remains mandatory because paid projects can incur charges.

Live tests using synthetic metadata generated two dialogue turns each through OpenRouter’s free router and the confirmed free-tier Gemini project. Both provider keys authenticated and were saved in `C:\\BAT\\private.env` after a verified backup. Automatic playback remains deferred until the next track; `#djforce` remains immediate.
''',encoding='utf8')
print('Published V664 native Gemini integration and documentation.')
