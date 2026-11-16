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
 assert s.count(a)==1,(a[:120],s.count(a));return s.replace(a,b,1)
dj=(root/'tests/runs/PAFPlayer_dj_v662_candidate_v2.py').read_text(encoding='utf8')
player=root/'PAFPlayer.py';lines=player.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines)
text=once(text,"'2026-11-11-v661-dj-private-key'","'2026-11-11-v662-free-dj-providers'")
text=once(text,"PROGRAM_VERSION                = 'V661'","PROGRAM_VERSION                = 'V662'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V661'","PROGRAM_RELEASE_LABEL          = 'V662'")
text=once(text,'<p>AI-generated voices. Track artist and title are sent to OpenAI when cloud providers are selected. No API key is displayed or saved here.</p>','<p>AI-generated voices. Track artist and title may be sent to OpenAI, OpenRouter, or Google when cloud providers are used. Free-provider data policies and availability vary. No API key is displayed or saved here.</p>')
text=once(text,'<label>Text provider <select id="dj_text_provider"><option value="auto">OpenAI, then Ollama</option><option value="ollama">Local Ollama only</option></select></label>','<label>Text provider <select id="dj_text_provider"><option value="auto">OpenAI → free OpenRouter → Gemini if confirmed → Ollama</option><option value="openrouter">Free OpenRouter, then Ollama</option><option value="gemini">Gemini free tier, then Ollama</option><option value="ollama">Local Ollama only</option></select></label>\n<label><input type="checkbox" id="dj_gemini_free_confirmed"> I confirmed that my Gemini project uses the free tier (a paid project can incur charges)</label>')
text=once(text,"['webBackgroundSection','Webpage Background'],['experimentalSection','Experimental'],['workflowDiscordSection','Discord'],['workflowSecuritySection','Security'],['workflowMonitorSection','Monitoring'],['windowsMediaSection','Windows / Lock Screen'],['monkeyMoteSection','MonkeyMote'],['steamSection','Steam'],['globalConfigSection','Global Config'],['workflowLogsSection','Logs']", "['webBackgroundSection','Webpage Background'],['experimentalSection','Experimental'],['workflowDiscordSection','Discord'],['workflowSecuritySection','Security'],['workflowMonitorSection','Monitoring'],['windowsMediaSection','Windows / Lock Screen'],['monkeyMoteSection','MonkeyMote'],['steamSection','Steam'],['globalConfigSection','Global Config'],['workflowLogsSection','Logs'],['warningsSection','Warnings']")
anchor="function organizeControlSections(){\n"
addition="""function organizeControlSections(){
  const frame=document.getElementById('choicesFrame');
  if(frame&&!document.getElementById('warningsSection')){
    const section=document.createElement('section');section.id='warningsSection';section.className='group';
    const heading=document.createElement('h3');heading.textContent='⚠ Warnings';
    const content=document.createElement('div');content.id='djWarningsContent';content.setAttribute('role','status');content.textContent='Checking AI DJ warnings…';
    section.append(heading,content);frame.appendChild(section);
  }
"""
text=once(text,anchor,addition)
text=once(text,"'piper_executable','piper_voices'];let loaded=false", "'piper_executable','piper_voices','gemini_free_confirmed'];let loaded=false")
needle="$('status').textContent=[d.error,d.notice,d.stage,d.ready?'Commentary ready':'',d.piper_available?'Piper executable found':'Piper executable not detected',String(d.piper_voices_found||0)+' Piper voice model files found',!local?'Change settings on the player computer':''].filter(Boolean).join(' · ')"
repl="$('status').textContent=[d.error,d.notice,d.stage,d.ready?'Commentary ready':'',d.piper_available?'Piper executable found':'Piper executable not detected',String(d.piper_voices_found||0)+' Piper voice model files found',d.openrouter_configured?'OpenRouter key found':'OpenRouter key not found',d.gemini_configured?'Gemini key found':'Gemini key not found',!local?'Change settings on the player computer':''].filter(Boolean).join(' · ');const warnings=document.getElementById('djWarningsContent');if(warnings)warnings.textContent=Array.isArray(d.warnings)&&d.warnings.length?d.warnings.join(' · '):'No AI DJ warnings.'"
text=once(text,needle,repl)
needle="    if log is not None and not log.path: rows.append('DJ diagnostic log unavailable; check folder permissions.')\n    if error:"
repl="    if log is not None and not log.path: rows.append('DJ diagnostic log unavailable; check folder permissions.')\n    for warning in getattr(controller, 'warning_messages', lambda: [])():\n        rows.extend(wrap_to_cells('WARNING: ' + clean(warning), width))\n    if error:"
text=once(text,needle,repl)
old="current_dj_snapshot = getattr(dj_controller, 'help_snapshot', lambda: None)()"
new="current_dj_snapshot = (getattr(dj_controller, 'help_snapshot', lambda: None)(), tuple(getattr(dj_controller, 'warning_messages', lambda: [])()))"
assert text.count(old)==2;text=text.replace(old,new)
compile(dj,'dj','exec');compile(text,str(player),'exec')
release=root/'releases/PAFPlayer_v662_free_dj_providers.py';notes=root/'releases/PAFPlayer_v662_free_dj_providers_release_notes.md';assert not release.exists() and not notes.exists()
replace(root/'src/PAFPlayer_dj.py',dj,root/'backups');replace(player,text,root/'releases');release.write_text(text,encoding='utf8',newline='')
test=root/'tests/test_v662_free_providers.py';s=test.read_text(encoding='utf8');s=once(s,"ROOT/'tests/runs/PAFPlayer_dj_v662_candidate.py'","ROOT/'src/PAFPlayer_dj.py'");replace(test,s,root/'backups')
readme=root/'docs/README.md';s=readme.read_text(encoding='utf8')
s=once(s,'Current release: **V661** — private-file AI DJ key loading.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v661_dj_private_key_release_notes.md).','Current release: **V662** — free DJ providers and credit warnings.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v662_free_dj_providers_release_notes.md).')
anchor='## Experimental AI Podcaster / DJ\n'
paragraph='''
Automatic text generation tries OpenAI, then OpenRouter's `openrouter/free`, then Gemini only if the user confirms its project is on the free tier, then local Ollama. Explicit OpenRouter or Gemini modes also fall back to Ollama. OpenRouter uses only its free router; Gemini's free-eligible model can incur charges if the Google project has paid billing, so its confirmation checkbox defaults off. Supply `OPENROUTER_API_KEY` and `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) through `C:\\BAT\\private.env` or the player environment; keys are never displayed in settings or written to DJ logs. Artist/title metadata goes to whichever hosted text provider is used, and free-tier provider data policies vary. Piper remains the local speech fallback.

If OpenAI returns the specific `credit_balance_exhausted` error, Help and the bottom **Warnings** web tab show the last confirmed observation. The warning persists across restarts for the same key and clears after a successful OpenAI text request. It does not claim a balance for an untested key, or treat an ordinary rate limit as exhausted credit.

'''
s=once(s,anchor,anchor+paragraph)
s=once(s,'If cloud text fails, PAFPlayer tries the smallest installed local Ollama model (or the configured model), with a bounded context.','If hosted text fails, PAFPlayer tries the smallest installed local Ollama model (or the configured model), with a bounded context.')
replace(readme,s,root/'docs')
changelog=root/'docs/PAFPlayer_changelog.md';s=changelog.read_text(encoding='utf8');s=once(s,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V662 — November 11, 2026\n\nAdd free OpenRouter and explicitly confirmed Gemini fallback, preserve Ollama/Piper, and show persistent evidence-based OpenAI credit warnings in Help and the bottom Warnings web tab. [Release notes](../releases/PAFPlayer_v662_free_dj_providers_release_notes.md).\n');replace(changelog,s,root/'backups')
notes.write_text('''# PAFPlayer V662 — free DJ providers and credit warnings

Text fallback adds OpenRouter's free router and Gemini's free-eligible model before Ollama. Gemini is skipped unless the user explicitly confirms the Google project is on the free tier; a paid project can incur charges. Local Piper remains the speech fallback. Keys come from private.env or the process environment; artist/title metadata is sent to the selected hosted service.

The exact OpenAI `credit_balance_exhausted` error creates a persistent key-scoped warning in Help and the bottom Warnings web tab; ordinary rate limits do not. A later successful OpenAI text request clears the warning. Free-provider availability and credentials require separate verification.
''',encoding='utf8')
print('Published V662 player, free providers, warnings, and documentation.')
