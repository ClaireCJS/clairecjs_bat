from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):
    assert s.count(a)==1,(a[:140],s.count(a));return s.replace(a,b,1)
def replace(p,data,archive):
    name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
    while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
    while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
    if dest!=b:shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_error_delivery.py';s=src.read_text(encoding='utf8')
s=once(s,'def next_playable_entry(order, current):','def next_playable_entry(order, current, on_missing=None):')
s=once(s,"        if candidate != current and file_problem(candidate) is None:\n            return candidate", "        if candidate == current: continue\n        problem = file_problem(candidate)\n        if problem is None: return candidate\n        if problem == 'missing' and on_missing is not None: on_missing(candidate)")
anchor='\ndef _popup(title, message):'
helper='''
def record_missing_playlist_entries(alerts, paths, continuing):
    """Record every encountered missing playlist entry without interrupting playback."""
    silent = {'ErrorPopupEnabled': 0, 'ErrorWindowsNotificationEnabled': 0, 'ErrorSoundEnabled': 0}
    for path in paths:
        alerts.emit(path=path, reason='The playlist audio file is missing.', settings=silent,
                    continuing=continuing)

'''+anchor
s=once(s,anchor,helper);compile(s,str(src),'exec')
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True)
idx=[i for i,line in enumerate(lines) if line.startswith('_PAF_BUNDLED_SOURCES = ')];assert len(idx)==1
bundle=ast.literal_eval(lines[idx[0]].split(' = ',1)[1]);assert 'PAFPlayer_error_delivery' in bundle
bundle['PAFPlayer_error_delivery']=s;lines[idx[0]]='_PAF_BUNDLED_SOURCES = '+repr(bundle)+'\n';text=''.join(lines)
text=once(text,'from PAFPlayer_error_delivery import ErrorAlerts, file_problem, next_playable_entry','from PAFPlayer_error_delivery import ErrorAlerts, file_problem, next_playable_entry, record_missing_playlist_entries')
text=once(text,"'2026-11-12-v667-dj-conversation-log'","'2026-11-12-v668-playlist-errors'")
text=once(text,"PROGRAM_VERSION                = 'V667'","PROGRAM_VERSION                = 'V668'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V667'","PROGRAM_RELEASE_LABEL          = 'V668'")
text=once(text,"['workflowLogsSection','Logs'],['warningsSection','Warnings']", "['workflowLogsSection','Logs'],['warningsSection','Warnings'],['errorsSection','Errors']")
anchor="  for(const id of ['artworkPopupEmojiMaxxConfigButton','floatingLyricsEmojiMaxxConfigButton'])"
insert="""  if(frame&&!document.getElementById('errorsSection')){
    const section=document.createElement('section');section.id='errorsSection';section.className='group';
    const heading=document.createElement('h3');heading.textContent='⚠ Errors';
    const view=document.createElement('iframe');view.src='/errors';view.title='Playback errors this session';view.loading='lazy';view.style.cssText='width:100%;height:380px;border:1px solid #536071;border-radius:7px;background:#0d1118';
    section.append(heading,view);frame.appendChild(section);
  }
"""+anchor
text=once(text,anchor,insert)
text=once(text,"errorBadge.onclick=()=>window.open('/errors','_blank','noopener');", "errorBadge.onclick=()=>{document.getElementById('choicesFrame')?.scrollIntoView({block:'nearest'});document.querySelector('#configTabs [data-target=\\\"errorsSection\\\"]')?.click()};")
text=once(text,'                    replacement = next_playable_entry(available_order, bad_audio)','                    skipped_missing = []\n                    replacement = next_playable_entry(available_order, bad_audio, on_missing=skipped_missing.append)\n                    record_missing_playlist_entries(error_alerts, ([bad_audio] if problem == \'missing\' else []) + skipped_missing, replacement is not None)\n                    if web_server is not None and (skipped_missing or problem == \'missing\'):\n                        web_server.publish(session_error_count=len(error_alerts.snapshot()))')
start=text.index("                pending_playlist_warning = f'{reason} {bad_audio.name}'",text.index('            problem = file_problem(current_audio)'))
end=text.index('                if replacement is None:',start)
old=text[start:end]
new='''                append_pafplayer_trace('playlist.entry-unplayable', playlist=playlist_path,
                                       track=bad_audio, reason=problem,
                                       continuing=replacement is not None)
                if problem != 'missing' or playlist_path is None:
                    pending_playlist_warning = f'{reason} {bad_audio.name}'
                    if error_alerts.emit(path=bad_audio, reason=reason,
                                         settings=load_player_settings(),
                                         tray=getattr(paf_workflows(), 'tray', None),
                                         ffplay_path=paf_ffmpeg_tool_path('ffplay'),
                                         continuing=replacement is not None):
                        record_pafplayer_runtime_warning(pending_playlist_warning, str(bad_audio))
                        if web_server is not None:
                            web_server.publish(session_error_count=len(error_alerts.snapshot()))
                    if web_server is not None:
                        web_server.publish_notice(pending_playlist_warning, seconds=5.0)
                    write_console('\\u26a0 ' + pending_playlist_warning + '\\n')
'''
text=text[:start]+new+text[end:];compile(text,str(p),'exec')
release=root/'releases/PAFPlayer_v668_playlist_errors.py';notes=root/'releases/PAFPlayer_v668_playlist_errors_release_notes.md';assert not release.exists() and not notes.exists()
readme=root/'docs/README.md';docs=readme.read_text(encoding='utf8')
docs=once(docs,'Current release: **V667** — readable DJ conversation log.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v667_dj_conversation_log_release_notes.md).','Current release: **V668** — missing playlist entries appear in the web Errors tab.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v668_playlist_errors_release_notes.md).')
docs=once(docs,'## Experimental AI Podcaster / DJ','## Playlist errors\n\nMissing playlist songs are skipped quietly, including consecutive missing entries; their paths and outcomes appear in the web configuration’s **Errors** tab. The list is newest-first and limited to the current player session. The error badge opens that tab. Other playback errors retain their configured alert delivery.\n\n## Experimental AI Podcaster / DJ')
changelog=root/'docs/PAFPlayer_changelog.md';change=changelog.read_text(encoding='utf8');change=once(change,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V668 — November 12, 2026\n\nSkip missing playlist entries without interrupting playback and show encountered missing files in the web configuration Errors tab. [Release notes](../releases/PAFPlayer_v668_playlist_errors_release_notes.md).\n')
replace(src,s,root/'src/backups');replace(p,text,root/'releases');release.write_text(text,encoding='utf8',newline='');replace(readme,docs,root/'docs');replace(changelog,change,root/'backups')
notes.write_text('# PAFPlayer V668 — Playlist Errors tab\n\nMissing playlist entries are recorded silently, including missing entries encountered while searching for a playable successor. The web configuration includes an Errors tab with the existing current-session list, and the error badge opens it. Other playback errors retain their configured alerts.\n',encoding='utf8')
print('Published V668 workspace release with verified backups.')
