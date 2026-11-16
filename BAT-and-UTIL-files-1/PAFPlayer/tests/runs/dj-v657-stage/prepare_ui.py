from pathlib import Path
import ast
here=Path(__file__).parent;p=here/'PAFPlayer_candidate.py';s=p.read_text(encoding='utf8');dj=(here/'PAFPlayer_dj_candidate_v2.py').read_text(encoding='utf8')
tree=ast.parse(s); value=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES' and ast.literal_eval(t.slice)=='PAFPlayer_dj' for t in n.targets))
lines=s.splitlines(keepends=True);line=lines[value.lineno-1].encode('utf8');lines[value.lineno-1]=(line[:value.col_offset]+repr(dj).encode('utf8')+line[value.end_col_offset:]).decode('utf8');s=''.join(lines)
html='''<div class="control-item" id="djSettings"><h4>AI Podcaster / DJ (experimental)</h4>
<p>AI-generated voices. Track artist and title are sent to OpenAI when cloud providers are selected. No API key is displayed or saved here.</p>
<label><input type="checkbox" id="dj_enabled"> Enable AI DJ</label>
<label>Recent tracks <input id="dj_history" type="number" min="1" max="100" value="10"></label>
<label>Every tracks <input id="dj_interval" type="number" min="1" max="50" value="2"></label>
<label>Approximate seconds <input id="dj_seconds" type="number" min="15" max="600" value="90"></label>
<label>Speakers <input id="dj_speakers" type="number" min="1" max="10" value="2"></label>
<label>Women <input id="dj_women" type="number" min="0" max="10" value="2"></label>
<label>Men <input id="dj_men" type="number" min="0" max="10" value="0"></label>
<label>Text provider <select id="dj_text_provider"><option value="auto">OpenAI, then Ollama</option><option value="ollama">Local Ollama only</option></select></label>
<label>OpenAI text model <input id="dj_text_model" value="gpt-6-luna"></label>
<label>Ollama model <input id="dj_ollama_model" placeholder="Blank = first installed model"></label>
<label>Speech provider <select id="dj_speech_provider"><option value="auto">OpenAI, then Piper</option><option value="piper">Local Piper only</option></select></label>
<label>OpenAI speech model <input id="dj_speech_model" value="gpt-realtime-2.1-mini"></label>
<label>OpenAI voices in speaker order <input id="dj_voices" value="marin,coral,cedar,sage,shimmer,alloy,ash,ballad,echo,fable,nova,onyx,verse"></label>
<label>Requested accent <select id="dj_accent"><option value="neutral">Neutral</option><option>American English</option><option>British English</option><option>Australian English</option></select></label>
<label>Piper executable <input id="dj_piper_executable" placeholder="Blank = search PATH"></label>
<label>Piper voice model paths, one per line <textarea id="dj_piper_voices" rows="2"></textarea></label>
<p>OpenAI voices are named presets: gender and requested accents are not guaranteed. Distinct listed voices are used in order; voices repeat if there are fewer choices than speakers. Piper accent and gender depend on its installed models; models repeat if needed.</p>
<p>Local speech requires Piper and one or more voice models; <a href="https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md" target="_blank" rel="noopener">Piper installation and voice downloads</a>. Its installer and selected voice models are downloaded separately; sizes depend on your selections. PAFPlayer does not overwrite existing installations.</p>
<button id="dj_save" type="button">Save AI DJ settings</button><p id="dj_status" role="status"></p></div>
'''
anchor='  <div class="control-grid" id="experimentalSelectControls"></div>'
assert s.count(anchor)==1;s=s.replace(anchor,html+anchor,1)
script=r'''<script>
(()=>{const $=x=>document.getElementById('dj_'+x), keys=['enabled','history','interval','seconds','speakers','women','men','text_provider','text_model','ollama_model','speech_provider','speech_model','voices','accent','piper_executable','piper_voices'];let loaded=false,local=false,token='';
function balance(changed){const total=Math.max(1,Math.min(10,Number($('speakers').value)||1));$('speakers').value=total;for(const k of ['women','men'])$(k).max=total;if(changed==='women'){$('women').value=Math.max(0,Math.min(total,Number($('women').value)||0));$('men').value=total-Number($('women').value)}else{$('men').value=Math.max(0,Math.min(total,Number($('men').value)||0));$('women').value=total-Number($('men').value)}}
for(const k of ['speakers','women','men'])$(k).addEventListener('input',()=>balance(k));
async function refresh(){try{const r=await fetch('/api/workflows/dj',{cache:'no-store'}),d=await r.json();if(!r.ok)throw new Error(d.error||'Unavailable');local=d.local;token=d.token||sessionStorage.getItem('paf-workflow-token')||'';if(!loaded){for(const k of keys){const e=$(k);if(e.type==='checkbox')e.checked=!!d.settings[k];else e.value=d.settings[k]}loaded=true}for(const k of keys)$(k).disabled=!local;$('save').disabled=!local;$('status').textContent=[d.error,d.notice,d.stage,d.ready?'Commentary ready':'',d.piper_available?'Piper executable configured or found':'Piper executable not detected',!local?'Change settings on the player computer':''].filter(Boolean).join(' · ')}catch(e){$('status').textContent=String(e)}}
$('save').onclick=async()=>{balance('men');const payload={};for(const k of keys){const e=$(k);payload[k]=e.type==='checkbox'?e.checked:e.type==='number'?Number(e.value):e.value}try{const r=await fetch('/api/workflows/dj',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify(payload)}),d=await r.json();if(!r.ok)throw new Error(d.error||'Save failed');$('status').textContent='AI DJ settings saved'}catch(e){$('status').textContent=String(e)}};refresh();setInterval(()=>{if(!document.hidden)refresh()},3000)})();
</script>'''
anchor="    html = screensaver_ui(html)"
# Append to the generated HTML only after all normal UI augmentations.
anchor='    return (\n        html.replace("__POLL_MS__", str(WEB_STATUS_POLL_MILLISECONDS))'
assert s.count(anchor)==1;s=s.replace(anchor,'    html = html.replace("</body>", '+repr(script)+' + "</body>", 1)\n'+anchor,1)
compile(s,str(p),'exec')
with (here/'PAFPlayer_candidate_v2.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
print('staged UI and bundled DJ')
