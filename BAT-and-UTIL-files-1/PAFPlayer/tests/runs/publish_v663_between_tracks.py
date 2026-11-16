from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def replace(path,data,archive):
 name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=path.with_name(name);i=0
 while b.exists():i+=1;b=path.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(path,b);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 path.write_text(data,encoding='utf8',newline='');dst=archive/b.name;i=0
 while dst.exists():i+=1;dst=archive/(b.stem+f' ({i})'+b.suffix)
 shutil.move(str(b),str(dst))
def once(s,a,b):
 assert s.count(a)==1,(a[:120],s.count(a));return s.replace(a,b,1)
src=root/'src/PAFPlayer_dj.py';dj=src.read_text(encoding='utf8')
dj=once(dj,"            stage = self.stage\n            if not stage and self.options['enabled']:","            stage = 'Ready for next song' if self.ready and not self.forced else self.stage\n            if not stage and self.options['enabled']:")
dj=once(dj,"return {'settings':dict(self.options),'stage':self.stage, 'history_count':len(self.history)","return {'settings':dict(self.options),'stage':('Ready for next song' if self.ready and not self.forced else self.stage), 'history_count':len(self.history)")
player=root/'PAFPlayer.py';lines=player.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines)
text=once(text,"'2026-11-11-v662-free-dj-providers'","'2026-11-12-v663-dj-between-tracks'")
text=once(text,"PROGRAM_VERSION                = 'V662'","PROGRAM_VERSION                = 'V663'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V662'","PROGRAM_RELEASE_LABEL          = 'V663'")
text=once(text,"    dj_controller = _get_dj_controller(paf_workflows())\n    dj_owned_pause = False", "    dj_controller = _get_dj_controller(paf_workflows())\n    # A prepared automatic segment may play at this track boundary only.\n    # Jobs becoming ready later wait for the next track.\n    dj_automatic_due_at_entry = bool(dj_controller.due() and not dj_controller.forced)\n    dj_owned_pause = False")
text=once(text,"if action is None and not startup_pause_transition and not help_overlay_until and dj_controller.due():", "if (action is None and not startup_pause_transition and not help_overlay_until\n                        and dj_controller.due() and (dj_controller.forced or dj_automatic_due_at_entry)):")
compile(dj,str(src),'exec');compile(text,str(player),'exec')
release=root/'releases/PAFPlayer_v663_dj_between_tracks.py';notes=root/'releases/PAFPlayer_v663_dj_between_tracks_release_notes.md';assert not release.exists() and not notes.exists()
replace(src,dj,root/'backups');replace(player,text,root/'releases');release.write_text(text,encoding='utf8',newline='')
test=root/'tests/test_v660_dj_modal.py';s=test.read_text(encoding='utf8');s=once(s,'if step[0]==1:step[0]=2;dj.prepared=True;return None','if step[0]==1:step[0]=2;dj.prepared=True;dj.forced=True;return None');replace(test,s,root/'backups')
readme=root/'docs/README.md';s=readme.read_text(encoding='utf8');s=once(s,'Current release: **V662** — free DJ providers and credit warnings.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v662_free_dj_providers_release_notes.md).','Current release: **V663** — automatic DJ commentary between tracks.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v663_dj_between_tracks_release_notes.md).')
s=once(s,'It plays at the next eligible track when ready.','Automatic commentary waits for a track boundary: if it becomes ready during a song, it plays at the beginning of the next eligible track. `#djforce` is an immediate interruption.')
replace(readme,s,root/'docs')
changelog=root/'docs/PAFPlayer_changelog.md';s=changelog.read_text(encoding='utf8');s=once(s,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V663 — November 12, 2026\n\nDefer automatically prepared DJ segments until the next track boundary, while preserving the explicit immediate `#djforce` command. [Release notes](../releases/PAFPlayer_v663_dj_between_tracks_release_notes.md).\n');replace(changelog,s,root/'backups')
notes.write_text('''# PAFPlayer V663 — automatic DJ commentary between tracks

Automatically prepared commentary that finishes during a song waits until the next track begins. The ready status says “Ready for next song.” `#djforce` remains an explicit immediate interruption. Track transport and modal Help behavior remain unchanged. V662 adds OpenRouter/Gemini text fallbacks and the OpenAI credit warning.
''',encoding='utf8')
print('Published V663 automatic track-boundary scheduling.')
