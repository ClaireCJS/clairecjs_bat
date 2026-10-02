"""Windows media settings UI, added without altering the console visualizer."""
HTML='''
<div class="group" id="windowsMediaSection"><h3>Windows / Lock Screen · Experimental</h3>
<p>Off by default until verified on your Windows installation. Windows decides whether the published media card appears on the lock screen. Source artwork and music tags are never modified.</p>
<div class="workflow-tools">
<label><input type="checkbox" data-windows-setting="enabled">Windows media / lock-screen integration</label>
<label><input type="checkbox" data-windows-setting="artwork" checked>Show album artwork</label>
<label>Artwork source <select data-windows-setting="source"><option value="primary">Primary cover</option><option value="current">Current PAFPlayer artwork</option><option value="none">No artwork</option></select></label>
<label>Lock-screen artwork brightness <input type="range" data-windows-setting="brightness" min="0" max="100" value="100"><output id="windowsBrightness">100%</output></label>
<label><input type="checkbox" data-windows-setting="play_pause" checked>Windows Play/Pause</label>
<label><input type="checkbox" data-windows-setting="previous_next" checked>Windows Previous/Next</label>
<label><input type="checkbox" data-windows-setting="seeking" checked>Windows seeking</label>
<label>Lock-screen title format <select data-windows-setting="title_format"><option value="artist-song">Artist — Song</option><option value="song-artist">Song — Artist</option><option value="song">Song only</option><option value="paf-artist-song">PAFPlayer: Artist — Song</option></select></label>
<label><input type="checkbox" data-windows-setting="album" checked>Publish album name</label>
<label><input type="checkbox" data-windows-setting="timeline" checked>Publish timeline / position</label>
</div><p id="windowsMediaStatus" role="status">Disabled — Windows integration is off</p></div>
'''
SCRIPT=r'''
<script>(()=>{
 const section=document.getElementById('windowsMediaSection'),controls=[...section.querySelectorAll('[data-windows-setting]')];let initialized=false,busy=false;
 function values(){return Object.fromEntries(controls.map(x=>[x.dataset.windowsSetting,x.type==='checkbox'?x.checked:x.type==='range'?Number(x.value):x.value]))}
 function enable(){const v=values();section.querySelector('[data-windows-setting="brightness"]').disabled=!v.enabled||!v.artwork||v.source==='none';document.getElementById('windowsBrightness').textContent=v.brightness+'%'}
 function status(value){const s=value.status;document.getElementById('windowsMediaStatus').textContent=s.state+' — '+s.reason+(s.title?' · '+s.title:'')+(s.brightness!==null?' · Artwork '+s.brightness+'%':'')}
 async function poll(){if(busy)return;try{const r=await fetch('/api/workflows/status'),state=await r.json();if(!r.ok)return;const value=state.windows_media;if(!initialized){for(const el of controls){const v=value.settings[el.dataset.windowsSetting];if(el.type==='checkbox')el.checked=!!v;else el.value=String(v)}initialized=true;enable()}status(value);if(!state.local)controls.forEach(x=>x.disabled=true)}catch(_){}}
 async function save(){enable();busy=true;try{const r=await fetch('/api/workflows/windows-media',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':sessionStorage.getItem('paf-workflow-token')||''},body:JSON.stringify(values())});const result=await r.json();if(!r.ok)throw new Error(result.error);status(result)}catch(e){document.getElementById('windowsMediaStatus').textContent=String(e)}finally{busy=false}}
 for(const el of controls){el.onchange=save;if(el.type==='range')el.oninput=enable}enable();poll();setInterval(()=>{if(!document.hidden)poll()},3000);
})();</script>
'''

def augment(page):
    return page.replace('<div class="group section-global-config" id="globalConfigSection">',HTML+'<div class="group section-global-config" id="globalConfigSection">',1).replace('</body>',SCRIPT+'</body>',1)
