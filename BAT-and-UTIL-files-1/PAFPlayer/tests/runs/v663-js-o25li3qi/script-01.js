
const ms=200;
const spectrumMs=100;
const spectrumDrawMs=1000/30.0;
const karaokeAnimMs=1000/15.0;
let artGeneration=-1;
let webArtIndex=0;
let latestState={};
let lyricText='';
let lyricSpans=[];
let spectrumTarget=[];
let spectrumCurrent=[];
let spectrumPaused=false;
let webVisualizerEnabled=true;
let webClockSample={position:0,duration:0,progress:0,speed:1,paused:true,playing:false,karaokeOffset:0,at:performance.now()};let lastWebClockPaint=0;
let webSeekPending=null;
let spectrumWorker=null;
let spectrumOutputBins=64;
let spectrumAgcGain=2.0;
let controlSchema=null;
let progressDemoSnapshot=null;
let progressDemoActive=false;
let lyricReservedHeight=0;
let lyricUnusedSince=null;
let lastMouseActivity=performance.now();
let loadedPlayerVersion=null;
let serverWebPrefs={};
let webPrefsSaveTimer=null;
async function loadWebPreferences(){
  try{const r=await fetch('/api/web-preferences',{cache:'no-store'});if(r.ok){const d=await r.json();if(d&&typeof d==='object'&&!Array.isArray(d))serverWebPrefs=d}}catch(e){}
}
function webPrefGet(key,fallback=null){
  if(Object.prototype.hasOwnProperty.call(serverWebPrefs,key))return serverWebPrefs[key];
  try{const raw=localStorage.getItem(key);if(raw===null)return fallback;try{return JSON.parse(raw)}catch(e){return raw}}catch(e){return fallback}
}
function webPrefSet(key,value){
  serverWebPrefs[key]=value;
  try{localStorage.setItem(key,typeof value==='string'?value:JSON.stringify(value))}catch(e){}
  clearTimeout(webPrefsSaveTimer);webPrefsSaveTimer=setTimeout(()=>{fetch('/api/web-preferences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(serverWebPrefs)}).catch(()=>{})},80);
}
function webPrefBool(key,fallback=false){const v=webPrefGet(key,fallback?1:0);return v===true||v===1||v==='1'||String(v).toLowerCase()==='true'}
let karaokeAutoExpand=localStorage.getItem('paf-karaoke-auto-expand')==='1';
const WEB_KARAOKE_KEY='paf-web-karaoke-v238';
let webKaraokeSettings={};
let rawWebLyric='';
let lastWebLyricRenderSignature='';
let webLyricRenderSequence=0;
let webLyricSolutions=[];
const webLyricStyleCache=new Map();
let webLyricTimeline=[];
let hostSolutionSignature='';
let lastLyricAnimationPaint=0;
let lastSpectrumAnimationPaint=0;
let lastLyricColorMode=-1;
let lyricWordByChar=[];
let lastRenderedUrlsSignature='';
let lastChipsHtml='';
let versionChipUntil=performance.now()+20000;
let lastWebBackgroundSignature='';
let webBgOverrideIndex=null;
let webBgMatchedIndex=null;
let webBgInfoSerial=0;
let webPlaylistOffset=null;
let webPlaylistLimit=100;
let webPlaylistRefreshTimer=null;
let activeEmojimaxTooltipSpan=null;
let webArtAutoRotateAt=performance.now()+20000;

function setupResizableWebPanes(){
  const root=document.documentElement;
  const artHandle=document.getElementById('artResizeHandle');
  const choicesHandle=document.getElementById('choicesResizeHandle');
  const savedTop=Number(localStorage.getItem('paf-web-top-height-px')||0);
  if(savedTop>0) root.style.setProperty('--paf-top-height',Math.max(160,Math.min(window.innerHeight*.68,savedTop))+'px');
  const savedLyric=Number(localStorage.getItem('paf-web-lyric-height-px')||0);
  if(savedLyric>0){lyricReservedHeight=Math.max(70,Math.min(window.innerHeight*.46,savedLyric));document.getElementById('lyricDock').style.height=lyricReservedHeight+'px';}
  function drag(handle,onMove){if(!handle)return;handle.addEventListener('pointerdown',e=>{e.preventDefault();handle.setPointerCapture(e.pointerId);const move=ev=>onMove(ev);const up=()=>{handle.removeEventListener('pointermove',move);handle.removeEventListener('pointerup',up)};handle.addEventListener('pointermove',move);handle.addEventListener('pointerup',up)})}
  drag(artHandle,e=>{const bodyTop=document.body.getBoundingClientRect().top;const px=Math.max(160,Math.min(window.innerHeight*.68,e.clientY-bodyTop));root.style.setProperty('--paf-top-height',px+'px');localStorage.setItem('paf-web-top-height-px',String(Math.round(px)));requestAnimationFrame(()=>{resizeCanvas();fitWebSongTitle();updateKaraokeReservation()})});
  drag(choicesHandle,e=>{const lyricTop=document.getElementById('lyricDock').getBoundingClientRect().top;const px=Math.max(70,Math.min(window.innerHeight*.46,e.clientY-lyricTop));lyricReservedHeight=px;document.getElementById('lyricDock').style.height=px+'px';localStorage.setItem('paf-web-lyric-height-px',String(Math.round(px)));requestAnimationFrame(fitKaraokeToDock)});
}

function markMouseActivity(){lastMouseActivity=performance.now()}
for(const eventName of ['pointermove','pointerdown','wheel']){
  window.addEventListener(eventName,markMouseActivity,{passive:true});
}
window.addEventListener('resize',()=>{if(karaokeAutoExpand&&lyricText){karaokeFitRetryCount=0;requestAnimationFrame(()=>requestAnimationFrame(fitKaraokeToDock))}},{passive:true});

function loadWebKaraokeSettings(){
  const base={enabled:true,style:1,treatment:2,emojimax:false,teenySolutions:true,teenySize:20,teenyDistance:1,teenyAbove:false,teenyInherit:false,teenyColor:'#f4f8ff',teenyOpacity:100,decensor:false,glow:true,glowColor:'#000000',glowSize:14,styleFav:[],treatmentFav:[],styleDefault:1,treatmentDefault:2};
  const saved=webPrefGet(WEB_KARAOKE_KEY,{});return {...base,...(saved&&typeof saved==='object'&&!Array.isArray(saved)?saved:{})}
}
function saveWebKaraokeSettings(){webPrefSet(WEB_KARAOKE_KEY,webKaraokeSettings)}
function webKaraokeEnabled(){return !!webKaraokeSettings.enabled}
function webKaraokeChoiceStore(kind){return kind==='style'?{fav:'styleFav',def:'styleDefault'}:{fav:'treatmentFav',def:'treatmentDefault'}}
function makeWebKaraokeSelect(kind,item){
  const wrap=document.createElement('div');wrap.className='control-item';wrap.title='Web-only '+item.label+'; saved separately from console karaoke';
  const label=document.createElement('label');label.textContent=item.label.replace('Karaoke ','');
  const row=document.createElement('div');row.className='select-with-marks';const select=document.createElement('select');select.title=wrap.title;
  const store=webKaraokeChoiceStore(kind);const favorites=new Set((webKaraokeSettings[store.fav]||[]).map(Number));
  for(const opt of item.options||[]){const o=document.createElement('option');o.value=String(opt.value);o.dataset.rawLabel=opt.label;select.appendChild(o)}
  function decorate(){for(const o of select.options){const v=Number(o.value),raw=o.dataset.rawLabel||o.textContent||'';const f=favorites.has(v),d=Number(webKaraokeSettings[store.def])===v;o.textContent=(f?'⭐ ':'')+(d?'✨ ':'')+raw;o.style.fontWeight=d?'800':'400'}}
  const marks=document.createElement('div');marks.className='choice-marks-stack';
  const favLabel=document.createElement('label');favLabel.className='choice-mark';const fav=document.createElement('input');fav.type='checkbox';favLabel.append(fav,document.createTextNode('Fav'));
  const defLabel=document.createElement('label');defLabel.className='choice-mark';const def=document.createElement('input');def.type='radio';def.name='web-karaoke-default-'+kind;defLabel.append(def,document.createTextNode('Def'));
  const cycle=document.createElement('button');cycle.type='button';cycle.className='secondary-button choice-tool-button';cycle.textContent='↻';cycle.title='Click: cycle saved favorites. Right-click: cycle all choices sequentially. Double-click: restore the default.';marks.append(favLabel,defLabel,cycle);
  function sync(){const v=Number(select.value);fav.checked=favorites.has(v);def.checked=Number(webKaraokeSettings[store.def])===v;decorate()}
  select.value=String(webKaraokeSettings[kind]||1);select.onchange=()=>{webKaraokeSettings[kind]=Number(select.value);saveWebKaraokeSettings();sync();renderWebLyric(rawWebLyric,true)};
  fav.onchange=()=>{const v=Number(select.value);if(fav.checked)favorites.add(v);else favorites.delete(v);webKaraokeSettings[store.fav]=[...favorites].sort((a,b)=>a-b);saveWebKaraokeSettings();sync()};
  def.onclick=e=>{const v=Number(select.value);const old=Number(webKaraokeSettings[store.def]);if(old===v){def.checked=true;return}e.preventDefault();const raw=select.options[select.selectedIndex]?.dataset.rawLabel||v,previous=[...select.options].find(o=>Number(o.value)===old)?.dataset.rawLabel||old;if(confirm('Are you sure you want to change the default Web Karaoke '+kind+' from “'+previous+'” to “'+raw+'”?')){webKaraokeSettings[store.def]=v;saveWebKaraokeSettings()}sync()};
  function cycleValues(favoritesOnly){const all=[...select.options].map(o=>Number(o.value));const values=favoritesOnly?all.filter(v=>favorites.has(v)):all;if(!values.length)return;const at=values.indexOf(Number(select.value));select.value=String(values[(at+1+values.length)%values.length]);select.onchange()}
  let cycleClicks=0,cycleTimer=null;cycle.onclick=()=>{cycleClicks++;if(cycleTimer)clearTimeout(cycleTimer);if(cycleClicks>=2){cycleClicks=0;cycleTimer=null;select.value=String(webKaraokeSettings[store.def]);select.onchange();return}cycleTimer=setTimeout(()=>{cycleClicks=0;cycleTimer=null;cycleValues(true)},240)};
  cycle.oncontextmenu=e=>{e.preventDefault();if(cycleTimer)clearTimeout(cycleTimer);cycleClicks=0;cycleTimer=null;cycleValues(false)};
  row.append(select,marks);wrap.append(label,row);sync();return wrap;
}
function applyWebKaraokeEnabled(){
  const section=document.getElementById('webKaraokeSection'),dock=document.getElementById('lyricDock'),master=document.getElementById('webKaraokeMasterToggle');
  if(master)master.checked=webKaraokeEnabled();if(section)section.classList.toggle('section-disabled',!webKaraokeEnabled());if(dock)dock.style.display=webKaraokeEnabled()?'':'none';
}
function webLyricStyleKey(text){return [String(text||''),webKaraokeSettings.style,!!webKaraokeSettings.emojimax,!!webKaraokeSettings.decensor].join('\u241f')}
function prepareWebLyric(text){
  const raw=String(text||''),key=webLyricStyleKey(raw);
  if(webLyricStyleCache.has(key))return webLyricStyleCache.get(key);
  const prepared={text:raw,solutions:[],ready:!raw,promise:null};
  webLyricStyleCache.set(key,prepared);
  while(webLyricStyleCache.size>32)webLyricStyleCache.delete(webLyricStyleCache.keys().next().value);
  prepared.promise=(async()=>{
    if(raw){try{const r=await fetch('/api/web-karaoke-render',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:raw,style:Number(webKaraokeSettings.style||1),emojimax:!!webKaraokeSettings.emojimax,decensor:!!webKaraokeSettings.decensor})});if(r.ok){const d=await r.json();prepared.text=String(d.text??raw);prepared.solutions=Array.isArray(d.solutions)?d.solutions:[]}}catch(e){}}
    prepared.ready=true;return prepared;
  })();
  return prepared;
}
async function renderWebLyric(text,force=false){
  rawWebLyric=String(text||'');const sig=webLyricStyleKey(rawWebLyric);
  if(!force&&sig===lastWebLyricRenderSignature)return;
  lastWebLyricRenderSignature=sig;const requestSequence=++webLyricRenderSequence;
  const prepared=prepareWebLyric(rawWebLyric);
  function present(){webLyricSolutions=prepared.solutions;setRainbowLyric(prepared.text,prepared.solutions);applyWebKaraokeEnabled();applyWebKaraokeGlow();updateWebEmojimaxToggle()}
  // The line changes at its deadline even if a style request is still in flight.
  present();
  if(!prepared.ready){await prepared.promise;if(requestSequence===webLyricRenderSequence)present()}
}
function scheduledWebLyric(now){
  if(!webLyricTimeline.length)return;
  const sample=webClockSample;
  let position=Number(sample.lyricPosition||0);
  if(sample.playing&&!sample.paused)position+=Math.max(0,Math.min(now,sample.validUntil??now)-sample.at)/1000*Math.max(0,Number(sample.speed||1));
  position=Math.max(0,position+Number(sample.karaokeOffset||0));
  let lo=0,hi=webLyricTimeline.length;
  while(lo<hi){const mid=(lo+hi)>>>1;if(Number(webLyricTimeline[mid][0])<=position)lo=mid+1;else hi=mid}
  const index=lo-1;
  // Prepare future styles without displaying a future cue on any surface.
  for(let next=Math.max(0,index);next<Math.min(webLyricTimeline.length,index+3);next++)prepareWebLyric(webLyricTimeline[next][1]);
  renderWebLyric(index>=0?webLyricTimeline[index][1]:'');
}
function updateTeenySolutions(){
 const enabled=!!webKaraokeSettings.emojimax,shown=enabled&&!!webKaraokeSettings.teenySolutions;
 const size=Math.max(5,Math.min(150,Number(webKaraokeSettings.teenySize??20)));
 const distance=Math.max(-50,Math.min(50,Number(webKaraokeSettings.teenyDistance??1)));
 const opacity=Math.max(0,Math.min(100,Number(webKaraokeSettings.teenyOpacity??100)));
 const color=/^#[0-9a-fA-F]{6}$/.test(String(webKaraokeSettings.teenyColor))?webKaraokeSettings.teenyColor:'#f4f8ff';
 const host=document.getElementById('lyric'),fontPixels=parseFloat(getComputedStyle(host).fontSize)||16,distancePixels=fontPixels*distance/100,reservePixels=Math.max(0,fontPixels*(size+distance)/100);host.classList.toggle('teeny-solutions',shown);host.classList.toggle('teeny-above',!!webKaraokeSettings.teenyAbove);host.classList.toggle('teeny-inherit',!!webKaraokeSettings.teenyInherit);host.style.setProperty('--teeny-size',size+'%');host.style.setProperty('--teeny-ratio',String(size/100));host.style.setProperty('--teeny-distance',distancePixels+'px');host.style.setProperty('--teeny-x-offset',(fontPixels*2/100)+'px');host.style.setProperty('--teeny-reserve',reservePixels+'px');host.style.setProperty('--teeny-color',color);host.style.setProperty('--teeny-opacity',String(opacity/100));
 document.getElementById('teenyToggleLabel').hidden=!enabled;document.getElementById('teenySolutions').checked=shown;
 for(const node of document.querySelectorAll('.teeny-option'))node.hidden=!shown;
 document.getElementById('teenySize').value=size;document.getElementById('teenySizeValue').textContent=size+'%';
 document.getElementById('teenyDistance').value=distance;document.getElementById('teenyDistanceValue').textContent=distance+'%';
 document.getElementById('teenyAbove').checked=!!webKaraokeSettings.teenyAbove;
 document.getElementById('teenyInherit').checked=!!webKaraokeSettings.teenyInherit;
 document.getElementById('teenyColorLabel').hidden=!shown||!!webKaraokeSettings.teenyInherit;
 document.getElementById('teenyColor').value=color;
 document.getElementById('teenyOpacity').value=opacity;document.getElementById('teenyOpacityValue').textContent=opacity+'%';
}
function updateWebEmojimaxToggle(){const b=document.getElementById('webEmojimaxToggle');if(b)b.checked=!!webKaraokeSettings.emojimax;updateTeenySolutions()}
function hexToRgba(hex,alpha){const raw=String(hex||'#000000').replace('#','');const n=parseInt(raw.length===3?raw.split('').map(x=>x+x).join(''):raw,16)||0;return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${alpha})`}
function applyWebKaraokeGlow(){
  const host=document.getElementById('lyric');if(!host)return;const enabled=!!webKaraokeSettings.glow;const pct=Math.max(0,Math.min(100,Number(webKaraokeSettings.glowSize||0)));
  const px=Math.max(0.5,(parseFloat(getComputedStyle(host).fontSize)||48)*(pct/100));const color=String(webKaraokeSettings.glowColor||'#000000');
  host.style.textShadow=enabled?`0 0 ${Math.max(1,px*.45)}px ${hexToRgba(color,.92)},0 0 ${Math.max(2,px)}px ${hexToRgba(color,.72)},0 0 ${Math.max(3,px*1.65)}px ${hexToRgba(color,.42)}`:'none';
  const label=document.getElementById('webKaraokeGlowLabel');if(label)label.textContent='Glow size '+Math.round(pct)+'%';
}
function setupWebKaraokeGlow(){
 const en=document.getElementById('webKaraokeGlow'),color=document.getElementById('webKaraokeGlowColor'),size=document.getElementById('webKaraokeGlowSize');if(!en||!color||!size)return;
 en.checked=!!webKaraokeSettings.glow;color.value=String(webKaraokeSettings.glowColor||'#000000');size.value=String(Number(webKaraokeSettings.glowSize||14));
 const sync=()=>{webKaraokeSettings.glow=en.checked;webKaraokeSettings.glowColor=color.value;webKaraokeSettings.glowSize=Number(size.value);saveWebKaraokeSettings();applyWebKaraokeGlow()};en.onchange=sync;color.oninput=sync;size.oninput=sync;sync();
}
function lyricNaturalHeight(){
  const host=document.getElementById('lyric');
  const previous=host.style.fontSize;
  host.style.fontSize='';
  const style=getComputedStyle(host);
  const margins=(parseFloat(style.marginTop)||0)+(parseFloat(style.marginBottom)||0);
  const height=Math.max(1,Math.ceil(host.getBoundingClientRect().height+margins),Math.ceil(host.scrollHeight+margins));
  host.style.fontSize=previous;
  return height;
}

function karaokeInkFits(host,available){
  const cs=getComputedStyle(host),fontSize=parseFloat(cs.fontSize)||42;
  const edgeGuard=Math.max(2,fontSize*.012);
  const dockBounds=host.parentElement.getBoundingClientRect();
  const inkRange=document.createRange();inkRange.selectNodeContents(host);
  const inkBounds=inkRange.getBoundingClientRect();
  // scrollHeight/scrollWidth are much more reliable for a lyric made of many
  // independently-colored inline spans than a Range's horizontal union.
  // However the actual glyph boxes may protrude vertically beyond the host's
  // line boxes at large font sizes, so also require their bounds to fit the
  // panel. Range width is deliberately not used for the horizontal test.
  return host.scrollHeight+edgeGuard<=available && host.scrollWidth<=host.clientWidth+1 &&
    inkBounds.top>=dockBounds.top+edgeGuard && inkBounds.bottom<=dockBounds.bottom-edgeGuard;
}
let karaokeFitRetryCount=0;
function fitKaraokeToDock(){
  const host=document.getElementById('lyric');
  const dock=document.getElementById('lyricDock');
  dock.classList.toggle('auto-expand',!!karaokeAutoExpand);
  if(!karaokeAutoExpand || !lyricText){host.style.fontSize='';host.style.paddingBottom='';host.style.lineHeight='';karaokeFitRetryCount=0;applyWebKaraokeGlow();return}
  // Do not permanently "fit" against a zero/half-laid-out grid.  This was the
  // other route to postage-stamp karaoke: the first rAF could run while the
  // full-width lyric row still reported a tiny clientWidth, then never retry.
  if(host.clientWidth<160 || dock.clientWidth<160){
    if(karaokeFitRetryCount++<8)requestAnimationFrame(fitKaraokeToDock);
    return;
  }
  karaokeFitRetryCount=0;
  host.style.fontSize='';host.style.paddingBottom='0.18em';host.style.lineHeight='1.04';
  const base=Math.max(28,parseFloat(getComputedStyle(host).fontSize)||42);
  // The resize handle owns the frame. Auto-Expand owns only the type inside it.
  // Fit both directions: even the normal font can be too large for a short dock.
  const available=Math.max(1,dock.clientHeight-4);
  const cap=Math.max(1024,Math.min(4096,Math.max(available*3,host.clientWidth*2)));
  let lo=4,hi=Math.max(base,Math.min(cap,available*1.5)),best=lo;
  host.style.fontSize=lo+'px';
  if(karaokeInkFits(host,available)){
    while(true){
      host.style.fontSize=hi+'px';
      if(!karaokeInkFits(host,available))break;
      best=hi;lo=hi;
      if(hi>=cap)break;
      hi=Math.min(cap,hi*2);
    }
    if(best<hi)for(let i=0;i<16;i++){
      const mid=(lo+hi)/2;host.style.fontSize=mid+'px';
      if(karaokeInkFits(host,available)){best=mid;lo=mid}else hi=mid;
    }
  }
  host.style.fontSize=Math.max(4,best*.997)+'px';applyWebKaraokeGlow();
}

function updateKaraokeReservation(now=performance.now()){
  const dock=document.getElementById('lyricDock');
  const needed=lyricNaturalHeight()+4;
  if(karaokeAutoExpand && lyricText){
    const manual=Number(localStorage.getItem('paf-web-lyric-height-px')||0);
    const manualHeight=manual>=70?manual:0;
    const assigned=manualHeight||Math.max(70,lyricReservedHeight||0,dock.clientHeight||0);
    lyricReservedHeight=assigned;
    lyricUnusedSince=null;dock.style.height=lyricReservedHeight+'px';
    requestAnimationFrame(()=>requestAnimationFrame(fitKaraokeToDock));return;
  }
  if(lyricReservedHeight<=0 || needed>lyricReservedHeight+1){lyricReservedHeight=needed;lyricUnusedSince=null;dock.style.height=lyricReservedHeight+'px';requestAnimationFrame(fitKaraokeToDock);return;}
  if(needed<lyricReservedHeight-1){
    if(lyricUnusedSince===null) lyricUnusedSince=now;
    if(now-lyricUnusedSince>=30000 && now-lastMouseActivity>=30000){lyricReservedHeight=needed;lyricUnusedSince=null;dock.style.height=lyricReservedHeight+'px';}
  }else lyricUnusedSince=null;
  requestAnimationFrame(fitKaraokeToDock);
}

function fitWebSongTitle(){
  const title=document.getElementById('songTitle');
  title.style.fontSize='';
  const target=parseFloat(getComputedStyle(title).fontSize)||76;
  function renderedLines(){const cs=getComputedStyle(title);const lh=parseFloat(cs.lineHeight)||((parseFloat(cs.fontSize)||1)*1.08);return Math.max(1,Math.round(title.getBoundingClientRect().height/Math.max(1,lh)));}
  title.style.fontSize=target+'px';
  if(renderedLines()<=2) return;
  let lo=16,hi=target,best=16;title.style.fontSize=lo+'px';if(renderedLines()>2)return;
  for(let i=0;i<11;i++){const mid=(lo+hi)/2;title.style.fontSize=mid+'px';if(renderedLines()<=2){best=mid;lo=mid}else hi=mid;}
  title.style.fontSize=Math.max(16,best)+'px';
}

function action(name){
  if(name==='playlist-delete-current-web-confirmed' &&
     !confirm('Remove current track from playlist? The audio file will NOT be deleted.')) return;
  return fetch('/api/action',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({action:name})
  }).catch(()=>{});
}

function fmtTime(seconds){
  if(seconds===null || seconds===undefined || !Number.isFinite(Number(seconds))) return 'unknown';
  const whole=Math.max(0,Math.floor(Number(seconds)));
  const h=Math.floor(whole/3600), rem=whole%3600, m=Math.floor(rem/60), s=rem%60;
  return h ? `${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
           : `${m}:${String(s).padStart(2,'0')}`;
}

function hideWebEmojimaxTooltip(){const tip=document.getElementById('emojimaxTooltip');if(tip)tip.style.display='none';activeEmojimaxTooltipSpan=null}
function webEmojimaxSolutionColor(lyricColor,inherit,configured){return inherit?lyricColor:(/^#[0-9a-fA-F]{6}$/.test(String(configured))?configured:'#f4f8ff')}
function currentWebEmojimaxSolutionColor(span){return webEmojimaxSolutionColor(getComputedStyle(span).color,!!webKaraokeSettings.teenyInherit,webKaraokeSettings.teenyColor)}
window.addEventListener('blur',hideWebEmojimaxTooltip);window.addEventListener('scroll',hideWebEmojimaxTooltip,{passive:true});window.addEventListener('resize',hideWebEmojimaxTooltip,{passive:true});document.addEventListener('visibilitychange',()=>{if(document.hidden)hideWebEmojimaxTooltip()});document.getElementById('lyricDock').addEventListener('pointerleave',hideWebEmojimaxTooltip);
function setRainbowLyric(text,solutions=[]){
  text=text||'';
  const solutionSig=JSON.stringify(solutions||[]);
  if(text===lyricText && solutionSig===hostSolutionSignature) return;
  lyricText=text;hostSolutionSignature=solutionSig;
  const host=document.getElementById('lyric'),chars=Array.from(text),tip=document.getElementById('emojimaxTooltip');
  hideWebEmojimaxTooltip();host.title=text||'Lyrics';host.textContent='';lyricSpans=[];
  const tagged=new Map();let searchFrom=0;
  function findSequence(haystack,needle,start){outer:for(let i=Math.max(0,start);i<=haystack.length-needle.length;i++){for(let j=0;j<needle.length;j++)if(haystack[i+j]!==needle[j])continue outer;return i}return -1}
  for(const item of (Array.isArray(solutions)?solutions:[])){const display=Array.from(String(item.display||''));if(!display.length)continue;let at=findSequence(chars,display,searchFrom);if(at<0)at=findSequence(chars,display,0);if(at<0)continue;const answer=String(item.solution_styled||item.solution||'');for(let i=at;i<at+display.length;i++)tagged.set(i,answer);searchFrom=at+display.length}
  let solutionGroup=null,previousAnswer=null;
  chars.forEach((ch,index)=>{const span=document.createElement('span');span.textContent=ch;span.dataset.i=String(index);const answer=tagged.get(index);if(answer){span.classList.add('emojimax-solution');span.dataset.solution=answer;span.title=String(answer);const show=e=>{if(!tip)return;activeEmojimaxTooltipSpan=span;const cs=getComputedStyle(span);tip.textContent=answer;tip.style.fontFamily=cs.fontFamily;tip.style.fontSize=cs.fontSize;tip.style.fontWeight=cs.fontWeight;tip.style.color=currentWebEmojimaxSolutionColor(span);tip.style.textShadow='none';tip.style.display='block';tip.style.left=Math.max(6,Math.min(window.innerWidth-tip.offsetWidth-8,e.clientX+14))+'px';tip.style.top=Math.max(6,e.clientY-tip.offsetHeight-12)+'px'};span.addEventListener('pointerenter',show);span.addEventListener('pointermove',show);span.addEventListener('pointerleave',hideWebEmojimaxTooltip);span.addEventListener('pointercancel',hideWebEmojimaxTooltip)}if(answer){if(!solutionGroup||answer!==previousAnswer){solutionGroup=document.createElement('span');solutionGroup.className='emojimax-token';solutionGroup.dataset.solution=answer;host.appendChild(solutionGroup)}solutionGroup.appendChild(span)}else{solutionGroup=null;host.appendChild(span)}previousAnswer=answer;lyricSpans.push(span)});updateTeenySolutions();
  lyricWordByChar=[];let wordIndex=0;for(let i=0;i<lyricSpans.length;i++){lyricWordByChar[i]=wordIndex;if(/\s/.test(lyricSpans[i].textContent||''))wordIndex++}
  lastLyricColorMode=-1;
  requestAnimationFrame(()=>requestAnimationFrame(()=>{updateKaraokeReservation();applyWebKaraokeGlow()}));
}

function configureLyricColorMode(effective){
  if(effective===lastLyricColorMode)return;
  lastLyricColorMode=effective;
  const host=document.getElementById('lyric'),count=Math.max(1,lyricSpans.length);
  lyricSpans.forEach((span,index)=>{
    let hue=205,sat=15,light=88,dynamic=false;
    if(effective===2){hue=(index/count)*330;sat=100;light=58;dynamic=true}
    else if(effective===3){hue=(lyricWordByChar[index]*57)%360;sat=100;light=60;dynamic=true}
    else if(effective===4){hue=((index*137.508)+(rawWebLyric.length*31))%360;sat=95;light=62}
    else if(effective===5){hue=((lyricWordByChar[index]*83)+(rawWebLyric.length*19))%360;sat=85;light=62}
    span.style.color=dynamic?`hsl(calc(${hue} + var(--paf-lyric-phase,0)) ${sat}% ${light}%)`:`hsl(${hue} ${sat}% ${light}%)`;
  });
  host.querySelectorAll('.emojimax-token').forEach(token=>{token.style.color=token.firstElementChild?.style.color||'inherit'});
  if(host && effective!==2 && effective!==3)host.style.setProperty('--paf-lyric-phase','0');
}

function animateLyric(now){
  scheduledWebLyric(now);
  if(spectrumPaused){requestAnimationFrame(animateLyric);return;}
  if(document.hidden || now-lastLyricAnimationPaint<karaokeAnimMs){requestAnimationFrame(animateLyric);return;}
  lastLyricAnimationPaint=now;
  const mode=Number(webKaraokeSettings.treatment||2);let effective=mode;if(mode>=6)effective=1+Math.floor((now/1800+(mode-6)*2)%5);
  configureLyricColorMode(effective);
  if(effective===2 || effective===3){const host=document.getElementById('lyric');if(host)host.style.setProperty('--paf-lyric-phase',String((now/28)%360));}
  if(activeEmojimaxTooltipSpan){const tip=document.getElementById('emojimaxTooltip'),cs=getComputedStyle(activeEmojimaxTooltipSpan);if(tip&&tip.style.display!=='none'){tip.style.color=currentWebEmojimaxSolutionColor(activeEmojimaxTooltipSpan);tip.style.textShadow='none';tip.style.fontFamily=cs.fontFamily;tip.style.fontSize=cs.fontSize;tip.style.fontWeight=cs.fontWeight}}
  requestAnimationFrame(animateLyric);
}

function resizeCanvas(){
  const canvas=document.getElementById('visualizer');
  const dpr=Math.max(1,window.devicePixelRatio||1);
  const rect=canvas.getBoundingClientRect();
  const w=Math.max(1,Math.round(rect.width*dpr));
  const h=Math.max(1,Math.round(rect.height*dpr));
  spectrumOutputBins=Math.max(32,Math.min(96,Math.round(rect.width/12)));
  if(canvas.width!==w || canvas.height!==h){canvas.width=w;canvas.height=h}
}

function adaptiveFrequencyBins(raw){
  const source=raw instanceof Uint8Array?raw:new Uint8Array(raw||0);
  const fraction=latestState.adaptive_frequency_enabled?Math.max(.25,Math.min(1,Number(latestState.adaptive_frequency_fraction)||1)):1;
  if(fraction>=1||!source.length)return source;
  return Uint8Array.from(source,(_,i)=>source[Math.min(source.length-1,Math.floor(i*fraction+.5))]);
}
function browserFrequencyWarpPosition(x,preset,custom){
  x=Math.max(0,Math.min(1,Number(x)||0));preset=Math.max(0,Math.min(7,Number(preset)||0));
  const piece=anchors=>{for(let i=1;i<anchors.length;i++){if(x<=anchors[i][0]){const [x0,y0]=anchors[i-1],[x1,y1]=anchors[i];let t=(x-x0)/Math.max(.0001,x1-x0);t=t*t*(3-2*t);return Math.max(0,Math.min(1,y0+(y1-y0)*t))}}return 1};
  if(preset===0)return x;if(preset===1){if(x<=.4){const t=x/.4;return .5*t*t*(3-2*t)}if(x<=.55){const t=(x-.4)/.15,t2=t*t,t3=t2*t;return Math.max(0,Math.min(1,(2*t3-3*t2+1)*.5+(-2*t3+3*t2)*.55+(t3-t2)*.15))}const u=(x-.55)/.45;return Math.max(0,Math.min(1,.55+.45*(u+2.25*u*u*u-2.25*u*u)))}
  if(preset===2)return piece([[0,0],[.2,.16],[.4,.36],[.6,.64],[.8,.84],[1,1]]);if(preset===3)return x**1.32;if(preset===4)return x**.78;if(preset===5)return piece([[0,0],[.2,.28],[.4,.43],[.6,.57],[.8,.72],[1,1]]);if(preset===6)return 1-(1-x)**1.38;
  const raw=Array.isArray(custom)?custom:[150,340,590,825];return piece([[0,0],[.2,Number(raw[0]??150)/1000],[.4,Number(raw[1]??340)/1000],[.6,Number(raw[2]??590)/1000],[.8,Number(raw[3]??825)/1000],[1,1]])
}
function browserSpectrumProcess(raw,width,mode,frequencyWarpPreset,frequencyWarpCustom){
  const source=raw instanceof Uint8Array?raw:new Uint8Array(raw||0);if(!source.length||!width)return [];
  mode=Math.max(1,Number(mode)||1);const horizontalPower=mode===1?2.30:2.40;let values=new Array(width);
  for(let column=0;column<width;column++){const f=column/Math.max(1,width-1),p=browserFrequencyWarpPosition(f,frequencyWarpPreset,frequencyWarpCustom);const index=Math.max(0,Math.min(source.length-1,Math.round((p**horizontalPower)*(source.length-1)*.90)));let v=source[index]/64;v=Math.max(0,v*(.30+.70*(((column+1)/width)**.30))-.065);values[column]=v}
  const treatment=Math.floor((mode-1)/25),visualizerType=(mode-1)%25;const radii=[0,1,2,3,0,1,2,0,3,1,0,2,4,0,1],radius=radii[Math.max(0,Math.min(radii.length-1,treatment))]||0;
  if(radius){const original=values;values=original.map((_,i)=>{let total=0,count=0;for(let j=Math.max(0,i-radius);j<Math.min(width,i+radius+1);j++){total+=original[j];count++}return total/Math.max(1,count)})}
  if([1,6,11].includes(treatment))values=values.map(v=>Math.max(0,v-.08));else if([3,8,13].includes(treatment))values=values.map(v=>v**.72);else if([4,9,14].includes(treatment))values=values.map(v=>Math.round(v*8)/8);else if([5,10].includes(treatment))values=values.map((v,i)=>v*(.72+.38*i/Math.max(1,width-1)));
  const gammas=[1,1.28,.78,1.08,.62,1.5,.9,1.15,.7,1.35,.82,1.7,.55,1.02,1.22],gains=[.90,.78,.98,.76,1,.72,.88,.82,1,.74,.96,.68,1,.86,.80],ti=Math.max(0,Math.min(14,treatment)),typeGain=visualizerType===0?1.08:(visualizerType===1?.95:1);
  values=values.map(v=>Math.min(1,(Math.max(0,v)**gammas[ti])*gains[ti]*typeGain));
  const nonzero=values.filter(v=>v>0).sort((a,b)=>a-b);if(!nonzero.length){spectrumAgcGain=Math.max(1,spectrumAgcGain*.92);return values}
  const robust=nonzero[Math.min(nonzero.length-1,Math.max(0,Math.round((nonzero.length-1)*.90)))];if(robust<.025){spectrumAgcGain=Math.max(1,spectrumAgcGain*.94);return values.map(v=>v<.01625?0:v)}
  const desired=Math.min(5,Math.max(1,.90/robust)),smooth=desired<spectrumAgcGain?.55:.30;spectrumAgcGain+= (desired-spectrumAgcGain)*smooth;return values.map(v=>Math.min(1,(v*spectrumAgcGain)**.92));
}

function initSpectrumWorker(){
  if(!window.Worker)return;
 const source=`let gain=2;function go(raw,width,mode,frequencyWarp){const s=new Uint8Array(raw);if(!s.length||!width)return [];const warp=x=>{x=Math.max(0,Math.min(1,x));if(x<=.4){const t=x/.4;return .5*t*t*(3-2*t)}if(x<=.55){const t=(x-.4)/.15,t2=t*t,t3=t2*t;return (2*t3-3*t2+1)*.5+(-2*t3+3*t2)*.55+(t3-t2)*.15}const u=(x-.55)/.45;return Math.max(0,Math.min(1,.55+.45*(u+2.25*u*u*u-2.25*u*u)))};mode=Math.max(1,Number(mode)||1);const hp=mode===1?2.30:2.40;let v=new Array(width);for(let c=0;c<width;c++){const f=c/Math.max(1,width-1),p=frequencyWarp?warp(f):f,i=Math.max(0,Math.min(s.length-1,Math.round((p**hp)*(s.length-1)*.90)));let x=s[i]/64;x=Math.max(0,x*(.30+.70*(((c+1)/width)**.30))-.065);v[c]=x}const t=Math.floor((mode-1)/25),vt=(mode-1)%25,r=[0,1,2,3,0,1,2,0,3,1,0,2,4,0,1][Math.max(0,Math.min(14,t))]||0;if(r){const o=v;v=o.map((_,i)=>{let z=0,n=0;for(let j=Math.max(0,i-r);j<Math.min(width,i+r+1);j++){z+=o[j];n++}return z/Math.max(1,n)})}if([1,6,11].includes(t))v=v.map(x=>Math.max(0,x-.08));else if([3,8,13].includes(t))v=v.map(x=>x**.72);else if([4,9,14].includes(t))v=v.map(x=>Math.round(x*8)/8);else if([5,10].includes(t))v=v.map((x,i)=>x*(.72+.38*i/Math.max(1,width-1)));const gs=[1,1.28,.78,1.08,.62,1.5,.9,1.15,.7,1.35,.82,1.7,.55,1.02,1.22],as=[.90,.78,.98,.76,1,.72,.88,.82,1,.74,.96,.68,1,.86,.80],q=Math.max(0,Math.min(14,t)),tg=vt===0?1.08:(vt===1?.95:1);v=v.map(x=>Math.min(1,(Math.max(0,x)**gs[q])*as[q]*tg));const nz=v.filter(x=>x>0).sort((a,b)=>a-b);if(!nz.length){gain=Math.max(1,gain*.92);return v}const peak=nz[Math.min(nz.length-1,Math.max(0,Math.round((nz.length-1)*.90)))];if(peak<.025){gain=Math.max(1,gain*.94);return v.map(x=>x<.01625?0:x)}const d=Math.min(5,Math.max(1,.90/peak)),sm=d<gain?.55:.30;gain+=(d-gain)*sm;return v.map(x=>Math.min(1,(x*gain)**.92))}onmessage=e=>{const d=e.data||{};postMessage(go(d.raw,d.width,d.mode,d.frequencyWarp))}`;
  try{const url=URL.createObjectURL(new Blob([source],{type:'application/javascript'}));spectrumWorker=new Worker(url);URL.revokeObjectURL(url);spectrumWorker.onmessage=e=>{if(webVisualizerEnabled)spectrumTarget=Array.isArray(e.data)?e.data:[]};}catch(e){spectrumWorker=null}
}
function processRawSpectrumBuffer(buffer){
  buffer=adaptiveFrequencyBins(buffer).buffer;
  const mode=Math.max(1,Number(latestState.visualizer_mode||1)),preset=Number(latestState.frequency_warp_preset??(latestState.frequency_warp_enabled?1:0));
  const custom=Array.isArray(latestState.frequency_warp_custom_permille)?latestState.frequency_warp_custom_permille:[150,340,590,825];
  if(spectrumWorker&&preset<=1){spectrumWorker.postMessage({raw:buffer,width:spectrumOutputBins,mode,frequencyWarp:preset===1},[buffer]);return}
  spectrumTarget=browserSpectrumProcess(new Uint8Array(buffer),spectrumOutputBins,mode,preset,custom);
}

let spectrumTimeline=null,lastTimelineClockAt=-Infinity;
function timelineSpectrumAt(now){
  const t=spectrumTimeline;if(!t||t.source!=='track')return null;
  const age=Math.max(0,now-t.at)/1000;
  if(age>4)return new Uint8Array(0);
  const position=t.position+(t.playing?age*t.speed:0);
  const frame=position*t.fps-t.start_frame,index=Math.floor(frame),count=t.raw.length/t.width;
  if(index<0||index>=count)return new Uint8Array(0);
  const next=Math.min(count-1,index+1),blend=frame-index,result=new Uint8Array(t.width);
  for(let i=0;i<t.width;i++)result[i]=Math.round(t.raw[index*t.width+i]*(1-blend)+t.raw[next*t.width+i]*blend);
  return result;
}
async function timelineTick(){
 try{
  const requested=performance.now(),r=await fetch('/api/timeline',{cache:'no-store'}),t=await r.json(),received=performance.now();
  const serverNow=Number(r.headers.get('X-PAF-Server-Time')||t.clock_epoch||0);
  const transit=Math.min(.25,Math.max(0,serverNow-Number(t.clock_epoch||serverNow))+(received-requested)/2000);
  const raw=Uint8Array.from(atob(t.frames||''),c=>c.charCodeAt(0));
  t.position=Number(t.position||0)+(t.playing?transit*Number(t.speed||0):0);t.at=received;t.raw=raw;
  spectrumTimeline=t;
  if(t.source!=='live'&&t.source!=='stopped'){
   const confirmed=Math.max(0,t.position-Number(t.ui_start||0));
   if(webSeekPending&&Math.abs(confirmed-webSeekPending.position)<=1.25)webSeekPending=null;
   if(!webSeekPending||received-webSeekPending.at>3000){webSeekPending=null;webClockSample={...webClockSample,position:confirmed,lyricPosition:t.position,speed:t.speed,paused:!t.playing,playing:t.playing,at:received,validUntil:received+4000};lastTimelineClockAt=received;}
  }
  if(t.source==='stopped'){spectrumTarget=[];spectrumCurrent=[];webClockSample.playing=false;webLyricTimeline=[];renderWebLyric('');}
 }catch(e){}
 setTimeout(timelineTick,document.hidden?1000:150);
}

function drawSpectrum(now){
  if(!webVisualizerEnabled || spectrumPaused || document.hidden){requestAnimationFrame(drawSpectrum);return;}
  if(now-lastSpectrumAnimationPaint<spectrumDrawMs){requestAnimationFrame(drawSpectrum);return;}
  lastSpectrumAnimationPaint=now;
  const canvas=document.getElementById('visualizer');
  const ctx=canvas.getContext('2d');
  const w=canvas.width,h=canvas.height;
  ctx.clearRect(0,0,w,h);ctx.fillStyle='#030609';ctx.fillRect(0,0,w,h);
  const scheduled=timelineSpectrumAt(now);
  if(scheduled!==null){
    spectrumTarget=browserSpectrumProcess(adaptiveFrequencyBins(scheduled),spectrumOutputBins,Math.max(1,Number(latestState.visualizer_mode||1)),Number(latestState.frequency_warp_preset??(latestState.frequency_warp_enabled?1:0)),Array.isArray(latestState.frequency_warp_custom_permille)?latestState.frequency_warp_custom_permille:[150,340,590,825]);
    spectrumCurrent=spectrumTarget.slice();
  }
  const target=spectrumTarget||[];if(spectrumCurrent.length!==target.length)spectrumCurrent=target.slice();
  for(let i=0;i<target.length;i++)spectrumCurrent[i]=(spectrumCurrent[i]||0)+(Number(target[i]||0)-(spectrumCurrent[i]||0))*.28;
  const n=spectrumCurrent.length;if(n){const gap=Math.max(1,Math.floor(w/600)),bw=Math.max(1,(w-gap*(n-1))/n);for(let i=0;i<n;i++){const v=Math.max(0,Math.min(1,spectrumCurrent[i]||0)),bh=Math.max(1,v*(h-3)),hue=((i/Math.max(1,n-1))*300+(now/40))%360;ctx.fillStyle=`hsl(${hue} 100% 52%)`;ctx.fillRect(i*(bw+gap),h-bh,bw,bh)}}
  requestAnimationFrame(drawSpectrum);
}


function makeMultiOutputDeviceControl(item){
  const wrap=document.createElement('div');wrap.className='control-item';wrap.dataset.controlKey=item.key;wrap.title=item.tooltip||item.label;const label=document.createElement('label');label.textContent=item.label;
  const box=document.createElement('div');box.className='multi-output-wrap';const button=document.createElement('button');button.type='button';button.className='secondary-button multi-output-button';const menu=document.createElement('div');menu.className='multi-output-menu';box.append(button,menu);
  const marks=document.createElement('span');marks.className='choice-marks-stack';const favLabel=document.createElement('label');favLabel.className='choice-mark';favLabel.title='Save/remove this exact output-device combination as a favorite';const fav=document.createElement('input');fav.type='checkbox';favLabel.append(fav,document.createTextNode('Fav'));const defLabel=document.createElement('label');defLabel.className='choice-mark';defLabel.title='Make this exact output-device combination the persistent default';const def=document.createElement('input');def.type='radio';def.name='paf-default-output-devices-mask';defLabel.append(def,document.createTextNode('Def'));marks.append(favLabel,defLabel);const row=document.createElement('div');row.className='select-with-marks';row.append(box,marks);wrap.append(label,row);
  const selected=new Set(),markKey=item.choice_mark_key||'output_devices_mask',favorites=new Set((item.favorite_values||[]).map(Number));let defaultValue=Number(item.default_value??1);
  function decode(mask){selected.clear();const value=Number(mask||1);for(const opt of item.options||[]){const index=Number(opt.value),bit=index<0?1:Math.pow(2,index+1);if((value & bit)!==0)selected.add(index)}if(!selected.size)selected.add(-1)}
  function encode(){let mask=0;for(const index of selected)mask+=index<0?1:Math.pow(2,index+1);return Math.max(1,Math.trunc(mask))}
  function selectionLabel(mask=encode()){const values=new Set();for(const opt of item.options||[]){const index=Number(opt.value),bit=index<0?1:Math.pow(2,index+1);if((Number(mask)&bit)!==0)values.add(index)}return (item.options||[]).filter(o=>values.has(Number(o.value))).map(o=>o.label).join(' + ')||'System default'}
  function sync(){for(const row of menu.querySelectorAll('.multi-output-option'))row.querySelector('input').checked=selected.has(Number(row.dataset.value));const text=selectionLabel();button.textContent=text+' ▾';button.title='Outputs: '+text;fav.checked=favorites.has(encode());def.checked=defaultValue===encode();const latency=document.getElementById('multiOutLatencyButton');if(latency)latency.style.display=selected.size>1?'':'none';syncMirroredPlaybackControls()}
  async function saveMark(kind,value,enabled){const r=await fetch('/api/choice-mark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,key:markKey,value,enabled})});const data=await r.json();if(!r.ok)throw new Error(data.error||'Could not save device choice');return data}
  fav.onchange=async()=>{const value=encode(),wanted=fav.checked;try{const data=await saveMark('favorite',value,wanted);favorites.clear();(data.favorite_values||[]).forEach(v=>favorites.add(Number(v)))}catch(_){fav.checked=!wanted}sync()};
  def.onclick=async event=>{const value=encode();if(defaultValue===value){def.checked=true;return}event.preventDefault();if(!confirm('Are you sure you want “'+selectionLabel(value)+'” to be the default playback device selection?')){sync();setTimeout(sync,0);return}try{const data=await saveMark('default',value,true);defaultValue=Number(data.default_value)}catch(error){alert('Could not save the default playback device: '+String(error))}finally{sync();setTimeout(sync,0)}};
  for(const opt of item.options||[]){const row=document.createElement('label');row.className='multi-output-option';row.dataset.value=String(opt.value);const cb=document.createElement('input');cb.type='checkbox';row.append(cb,document.createTextNode(opt.label));cb.onchange=()=>{const v=Number(opt.value);if(cb.checked)selected.add(v);else selected.delete(v);if(!selected.size)selected.add(-1);sync();action('web-set:output_devices_mask:'+encode())};menu.appendChild(row)}
  button.onclick=e=>{e.preventDefault();box.classList.toggle('open')};document.addEventListener('pointerdown',e=>{if(!box.contains(e.target))box.classList.remove('open')});
  wrap._setMultiOutputMask=mask=>{decode(mask);sync()};decode(1);sync();return wrap;
}
let multiOutMicTimer=null,multiOutMicMonitoring=false;
function multiOutStatus(text,error=false){const host=document.getElementById('multiOutLatencyStatus');if(host){host.textContent=text||'';host.style.color=error?'#ff9b9b':'#a7e4be'}}
async function multiOutGet(path){const r=await fetch(path,{cache:'no-store'});const d=await r.json();if(!r.ok)throw new Error(d.error||'request failed');return d}
async function multiOutPost(path,payload){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload||{})});const d=await r.json();if(!r.ok)throw new Error(d.error||'request failed');return d}
function currentMultiOutLatencies(){const values={};document.querySelectorAll('#multiOutLatencyRows .multiout-row').forEach(row=>{values[row.dataset.index]=Number(row.querySelector('input[type=number]').value||0)});return values}
function renderMultiOutRows(data){const host=document.getElementById('multiOutLatencyRows');host.textContent='';for(const device of data.devices||[]){const row=document.createElement('div');row.className='multiout-row';row.dataset.index=String(device.index);const label=document.createElement('div');label.className='multiout-label';label.textContent=device.label;label.title=device.label;const range=document.createElement('input');range.type='range';range.min=String(data.min_ms??-2000);range.max=String(data.max_ms??2000);range.step='1';range.value=String(device.latency_ms||0);const number=document.createElement('input');number.type='number';number.min=range.min;number.max=range.max;number.step='1';number.value=range.value;number.title='Exact latency correction in milliseconds';const effective=document.createElement('div');effective.className='multiout-effective';effective.textContent='Effective realizable delay: '+Number(device.effective_delay_ms||0)+' ms';range.oninput=()=>{number.value=range.value};number.oninput=()=>{let v=Math.max(Number(number.min),Math.min(Number(number.max),Number(number.value||0)));range.value=String(v)};range.onchange=()=>applyMultiOutLatency(false);number.onchange=()=>applyMultiOutLatency(false);row.append(label,range,number,effective);host.appendChild(row)}}
async function refreshMultiOutLatency(){const data=await multiOutGet('/api/multi-output-latency');renderMultiOutRows(data);return data}
async function applyMultiOutLatency(showMessage=true){try{const d=await multiOutPost('/api/multi-output-latency',{latencies:currentMultiOutLatencies()});renderMultiOutRows(d);if(showMessage)multiOutStatus(d.restart_queued?'Saved; audio restart queued so the new alignment is live.':'Saved latency calibration.')}catch(e){multiOutStatus(String(e),true)}}
async function loadMultiOutMicrophones(){const host=document.getElementById('multiOutMicrophones');host.textContent='Loading microphones…';try{const d=await multiOutGet('/api/multi-output-microphones');host.textContent='';for(const mic of d.microphones||[]){const row=document.createElement('label');row.className='multiout-mic-row';row.dataset.index=String(mic.index);const cb=document.createElement('input');cb.type='checkbox';cb.checked=!!mic.default;const name=document.createElement('span');name.textContent=(mic.default?'★ ':'')+mic.label;const meter=document.createElement('div');meter.className='multiout-meter';meter.innerHTML='<span></span>';row.append(cb,name,meter);host.appendChild(row)}if(!host.children.length)host.textContent='No usable WASAPI microphones found.'}catch(e){host.textContent=String(e)}}
function selectedMultiOutMics(){return [...document.querySelectorAll('#multiOutMicrophones .multiout-mic-row input:checked')].map(cb=>Number(cb.closest('.multiout-mic-row').dataset.index))}
async function pollMultiOutMicLevels(){if(!multiOutMicMonitoring)return;try{const d=await multiOutGet('/api/multi-output-mic-levels');for(const row of document.querySelectorAll('#multiOutMicrophones .multiout-mic-row')){const value=Number((d.levels||{})[row.dataset.index]||0);row.querySelector('.multiout-meter>span').style.width=Math.round(Math.max(0,Math.min(1,value))*100)+'%'}}catch(e){}multiOutMicTimer=setTimeout(pollMultiOutMicLevels,140)}
async function toggleMultiOutMicMonitor(forceStop=false){const button=document.getElementById('multiOutMicMonitor');if(multiOutMicMonitoring||forceStop){await multiOutPost('/api/multi-output-mic-monitor',{op:'stop'}).catch(()=>{});multiOutMicMonitoring=false;clearTimeout(multiOutMicTimer);button.textContent='Start microphone test';if(forceStop)return}if(!forceStop){const indexes=selectedMultiOutMics();if(!indexes.length){multiOutStatus('Select at least one microphone.',true);return}try{await multiOutPost('/api/multi-output-mic-monitor',{op:'start',indexes});multiOutMicMonitoring=true;button.textContent='Stop microphone test';pollMultiOutMicLevels()}catch(e){multiOutStatus(String(e),true)}}}
async function openMultiOutLatency(){document.getElementById('multiOutLatencyModal').classList.add('open');multiOutStatus('');try{await refreshMultiOutLatency()}catch(e){multiOutStatus(String(e),true)}}
async function closeMultiOutLatency(){await toggleMultiOutMicMonitor(true);document.getElementById('multiOutLatencyModal').classList.remove('open')}
async function runMultiOutAutoSync(){const indexes=selectedMultiOutMics();if(!indexes.length){multiOutStatus('Select at least one microphone.',true);return}await toggleMultiOutMicMonitor(true);multiOutStatus('Listening… sending distinct synchronized test tones to each output.');const button=document.getElementById('multiOutRunAutoSync');button.disabled=true;try{const d=await multiOutPost('/api/multi-output-auto-sync',{microphone_indexes:indexes});await refreshMultiOutLatency();multiOutStatus('Auto sync complete. Relative output latency was measured and corrected.')}catch(e){multiOutStatus(String(e),true)}finally{button.disabled=false}}
function setupMultiOutLatencyUI(){document.getElementById('multiOutLatencyCloseX').onclick=closeMultiOutLatency;document.getElementById('multiOutLatencyApply').onclick=()=>applyMultiOutLatency(true);document.getElementById('multiOutLatencyZero').onclick=()=>{document.querySelectorAll('#multiOutLatencyRows input[type=number],#multiOutLatencyRows input[type=range]').forEach(el=>el.value='0');applyMultiOutLatency(true)};document.getElementById('multiOutAutoSyncToggle').onclick=async()=>{const panel=document.getElementById('multiOutAutoSync');panel.classList.toggle('open');if(panel.classList.contains('open')&&!document.getElementById('multiOutMicrophones').children.length)await loadMultiOutMicrophones();else if(!panel.classList.contains('open'))await toggleMultiOutMicMonitor(true)};document.getElementById('multiOutMicMonitor').onclick=()=>toggleMultiOutMicMonitor(false);document.getElementById('multiOutRunAutoSync').onclick=runMultiOutAutoSync;document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.getElementById('multiOutLatencyModal').classList.contains('open')){e.preventDefault();closeMultiOutLatency()}})}

function makeSelect(item){
  const wrap=document.createElement('div');wrap.dataset.controlKey=item.key;wrap.className='control-item'+(item.experimental?' experimental':'')+(item.theme?' control-theme-'+item.theme:'');wrap.title=item.tooltip||item.label;
  const label=document.createElement('label');label.textContent=item.label;label.title=item.tooltip||item.label;
  const row=document.createElement('div');row.className='select-with-marks';
  const select=document.createElement('select');select.id='ctl-'+item.key;select.dataset.key=item.key;select.title=item.tooltip||item.label;
  const favoriteValues=new Set((item.favorite_values||[]).map(v=>String(v)));
  item.options.forEach(opt=>{const option=document.createElement('option');option.value=String(opt.value);option.dataset.rawLabel=opt.label;select.appendChild(option)});
  row.appendChild(select);let fav=null,def=null;
  function decorateOptions(){
    const options=[...select.options];
    options.forEach(option=>{const raw=option.dataset.rawLabel||option.textContent||'';const isFav=favoriteValues.has(String(option.value));const isDef=String(item.default_value??'')===String(option.value);option.textContent=(isFav?'⭐ ':'')+(isDef?'✨ ':'')+raw;option.style.fontWeight=isDef?'800':'400';option.classList.toggle('default-option',isDef)});
    // Preserve stored IDs while presenting the default first, then favorites in
    // their saved order, followed by all remaining choices in schema order.
    const byValue=new Map(options.map(option=>[String(option.value),option]));const ordered=[];
    const add=value=>{const option=byValue.get(String(value));if(option&&!ordered.includes(option))ordered.push(option)};
    add(item.default_value);for(const value of item.favorite_values||[])add(value);for(const option of options)add(option.value);
    ordered.forEach(option=>select.appendChild(option));
  }
  function syncMarks(){if(fav)fav.checked=favoriteValues.has(String(select.value));if(def)def.checked=String(item.default_value??'')===String(select.value);decorateOptions()}
  async function saveMark(kind,value,enabled){const r=await fetch('/api/choice-mark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,key:item.key,value:Number(value),enabled})});if(!r.ok)throw new Error('save failed');return await r.json()}
  select.onchange=()=>{action('web-set:'+item.key+':'+select.value);syncMarks()};
  if(item.choice_marks){
    const favLabel=document.createElement('label');favLabel.className='choice-mark';favLabel.title='Save/remove the selected choice as a favorite';fav=document.createElement('input');fav.type='checkbox';const favText=document.createElement('span');favText.textContent='Fav';
    fav.onchange=async()=>{const value=String(select.value),wanted=fav.checked;try{const data=await saveMark('favorite',value,wanted);favoriteValues.clear();(data.favorite_values||[]).forEach(v=>favoriteValues.add(String(v)));syncMarks()}catch(e){fav.checked=!wanted;syncMarks()}};favLabel.append(fav,favText);
    const defLabel=document.createElement('label');defLabel.className='choice-mark';defLabel.title='Make the selected choice the persistent default';def=document.createElement('input');def.type='radio';def.name='default-'+item.key;const defText=document.createElement('span');defText.textContent='Def';
    def.onclick=async event=>{const value=String(select.value);if(String(item.default_value??'')===value){def.checked=true;return}event.preventDefault();const raw=select.options[select.selectedIndex]?.dataset.rawLabel||value;if(!confirm('Are you sure you want “'+raw+'” to be the default for '+item.label+'?')){syncMarks();return}try{const data=await saveMark('default',value,true);item.default_value=Number(data.default_value);syncMarks()}catch(e){syncMarks()}};defLabel.append(def,defText);
    const marksStack=document.createElement('div');marksStack.className='choice-marks-stack';marksStack.append(favLabel,defLabel);row.appendChild(marksStack);
  }
  select._pafReplaceFavoriteValues=values=>{favoriteValues.clear();for(const value of values||[])favoriteValues.add(String(value));item.favorite_values=[...(values||[])];};select._pafSyncMarks=syncMarks;wrap.append(label,row);syncMarks();return wrap;
}

function setupMicrotileModeControl(selectId,toolsId,key,channel){
  const select=document.getElementById(selectId),tools=document.getElementById(toolsId);if(!select||!tools)return;
  const item=(controlSchema.selects||[]).find(x=>x.key===key);if(!item)return;
  const favorites=new Set((item.favorite_values||[]).map(v=>String(v)));
  select.textContent='';
  const optionGroups=new Map();
  for(const opt of item.options||[]){let host=select;const group=String(opt.group||'');if(group){if(!optionGroups.has(group)){const og=document.createElement('optgroup');og.label=group;optionGroups.set(group,og);select.appendChild(og)}host=optionGroups.get(group)}const option=document.createElement('option');option.value=String(opt.value);option.dataset.rawLabel=String(opt.label);option.textContent=String(opt.label);host.appendChild(option)}
  const favLabel=document.createElement('label');favLabel.className='choice-mark';favLabel.title='Save/remove the selected artwork-detail mode as a favorite';
  const fav=document.createElement('input');fav.type='checkbox';const favText=document.createElement('span');favText.textContent='Fav';favLabel.append(fav,favText);
  const defLabel=document.createElement('label');defLabel.className='choice-mark';defLabel.title='Make the selected artwork-detail mode the persistent default';
  const def=document.createElement('input');def.type='radio';def.name='default-'+key;const defText=document.createElement('span');defText.textContent='Def';defLabel.append(def,defText);
  const marks=document.createElement('div');marks.className='choice-marks-stack';marks.append(favLabel,defLabel);
  const cycle=document.createElement('button');cycle.type='button';cycle.className='secondary-button favorite-cycle-button';cycle.textContent='♻️';
  tools.replaceChildren(marks,cycle);
  function rawLabelFor(value){const option=[...select.options].find(o=>String(o.value)===String(value));return option?(option.dataset.rawLabel||option.textContent||String(value)):String(value)}
  function defaultLabel(){return rawLabelFor(item.default_value)}
  function updateCycleTip(){const tip='Click to cycle saved favorite '+channel+' artwork-detail modes. Right-click to cycle all modes sequentially. Double-click to restore the default mode of '+defaultLabel();cycle.dataset.tip=tip;cycle.setAttribute('aria-label',tip)}
  function decorate(){for(const option of select.options){const raw=option.dataset.rawLabel||option.textContent||'';const isFav=favorites.has(String(option.value)),isDef=String(item.default_value??'')===String(option.value);option.textContent=(isFav?'⭐ ':'')+(isDef?'✨ ':'')+raw;option.style.fontWeight=isDef?'800':'400'}updateCycleTip()}
  function sync(){fav.checked=favorites.has(String(select.value));def.checked=String(item.default_value??'')===String(select.value);decorate()}
  async function saveMark(kind,value,enabled){const r=await fetch('/api/choice-mark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,key,value:Number(value),enabled})});if(!r.ok)throw new Error('save failed');return await r.json()}
  function commit(value){select.value=String(value);action('web-set:'+key+':'+select.value);sync()}
  select.onchange=()=>{action('web-set:'+key+':'+select.value);sync()};
  fav.onchange=async()=>{const value=String(select.value),wanted=fav.checked;try{const data=await saveMark('favorite',value,wanted);favorites.clear();(data.favorite_values||[]).forEach(v=>favorites.add(String(v)));sync()}catch(e){fav.checked=!wanted;sync()}};
  def.onclick=async event=>{const value=String(select.value);if(String(item.default_value??'')===value){def.checked=true;return}event.preventDefault();const raw=rawLabelFor(value);if(!confirm('Are you sure you want “'+raw+'” to be the default for '+channel+' artwork detail?')){sync();return}try{const data=await saveMark('default',value,true);item.default_value=Number(data.default_value);sync()}catch(e){sync()}};
  function cycleValues(steps,favoritesOnly){const ordered=[...select.options].map(o=>String(o.value)).filter(v=>!favoritesOnly||favorites.has(v));if(!ordered.length)return;const delta=Number(steps)||1,direction=delta<0?-1:1,count=Math.max(1,Math.abs(Math.trunc(delta)));let index=ordered.indexOf(String(select.value));if(index<0)index=direction>0?-1:0;for(let i=0;i<count;i++)index=(index+direction+ordered.length)%ordered.length;commit(ordered[index])}
  function restoreDefault(){if(item.default_value===undefined||item.default_value===null)return;commit(item.default_value)}
  let clickCount=0,clickTimer=null;
  cycle.addEventListener('click',event=>{event.preventDefault();clickCount++;if(clickCount>=2){clearTimeout(clickTimer);clickTimer=null;clickCount=0;restoreDefault();return}clearTimeout(clickTimer);clickTimer=setTimeout(()=>{clickCount=0;cycleValues(1,true)},260)});
  cycle.addEventListener('contextmenu',event=>{event.preventDefault();clearTimeout(clickTimer);clickTimer=null;clickCount=0;cycleValues(1,false)});
  select._pafSyncMarks=sync;cycle._pafRestoreDefault=restoreDefault;sync();
}

function sliderDisplayLabel(item,value){
  if(item.key==='locked_bass_reduction_percent')return 'Reduce bass by '+Number(value)+'% while locked';
  if(item.key==='bass_boost_percent'){const amount=Number(value);return amount<0?'Reduce bass by '+Math.abs(amount)+'%':amount>0?'Boost bass by '+amount+'%':'No bass change (0%)'}
  if(item.value_in_textbox)return item.label;
  if(item.key==='visualizer_rows')return 'Visualizer Rows\n('+value+' rows)';
  if(item.key==='floating_track_intro_seconds')return 'Display song title for first '+Number(value)+' seconds';
  if(item.key==='balance')return Number(value)===0?'Balance: Center':'Balance: '+Math.abs(Number(value))+'% '+(Number(value)<0?'Left':'Right');
  return item.label+' '+value+(item.suffix||'');
}
function makeSlider(item){
  const wrap=document.createElement('div');wrap.dataset.controlKey=item.key;wrap.className='control-item'+(item.experimental?' experimental':'')+(item.theme?' control-theme-'+item.theme:'');wrap.title=item.tooltip||item.label;
  const label=document.createElement('label');label.id='lbl-'+item.key;label.textContent=item.label;label.title=item.tooltip||item.label;
  if(item.text_only){
    const entry=document.createElement('input');entry.type='number';entry.id='ctl-'+item.key;entry.dataset.key=item.key;entry.min=item.min;entry.max=item.max;entry.step=item.step;entry.value=String(item.default??60);entry.style.width='100px';entry.setAttribute('aria-label',item.label+' (FPS)');
    entry.onchange=()=>{const n=Number(entry.value);if(entry.value.trim()===''||!Number.isInteger(n)||n<Number(item.min)||n>Number(item.max)){entry.setCustomValidity('Enter a whole number from '+item.min+' to '+item.max+' FPS.');entry.reportValidity();entry.setCustomValidity('');entry.value=entry.dataset.lastValid||String(item.default??60);return}entry.dataset.lastValid=String(n);action('web-set:'+item.key+':'+n)};
    const unit=document.createElement('span');unit.className='slider-unit';unit.textContent='FPS';wrap.append(label,entry,unit);return wrap;
  }
  const input=document.createElement('input');input.type='range';input.id='ctl-'+item.key;input.dataset.key=item.key;
  input.min=item.min;input.max=item.max;input.step=item.step;input.title=item.tooltip||item.label;
  let timer=null,number=null;
  const numericScale=Number(item.numeric_scale||1);
  const numericValue=raw=>String(Math.round(Number(raw)/numericScale*1000)/1000);
  const commit=(snapZero=false)=>{
    if(snapZero&&Number(item.snap_zero)>0&&Math.abs(Number(input.value))<=Number(item.snap_zero))input.value='0';
    if(number&&document.activeElement!==number)number.value=numericValue(input.value);
    label.textContent=sliderDisplayLabel(item,input.value);
    clearTimeout(timer);timer=setTimeout(()=>action('web-set:'+item.key+':'+input.value),80);
  };
  input.oninput=()=>commit(true);
  wrap.append(label,input);
  if(item.numeric){number=document.createElement('input');number.type='number';number.id='num-'+item.key;number.min=Number(item.min)/numericScale;number.max=Number(item.max)/numericScale;number.step=item.numeric_step??Number(item.step)/numericScale;number.style.width='100px';number.setAttribute('aria-label',item.label+' numeric value in '+(numericScale===1000?'seconds':'units'));
   number.onchange=()=>{const n=Number(number.value);if(number.value.trim()===''||!Number.isFinite(n)){number.value=numericValue(input.value);return}const step=Number(item.numeric_step??Number(item.step)/numericScale)*numericScale||1;const snapped=Math.round(n*numericScale/step)*step;input.value=String(Math.max(item.min,Math.min(item.max,snapped)));number.value=numericValue(input.value);commit(false)};wrap.appendChild(number);
   if(item.numeric_suffix){const unit=document.createElement('span');unit.className='slider-unit';unit.textContent=item.numeric_suffix;wrap.appendChild(unit)}}return wrap;
}

function confirmSixelEnable(confirmDialog=confirm){
  return confirmDialog('Enable experimental SIXEL visualizer? Some terminal and font sizes may cause display problems.') &&
         confirmDialog('Confirm again: enable SIXEL now? If the console display breaks, restart with --no-sixel-visualizer or turn this checkbox off.');
}
function makeToggle(item){
  const wrap=document.createElement('label');wrap.dataset.controlKey=item.key;wrap.className='toggle'+(item.experimental?' experimental':'')+(item.theme?' control-theme-'+item.theme:'');wrap.title=item.tooltip||item.label;
  const input=document.createElement('input');input.type='checkbox';input.id='ctl-'+item.key;input.dataset.key=item.key;if(item.default!==undefined)input.checked=!!item.default;
   input.onchange=()=>{if(item.key==='sixel_enabled'&&input.checked&&!confirmSixelEnable()){input.checked=false;return}const desired=item.invert?!input.checked:input.checked;item.web_key?action('web-set:'+item.web_key+':'+(desired?'1':'0')):action(item.action)};
  const text=document.createElement('span');text.textContent=item.label;
  wrap.append(input,text);return wrap;
}

function setControlApplicability(key,enabled){
  const wrap=document.querySelector('[data-control-key="'+key+'"]');if(!wrap)return;
  wrap.classList.toggle('control-inapplicable',!enabled);
  for(const el of wrap.querySelectorAll('input,select,button'))el.disabled=!enabled;
}
function updateLayerSwitchText(id,enabled){const el=document.getElementById(id);if(el)el.textContent=enabled?'ON':'OFF'}
function applyVisualizerLayerEnablement(){
  const section=document.getElementById('visualizerSection'),master=document.getElementById('visualizerMasterToggle');
  const bars=document.getElementById('ctl-visualizer_bars_enabled'),barArtwork=document.getElementById('ctl-art_color_bars'),background=document.getElementById('ctl-visualizer_background_artwork_enabled');
  if(!section||!bars||!barArtwork||!background)return;
  const masterOn=!master||!!master.checked,barsOn=masterOn&&!!bars.checked,barArtworkOn=barsOn&&!!barArtwork.checked,backgroundOn=masterOn&&!!background.checked,anyLayer=barsOn||backgroundOn;
  updateLayerSwitchText('visualizerBarsState',!!bars.checked);updateLayerSwitchText('visualizerBarArtworkState',!!barArtwork.checked);updateLayerSwitchText('visualizerBackgroundArtworkState',!!background.checked);
  const barArtworkCard=document.querySelector('[data-control-key="art_color_bars"]');barArtwork.disabled=!barsOn;if(barArtworkCard)barArtworkCard.classList.toggle('control-inapplicable',!barsOn);
  const barKeys=['visualizer_type','visualizer_treatment','color_style','processing_style','persistence_mode','fade_style','color_reverse','frequency_warp_preset'];
  const barArtworkKeys=['art_color_bar_strength','art_color_bar_blend_mode','art_color_bar_opacity','drcs_art_bar_microtile_mode'];
  const backgroundKeys=['art_color_black_strength','drcs_art_microtile_mode'];
  const commonKeys=['visualizer_granularity','visualizer_rows','truncate_visualizer_rows'];
  for(const key of barKeys)setControlApplicability(key,barsOn);
  for(const key of barArtworkKeys)setControlApplicability(key,barArtworkOn);
  for(const key of backgroundKeys)setControlApplicability(key,backgroundOn);
  for(const key of commonKeys)setControlApplicability(key,anyLayer);
  const granularity=document.getElementById('ctl-visualizer_granularity');
  const forcedUnicode=section.dataset.unicodeHalfcellForced==='true';
  const detailSupported=!!granularity&&Number(granularity.value)===3&&!forcedUnicode;
  const detailReason=forcedUnicode?'Unavailable while the forced Unicode renderer is active.':'Requires Granularity: 2× Twin DRCS.';
  for(const [key,reasonId,layerOn] of [['drcs_art_bar_microtile_mode','microtileBarsReason',barArtworkOn],['drcs_art_microtile_mode','microtileBlacknessReason',backgroundOn]]){
    setControlApplicability(key,layerOn&&detailSupported);
    const reason=document.getElementById(reasonId);if(reason){reason.hidden=detailSupported;reason.textContent=detailSupported?'':detailReason;}
  }
}
function applyConsoleAlertsEnablement(){
  const master=document.getElementById('ctl-console_alerts_enabled'),section=document.getElementById('consoleAlertsSection'),host=document.getElementById('consoleAlertsControls');if(!master||!section||!host)return;
  const enabled=!!master.checked;section.classList.toggle('section-disabled',!enabled);for(const el of host.querySelectorAll('input,select,button'))el.disabled=!enabled;
}

function syncBassReductionControlState(){
  const toggle=document.getElementById('ctl-reduce_bass_when_locked');
  const slider=document.querySelector('[data-control-key="locked_bass_reduction_percent"]');
  if(!toggle||!slider)return;
  const enabled=!!toggle.checked;
  slider.classList.toggle('control-inapplicable',!enabled);
  slider.querySelectorAll('input').forEach(el=>el.disabled=!enabled);
  slider.title=enabled?'Amount of bass reduction applied while Windows is locked.':'Enable Bass Reduction while Locked to adjust this amount.';
}
document.addEventListener('change',e=>{if(e.target&&e.target.id==='ctl-reduce_bass_when_locked')syncBassReductionControlState()});
function syncControls(s){
  if(!controlSchema) return;
  const artworkDetailSection=document.getElementById('visualizerSection');
  if(artworkDetailSection&&s.visualizer_unicode_halfcell_forced!==undefined)artworkDetailSection.dataset.unicodeHalfcellForced=String(!!s.visualizer_unicode_halfcell_forced);
  for(const item of controlSchema.selects||[]){
    const el=document.getElementById('ctl-'+item.key);
    let value=s[item.key];
    if(value===undefined && s.visualizer_mode!==undefined){
      const mode=Math.max(1,Number(s.visualizer_mode))-1;
      if(item.key==='visualizer_type') value=(mode%25)+1;
      if(item.key==='visualizer_treatment') value=Math.floor(mode/25)+1;
    }
    if(el && value!==undefined){const wanted=String(value);if(el.value!==wanted){el.value=wanted;if(typeof el._pafSyncMarks==='function')el._pafSyncMarks();if(typeof el._pafChoiceButtonSync==='function')el._pafChoiceButtonSync();}}
  }
  for(const item of controlSchema.sliders||[]){
    const el=document.getElementById('ctl-'+item.key);
    const label=document.getElementById('lbl-'+item.key);
    if(el && s[item.key]!==undefined){const wanted=String(Math.max(Number(item.min),Math.min(Number(item.max),Number(s[item.key]))));if(el.value!==wanted&&(!item.text_only||document.activeElement!==el))el.value=wanted;if(item.text_only)el.dataset.lastValid=wanted;const number=document.getElementById('num-'+item.key);if(number&&document.activeElement!==number)number.value=String(Math.round(Number(wanted)/Number(item.numeric_scale||1)*1000)/1000);const wantedLabel=sliderDisplayLabel(item,wanted);if(label && label.textContent!==wantedLabel)label.textContent=wantedLabel}
  }
  for(const item of controlSchema.toggles||[]){
    const el=document.getElementById('ctl-'+item.key);if(el && s[item.key]!==undefined){const wanted=item.invert?!s[item.key]:!!s[item.key];if(el.checked!==wanted)el.checked=wanted;}
  }
  syncBassReductionControlState();
  for(const key of ['art_color_bars','art_color_blackness']){const mirror=document.getElementById('art-saturation-enabled-'+key);if(mirror&&s[key]!==undefined&&typeof mirror._pafSyncFromServer==='function')mirror._pafSyncFromServer(s[key]);}
  const microtileBarsMode=document.getElementById('microtileBarsMode'),microtileBlacknessMode=document.getElementById('microtileBlacknessMode');
  if(microtileBarsMode){const v=(s.drcs_art_bar_microtile_mode!==undefined)?s.drcs_art_bar_microtile_mode:(s.drcs_art_bar_microtiles?1:0);microtileBarsMode.value=String(v);if(typeof microtileBarsMode._pafSyncMarks==='function')microtileBarsMode._pafSyncMarks();}
  if(microtileBlacknessMode){const v=(s.drcs_art_microtile_mode!==undefined)?s.drcs_art_microtile_mode:(s.drcs_art_microtiles?1:0);microtileBlacknessMode.value=String(v);if(typeof microtileBlacknessMode._pafSyncMarks==='function')microtileBlacknessMode._pafSyncMarks();}
  const visualizerMaster=document.getElementById('visualizerMasterToggle');
  const visualizerSection=document.getElementById('visualizerSection');
  if(visualizerMaster && s.drcs_enabled!==undefined) visualizerMaster.checked=!!s.drcs_enabled;
  if(visualizerSection && s.drcs_enabled!==undefined) visualizerSection.classList.toggle('visualizer-disabled',!s.drcs_enabled);
  applyVisualizerLayerEnablement();
  applyConsoleAlertsEnablement();
  if(typeof progressDemoActive!=='undefined'&&progressDemoActive)setTimeout(()=>{for(const el of document.querySelectorAll('#progressControls input:not(#progressDemoToggle),#progressControls select,#progressControls button:not(#progressDemoToggle),#progressMasterToggle'))el.disabled=true},0);
  const karaokeMaster=document.getElementById('karaokeMasterToggle'), karaokeSection=document.getElementById('karaokeSection');
  if(karaokeMaster && s.console_karaoke_enabled!==undefined) karaokeMaster.checked=!!s.console_karaoke_enabled;
  if(karaokeSection && s.console_karaoke_enabled!==undefined) karaokeSection.classList.toggle('section-disabled',!s.console_karaoke_enabled);
  const popupMaster=document.getElementById('artworkPopupMasterToggle'),popupKaraoke=document.getElementById('artworkPopupKaraokeToggle'),popupConfig=document.getElementById('artworkPopupConfigButton'),popupBringTop=document.getElementById('artworkPopupBringTopButton'),popupTopmost=document.getElementById('artworkPopupTopmostButton'),popupEmojiMaxx=document.getElementById('artworkPopupEmojiMaxxButton'),popupEmojiMaxxConfig=document.getElementById('artworkPopupEmojiMaxxConfigButton'),popupDecensor=document.getElementById('artworkPopupDecensorButton'),popupCenter=document.getElementById('artworkPopupBringCenterButton');
  if(popupMaster && s.external_album_art_enabled!==undefined) popupMaster.checked=!!s.external_album_art_enabled;
  const lyricMode=Number(s.lyrics_mode??0), artworkKaraoke=s.artwork_karaoke_enabled!==undefined ? !!s.artwork_karaoke_enabled : (lyricMode===0||lyricMode===2);
  if(popupKaraoke) { popupKaraoke.checked=artworkKaraoke; popupKaraoke.disabled=!!(popupMaster&&!popupMaster.checked); }
  const popupDisabled=!!(popupMaster&&!popupMaster.checked),popupKaraokeDisabled=popupDisabled||!artworkKaraoke;
  if(popupConfig) popupConfig.disabled=popupKaraokeDisabled;
  if(popupTopmost){popupTopmost.checked=!!s.art_topmost;popupTopmost.disabled=popupDisabled;}
  if(popupEmojiMaxx){popupEmojiMaxx.checked=s.popup_emojimax_enabled!==undefined?!!s.popup_emojimax_enabled:true;popupEmojiMaxx.disabled=popupKaraokeDisabled;}
  if(popupEmojiMaxxConfig)popupEmojiMaxxConfig.disabled=popupKaraokeDisabled;
  if(popupDecensor){popupDecensor.checked=!!s.decensor_artwork_lyrics;popupDecensor.disabled=popupKaraokeDisabled;}
  if(popupBringTop){popupBringTop.disabled=popupDisabled;popupBringTop.classList.toggle('topmost-active-foreground',!!s.art_topmost&&!popupDisabled);popupBringTop.title=!!s.art_topmost?'Always On Top is enabled; Bring to Top remains available.':'Bring the artwork pop-up to the top without changing its saved always-on-top setting'}if(popupCenter)popupCenter.disabled=popupDisabled;
  syncDesktopSolutionControls('artwork',s,popupKaraokeDisabled);
  const floatingMaster=document.getElementById('floatingLyricsMasterToggle'),floatingConfig=document.getElementById('floatingLyricsConfigButton'),floatingBringTop=document.getElementById('floatingLyricsBringTopButton'),floatingTopmost=document.getElementById('floatingLyricsTopmostButton'),floatingEmojiMaxx=document.getElementById('floatingLyricsEmojiMaxxButton'),floatingEmojiMaxxConfig=document.getElementById('floatingLyricsEmojiMaxxConfigButton'),floatingDecensor=document.getElementById('floatingLyricsDecensorButton'),floatingCenter=document.getElementById('floatingLyricsBringCenterButton');
  if(floatingMaster && s.floating_lyrics_enabled!==undefined) floatingMaster.checked=!!s.floating_lyrics_enabled;
  const floatingDisabled=!!(floatingMaster&&!floatingMaster.checked);
  if(floatingTopmost){floatingTopmost.checked=!!s.floating_topmost;floatingTopmost.disabled=floatingDisabled;}
  const floatingOpacity=document.getElementById('floatingLyricsOpacity'),floatingOpacityValue=document.getElementById('floatingLyricsOpacityValue');
  if(floatingOpacity){if(document.activeElement!==floatingOpacity&&s.floating_opacity!==undefined)floatingOpacity.value=s.floating_opacity;floatingOpacity.disabled=floatingDisabled;if(floatingOpacityValue)floatingOpacityValue.textContent=floatingOpacity.value+'%';}
  if(floatingEmojiMaxx){floatingEmojiMaxx.checked=s.popup_emojimax_enabled!==undefined?!!s.popup_emojimax_enabled:true;floatingEmojiMaxx.disabled=floatingDisabled;}
  if(floatingEmojiMaxxConfig)floatingEmojiMaxxConfig.disabled=floatingDisabled;
  if(floatingDecensor){floatingDecensor.checked=!!s.decensor_floating_lyrics;floatingDecensor.disabled=floatingDisabled;}
  if(floatingConfig) floatingConfig.disabled=floatingDisabled;
  if(floatingBringTop){floatingBringTop.disabled=floatingDisabled;floatingBringTop.classList.toggle('topmost-active-foreground',!!s.floating_topmost&&!floatingDisabled);floatingBringTop.title=!!s.floating_topmost?'Always On Top is enabled; Bring to Top remains available.':'Bring the floating lyrics window to the top without changing its saved always-on-top setting'}if(floatingCenter)floatingCenter.disabled=floatingDisabled;
  syncDesktopSolutionControls('floating',s,floatingDisabled);
  const progressMaster=document.getElementById('progressMasterToggle'), progressSection=document.getElementById('progressSection');
  if(progressMaster && s.progress_bar_enabled!==undefined) progressMaster.checked=!!s.progress_bar_enabled;
  if(progressSection && s.progress_bar_enabled!==undefined) progressSection.classList.toggle('section-disabled',!s.progress_bar_enabled);
  const reactiveOn=!!s.progress_beat_reactive;
  for(const key of ['progress_beat_detector','progress_beat_treatment','progress_beat_overlay_mode']){const el=document.getElementById('ctl-'+key),wrap=document.querySelector('[data-control-key="'+key+'"]');if(el)el.disabled=!reactiveOn;if(wrap)wrap.classList.toggle('control-inapplicable',!reactiveOn)}
   const repeatNames=['Repeat track','Repeat current folder','Playlist','Repeat OFF'];
  const shuffleNames=['Sequential','Shuffle by history','Shuffle randomly','Repeat Folder','Playlist','Repeat OFF'];
  const repeatDescriptions=['playback repeats the current file','playback continues through the folder and repeats it','playback continues through the playlist and repeats it','playback stops after the end of the file'];
  const shuffleDescriptions=['playback follows the playlist order','shuffle based on listening history, preferring music we haven’t heard in awhile','shuffle completely randomly','playback continues through the folder and repeats it','playback continues through the playlist and repeats it','playback stops after the end of the playlist'];
  const repeatIndex=Math.max(0,Math.min(repeatNames.length-1,Number(s.repeat_mode??(s.loop?0:3))));
  const shuffleIndex=Math.max(0,Math.min(shuffleNames.length-1,Number(s.shuffle_mode??(s.shuffle?1:0))));
  const orderTip=(label,index,names,descriptions,nextAction,prevAction,doubleAction)=>label+'.\n\nCURRENT MODE: '+names[index]+'\n\nThis mode '+descriptions[index]+'.\n\nRight-click for next mode, which is '+names[(index+1)%names.length]+'.\n\nLeft-click for previous mode, which is '+names[(index+names.length-1)%names.length]+'.\n\nDouble-click to toggle between '+names[names.length-2]+' and '+names[names.length-1]+'.';
  const transportShuffle=document.getElementById('transportShuffle');if(transportShuffle){const name=shuffleNames[shuffleIndex];transportShuffle.textContent=shuffleIndex===0?'123':shuffleIndex===1?'🔀📖':shuffleIndex===2?'🔀🎲':shuffleIndex===3?'🔁📁':shuffleIndex===4?'🔁☷':'↪';transportShuffle.classList.toggle('active-toggle',shuffleIndex!==0&&shuffleIndex!==5);transportShuffle.setAttribute('aria-label','Shuffle: '+name);transportShuffle.title=orderTip('Shuffle',shuffleIndex,shuffleNames,shuffleDescriptions,'shuffle-next','shuffle-prev','shuffle-double')}
  const transportLoop=document.getElementById('transportLoop');if(transportLoop){const name=repeatNames[repeatIndex];transportLoop.textContent=repeatIndex===0?'🔂1':repeatIndex===1?'🔁📁':repeatIndex===2?'🔁☷':'↪';transportLoop.classList.toggle('active-toggle',repeatIndex!==3);transportLoop.setAttribute('aria-label','Repeat: '+name);transportLoop.title=orderTip('Repeat',repeatIndex,repeatNames,repeatDescriptions,'repeat-next','repeat-prev','repeat-double')}
  const transportVolume=document.getElementById('transportVolume');if(transportVolume && s.volume!==undefined) transportVolume.value=String(s.volume);
  const transportSpeedSelect=document.getElementById('transportSpeedSelect');if(transportSpeedSelect && s.speed_index!==undefined) transportSpeedSelect.value=String(s.speed_index);
  const shuffleExpiration=document.getElementById('shuffleExpirationHours');if(shuffleExpiration){if(s.shuffle_expiration_hours!==undefined&&document.activeElement!==shuffleExpiration)shuffleExpiration.value=String(Number(s.shuffle_expiration_hours));const applicable=shuffleIndex===1;shuffleExpiration.disabled=!applicable;const card=shuffleExpiration.closest('[data-control-key="shuffle_expiration_hours"]');if(card){card.classList.toggle('control-inapplicable',!applicable);card.title=applicable?'Age of the saved history shuffle before rebuilding it. Zero always rebuilds.':'Fresh shuffle age applies only to Shuffle by history.'}}
  const speedValue=Number(s.speed??1), speedText=(speedValue===1?'1':String(speedValue))+'×', minusSpeed=document.querySelector('.wawi-speed-minus'), plusSpeed=document.querySelector('.wawi-speed-plus');
  if(minusSpeed){minusSpeed.classList.toggle('speed-favored',speedValue>1);minusSpeed.title='Decrease the speed from '+speedText+' to the next slower setting.\\nDouble-right-click to restore speed to 1×'}
  if(plusSpeed){plusSpeed.classList.toggle('speed-favored',speedValue<1);plusSpeed.title='Increase the speed from '+speedText+' to the next faster setting.\\nDouble-right-click to restore speed to 1×'}
}

function appendLinkified(parent,text){
  const source=String(text??'');
  const re=/https?:\/\/[^\s<>"']+/gi;
  let cursor=0;
  for(const match of source.matchAll(re)){
    if(match.index>cursor) parent.appendChild(document.createTextNode(source.slice(cursor,match.index)));
    let url=match[0], trailing='';
    while(/[),.;\]}]$/.test(url)){trailing=url.slice(-1)+trailing;url=url.slice(0,-1)}
    const a=document.createElement('a');
    a.href=url;a.textContent=url;a.target='_blank';a.rel='noopener noreferrer';
    parent.appendChild(a);
    if(trailing) parent.appendChild(document.createTextNode(trailing));
    cursor=(match.index||0)+match[0].length;
  }
  if(cursor<source.length) parent.appendChild(document.createTextNode(source.slice(cursor)));
}

function renderDetectedUrls(urls){
  const items=Array.isArray(urls)?urls:[];
  const signature=items.map(String).join('\n');
  if(signature===lastRenderedUrlsSignature) return;
  lastRenderedUrlsSignature=signature;
  const host=document.getElementById('urls');host.textContent='';
  for(const url of items){
    const a=document.createElement('a');
    a.href=String(url);a.textContent=String(url);a.target='_blank';a.rel='noopener noreferrer';
    host.appendChild(a);
  }
}

function currentArtCount(){
  return Math.max(0,Number(latestState.art_count||0));
}
function updateWebArtTitle(){const count=currentArtCount(),art=document.getElementById('art');if(!art)return;art.title=(count>1?'Left: previous art • Right: next art • ':'')+'Middle: open full-size'}
function webArtRotationWeights(count){if(count<=0)return[];if(count===1)return[1];if(count===2)return[2/3,1/3];if(count===3)return[.60,.20,.20];if(count===4)return[.50,.20,.15,.15];if(count===5)return[.50,.18,.1066666667,.1066666667,.1066666667];if(count===6)return[.50,.15,.0875,.0875,.0875,.0875];return[.50,.10,...Array(count-2).fill(.40/(count-2))]}
function chooseWeightedIndex(weights){let total=weights.reduce((a,b)=>a+Math.max(0,Number(b)||0),0),r=Math.random()*Math.max(.000001,total);for(let i=0;i<weights.length;i++){r-=Math.max(0,Number(weights[i])||0);if(r<=0)return i}return Math.max(0,weights.length-1)}
function showWebArt(index,manual=true){
  const count=currentArtCount();if(count<=0)return;
  webArtIndex=((Number(index)%count)+count)%count;
  document.getElementById('art').src='/api/art?g='+(artGeneration||0)+'&index='+webArtIndex;
  if(manual)webArtAutoRotateAt=performance.now()+20000;updateWebArtTitle();
}
function maybeAutoRotateWebArt(now=performance.now()){const count=currentArtCount();if(count<=1||now<webArtAutoRotateAt)return;webArtAutoRotateAt=now+20000;let weights=webArtRotationWeights(count),chosen=chooseWeightedIndex(weights),popup=Number(latestState.art_popup_variant_index||0);if(chosen>0&&popup>0&&chosen===popup&&count>2){const alternatives=[];for(let i=1;i<count;i++)if(i!==popup)alternatives.push(i);if(alternatives.length){const aw=alternatives.map(i=>weights[i]);chosen=alternatives[chooseWeightedIndex(aw)]}}showWebArt(chosen,false)}
function maybeCycleBackgroundWithArt(delta){
  const count=currentArtCount(),c=webBgConfig();if(!c.enabled||count<=1)return;
  const active=(webBgOverrideIndex===null||webBgOverrideIndex===undefined)?webBgMatchedIndex:webBgOverrideIndex;
  if(Number(active)!==Number(webArtIndex))return;
  webBgOverrideIndex=((Number(active)+Number(delta))%count+count)%count;webBgMatchedIndex=webBgOverrideIndex;lastWebBackgroundSignature='';updateWebBackground();
}
const webArt=document.getElementById('art');
webArt.addEventListener('click',event=>{if(event.button!==0) return;showWebArt(webArtIndex-1)});
webArt.addEventListener('contextmenu',event=>{event.preventDefault();showWebArt(webArtIndex+1)});
webArt.addEventListener('auxclick',event=>{if(event.button!==1) return;event.preventDefault();const url='/api/art?g='+(artGeneration||0)+'&index='+webArtIndex;window.open(url,'_blank','noopener')});
webArt.addEventListener('mousedown',event=>{if(event.button===1)event.preventDefault()});


function makeDualRange(parent,prefix,defaultLow='0',defaultHigh='100'){
  const wrap=document.createElement('span');wrap.className='dual-range-wrap';const track=document.createElement('span');track.className='dual-range-track';const fill=document.createElement('span');fill.className='dual-range-fill';
  const low=document.createElement('input'),high=document.createElement('input');for(const i of [low,high]){i.type='range';i.min='0';i.max='100';i.step='1'}
  low.value=String(webPrefGet(prefix+'-min',defaultLow));high.value=String(webPrefGet(prefix+'-max',defaultHigh));const values=document.createElement('span');values.className='dual-range-values';const listeners=[];
  function sync(changed,notify=true){let a=Number(low.value),b=Number(high.value);if(changed===low&&a>b){a=b;low.value=String(a)}if(changed===high&&b<a){b=a;high.value=String(b)}webPrefSet(prefix+'-min',Number(low.value));webPrefSet(prefix+'-max',Number(high.value));values.textContent=low.value+'% – '+high.value+'%';fill.style.left=low.value+'%';fill.style.width=(Number(high.value)-Number(low.value))+'%';if(notify)for(const fn of listeners)fn()}
  low.oninput=()=>sync(low);high.oninput=()=>sync(high);wrap.append(track,fill,low,high);parent.append(wrap,values);sync(null,false);return {low,high,sync,onChange(fn){listeners.push(fn)}};
}
function slideIntervalFromControl(raw){
  const t=Math.max(0,Math.min(1,Number(raw)/1000));
  return .05*Math.pow(1200,t); // V239: 0.05s → 60s, logarithmic resolution.
}
function slideControlFromInterval(seconds){
  const v=Math.max(.05,Math.min(60,Number(seconds)||4));return Math.round(1000*Math.log(v/.05)/Math.log(1200));
}
function formatSlideSeconds(seconds){return (seconds<.1?seconds.toFixed(2):seconds<1?seconds.toFixed(2):seconds<10?seconds.toFixed(1):seconds.toFixed(0))+'s'}
function setupOneArtSaturation(key,toggleKey,storagePrefix){
  const control=document.querySelector('[data-control-key="'+key+'"]');if(!control)return null;control.classList.add('art-saturation-card','control-theme-visualizer');
  const main=document.getElementById('ctl-'+key);const enable=document.createElement('label');enable.className='art-saturation-enable';const enabled=document.createElement('input');enabled.type='checkbox';enabled.id='art-saturation-enabled-'+toggleKey;enabled.dataset.toggleKey=toggleKey;enabled.title='Turn album-art coloring for this region on/off';const toggleState=document.getElementById('ctl-'+toggleKey);enabled.checked=toggleState?toggleState.checked:true;enable.append(enabled,document.createTextNode('Art on'));
  const box=document.createElement('div');box.className='autoslide-box';box.title='Automatically sweep saturation smoothly inside PAFPlayer; the browser sends configuration only';const auto=document.createElement('input');auto.type='checkbox';auto.checked=webPrefBool(storagePrefix+'-enabled',false);box.append(auto,document.createTextNode('autoslide'));
  const range=document.createElement('div');range.className='autoslide-range';const dual=makeDualRange(range,storagePrefix,'0','100');const intervalLabel=document.createElement('span');intervalLabel.textContent='Slide interval';intervalLabel.title='Time for one complete min → max → min saturation cycle';const interval=document.createElement('input');interval.className='slide-interval';interval.type='range';interval.min='0';interval.max='1000';interval.step='1';let independentInterval=Math.max(.05,Math.min(60,Number(webPrefGet(storagePrefix+'-interval',4))));interval.value=String(slideControlFromInterval(independentInterval));const intervalValue=document.createElement('span');intervalValue.className='slide-value';range.append(intervalLabel,interval,intervalValue);box.append(range);control.append(enable,box);
  let sharedIntervalCallback=null,locked=false,sendTimer=null;
  const channel=key.includes('black')?'black':'bar';
  function showInterval(seconds){independentInterval=Math.max(.05,Math.min(60,Number(seconds)||4));interval.value=String(slideControlFromInterval(independentInterval));intervalValue.textContent=formatSlideSeconds(independentInterval)}
  function sendConfig(){sendTimer=null;action('web-set:art_color_'+channel+'_autoslide_enabled:'+(auto.checked?'1':'0'));action('web-set:art_color_'+channel+'_autoslide_min:'+Math.round(Number(dual.low.value)));action('web-set:art_color_'+channel+'_autoslide_max:'+Math.round(Number(dual.high.value)));action('web-set:art_color_'+channel+'_autoslide_interval_ms:'+Math.round(independentInterval*1000))}
  function scheduleSend(immediate=false){if(sendTimer!==null)clearTimeout(sendTimer);if(immediate){sendConfig();return}sendTimer=setTimeout(sendConfig,90)}
  function syncInterval(){const seconds=slideIntervalFromControl(interval.value);if(locked&&sharedIntervalCallback){sharedIntervalCallback(seconds);return}showInterval(seconds);webPrefSet(storagePrefix+'-interval',independentInterval);scheduleSend()}
  interval.oninput=syncInterval;dual.onChange(()=>scheduleSend());showInterval(independentInterval);
  function apply(sendToggle=true){box.classList.toggle('enabled',auto.checked);main.style.display=auto.checked?'none':'';webPrefSet(storagePrefix+'-enabled',auto.checked?1:0);control.classList.toggle('art-saturation-disabled',!enabled.checked);if(sendToggle){action('web-set:'+toggleKey+':'+(enabled.checked?'1':'0'));scheduleSend(true)}}
  enabled._pafSyncFromServer=value=>{const wanted=!!value;if(enabled.checked!==wanted)enabled.checked=wanted;control.classList.toggle('art-saturation-disabled',!enabled.checked)};
  auto.onchange=()=>apply(true);enabled.onchange=()=>apply(true);apply(false);
  return {box,auto,independentInterval(){return independentInterval},setLocked(value){locked=!!value},setSharedInterval(seconds){showInterval(seconds);webPrefSet(storagePrefix+'-interval',independentInterval);scheduleSend()},setSharedIntervalCallback(fn){sharedIntervalCallback=fn},send(){scheduleSend(true)}};
}
function setupArtSaturationAutoslide(){
  const bar=setupOneArtSaturation('art_color_bar_strength','art_color_bars','paf-art-bars-autoslide'),black=setupOneArtSaturation('art_color_black_strength','art_color_blackness','paf-art-black-autoslide');
  const lockLabel=document.createElement('label');lockLabel.className='toggle autoslide-lock';lockLabel.title='Use one smooth console-side phase and interval for blackness and bars while keeping their min/max ranges independent';const lock=document.createElement('input');lock.id='artAutoSlideLock';lock.type='checkbox';lock.checked=webPrefBool('paf-art-autoslides-locked',false);lockLabel.append(lock,document.createTextNode('Lock autoslides'));const lockHost=(bar&&bar.box)||(black&&black.box);if(lockHost){const range=lockHost.querySelector('.autoslide-range');if(range)lockHost.insertBefore(lockLabel,range);else lockHost.appendChild(lockLabel)}
  let sharedSeconds=Math.max(.05,Math.min(60,Number(webPrefGet('paf-art-autoslides-lock-interval',bar?bar.independentInterval():black?black.independentInterval():4))));
  function setSharedInterval(seconds){sharedSeconds=Math.max(.05,Math.min(60,Number(seconds)||4));webPrefSet('paf-art-autoslides-lock-interval',sharedSeconds);bar&&bar.setSharedInterval(sharedSeconds);black&&black.setSharedInterval(sharedSeconds)}
  bar&&bar.setSharedIntervalCallback(setSharedInterval);black&&black.setSharedIntervalCallback(setSharedInterval);
  function applyLock(initial=false){if(lock.checked&&!initial&&bar)sharedSeconds=bar.independentInterval();if(lock.checked)setSharedInterval(sharedSeconds);bar&&bar.setLocked(lock.checked);black&&black.setLocked(lock.checked);webPrefSet('paf-art-autoslides-locked',lock.checked?1:0);if(!initial){action('web-set:art_color_autoslides_locked:'+(lock.checked?'1':'0'));bar&&bar.send();black&&black.send()}}
  lock.onchange=()=>applyLock(false);applyLock(true);
}
function matrixSpeakerLabel(code){return code==='LFE'?'SUB':code}
let matrixToneState=null;
async function matrixTonePost(op,extra={}){const r=await fetch('/api/test-tone',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({op,...extra})}),d=await r.json();if(!r.ok)throw new Error(d.error||'Test Tone operation failed');matrixToneState=d;renderMatrixTones();return d}
function renderMatrixTones(){if(!matrixToneState)return;document.getElementById('matrixTestToneEnabled').checked=!!matrixToneState.enabled;const host=document.getElementById('matrixTestToneRows');host.textContent='';matrixToneState.tones.forEach((tone,index)=>{const row=document.createElement('div');row.className='matrix-actions';const selected=document.createElement('button');selected.className='secondary-button';selected.textContent=(index===matrixToneState.selected?'● ':'○ ')+'Tone '+(index+1);selected.onclick=()=>matrixTonePost('update',{index});const hz=document.createElement('input');hz.type='number';hz.min='20';hz.max='20000';hz.step='1';hz.value=String(Math.round(tone.frequency*100)/100);hz.title='Frequency in Hz';hz.onchange=()=>matrixTonePost('update',{index,frequency:Number(hz.value)});const pattern=document.createElement('select');matrixToneState.patterns.forEach((name,i)=>{const option=document.createElement('option');option.value=String(i);option.textContent=name;pattern.append(option)});pattern.value=String(tone.pattern);pattern.onchange=()=>matrixTonePost('update',{index,pattern:Number(pattern.value)});const volume=document.createElement('input');volume.type='range';volume.min='0';volume.max='50';volume.value=String(tone.volume);volume.title='Tone '+(index+1)+' volume';const volumeText=document.createElement('span');volumeText.textContent=tone.volume+'%';volume.oninput=()=>volumeText.textContent=volume.value+'%';volume.onchange=()=>matrixTonePost('update',{index,volume:Number(volume.value)});const remove=document.createElement('button');remove.className='secondary-button';remove.textContent='Remove';remove.disabled=matrixToneState.tones.length===1;remove.onclick=()=>matrixTonePost('remove',{index});row.append(selected,hz,pattern,volume,volumeText,remove);host.append(row)});const sets=document.getElementById('matrixTestToneSets'),chosen=sets.value;sets.textContent='';matrixToneState.saved_sets.forEach(name=>{const option=document.createElement('option');option.value=option.textContent=name;sets.append(option)});if([...sets.options].some(x=>x.value===chosen))sets.value=chosen}
document.getElementById('matrixTestToneEnabled').onchange=event=>matrixTonePost(event.target.checked?'enable':'disable').catch(error=>matrixSetStatus(error,true));document.getElementById('matrixTestToneAdd').onclick=()=>matrixTonePost('add').catch(error=>matrixSetStatus(error,true));document.getElementById('matrixTestToneSave').onclick=()=>{const description=document.getElementById('matrixTestToneDescription').value.trim();matrixTonePost('save',{description,set_name:description}).catch(error=>matrixSetStatus(error,true))};document.getElementById('matrixTestToneLoad').onclick=()=>matrixTonePost('load',{set_name:document.getElementById('matrixTestToneSets').value}).catch(error=>matrixSetStatus(error,true));
function matrixSetStatus(text,bad=false){const h=document.getElementById('matrixStatus');h.textContent=text||'';h.style.color=bad?'#ff9ca8':'#9ee5b9'}
async function testMatrixSpeaker(channels,speaker){
 matrixSetStatus('Testing '+matrixSpeakerLabel(speaker)+'…');
 try{
  const r=await fetch('/api/matrix-test',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({output_channels:Number(channels),speaker,output_rate:Number(latestState.output_rate_hz||48000),output_bit_depth:Number(latestState.output_bit_depth||16),output_device:Number(latestState.output_device??-1)})});
  const d=await r.json();if(!r.ok)throw new Error(d.error||'speaker test failed');matrixSetStatus('Test tone sent to '+matrixSpeakerLabel(speaker));
 }catch(e){matrixSetStatus(String(e),true)}
}
function matrixRows(host,rows,crossover,mutes){
 host.textContent='';const muted=new Set((mutes||[]).map(String));
 for(const head of ['Test','Speaker','Mute','L input','R input','Crossover','Live level']){const b=document.createElement('b');b.textContent=head;b.title=head;if(head==='Speaker')b.style.textAlign='right';host.appendChild(b)}
 for(const row of rows){
  const speaker=String(row[0]);
  const test=document.createElement('button');test.className='secondary-button matrix-test-button';test.textContent='▶';test.title='Play a short discrete test tone through '+matrixSpeakerLabel(speaker);test.onclick=()=>testMatrixSpeaker(host.dataset.channels,speaker);
  const name=document.createElement('span');name.className='matrix-speaker';name.textContent=matrixSpeakerLabel(speaker);name.title='Destination speaker '+matrixSpeakerLabel(speaker);
  const muteWrap=document.createElement('label');muteWrap.title='Mute '+matrixSpeakerLabel(speaker);const mute=document.createElement('input');mute.type='checkbox';mute.dataset.muteSpeaker=speaker;mute.checked=muted.has(speaker);mute.onchange=()=>{syncMatrixMuteAllButton(host.id);scheduleMatrixLiveApply('Mute change applied')};muteWrap.appendChild(mute);
  const l=document.createElement('input'),r=document.createElement('input');
  for(const [inp,side] of [[l,'left'],[r,'right']]){inp.type='number';inp.step='0.05';inp.min='-4';inp.max='4';inp.title=side+' stereo input coefficient sent to '+matrixSpeakerLabel(speaker);inp.onchange=()=>scheduleMatrixLiveApply('Matrix value applied')}
  l.value=row[1];r.value=row[2];l.dataset.speaker=r.dataset.speaker=speaker;
  host.append(test,name,muteWrap,l,r);
  if(speaker==='LFE'){
   const cross=document.createElement('div');cross.className='matrix-crossover';
   const enabled=document.createElement('input');enabled.type='checkbox';enabled.checked=!!(crossover&&crossover.enabled);enabled.dataset.crossoverEnabled='1';enabled.title='Enable SUB crossover; only audio below the selected cutoff is sent to SUB';
   const slider=document.createElement('input');slider.type='range';slider.min='20';slider.max='250';slider.step='1';slider.value=Number(crossover&&crossover.hz||60);slider.dataset.crossoverHz='1';slider.title='SUB crossover frequency';
   const value=document.createElement('span');value.textContent=slider.value+' Hz';slider.oninput=()=>{value.textContent=slider.value+' Hz';scheduleMatrixLiveApply('Crossover applied')};enabled.onchange=()=>scheduleMatrixLiveApply('Crossover applied');
   cross.append(enabled,slider,value);host.appendChild(cross);
  }else{host.appendChild(document.createElement('span'))}
  const level=document.createElement('div');level.className='matrix-level';level.dataset.levelSpeaker=speaker;level.dataset.levelChannels=host.dataset.channels;
  const track=document.createElement('span');track.className='matrix-level-track';const fill=document.createElement('span');fill.className='matrix-level-fill';track.appendChild(fill);
  const text=document.createElement('span');text.className='matrix-level-text';text.textContent='—';level.append(track,text);host.appendChild(level);
 }
 syncMatrixMuteAllButton(host.id);
}
function readMatrix(host){return [...host.querySelectorAll('input[type=number][data-speaker]')].reduce((rows,input,index,array)=>{if(index%2===0)rows.push([input.dataset.speaker,Number(input.value),Number(array[index+1].value)]);return rows},[])}
function readCrossover(host){const e=host.querySelector('[data-crossover-enabled]'),h=host.querySelector('[data-crossover-hz]');return {enabled:!!(e&&e.checked),hz:Number(h&&h.value||60)}}
function readMutes(host){return [...host.querySelectorAll('[data-mute-speaker]')].filter(x=>x.checked).map(x=>x.dataset.muteSpeaker)}
function syncMatrixMuteAllButton(hostId){const host=document.getElementById(hostId),button=document.querySelector('[data-mute-all="'+hostId+'"]');if(!host||!button)return;const boxes=[...host.querySelectorAll('[data-mute-speaker]')];const all=boxes.length>0&&boxes.every(x=>x.checked);button.textContent=all?'Unmute all':'Mute all';button.dataset.allMuted=all?'1':'0'}
function wireMatrixMuteAll(){document.querySelectorAll('[data-mute-all]').forEach(button=>{button.onclick=()=>{const host=document.getElementById(button.dataset.muteAll);if(!host)return;const setTo=button.dataset.allMuted!=='1';host.querySelectorAll('[data-mute-speaker]').forEach(x=>x.checked=setTo);syncMatrixMuteAllButton(host.id);scheduleMatrixLiveApply(setTo?'All speakers muted':'All speakers unmuted')}})}
async function refreshMatrixEditor(selectedProfile){
 const d=await (await fetch('/api/matrix',{cache:'no-store'})).json();
 matrixRows(document.getElementById('matrix5'),d.matrix5||[],d.crossover5||{},d.mutes5||[]);
 matrixRows(document.getElementById('matrix7'),d.matrix7||[],d.crossover7||{},d.mutes7||[]);
 matrixRows(document.getElementById('matrix12'),d.matrix12||[],d.crossover12||{},d.mutes12||[]);
 const p=document.getElementById('matrixProfiles');const wanted=selectedProfile||p.value||'default';p.textContent='';
 for(const name of d.profiles||['default']){const o=document.createElement('option');o.value=o.textContent=name;p.appendChild(o)}
 if([...p.options].some(o=>o.value===wanted))p.value=wanted;wireMatrixMuteAll();return d
}
async function matrixPost(payload){const r=await fetch('/api/matrix',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)throw new Error(d.error||'Matrix operation failed');return d}
function currentMatrixPayload(op){const h5=document.getElementById('matrix5'),h7=document.getElementById('matrix7'),h12=document.getElementById('matrix12');return {op,matrix5:readMatrix(h5),matrix7:readMatrix(h7),matrix12:readMatrix(h12),crossover5:readCrossover(h5),crossover7:readCrossover(h7),crossover12:readCrossover(h12),mutes5:readMutes(h5),mutes7:readMutes(h7),mutes12:readMutes(h12)}}
let matrixLiveApplyTimer=null,matrixLiveApplySerial=0;function scheduleMatrixLiveApply(message='Matrix applied'){clearTimeout(matrixLiveApplyTimer);const serial=++matrixLiveApplySerial;matrixLiveApplyTimer=setTimeout(async()=>{try{matrixSetStatus('Applying matrix…');const d=await matrixPost(currentMatrixPayload('update'));if(serial!==matrixLiveApplySerial)return;matrixSetStatus((message||'Matrix applied')+(Number(d.active_output_channels)===2?' (saved; current output is Stereo).':d.native_matrix_renderer_enabled?' through native speaker-mapped output.':' — native matrix renderer will engage on restart.'))}catch(e){if(serial===matrixLiveApplySerial)matrixSetStatus(String(e),true)}},180)}
let matrixLevelTimer=null;
async function refreshMatrixLevels(){if(!document.getElementById('matrixModal').classList.contains('open'))return;try{const d=await (await fetch('/api/matrix-levels',{cache:'no-store'})).json();document.querySelectorAll('[data-level-speaker]').forEach(level=>{const speaker=level.dataset.levelSpeaker,channels=Number(level.dataset.levelChannels),row=(d.active&&Number(d.output_channels)===channels&&d.levels)?d.levels[speaker]:null;const fill=level.querySelector('.matrix-level-fill'),text=level.querySelector('.matrix-level-text');if(!row){fill.style.width='0%';text.textContent='—';return}const db=Number(row.dbfs);const pct=Math.max(0,Math.min(100,(db+60)/60*100));fill.style.width=pct+'%';text.textContent=db<=-119?'−∞':db.toFixed(1)+' dB'})}catch(e){}}
function startMatrixLevelPolling(){stopMatrixLevelPolling();refreshMatrixLevels();matrixLevelTimer=setInterval(refreshMatrixLevels,160)}
function stopMatrixLevelPolling(){if(matrixLevelTimer!==null){clearInterval(matrixLevelTimer);matrixLevelTimer=null}}
async function openMatrixEditor(){document.getElementById('matrixModal').classList.add('open');matrixSetStatus('');await Promise.all([refreshMatrixEditor('default'),matrixTonePost('snapshot')]);startMatrixLevelPolling()}
function closeMatrixEditor(){stopMatrixLevelPolling();document.getElementById('matrixModal').classList.remove('open')}
function matrixSectionLabel(channels){return Number(channels)===5?'5.1':Number(channels)===7?'7.1':'Dolby Atmos 7.1.4'}
async function resetMatrixSection(channels){
 const label=matrixSectionLabel(channels);
 clearTimeout(matrixLiveApplyTimer);++matrixLiveApplySerial;
 const saveFirst=confirm('Before resetting '+label+', would you like to save the CURRENT COMPLETE 5.1 + 7.1 + Atmos configuration as a named recovery profile first?\n\nOK = Save first\nCancel = Continue without saving');
 let savedName='';
 try{
  if(saveFirst){
   savedName=(prompt('Save current complete matrix configuration as profile:','before '+label+' factory reset')||'').trim();
   if(!savedName){matrixSetStatus('Reset cancelled; no recovery profile was saved.');return}
   const savePayload=currentMatrixPayload('save-profile');savePayload.name=savedName;await matrixPost(savePayload);
  }else{
   // Flush any just-edited values in the other sections before changing only this one.
   await matrixPost(currentMatrixPayload('update'));
  }
  if(!confirm('Reset ONLY '+label+' to the factory PAFPlayer matrix?\n\nThis resets that section’s coefficients, speaker mutes, and SUB crossover. The other two sections will not change.')){
   matrixSetStatus(savedName?'Saved profile “'+savedName+'”; factory reset cancelled.':'Factory reset cancelled.');return
  }
  const d=await matrixPost({op:'reset-section',output_channels:Number(channels)});
  await refreshMatrixEditor(savedName||undefined);
  matrixSetStatus((savedName?'Saved profile “'+savedName+'”. ':'')+label+' factory values restored; the other matrix sections were left untouched'+(Number(d.active_output_channels)===2?'. Current output is Stereo.':', and the active multichannel renderer was refreshed.'));
 }catch(e){matrixSetStatus(String(e),true)}
}
function wireMatrixSectionResets(){document.querySelectorAll('[data-reset-section]').forEach(button=>{button.onclick=()=>resetMatrixSection(Number(button.dataset.resetSection))})}
function wireMatrixButtons(){
 document.getElementById('matrixCloseX').onclick=closeMatrixEditor;
 document.addEventListener('keydown',event=>{if(event.key!=='Escape'||!document.getElementById('matrixModal').classList.contains('open'))return;event.preventDefault();if(confirm('Exit Speaker Expansion Matrix without applying any unsaved changes?'))closeMatrixEditor()});
 document.getElementById('matrixApply').onclick=async()=>{try{const d=await matrixPost(currentMatrixPayload('update'));matrixSetStatus(Number(d.active_output_channels)===2?'Matrix saved. Current output is Stereo; choose 5.1/7.1/Atmos to hear it.':(d.restart_queued?'Matrix saved; native speaker-mapped renderer engaged and audio restart queued.':'Matrix saved; native speaker-mapped renderer will be used for multichannel playback.'))}catch(e){matrixSetStatus(String(e),true)}};
 document.getElementById('matrixSaveProfile').onclick=async()=>{try{let name=document.getElementById('matrixProfileName').value.trim();if(!name)name=(prompt('Profile name:','profile 1')||'').trim();if(!name)return;const payload=currentMatrixPayload('save-profile');payload.name=name;await matrixPost(payload);await refreshMatrixEditor(name);document.getElementById('matrixProfileName').value='';matrixSetStatus('Saved profile “'+name+'”.')}catch(e){matrixSetStatus(String(e),true)}};
 document.getElementById('matrixRestoreProfile').onclick=async()=>{const name=document.getElementById('matrixProfiles').value;if(!name)return;if(confirm('Restore matrix profile “'+name+'”?'))try{const d=await matrixPost({op:'restore-profile',name});await refreshMatrixEditor(name);matrixSetStatus('Restored profile “'+name+'”'+(Number(d.active_output_channels)===2?' (current output is Stereo).':', applied to playback.'))}catch(e){matrixSetStatus(String(e),true)}};
 wireMatrixMuteAll();wireMatrixSectionResets();
}
wireMatrixButtons();

const WEB_BG_KEY='paf-web-background-config-v238';
const WEB_BG_PROFILES_KEY='paf-web-background-profiles-v252';
const WEB_BG_LAST_PROFILE_KEY='paf-web-background-last-profile-v453';
function webBgConfig(){
 const base={enabled:false,first:'back',second:'inlay',third:'cover',final:'any',saturation:100,brightness:100,alpha:34,titleBleed:10,aspect:'stretch-h',tiling:'none',checkerboard:true,scale:.25};
 const saved=webPrefGet(WEB_BG_KEY,{});return {...base,...(saved&&typeof saved==='object'&&!Array.isArray(saved)?saved:{})}
}
function saveWebBgConfig(c){webPrefSet(WEB_BG_KEY,c);updateWebBackground()}
function bgScaleFromSlider(raw){
 const t=Math.max(0,Math.min(1,Number(raw)/1000));
 if(t<=.65)return .05*Math.pow(20,t/.65); // 65% of the slider is devoted to 0.05× → 1×.
 return Math.pow(40,(t-.65)/.35);          // remaining 35% covers 1× → 40×.
}
function bgSliderFromScale(scale){
 const v=Math.max(.05,Math.min(40,Number(scale)||.25));
 if(v<=1)return Math.round(1000*.65*Math.log(v/.05)/Math.log(20));
 return Math.round(1000*(.65+.35*Math.log(v)/Math.log(40)));
}
function applyTitleBox(c){
 const bleed=Math.max(0,Math.min(100,Number(c.titleBleed??10))),a=1-bleed/100,title=document.getElementById('songTitle');
 if(!title)return;const aa=Math.max(.05,Math.min(1,a));title.style.background=`linear-gradient(90deg,rgba(255,72,116,${aa}),rgba(255,190,67,${aa}),rgba(94,229,119,${aa}),rgba(64,189,255,${aa}),rgba(157,88,255,${aa}))`;
 const label=document.getElementById('titleBleedLabel');if(label)label.textContent='Title background bleed '+Math.round(bleed)+'%';
}
function webBgProfiles(){const raw=webPrefGet(WEB_BG_PROFILES_KEY,{});return raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:{}}
function normalizedWebBgConfig(c){const x={...(c||{})};for(const k of ['saturation','brightness','alpha','titleBleed','scale'])if(x[k]!==undefined)x[k]=Number(x[k]);x.enabled=!!x.enabled;x.checkerboard=x.checkerboard!==false;return x}
function sameWebBgConfig(a,b){return JSON.stringify(normalizedWebBgConfig(a))===JSON.stringify(normalizedWebBgConfig(b))}
function syncWebBgProfileName(c){const input=document.getElementById('webBgProfileName');if(!input)return;const name=String(webPrefGet(WEB_BG_LAST_PROFILE_KEY,'')||''),profile=webBgProfiles()[name];input.value=(name&&profile&&sameWebBgConfig(c,profile))?name:''}
function refreshWebBgProfileList(selected=''){const sel=document.getElementById('webBgProfiles');if(!sel)return;const profiles=webBgProfiles();sel.textContent='';for(const name of Object.keys(profiles).sort((a,b)=>a.localeCompare(b))){const o=document.createElement('option');o.value=name;o.textContent=name;sel.appendChild(o)}if(selected&&profiles[selected])sel.value=selected}
function applyWebBgProfile(c){if(!c||typeof c!=='object')return;document.getElementById('webBgEnabled').checked=!!c.enabled;const mapping={webBgFirst:'first',webBgSecond:'second',webBgThird:'third',webBgFinal:'final'};for(const [id,key] of Object.entries(mapping))if(c[key]!==undefined)document.getElementById(id).value=String(c[key]);for(const [id,key] of [['webBgSaturation','saturation'],['webBgBrightness','brightness'],['webBgAlpha','alpha'],['titleBleed','titleBleed']])if(c[key]!==undefined)document.getElementById(id).value=String(c[key]);if(c.aspect!==undefined)document.getElementById('webBgAspect').value=String(c.aspect);if(c.scale!==undefined)document.getElementById('webBgScale').value=String(bgSliderFromScale(c.scale));document.getElementById('webBgCheckerboard').checked=c.checkerboard!==false;const radio=document.querySelector('input[name="webBgTiling"][value="'+String(c.tiling||'none')+'"]');if(radio)radio.checked=true;document.getElementById('webBgScale').dispatchEvent(new Event('input',{bubbles:true}))}
function setupWebBackgroundConfig(){
 const ids=['webBgFirst','webBgSecond','webBgThird','webBgFinal'];const labels=[['back','Back'],['inlay','Inlay'],['cover','Cover'],['any','Any'],['none','None']];for(const id of ids){const sel=document.getElementById(id);for(const [v,l] of labels){const o=document.createElement('option');o.value=v;o.textContent=l;sel.appendChild(o)}}
 const c=webBgConfig();document.getElementById('webBgEnabled').checked=!!c.enabled;for(const id of ids)document.getElementById(id).value=c[{webBgFirst:'first',webBgSecond:'second',webBgThird:'third',webBgFinal:'final'}[id]];document.getElementById('webBgSaturation').value=c.saturation;document.getElementById('webBgBrightness').value=c.brightness;document.getElementById('webBgAlpha').value=c.alpha;document.getElementById('titleBleed').value=String(c.titleBleed??10);document.getElementById('webBgAspect').value=c.aspect;document.getElementById('webBgScale').value=String(bgSliderFromScale(c.scale));document.getElementById('webBgCheckerboard').checked=c.checkerboard!==false;const tiling=document.querySelector('input[name="webBgTiling"][value="'+c.tiling+'"]')||document.querySelector('input[name="webBgTiling"][value="none"]');if(tiling)tiling.checked=true;
 function pull(){const checked=document.querySelector('input[name="webBgTiling"]:checked');const scale=bgScaleFromSlider(document.getElementById('webBgScale').value);const n={enabled:document.getElementById('webBgEnabled').checked,first:document.getElementById('webBgFirst').value,second:document.getElementById('webBgSecond').value,third:document.getElementById('webBgThird').value,final:document.getElementById('webBgFinal').value,saturation:Number(document.getElementById('webBgSaturation').value),brightness:Number(document.getElementById('webBgBrightness').value),alpha:Number(document.getElementById('webBgAlpha').value),titleBleed:Number(document.getElementById('titleBleed').value),aspect:document.getElementById('webBgAspect').value,scale,tiling:checked?checked.value:'none',checkerboard:document.getElementById('webBgCheckerboard').checked};document.getElementById('webBgSatLabel').textContent='Saturation '+n.saturation+'%';document.getElementById('webBgBrightnessLabel').textContent='Brightness '+n.brightness+'%';document.getElementById('webBgAlphaLabel').textContent='Alpha '+n.alpha+'%';document.getElementById('webBgScaleLabel').textContent='Scale '+n.scale.toLocaleString(undefined,{maximumFractionDigits:n.scale<1?2:1})+'×';applyTitleBox(n);webBgOverrideIndex=null;saveWebBgConfig(n);syncWebBgProfileName(n)}
 for(const id of ['webBgEnabled',...ids,'webBgSaturation','webBgBrightness','webBgAlpha','titleBleed','webBgAspect','webBgScale','webBgCheckerboard'])document.getElementById(id).addEventListener('input',pull);for(const radio of document.querySelectorAll('input[name="webBgTiling"]'))radio.addEventListener('change',pull);refreshWebBgProfileList();document.getElementById('webBgSaveProfile').onclick=()=>{let name=document.getElementById('webBgProfileName').value.trim();if(!name)name=(prompt('Background profile name:','profile 1')||'').trim();if(!name)return;const profiles=webBgProfiles();profiles[name]=webBgConfig();webPrefSet(WEB_BG_PROFILES_KEY,profiles);webPrefSet(WEB_BG_LAST_PROFILE_KEY,name);refreshWebBgProfileList(name);document.getElementById('webBgProfileName').value=name};document.getElementById('webBgLoadProfile').onclick=()=>{const name=document.getElementById('webBgProfiles').value,profile=webBgProfiles()[name];if(profile&&confirm('Restore page-background profile “'+name+'”?')){webPrefSet(WEB_BG_LAST_PROFILE_KEY,name);applyWebBgProfile(profile);document.getElementById('webBgProfileName').value=name}};document.getElementById('webBgDeleteProfile').onclick=()=>{const name=document.getElementById('webBgProfiles').value;if(!name||!confirm('Delete page-background profile “'+name+'”?'))return;const profiles=webBgProfiles();delete profiles[name];webPrefSet(WEB_BG_PROFILES_KEY,profiles);if(String(webPrefGet(WEB_BG_LAST_PROFILE_KEY,'')||'')===name)webPrefSet(WEB_BG_LAST_PROFILE_KEY,'');refreshWebBgProfileList();syncWebBgProfileName(webBgConfig())};applyTitleBox(c);pull();syncWebBgProfileName(webBgConfig());
}
const globalConfigDirectTargets=[
    ['floating_track_intro_seconds','FloatingLyricsTrackIntroSeconds'],
 ["artist_throb_ms","ArtistThrobMs"],["song_throb_ms","SongThrobMs"],
 ['adaptive_frequency_enabled','AdaptiveFrequency'],['external_media_loudness_match','ExternalMediaLoudnessMatch'],['frequency_warp_preset','FrequencyWarpPreset'],['frequency_warp_custom_20','FrequencyWarpCustom20'],['frequency_warp_custom_40','FrequencyWarpCustom40'],['frequency_warp_custom_60','FrequencyWarpCustom60'],['frequency_warp_custom_80','FrequencyWarpCustom80'],
 ['visualizer_mode','VisualizerMode'],['persistence_mode','PersistenceMode'],['visualizer_granularity','VisualizerGranularity'],['visualizer_input_source','VisualizerInputSource'],
 ['processing_style','ProcessingStyle'],['color_style','ColorStyle'],['karaoke_style','KaraokeStyle'],['karaoke_style_spaced','KaraokeStyleSpaced'],['karaoke_style_framed','KaraokeStyleFramed'],['karaoke_style_frame','KaraokeStyleFrame'],['karaoke_treatment','KaraokeTreatment'],
 ['console_karaoke_enabled','ConsoleKaraokeEnabled'],['console_alerts_enabled','ConsoleAlertsEnabled'],['error_popup_enabled','ErrorPopupEnabled'],['error_windows_notification_enabled','ErrorWindowsNotificationEnabled'],['error_sound_enabled','ErrorSoundEnabled'],['visualizer_bars_enabled','VisualizerBarsEnabled'],['visualizer_background_artwork_enabled','VisualizerBackgroundArtworkEnabled'],
 ['console_visualizer_volume_feedback_enabled','ConsoleVisualizerOverlayMessagesEnabled'],['decensor_console_karaoke','DecensorConsoleKaraoke'],['decensor_artwork_lyrics','DecensorArtworkLyrics'],['decensor_floating_lyrics','DecensorFloatingLyrics'],
 ['alert_no_replaygain','AlertNoReplayGain'],['alert_missing_artist','AlertMissingArtist'],['alert_missing_title','AlertMissingTitle'],['alert_missing_karaoke','AlertMissingKaraoke'],['alert_missing_lyrics','AlertMissingLyrics'],['alert_missing_artwork','AlertMissingArtwork'],['alert_unknown_year','AlertUnknownYear'],['alert_unknown_genre','AlertUnknownGenre'],['alert_embedded_lyrics_mismatch','AlertEmbeddedLyricsMismatch'],['alert_non_default_speed','AlertNonDefaultSpeed'],
  ['progress_style','ProgressStyle'],['progress_invert_order','ProgressInvertOrder'],['progress_invert_palette','ProgressInvertPalette'],['progress_beat_overlay_mode','ProgressBeatOverlayMode'],['console_title_style','ConsoleTitleStyle'],['progress_bar_enabled','ProgressBarEnabled'],['progress_beat_reactive','ProgressBeatReactive'],['progress_beat_detector','ProgressBeatDetector'],['progress_beat_treatment','ProgressBeatTreatment'],['progress_beat_visual_offset_ms','ProgressBeatVisualOffsetMs'],['cursive_fix','CursiveFix'],
 ['drcs_art_microtile_mode','DrcsArtMicrotileDetailModeV370'],['drcs_art_bar_microtile_mode','DrcsArtBarMicrotileDetailModeV370'],['fade_style','BarFadeStyle'],['speed_index','SpeedIndex'],['output_channels','OutputChannels'],['output_rate','OutputRate'],['output_bit_depth','OutputBitDepth'],['output_device','OutputDevice'],['output_devices_mask','OutputDevicesMask'],['mm_inspired_renderer_enabled','MMInspiredRenderer'],['volume','Volume'],['balance','Balance'],['karaoke_visualizer_height_mode','KaraokeVisualizerHeightMode'],
 ['external_media_auto_pause','ExternalMediaAutoPause'],['external_media_resume_fade_seconds','ExternalMediaResumeFadeSeconds'],['inter_track_timing_ms','InterTrackTimingAdjustmentMs'],['floating_track_intro_ms','FloatingLyricsTrackIntroMs'],['artwork_seam_strategy','ArtworkSeamStrategy'],['art_color_representation','ArtColorRepresentation'],['art_color_blackness',null],['art_color_bars',null],['art_color_bar_strength','ArtColorBarStrength'],['art_color_bar_opacity','ArtColorBarOpacity'],['art_color_black_strength','ArtColorBlackStrength'],['art_color_karaoke_sides','ArtColorKaraokeSides'],['art_color_karaoke','ArtColorKaraoke'],['art_topmost',null],['floating_topmost',null]
];
const globalConfigToggleTargets=[
 ['drcs_enabled','DrcsEnabled','drcs-visualizer-toggle'],['sixel_enabled','SixelEnabled','sixel-visualizer-toggle'],['hud_details','HudDetails','hud-details-toggle'],['karaoke_emojimax','KaraokeEmojimax','karaoke-emoji-toggle'],['frequency_warp_enabled','FrequencyWarp','frequency-warp-toggle'],['shuffle','Shuffle','random-toggle'],['loop','Looping','loop-toggle'],['karaoke_visualizer_expansion_enabled','KaraokeVisualizerExpansion','karaoke-visualizer-expand-toggle'],['karaoke_visualizer_overlay',null,'karaoke-visualizer-overlay-toggle'],['external_album_art_enabled',null,'external-album-art-toggle'],['floating_lyrics_enabled',null,'floating-lyrics-toggle']
];
async function globalConfigPost(payload){const r=await fetch('/api/global-config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();if(!r.ok)throw new Error(d.error||'Global Config operation failed');return d}
function globalConfigStatus(text,bad=false){const node=document.getElementById('globalConfigStatus');if(node){node.textContent=text||'';node.style.color=bad?'#ff9ca8':'#b7e8af'}}
async function refreshGlobalConfigList(selected=''){
 const sel=document.getElementById('globalConfigProfiles');if(!sel)return;
 try{
  const r=await fetch('/api/global-config',{cache:'no-store'}),d=await r.json();if(!r.ok)throw new Error(d.error||'Global Config unavailable');
  sel.textContent='';for(const name of d.profiles||[]){const o=document.createElement('option');o.value=name;o.textContent=name;sel.appendChild(o)}if(selected&&[...sel.options].some(o=>o.value===selected))sel.value=selected;
  const choice=d.developer_choice||{},row=document.getElementById('globalConfigDeveloperChoiceRow'),file=document.getElementById('globalConfigDeveloperChoiceFile');if(row)row.hidden=!choice.available;if(file&&choice.available)file.textContent=choice.exists?'PAFPlayer.dcc found':'PAFPlayer.dcc not saved yet';
 }catch(e){globalConfigStatus(String(e),true)}
}
function globalConfigValue(profile,statusKey,settingKey){const state=profile&&profile.runtime_state&&typeof profile.runtime_state==='object'?profile.runtime_state:{};if(Object.prototype.hasOwnProperty.call(state,statusKey))return state[statusKey];const settings=profile&&profile.player_settings&&typeof profile.player_settings==='object'?profile.player_settings:{};return settingKey&&Object.prototype.hasOwnProperty.call(settings,settingKey)?settings[settingKey]:undefined}
function globalConfigApplyRuntime(profile){
 for(const [statusKey,settingKey] of globalConfigDirectTargets){const value=globalConfigValue(profile,statusKey,settingKey);if(value!==undefined&&value!==null)action('web-set:'+statusKey+':'+(typeof value==='boolean'?(value?'1':'0'):String(value)))}
 for(const [statusKey,settingKey,command] of globalConfigToggleTargets){const value=globalConfigValue(profile,statusKey,settingKey);if(value===undefined||value===null)continue;const current=latestState[statusKey];if(current!==undefined&&Boolean(current)!==Boolean(value))action(command)}
}
function globalConfigApplyWebPreferences(profile){
 const prefs=profile&&profile.web_preferences;if(!prefs||typeof prefs!=='object'||Array.isArray(prefs))return;
 serverWebPrefs={...prefs};for(const [key,value] of Object.entries(prefs)){try{localStorage.setItem(key,typeof value==='string'?value:JSON.stringify(value))}catch(e){}}
}
async function loadGlobalConfigProfile(name,developerChoice=false){
 if(!name)return; if(!confirm('Load complete Global Config profile “'+name+'”? Current PAFPlayer settings will be replaced.'))return;
 try{const d=await globalConfigPost({op:'load',name,developer_choice:developerChoice});globalConfigApplyWebPreferences(d.profile);globalConfigApplyRuntime(d.profile);globalConfigStatus('Loaded “'+name+'”; applying all live controls and refreshing the page…');setTimeout(()=>location.reload(),450)}catch(e){globalConfigStatus(String(e),true)}
}
function setupGlobalConfigUI(){
 const nameInput=document.getElementById('globalConfigProfileName'),select=document.getElementById('globalConfigProfiles');if(!nameInput||!select)return;
 document.getElementById('globalConfigSaveProfile').onclick=async()=>{let name=nameInput.value.trim();if(!name)name=(prompt('Global Config profile name:','profile 1')||'').trim();if(!name)return;try{await globalConfigPost({op:'save',name});nameInput.value='';await refreshGlobalConfigList(name);globalConfigStatus('Saved complete profile “'+name+'”.')}catch(e){globalConfigStatus(String(e),true)}};
 document.getElementById('globalConfigLoadProfile').onclick=()=>loadGlobalConfigProfile(select.value,false);
 document.getElementById('globalConfigDeleteProfile').onclick=async()=>{const name=select.value;if(!name||!confirm('Delete Global Config profile “'+name+'”?'))return;try{await globalConfigPost({op:'delete',name});await refreshGlobalConfigList();globalConfigStatus('Deleted profile “'+name+'”.')}catch(e){globalConfigStatus(String(e),true)}};
 document.getElementById('globalConfigSaveDeveloperChoice').onclick=async()=>{try{const result=await globalConfigPost({op:'save',developer_choice:true});await refreshGlobalConfigList();globalConfigStatus('Saved Developer’s Choice to '+result.saved_path+'. '+(result.backup_path?'Created and verified backup: '+result.backup_path:'No previous file needed a backup.'))}catch(e){globalConfigStatus(String(e),true)}};
 document.getElementById('globalConfigLoadDeveloperChoice').onclick=()=>loadGlobalConfigProfile("Developer's Choice",true);
 refreshGlobalConfigList();
}
let webBgProbeSerial=0;
function applyWebBackgroundGeometry(host,c,scale,naturalWidth=0,naturalHeight=0){
 const w=Math.max(1,host.clientWidth||window.innerWidth),h=Math.max(1,host.clientHeight||window.innerHeight),nw=Math.max(0,Number(naturalWidth)||0),nh=Math.max(0,Number(naturalHeight)||0);let sw=0,sh=0;
 if(nw>0&&nh>0){if(c.aspect==='stretch-h'){sw=w*scale;sh=sw*nh/nw}else if(c.aspect==='stretch-v'){sh=h*scale;sw=sh*nw/nh}else if(c.aspect==='stretch-both'){sw=w*scale;sh=h*scale}else if(c.aspect==='fit'){const fit=Math.min(w/nw,h/nh)*scale;sw=nw*fit;sh=nh*fit}else{sw=nw*scale;sh=nh*scale}host.style.backgroundSize=Math.max(1,sw)+'px '+Math.max(1,sh)+'px'}
 else{if(c.aspect==='stretch-v')host.style.backgroundSize='auto '+(100*scale)+'%';else if(c.aspect==='stretch-both')host.style.backgroundSize=(100*scale)+'% '+(100*scale)+'%';else if(c.aspect==='fit')host.style.backgroundSize=(100*scale)+'% auto';else if(c.aspect==='actual')host.style.backgroundSize='auto';else host.style.backgroundSize=(100*scale)+'% auto'}
 host.style.backgroundRepeat=c.tiling==='none'?'no-repeat':'repeat';
}
async function refreshWebBackgroundMatch(order,tileAll){
 if(tileAll){webBgMatchedIndex=null;return}const serial=++webBgInfoSerial;
 try{const d=await (await fetch('/api/background-art-info?g='+artGeneration+'&order='+encodeURIComponent(order),{cache:'no-store'})).json();if(serial===webBgInfoSerial)webBgMatchedIndex=(d.index===null||d.index===undefined)?null:Number(d.index)}catch(e){if(serial===webBgInfoSerial)webBgMatchedIndex=null}
}
function updateWebBackground(){
 const c=webBgConfig(),host=document.getElementById('webBackground');applyTitleBox(c);const signature=JSON.stringify([c.enabled,c.first,c.second,c.third,c.final,c.saturation,c.brightness,c.alpha,c.titleBleed,c.aspect,c.tiling,c.checkerboard,c.scale,artGeneration,webBgOverrideIndex]);if(signature===lastWebBackgroundSignature)return;lastWebBackgroundSignature=signature;const serial=++webBgProbeSerial;if(!c.enabled){host.style.backgroundImage='none';webBgMatchedIndex=null;return}const order=[c.first,c.second,c.third,c.final].join(',');const tileAll=c.tiling==='all';const imageUrl=webBgOverrideIndex!==null?('/api/background-art?g='+artGeneration+'&index='+webBgOverrideIndex):('/api/background-art?g='+artGeneration+'&order='+encodeURIComponent(order)+'&tile_all='+(tileAll?'1':'0')+'&checkerboard='+(c.checkerboard===false?'0':'1'));host.style.backgroundImage='url("'+imageUrl+'")';host.style.setProperty('--web-bg-sat',String(Math.max(0,c.saturation)/100));host.style.filter='saturate('+Math.max(0,c.saturation)/100+') brightness('+Math.max(0,c.brightness)/100+')';host.style.opacity=String(Math.max(0,Math.min(100,c.alpha))/100);const scale=Math.max(.05,Math.min(40,Number(c.scale)||.25));applyWebBackgroundGeometry(host,c,scale);if(webBgOverrideIndex!==null)webBgMatchedIndex=Number(webBgOverrideIndex);else refreshWebBackgroundMatch(order,tileAll);const probe=new Image();probe.onload=()=>{if(serial!==webBgProbeSerial)return;applyWebBackgroundGeometry(host,c,scale,probe.naturalWidth,probe.naturalHeight)};probe.src=imageUrl;
}

function webPlaylistEscape(text){return String(text??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
async function webQueuePaths(paths){
 try{
  const r=await fetch('/api/playlist-queue',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({paths})});const d=await r.json();
  if(!r.ok) throw new Error(d.error||'queue failed');
  setTimeout(()=>refreshWebPlaylistQueue(false),120);return d;
 }catch(e){const host=document.getElementById('webPlaylistQueueList');if(host)host.textContent='Queue error: '+e}
}
async function refreshWebPlaylistQueue(reset=false){
 const host=document.getElementById('webPlaylistQueueList');if(!host)return;
 if(reset)webPlaylistOffset=null;
 const qs=new URLSearchParams({limit:String(webPlaylistLimit)});if(webPlaylistOffset!==null)qs.set('offset',String(webPlaylistOffset));
 try{
  const r=await fetch('/api/playlist?'+qs.toString(),{cache:'no-store'}),d=await r.json();
  if(!d.active){host.textContent='No active playlist.';return}
  webPlaylistOffset=Number(d.offset||0);
  const items=Array.isArray(d.items)?d.items:[];
  const controls=document.createElement('div');controls.className='playlist-queue-page';
  const prev=document.createElement('button');prev.className='secondary-button';prev.textContent='← Earlier';prev.disabled=webPlaylistOffset<=0;prev.onclick=()=>{webPlaylistOffset=Math.max(0,webPlaylistOffset-webPlaylistLimit);refreshWebPlaylistQueue(false)};
  const page=document.createElement('span');
  page.textContent=' '+(items.length?(webPlaylistOffset+1).toLocaleString()+'–'+Math.min(Number(d.total||0),webPlaylistOffset+items.length).toLocaleString():'0')+' / '+Number(d.total||0).toLocaleString()+' ';
  const next=document.createElement('button');next.className='secondary-button';next.textContent='Later →';next.disabled=webPlaylistOffset+items.length>=Number(d.total||0);next.onclick=()=>{webPlaylistOffset+=webPlaylistLimit;refreshWebPlaylistQueue(false)};
  controls.append(prev,page,next);
  const frag=document.createDocumentFragment();frag.appendChild(controls);
  for(const item of items){const row=document.createElement('div');row.className='playlist-queue-row'+(item.current?' current':'')+(item.queued?' queued':'');row.title=item.path||'';
    const n=document.createElement('span');n.textContent=(item.queued?'⭐ ':'')+Number(item.index||0).toLocaleString();
    const name=document.createElement('span');name.textContent=item.label||item.filename||item.path||'';
    const btn=document.createElement('button');btn.className='secondary-button';btn.textContent=item.queued?'Queued next':'Play next';btn.disabled=!!item.queued;btn.title='Put this track into PAFPlayer’s explicit play-next queue';btn.onclick=()=>webQueuePaths([item.path]);
    row.append(n,name,btn);frag.appendChild(row)}
  host.replaceChildren(frag);
 }catch(e){host.textContent='Playlist/queue unavailable: '+e}
}
function setupWebPlaylistQueue(){
 const standalone=new URLSearchParams(location.search).get('view')==='playlist';
 document.documentElement.classList.toggle('playlist-only',standalone);
 if(standalone)document.title='PAFPlayer — Playlist';
 const open=document.getElementById('webPlaylistOpen');if(open)open.onclick=()=>window.open('/?view=playlist','_blank','noopener');
 const refresh=document.getElementById('webPlaylistRefresh'),reload=document.getElementById('webPlaylistReload'),remove=document.getElementById('webPlaylistRemoveCurrent'),clear=document.getElementById('webQueueClear');if(!refresh||!reload||!remove||!clear)return;
 refresh.onclick=()=>refreshWebPlaylistQueue(true);
 reload.onclick=()=>{action('force-shuffle-rebuild');setTimeout(()=>refreshWebPlaylistQueue(true),180)};
 remove.onclick=()=>{if(!confirm('Remove the currently playing track from the active playlist? The audio file itself will not be deleted.'))return;action('playlist-delete-current-web-confirmed');setTimeout(()=>refreshWebPlaylistQueue(true),180)};
 clear.onclick=async()=>{if(!confirm('Clear the explicit play-next queue?'))return;try{await fetch('/api/playlist-clear',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});setTimeout(()=>refreshWebPlaylistQueue(false),120)}catch(e){}};
 const initial=document.getElementById('webPlaylistQueueList');if(initial)initial.textContent=standalone?'Loading playlist…':'Press Refresh to load the playlist / play-next queue.';
 if(standalone)refreshWebPlaylistQueue(true);
}

let playbackMirrorSource=null;
function setupMirroredPlayback(sourceLayout){
  const host=document.getElementById('playbackMirrorHost');if(!host||!sourceLayout)return;
  playbackMirrorSource=sourceLayout;host.textContent='';
  let tokenIndex=0;
  sourceLayout.querySelectorAll('button,input,select').forEach(el=>{if(!el.dataset.playbackMirrorToken)el.dataset.playbackMirrorToken='pbm-'+(++tokenIndex)});
  const clone=sourceLayout.cloneNode(true);clone.id='playbackMirrorLayout';
  clone.querySelectorAll('[id]').forEach(el=>{el.id='mirror-'+el.id});
   clone.querySelectorAll('input[type=radio]').forEach(el=>{if(el.name)el.name='mirror-'+el.name});
  clone.querySelectorAll('button,input,select').forEach(el=>{
    const token=el.dataset.playbackMirrorToken;if(!token)return;
    const source=sourceLayout.querySelector('[data-playback-mirror-token="'+token+'"]');if(!source)return;
    if(el.classList.contains('multi-output-button')){
      el.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();const menu=el.closest('.multi-output-wrap')?.querySelector('.multi-output-menu');if(menu)menu.style.display=menu.style.display==='block'?'none':'block'});return;
    }
    if(el.tagName==='BUTTON'){
      el.addEventListener('click',event=>{event.preventDefault();source.click();setTimeout(syncMirroredPlaybackControls,0)});return;
    }
    if(el.type==='radio'&&typeof source.onclick==='function'){
      el.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();source.click();setTimeout(syncMirroredPlaybackControls,0)});return;
    }
    const copyToSource=()=>{if(el.type==='checkbox'||el.type==='radio')source.checked=el.checked;else source.value=el.value};
    if(el.type==='range')el.addEventListener('input',()=>{copyToSource();source.dispatchEvent(new Event('input',{bubbles:true}))});
    else el.addEventListener('change',()=>{copyToSource();source.dispatchEvent(new Event('change',{bubbles:true}))});
  });
  host.appendChild(clone);syncMirroredPlaybackControls();
}
function syncMirroredPlaybackControls(){
  if(!playbackMirrorSource)return;
  const mirror=document.getElementById('playbackMirrorLayout');if(!mirror)return;
  mirror.querySelectorAll('[data-playback-mirror-token]').forEach(el=>{
    const source=playbackMirrorSource.querySelector('[data-playback-mirror-token="'+el.dataset.playbackMirrorToken+'"]');if(!source)return;
    if('checked' in el)el.checked=source.checked;if('value' in el&&source.value!==undefined)el.value=source.value;
    el.disabled=!!source.disabled;el.hidden=!!source.hidden;el.title=source.title||el.title;
    if(source.tagName==='BUTTON'){el.textContent=source.textContent;el.style.display=source.style.display;el.className=source.className}
  });
  const status=document.getElementById('externalMediaStatusMirror'),sourceStatus=document.getElementById('externalMediaStatus');if(status&&sourceStatus)status.textContent=sourceStatus.textContent;
}

let configTabScrollRaf=0;
function setupConfigTabs(){
  const frame=document.getElementById('choicesFrame'),bar=document.getElementById('configTabs');if(!frame||!bar)return;
  const defs=[
    ['playbackMirrorSection','Playback'],['tagsSection','Tags'],['metadataMaintenanceSection','Metadata / Maintenance'],['lastFmSection','Last.fm'],['webKaraokeSection','Web Karaoke'],['artworkPopupSection','Artwork'],['idleBehaviorSection','Idle Behavior'],['floatingLyricsSection','Floating Lyrics'],
    ['playlistSection','Playlist'],['karaokeSection','Console Karaoke'],['visualizerSection','Console Visualizer'],['consoleAlertsSection','Console Alerts'],['errorDeliverySection','Error delivery'],['progressSection','Progress Bar'],
  ['webBackgroundSection','Webpage Background'],['experimentalSection','Experimental'],['workflowDiscordSection','Discord'],['workflowSecuritySection','Security'],['workflowMonitorSection','Monitoring'],['windowsMediaSection','Windows / Lock Screen'],['monkeyMoteSection','MonkeyMote'],['steamSection','Steam'],['globalConfigSection','Global Config'],['workflowLogsSection','Logs'],['warningsSection','Warnings'],['errorsSection','Errors']
  ];
  const entries=[];bar.textContent='';
  const orderedDefs=defs.filter(([id])=>{const section=document.getElementById(id);return section&&!section.hidden}).sort(([a],[b])=>{
    const first=document.getElementById(a),second=document.getElementById(b);
    return first===second?0:first.compareDocumentPosition(second)&Node.DOCUMENT_POSITION_FOLLOWING?-1:1;
  });
  for(const [id,label] of orderedDefs){const section=document.getElementById(id);const button=document.createElement('button');button.type='button';button.className='config-tab';button.setAttribute('role','tab');button.textContent=label;button.dataset.target=id;button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();const frameRect=frame.getBoundingClientRect(),sectionRect=section.getBoundingClientRect();const top=Math.max(0,frame.scrollTop+(sectionRect.top-frameRect.top)-bar.offsetHeight-8);for(const [,b] of entries){b.classList.toggle('active',b===button);b.setAttribute('aria-selected',b===button?'true':'false')}frame.scrollTop=top;requestAnimationFrame(refresh)});bar.appendChild(button);entries.push([section,button])}
  const refresh=()=>{configTabScrollRaf=0;const marker=frame.getBoundingClientRect().top+bar.offsetHeight+18;let active=entries[0]||null,best=Infinity;for(const entry of entries){const rect=entry[0].getBoundingClientRect();const d=rect.top<=marker?Math.abs(rect.top-marker):Math.abs(rect.top-marker)+120;if(d<best){best=d;active=entry}}if(frame.scrollTop+frame.clientHeight>=frame.scrollHeight-3)active=entries.at(-1)||active;for(const [,button] of entries){const on=!!active&&button===active[1];button.classList.toggle('active',on);button.setAttribute('aria-selected',on?'true':'false')}if(active)active[1].scrollIntoView({block:'nearest',inline:'nearest'})};
  frame.addEventListener('scroll',()=>{if(!configTabScrollRaf)configTabScrollRaf=requestAnimationFrame(refresh)},{passive:true});refresh();
  const openHash=()=>{let id;try{id=decodeURIComponent(location.hash.slice(1))}catch(_){return}const entry=entries.find(([section])=>section.id===id);if(entry)entry[1].click()};
  if(window.pafConfigHashHandler)window.removeEventListener('hashchange',window.pafConfigHashHandler);
  window.pafConfigHashHandler=openHash;window.addEventListener('hashchange',openHash);
  requestAnimationFrame(openHash);
}

function organizeControlSections(){
  const frame=document.getElementById('choicesFrame');
  if(frame&&!document.getElementById('warningsSection')){
    const section=document.createElement('section');section.id='warningsSection';section.className='group';
    const heading=document.createElement('h3');heading.textContent='⚠ Warnings';
    const content=document.createElement('div');content.id='djWarningsContent';content.setAttribute('role','status');content.textContent='Checking AI DJ warnings…';
    section.append(heading,content);frame.appendChild(section);
  }
  if(frame&&!document.getElementById('errorsSection')){
    const section=document.createElement('section');section.id='errorsSection';section.className='group';
    const heading=document.createElement('h3');heading.textContent='⚠ Errors';
    const view=document.createElement('iframe');view.src='/errors';view.title='Playback errors this session';view.loading='lazy';view.style.cssText='width:100%;height:380px;border:1px solid #536071;border-radius:7px;background:#0d1118';
    section.append(heading,view);frame.insertBefore(section,document.getElementById('warningsSection'));
  }
  for(const id of ['artworkPopupEmojiMaxxConfigButton','floatingLyricsEmojiMaxxConfigButton'])document.getElementById(id)?.remove();
  const karaoke=document.getElementById('karaokeSection');
  if(karaoke)for(const id of ['playlistSection','tagsSection']){const section=document.getElementById(id);if(section)karaoke.before(section)}
  const experimentalSection=document.getElementById('experimentalSection'),brokenSection=document.getElementById('brokenSection'),experimentalControls=document.getElementById('experimentalControls'),brokenControls=document.getElementById('brokenControls');
  if(experimentalSection){const heading=experimentalSection.querySelector('h3');if(heading&&!heading.textContent.trim().startsWith('🧪'))heading.textContent='🧪 '+heading.textContent.trim()}
  if(experimentalControls&&brokenControls)experimentalControls.append(...[...brokenControls.children]);
  if(brokenSection)brokenSection.hidden=true;
  const discord=document.getElementById('workflowDiscordSection');
  if(discord){
    const heading=discord.querySelector('h3');if(heading)heading.textContent='💬 Discord integration';if(experimentalSection)experimentalSection.after(discord);
  }
  const repair=document.getElementById('workflowRepairSection'),playlist=document.getElementById('playlistSection');
  if(repair&&playlist){const heading=repair.querySelector('h3');if(heading)heading.textContent='🛠 Playlist repair';if(!repair.querySelector('.playlist-repair-explanation')){const note=document.createElement('p');note.className='workflow-note playlist-repair-explanation';note.textContent='These tools repair playlist references when audio files move or are renamed. They update matching path entries; they do not rename unrelated music, delete tracks, or scan outside the configured playlist/library locations.';if(heading)heading.after(note);else repair.prepend(note)}playlist.append(...[...repair.children]);repair.remove()}
  const security=document.getElementById('workflowSecuritySection');
  if(security&&!security.querySelector('.library-roots-explanation')){const note=document.createElement('p');note.className='workflow-note library-roots-explanation';note.textContent='Library roots are trusted folders PAFPlayer may scan for media, missing-file repair candidates, and folder-monitor indexing. They do not move or upload files by themselves.';security.appendChild(note)}
  if(discord&&!document.getElementById('discordHelpButton')){const help=document.createElement('button');help.type='button';help.id='discordHelpButton';help.className='secondary-button';help.textContent='Help';help.title='Open step-by-step Discord profile activity setup help';help.onclick=()=>window.open('/help/discord','_blank','noopener');discord.appendChild(help)}
}

function attachChoiceButtons(key){
  const control=document.querySelector('[data-control-key="'+key+'"]'),select=document.getElementById('ctl-'+key);if(!control||!select)return;
  const item=(controlSchema.selects||[]).find(x=>x.key===key);if(!item)return;
  const oldMarks=control.querySelector('.choice-marks-stack');if(oldMarks)oldMarks.remove();
  const row=control.querySelector('.select-with-marks')||control;
  const tools=document.createElement('span');tools.className='choice-button-tools';
  const favLabel=document.createElement('label');favLabel.className='choice-mark';const fav=document.createElement('input');fav.type='checkbox';favLabel.append(fav,document.createTextNode('Fav'));
  const defLabel=document.createElement('label');defLabel.className='choice-mark';const def=document.createElement('input');def.type='radio';def.name='paf-default-'+key;defLabel.append(def,document.createTextNode('Def'));
  const marks=document.createElement('span');marks.className='choice-marks-stack';
  const cycle=document.createElement('button');cycle.type='button';cycle.className='secondary-button favorite-cycle-button';cycle.textContent='♻️';
  const favorites=new Set((item.favorite_values||[]).map(v=>String(v)));
  const raw=value=>{const o=[...select.options].find(x=>String(x.value)===String(value));return o?(o.dataset.rawLabel||o.textContent||String(value)):String(value)};
  const updateCycleTip=()=>{const tip='Click to cycle saved favorites. Right-click to cycle all choices sequentially. Double-click to restore the default mode of '+raw(item.default_value);cycle.dataset.tip=tip;cycle.setAttribute('aria-label',tip)};
  const sync=()=>{def.checked=String(item.default_value??'')===String(select.value);fav.checked=favorites.has(String(select.value));updateCycleTip();if(typeof select._pafSyncMarks==='function')select._pafSyncMarks();syncMirroredPlaybackControls()};
  async function save(kind,value,enabled){const r=await fetch('/api/choice-mark',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind,key,value:Number(value),enabled})});if(!r.ok)throw new Error('save failed');return await r.json()}
   def.title='Make the selected choice the persistent default';def.onclick=async event=>{const previous=item.default_value;if(String(previous??'')===String(select.value)){def.checked=true;return}event.preventDefault();const question=previous===undefined||previous===null?'Are you sure you want to set the default '+item.label+' to “'+raw(select.value)+'”?' :'Are you sure you want to change the default '+item.label+' from “'+raw(previous)+'” to “'+raw(select.value)+'”?';if(!confirm(question)){sync();setTimeout(sync,0);return}try{const data=await save('default',select.value,true);item.default_value=Number(data.default_value)}catch(error){alert('Could not save the default '+item.label+': '+String(error))}finally{sync();setTimeout(sync,0)}};
  fav.title='Add/remove the selected choice from favorites';fav.onchange=async()=>{const value=String(select.value),wanted=fav.checked,data=await save('favorite',value,wanted);favorites.clear();(data.favorite_values||[]).forEach(v=>favorites.add(String(v)));if(typeof select._pafReplaceFavoriteValues==='function')select._pafReplaceFavoriteValues(data.favorite_values||[]);else item.favorite_values=(data.favorite_values||[]);sync()};
  const cycleValues=(step,favoritesOnly)=>{const ordered=[...select.options].map(o=>String(o.value)).filter(v=>!favoritesOnly||favorites.has(v));if(!ordered.length)return;let i=ordered.indexOf(String(select.value));if(i<0)i=step>0?-1:0;i=(i+step+ordered.length)%ordered.length;select.value=ordered[i];select.dispatchEvent(new Event('change',{bubbles:true}));sync()};
  let clicks=0,timer=null;cycle.onclick=e=>{e.preventDefault();clicks++;clearTimeout(timer);if(clicks>=2){clicks=0;if(item.default_value!==undefined){select.value=String(item.default_value);select.dispatchEvent(new Event('change',{bubbles:true}));sync()}return}timer=setTimeout(()=>{clicks=0;cycleValues(1,true)},260)};cycle.oncontextmenu=e=>{e.preventDefault();clearTimeout(timer);clicks=0;cycleValues(1,false)};
  marks.append(favLabel,defLabel);tools.append(marks,cycle);row.appendChild(tools);const original=select.onchange;select.onchange=e=>{if(original)original.call(select,e);sync()};select._pafChoiceButtonSync=sync;sync();
}

const FREQUENCY_WARP_CUSTOM_PRESETS_KEY='paf-frequency-warp-custom-presets-v453';
let frequencyWarpEditorValues=[150,340,590,825],frequencyWarpDragIndex=-1;
function clampFrequencyWarpValues(values){const out=(values||[]).slice(0,4).map(v=>Math.round(Number(v)||0));while(out.length<4)out.push([150,340,590,825][out.length]);for(let i=0;i<4;i++){const lo=i?out[i-1]+10:10,hi=i<3?Math.max(lo,(out[i+1]||1000)-10):990;out[i]=Math.max(lo,Math.min(hi,out[i]))}return out}
function drawFrequencyWarpEditor(){
  frequencyWarpEditorValues=clampFrequencyWarpValues(frequencyWarpEditorValues);const canvas=document.getElementById('frequencyWarpEditor');if(!canvas)return;const ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;ctx.clearRect(0,0,w,h);ctx.strokeStyle='#24384b';ctx.lineWidth=1;for(let i=0;i<=10;i++){ctx.beginPath();ctx.moveTo(i*w/10,0);ctx.lineTo(i*w/10,h);ctx.stroke();ctx.beginPath();ctx.moveTo(0,i*h/10);ctx.lineTo(w,i*h/10);ctx.stroke()}const points=[[0,0],[.2,frequencyWarpEditorValues[0]/1000],[.4,frequencyWarpEditorValues[1]/1000],[.6,frequencyWarpEditorValues[2]/1000],[.8,frequencyWarpEditorValues[3]/1000],[1,1]];ctx.strokeStyle='#52e5b1';ctx.lineWidth=4;ctx.beginPath();points.forEach(([x,y],i)=>{const px=x*w,py=h-y*h;if(i)ctx.lineTo(px,py);else ctx.moveTo(px,py)});ctx.stroke();for(let i=1;i<5;i++){const [x,y]=points[i];ctx.fillStyle=i-1===frequencyWarpDragIndex?'#ffe36a':'#8bc8ff';ctx.beginPath();ctx.arc(x*w,h-y*h,8,0,Math.PI*2);ctx.fill()}const sliders=document.querySelectorAll('#frequencyWarpSliders input[type=range]');sliders.forEach((el,i)=>{el.value=String(frequencyWarpEditorValues[i]);const text=el.closest('.frequency-warp-slider')?.querySelector('output');if(text)text.value=(frequencyWarpEditorValues[i]/10).toFixed(1)+'%'});const explanation=document.getElementById('frequencyWarpExplanation');if(explanation){const first=(frequencyWarpEditorValues[0]/10).toFixed(1);explanation.textContent='Lowest '+first+'% of source frequencies occupies the left 20% of the display. Moving the first point down spreads lows more; moving it up compresses lows.'}
}
function frequencyWarpSavedProfiles(){const raw=webPrefGet(FREQUENCY_WARP_CUSTOM_PRESETS_KEY,{});return raw&&typeof raw==='object'&&!Array.isArray(raw)?raw:{}}
function refreshFrequencyWarpProfiles(selected=''){const sel=document.getElementById('frequencyWarpProfiles');if(!sel)return;const profiles=frequencyWarpSavedProfiles();sel.textContent='';for(const name of Object.keys(profiles).sort((a,b)=>a.localeCompare(b))){const o=document.createElement('option');o.value=name;o.textContent=name;sel.appendChild(o)}if(selected&&profiles[selected])sel.value=selected}
async function applyFrequencyWarpCustom(){frequencyWarpEditorValues=clampFrequencyWarpValues(frequencyWarpEditorValues);for(const [mark,value] of [[20,frequencyWarpEditorValues[0]],[40,frequencyWarpEditorValues[1]],[60,frequencyWarpEditorValues[2]],[80,frequencyWarpEditorValues[3]]])await action('web-set:frequency_warp_custom_'+mark+':'+value);await action('web-set:frequency_warp_preset:7');document.getElementById('frequencyWarpModal').classList.remove('open')}
function openFrequencyWarpCustomizer(){const raw=Array.isArray(latestState.frequency_warp_custom_permille)?latestState.frequency_warp_custom_permille:[latestState.frequency_warp_custom_20,latestState.frequency_warp_custom_40,latestState.frequency_warp_custom_60,latestState.frequency_warp_custom_80];frequencyWarpEditorValues=clampFrequencyWarpValues(raw.some(v=>v!==undefined)?raw:[150,340,590,825]);drawFrequencyWarpEditor();refreshFrequencyWarpProfiles();document.getElementById('frequencyWarpModal').classList.add('open')}
function setupFrequencyWarpCustomizer(){
  const control=document.querySelector('[data-control-key="frequency_warp_preset"]');if(!control)return;const row=control.querySelector('.select-with-marks')||control;const tools=document.createElement('span');tools.className='frequency-warp-tools';const button=document.createElement('button');button.className='secondary-button';button.textContent='Configure custom…';button.title='Open the frequency spread graph and named profiles';button.onclick=openFrequencyWarpCustomizer;tools.appendChild(button);row.appendChild(tools);
  const sliders=document.getElementById('frequencyWarpSliders');sliders.textContent='';[20,40,60,80].forEach((mark,index)=>{const row=document.createElement('label');row.className='frequency-warp-slider';const name=document.createElement('span');name.textContent='At display '+mark+'%';const input=document.createElement('input');input.type='range';input.min='10';input.max='990';input.step='1';input.setAttribute('aria-label','Source frequency percentile at display '+mark+'%');input.oninput=()=>{frequencyWarpEditorValues[index]=Number(input.value);frequencyWarpEditorValues=clampFrequencyWarpValues(frequencyWarpEditorValues);drawFrequencyWarpEditor()};const out=document.createElement('output');row.append(name,input,out);sliders.appendChild(row)});
  const canvas=document.getElementById('frequencyWarpEditor');const pick=e=>{const r=canvas.getBoundingClientRect(),x=(e.clientX-r.left)/Math.max(1,r.width);frequencyWarpDragIndex=Math.max(0,Math.min(3,Math.round((x-.2)/.2)));update(e)};const update=e=>{if(frequencyWarpDragIndex<0)return;const r=canvas.getBoundingClientRect(),y=1-(e.clientY-r.top)/Math.max(1,r.height);frequencyWarpEditorValues[frequencyWarpDragIndex]=Math.round(Math.max(.01,Math.min(.99,y))*1000);frequencyWarpEditorValues=clampFrequencyWarpValues(frequencyWarpEditorValues);drawFrequencyWarpEditor()};canvas.addEventListener('pointerdown',e=>{canvas.setPointerCapture(e.pointerId);pick(e)});canvas.addEventListener('pointermove',update);canvas.addEventListener('pointerup',e=>{frequencyWarpDragIndex=-1;drawFrequencyWarpEditor();try{canvas.releasePointerCapture(e.pointerId)}catch(_){ }});
  document.getElementById('frequencyWarpApply').onclick=applyFrequencyWarpCustom;document.getElementById('frequencyWarpReset').onclick=()=>{frequencyWarpEditorValues=[150,340,590,825];drawFrequencyWarpEditor()};document.getElementById('frequencyWarpClose').onclick=()=>document.getElementById('frequencyWarpModal').classList.remove('open');
  document.getElementById('frequencyWarpSaveProfile').onclick=()=>{let name=document.getElementById('frequencyWarpProfileName').value.trim();if(!name)name=(prompt('Custom frequency-warp preset name:','custom 1')||'').trim();if(!name)return;const profiles=frequencyWarpSavedProfiles();profiles[name]=clampFrequencyWarpValues(frequencyWarpEditorValues);webPrefSet(FREQUENCY_WARP_CUSTOM_PRESETS_KEY,profiles);refreshFrequencyWarpProfiles(name);document.getElementById('frequencyWarpProfileName').value=name};
  document.getElementById('frequencyWarpLoadProfile').onclick=()=>{const name=document.getElementById('frequencyWarpProfiles').value,values=frequencyWarpSavedProfiles()[name];if(!values)return;frequencyWarpEditorValues=clampFrequencyWarpValues(values);document.getElementById('frequencyWarpProfileName').value=name;drawFrequencyWarpEditor()};
  document.getElementById('frequencyWarpDeleteProfile').onclick=()=>{const name=document.getElementById('frequencyWarpProfiles').value;if(!name||!confirm('Delete custom frequency-warp preset “'+name+'”?'))return;const profiles=frequencyWarpSavedProfiles();delete profiles[name];webPrefSet(FREQUENCY_WARP_CUSTOM_PRESETS_KEY,profiles);refreshFrequencyWarpProfiles();document.getElementById('frequencyWarpProfileName').value=''};
}

function mountDesktopSolutionControls(target){
  const host=document.getElementById(target+'SolutionOptions');if(!host)return;
  const prefix=target+'Solution';
  host.innerHTML=`<label class="tiny-toggle"><input type="checkbox" id="${prefix}Show">Show Emojimaxx solutions</label>
    <label class="tiny-toggle solution-option">Solution size <input type="range" id="${prefix}Size" min="5" max="150" value="20"><output id="${prefix}SizeValue">20%</output> of original</label>
    <label class="tiny-toggle solution-option">Solution distance <input type="range" id="${prefix}Distance" min="-50" max="50" value="1"><output id="${prefix}DistanceValue">1%</output></label>
    <label class="tiny-toggle solution-option"><input type="checkbox" id="${prefix}Above">Over (off = under)</label>
    <label class="tiny-toggle solution-option"><input type="checkbox" id="${prefix}Inherit">Inherit lyric colors</label>
    <label class="tiny-toggle solution-option solution-color-option">Solution color <input type="color" id="${prefix}Color" value="#f4f8ff"></label>
    <label class="tiny-toggle solution-option">Opacity <input type="range" id="${prefix}Opacity" min="0" max="100" value="100"><output id="${prefix}OpacityValue">100%</output></label>`;
  for(const [setting,suffix] of [['show','Show'],['size','Size'],['distance','Distance'],['above','Above'],['inherit','Inherit'],['color','Color'],['opacity','Opacity']]){
    const input=document.getElementById(prefix+suffix);let timer=null;
    const send=()=>{const raw=input.type==='checkbox'?(input.checked?1:0):input.type==='color'?parseInt(input.value.slice(1),16):Number(input.value);action('web-set:'+target+'_solution_'+setting+':'+raw)};
    input.addEventListener(input.type==='range'?'input':'change',()=>{
      if(input.type==='range'){
        document.getElementById(prefix+suffix+'Value').textContent=input.value+'%';
        clearTimeout(timer);timer=setTimeout(send,90);
      }else send();
      if(setting==='show'||setting==='inherit')syncDesktopSolutionControls(target,{...latestState,[target+'_solution_'+setting]:input.checked});
    });
  }
}
function syncDesktopSolutionControls(target,s,disabled=false){
  const host=document.getElementById(target+'SolutionOptions');if(!host)return;
  const prefix=target+'Solution',defaults={show:true,size:20,distance:1,above:false,inherit:false,color:'#f4f8ff',opacity:100};
  for(const [setting,suffix] of [['show','Show'],['size','Size'],['distance','Distance'],['above','Above'],['inherit','Inherit'],['color','Color'],['opacity','Opacity']]){
    const input=document.getElementById(prefix+suffix);if(!input)continue;
    const value=s?.[target+'_solution_'+setting]??defaults[setting];
    if(document.activeElement!==input){if(input.type==='checkbox')input.checked=!!value;else input.value=setting==='color'?String(value):String(value)}
    input.disabled=!!disabled;
    const output=document.getElementById(prefix+suffix+'Value');if(output)output.textContent=input.value+'%';
  }
  const shown=document.getElementById(prefix+'Show').checked,inherit=document.getElementById(prefix+'Inherit').checked;
  for(const option of host.querySelectorAll('.solution-option'))option.hidden=!shown;
  const picker=host.querySelector('.solution-color-option');if(picker)picker.hidden=!shown||inherit;
}
function openExtendedEmojiMaxxConfiguration(target='web'){
  const section=document.getElementById(target==='artwork'?'artworkEmojimaxOptions':target==='floating'?'floatingEmojimaxOptions':'webEmojimaxOptions');
  if(section)section.scrollIntoView({behavior:'smooth',block:'start'});
  const toggle=document.getElementById(target==='artwork'?'artworkPopupEmojiMaxxButton':target==='floating'?'floatingLyricsEmojiMaxxButton':'webEmojimaxToggle');
  if(toggle)setTimeout(()=>toggle.focus(),180);
}

function setupConsoleTitleExperiment(){
  const test=document.getElementById('consoleTitleTest');if(test)test.onclick=()=>action('web-set:console_title_preview_seconds:5');
}

async function openLastFmProfile(){
  let url=String(latestState.lastfm_profile_url||'');if(url){window.open(url,'_blank','noopener');return}
  let username=(prompt('PAFPlayer does not know your Last.fm username yet. Enter it:','')||'').trim();if(!username)return;const pending=window.open('about:blank','_blank');
  try{const r=await fetch('/api/lastfm-profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username})});const d=await r.json();if(!r.ok)throw new Error(d.error||'Could not save Last.fm username');url=String(d.url||'');latestState.lastfm_profile_url=url;if(pending&&url)pending.location.href=url;else if(url)window.open(url,'_blank','noopener')}catch(e){if(pending)pending.close();alert(String(e))}
}

async function build(){
  controlSchema=await (await fetch('/api/control-schema')).json();
  setupConsoleTitleExperiment();
  setupResizableWebPanes();
  setupWebPlaylistQueue();
  setupGlobalConfigUI();
  mountDesktopSolutionControls('artwork');mountDesktopSolutionControls('floating');
  const autoExpand=document.getElementById('karaokeAutoExpand');
  karaokeAutoExpand=localStorage.getItem('paf-karaoke-auto-expand')==='1';autoExpand.checked=karaokeAutoExpand;
  autoExpand.onchange=()=>{karaokeAutoExpand=!!autoExpand.checked;localStorage.setItem('paf-karaoke-auto-expand',karaokeAutoExpand?'1':'0');const dock=document.getElementById('lyricDock');if(karaokeAutoExpand&&lyricReservedHeight<=0)lyricReservedHeight=Math.max(70,Number(localStorage.getItem('paf-web-lyric-height-px')||0),dock.clientHeight||0);dock.classList.toggle('auto-expand',karaokeAutoExpand);updateKaraokeReservation();fitKaraokeToDock()};
  for(const [id,key,property] of [['teenySolutions','teenySolutions','checked'],['teenySize','teenySize','value'],['teenyDistance','teenyDistance','value'],['teenyAbove','teenyAbove','checked'],['teenyInherit','teenyInherit','checked'],['teenyColor','teenyColor','value'],['teenyOpacity','teenyOpacity','value']]){
    document.getElementById(id).addEventListener(property==='checked'?'change':'input',e=>{webKaraokeSettings[key]=property==='checked'?!!e.target.checked:property==='value'&&e.target.type==='range'?Number(e.target.value):e.target.value;saveWebKaraokeSettings();updateTeenySolutions();updateKaraokeReservation()});
  }
  document.getElementById('editLyrButton').onclick=()=>action('web-edit-lyr');document.getElementById('editKarButton').onclick=()=>action('web-edit-kar');document.getElementById('webEmojimaxToggle').onchange=e=>{webKaraokeSettings.emojimax=!!e.target.checked;saveWebKaraokeSettings();renderWebLyric(rawWebLyric,true)};
  document.getElementById('webDecensorToggle').checked=!!webKaraokeSettings.decensor;document.getElementById('webDecensorToggle').onchange=e=>{webKaraokeSettings.decensor=!!e.target.checked;saveWebKaraokeSettings();renderWebLyric(rawWebLyric,true)};setupWebKaraokeGlow();
  const webKaraokeMaster=document.getElementById('webKaraokeMasterToggle');webKaraokeMaster.onchange=()=>{webKaraokeSettings.enabled=!!webKaraokeMaster.checked;saveWebKaraokeSettings();applyWebKaraokeEnabled()};applyWebKaraokeEnabled();updateWebEmojimaxToggle();
  const webKaraokeControls=document.getElementById('webKaraokeControls');for(const k of ['karaoke_style','karaoke_treatment']){const item=(controlSchema.selects||[]).find(x=>x.key===k);if(item)webKaraokeControls.appendChild(makeWebKaraokeSelect(k==='karaoke_style'?'style':'treatment',item))}
  const visualizer=document.getElementById('visualizerControls'), karaoke=document.getElementById('karaokeControls'), progress=document.getElementById('progressControls'), playback=document.getElementById('playbackControls'), idleBehavior=document.getElementById('idleBehaviorControls'), consoleAlerts=document.getElementById('consoleAlertsControls'), errorDelivery=document.getElementById('errorDeliveryControls'), experimentalSelects=document.getElementById('experimentalSelectControls');
  const visualizerMaster=document.getElementById('visualizerMasterToggle');
  visualizerMaster.onchange=()=>{action('drcs-visualizer-toggle');setTimeout(applyVisualizerLayerEnablement,0)};
  const visualizerBarsSwitch=document.getElementById('ctl-visualizer_bars_enabled'),visualizerBarArtworkSwitch=document.getElementById('ctl-art_color_bars'),visualizerBackgroundArtworkSwitch=document.getElementById('ctl-visualizer_background_artwork_enabled');
  visualizerBarsSwitch.onchange=()=>{applyVisualizerLayerEnablement();action('web-set:visualizer_bars_enabled:'+(visualizerBarsSwitch.checked?'1':'0'))};
  visualizerBarArtworkSwitch.onchange=()=>{applyVisualizerLayerEnablement();const mirror=document.getElementById('art-saturation-enabled-art_color_bars');if(mirror&&typeof mirror._pafSyncFromServer==='function')mirror._pafSyncFromServer(visualizerBarArtworkSwitch.checked);action('web-set:art_color_bars:'+(visualizerBarArtworkSwitch.checked?'1':'0'))};
  visualizerBackgroundArtworkSwitch.onchange=()=>{applyVisualizerLayerEnablement();action('web-set:visualizer_background_artwork_enabled:'+(visualizerBackgroundArtworkSwitch.checked?'1':'0'))};
  const consoleAlertsMaster=document.getElementById('ctl-console_alerts_enabled');consoleAlertsMaster.onchange=()=>{applyConsoleAlertsEnablement();action('web-set:console_alerts_enabled:'+(consoleAlertsMaster.checked?'1':'0'))};
  const karaokeMaster=document.getElementById('karaokeMasterToggle');
  karaokeMaster.onchange=()=>action('web-set:console_karaoke_enabled:'+(karaokeMaster.checked?'1':'0'));
  const progressMaster=document.getElementById('progressMasterToggle');
  progressMaster.onchange=()=>action('web-set:progress_bar_enabled:'+(progressMaster.checked?'1':'0'));
  for(const item of [...(controlSchema.selects||[]),...(controlSchema.sliders||[])]){
    if(item.custom_microtile)continue;
    let host=visualizer;
    if(['art_color_bar_blend_mode','visualizer_granularity','karaoke_visualizer_height_mode'].includes(item.key)) host=visualizer;
    else if(item.key==='floating_track_intro_seconds') host=document.getElementById('floatingLyricsControls');
    else if(['artist_throb_ms','song_throb_ms'].includes(item.key)) host=karaoke;
    else if(item.key==='artwork_seam_strategy') host=visualizer;
    else if(item.key==='progress_beat_visual_offset_ms') host=progress;
    else if(item.theme==='idle') host=idleBehavior;
    else if(item.experimental) host=experimentalSelects;
    else if(['external_media_resume_fade_seconds','inter_track_timing_ms','output_device','output_rate','output_bit_depth','speed_index','output_channels','volume','balance','locked_bass_reduction_percent','bass_boost_percent','visualizer_input_source'].includes(item.key)) host=playback;
    else if(item.key.startsWith('karaoke')) host=karaoke;
    else if(item.key.includes('progress')) host=progress;
    const control=item.key==='output_device'?makeMultiOutputDeviceControl(item):(item.min===undefined?makeSelect(item):makeSlider(item));
    host.appendChild(control);
    if(item.key==='visualizer_rows'){
      control.classList.add('visualizer-height-control');
      const rowsDefault=document.createElement('button');rowsDefault.className='secondary-button visualizer-height-default';rowsDefault.textContent='Default';rowsDefault.title='Restore the normal 16-row visualizer height';rowsDefault.onclick=()=>action('web-set:visualizer_rows:16');control.appendChild(rowsDefault);
      const rowsTallest=document.createElement('button');rowsTallest.className='secondary-button visualizer-height-tallest';rowsTallest.textContent='Set to tallest';rowsTallest.title='Fill the tallest usable height for the current console and HUD once';rowsTallest.onclick=()=>action('visualizer-rows-tallest');control.appendChild(rowsTallest);
    }
  }
  const playbackToggles=document.getElementById('playbackToggles');
  const experimental=document.getElementById('experimentalControls'),idleBehaviorToggles=document.getElementById('idleBehaviorToggles');
  (controlSchema.toggles||[]).forEach(item=>{
    if(item.hidden)return;
    if(['drcs_enabled','visualizer_bars_enabled','visualizer_background_artwork_enabled','console_alerts_enabled','art_color_blackness','art_color_bars','shuffle','loop'].includes(item.key)) return;
  const playbackKeys=['external_media_auto_pause','external_media_loudness_match','shuffle','loop','mm_inspired_renderer_enabled','bass_boost_enabled','reduce_bass_when_locked'];
    const karaokeKeys=['karaoke_emojimax','decensor_console_karaoke'];
    const webKaraokeKeys=['cursive_fix'];
    const visualizerKeys=['color_reverse','karaoke_visualizer_expansion_enabled','console_visualizer_volume_feedback_enabled'];
    const progressKeys=['progress_beat_reactive','progress_invert_order','progress_invert_palette'];
    const errorDeliveryKeys=['error_popup_enabled','error_windows_notification_enabled','error_sound_enabled'];
    const alertKeys=['alert_no_replaygain','alert_missing_artist','alert_missing_title','alert_missing_karaoke','alert_missing_lyrics','alert_missing_artwork','alert_unknown_year','alert_unknown_genre','alert_embedded_lyrics_mismatch','alert_non_default_speed'];
    const brokenKeys=['sixel_enabled','album_art_visualizer_enabled','karaoke_visualizer_overlay','art_color_karaoke'];
    let target=visualizer;
    if(['external_album_art_enabled','floating_lyrics_enabled','decensor_artwork_lyrics','decensor_floating_lyrics'].includes(item.key)) return;
    if(item.theme==='idle') target=idleBehaviorToggles;
    else if(item.key==='art_color_karaoke_sides') target=experimental;
    else if(brokenKeys.includes(item.key)) target=experimental;
    else if(playbackKeys.includes(item.key)) target=playbackToggles;
    else if(webKaraokeKeys.includes(item.key)) target=webKaraokeControls;
    else if(visualizerKeys.includes(item.key)) target=visualizer;
    else if(item.key==='adaptive_frequency_enabled') target=visualizer;
    else if(item.experimental) target=experimental;
    else if(item.key.startsWith('art_color_') || item.key==='drcs_enabled') target=visualizer;
    else if(progressKeys.includes(item.key)) target=progress;
    else if(alertKeys.includes(item.key)) target=consoleAlerts;
    else if(errorDeliveryKeys.includes(item.key)) target=errorDelivery;
    else if(karaokeKeys.includes(item.key)) target=karaoke;
    target.appendChild(makeToggle(item));
  });
  // All current experiments now live beside their related controls or in Broken.
  experimental.closest('.experimental-area').hidden=!experimental.children.length&&!experimentalSelects.children.length&&!document.getElementById('consoleTitleExperiment');
  organizeControlSections();
  {const current=document.getElementById('renameRepairCurrent'),others=document.getElementById('renameRepairOthers'),status=document.getElementById('renameRepairStatus');let loaded=false;
   const sync=()=>{others.disabled=!current.checked;if(!current.checked)others.checked=false};
   const save=async()=>{sync();try{const r=await fetch('/api/rename-repair-settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({repair_current:current.checked,repair_others:others.checked})}),v=await r.json();if(!r.ok)throw Error(v.error);status.textContent='Rename repair settings saved.'}catch(e){status.textContent=String(e)}};
   current.onchange=()=>{if(current.checked&&!loaded)others.checked=true;else if(current.checked)others.checked=true;loaded=true;save()};others.onchange=save;
   try{const r=await fetch('/api/rename-repair-settings'),v=await r.json();current.checked=!!v.repair_current;others.checked=!!v.repair_others;loaded=true;sync();status.textContent='F2 rename repair settings loaded.'}catch(e){status.textContent=String(e)}}
  for(const item of controlSchema.selects||[])if(item.choice_marks&&!item.custom_microtile)attachChoiceButtons(item.key);
  setupMicrotileModeControl('microtileBarsMode','microtileBarsTools','drcs_art_bar_microtile_mode','Bars');
  setupMicrotileModeControl('microtileBlacknessMode','microtileBlacknessTools','drcs_art_microtile_mode','Blackness');
  setupFrequencyWarpCustomizer();
  const paletteControl=document.querySelector('[data-control-key="color_style"]'),reversePalette=document.querySelector('[data-control-key="color_reverse"]');if(paletteControl&&reversePalette){const row=paletteControl.querySelector('.select-with-marks')||paletteControl;reversePalette.classList.add('palette-inline-reverse');row.appendChild(reversePalette)}
  const popupMaster=document.getElementById('artworkPopupMasterToggle'),popupKaraoke=document.getElementById('artworkPopupKaraokeToggle'),floatingMaster=document.getElementById('floatingLyricsMasterToggle');
  const popupBringTop=document.getElementById('artworkPopupBringTopButton'),popupBringCenter=document.getElementById('artworkPopupBringCenterButton'),popupTopmost=document.getElementById('artworkPopupTopmostButton'),popupConfig=document.getElementById('artworkPopupConfigButton'),popupEmojiMaxx=document.getElementById('artworkPopupEmojiMaxxButton'),popupEmojiMaxxConfig=document.getElementById('artworkPopupEmojiMaxxConfigButton'),popupDecensor=document.getElementById('artworkPopupDecensorButton');
  const floatingBringTop=document.getElementById('floatingLyricsBringTopButton'),floatingBringCenter=document.getElementById('floatingLyricsBringCenterButton'),floatingCenterVisualizer=document.getElementById('floatingLyricsCenterVisualizerButton'),floatingTopmost=document.getElementById('floatingLyricsTopmostButton'),floatingConfig=document.getElementById('floatingLyricsConfigButton'),floatingEmojiMaxx=document.getElementById('floatingLyricsEmojiMaxxButton'),floatingEmojiMaxxConfig=document.getElementById('floatingLyricsEmojiMaxxConfigButton'),floatingDecensor=document.getElementById('floatingLyricsDecensorButton');
  const pressed=button=>button&&button.getAttribute('aria-pressed')==='true';
  const setPressed=(button,on)=>{if(!button)return;button.classList.toggle('active-toggle',!!on);button.setAttribute('aria-pressed',on?'true':'false')};
  if(popupMaster)popupMaster.onchange=()=>{const on=popupMaster.checked;if(popupKaraoke)popupKaraoke.disabled=!on;for(const el of [popupBringTop,popupBringCenter,popupTopmost,popupConfig,popupEmojiMaxx,popupEmojiMaxxConfig,popupDecensor])if(el)el.disabled=!on||(el===popupConfig||el===popupEmojiMaxx||el===popupEmojiMaxxConfig||el===popupDecensor)&&!popupKaraoke.checked;action('external-album-art-toggle')};
  if(floatingMaster)floatingMaster.onchange=()=>action('floating-lyrics-toggle');
  if(popupBringTop){popupBringTop.onclick=()=>action('external-album-art-foreground');popupBringTop.title='Bring the artwork pop-up to the top. Keyboard shortcut: Ctrl+Alt+A.'}
  if(floatingBringTop)floatingBringTop.onclick=()=>action('external-floating-lyrics-foreground');
  if(popupBringCenter)popupBringCenter.onclick=()=>action('external-album-art-center');
  if(floatingBringCenter)floatingBringCenter.onclick=()=>action('external-floating-lyrics-center');
  if(floatingCenterVisualizer)floatingCenterVisualizer.onclick=()=>action('external-floating-lyrics-console-center');
  const barBlend=document.querySelector('[data-control-key="art_color_bar_blend_mode"]'),barOpacity=document.querySelector('[data-control-key="art_color_bar_opacity"]');
  if(barBlend&&barOpacity)barBlend.insertAdjacentElement('afterend',barOpacity);
  if(popupTopmost)popupTopmost.onchange=()=>action('web-set:art_topmost:'+(popupTopmost.checked?'1':'0'));
  if(floatingTopmost)floatingTopmost.onchange=()=>action('web-set:floating_topmost:'+(floatingTopmost.checked?'1':'0'));
  const floatingOpacity=document.getElementById('floatingLyricsOpacity'),floatingOpacityValue=document.getElementById('floatingLyricsOpacityValue');
  if(floatingOpacity){floatingOpacity.oninput=()=>{if(floatingOpacityValue)floatingOpacityValue.textContent=floatingOpacity.value+'%'};floatingOpacity.onchange=()=>action('web-set:floating_opacity:'+floatingOpacity.value)}
  for(const [control,key] of [[popupEmojiMaxx,'popup_emojimax'],[floatingEmojiMaxx,'popup_emojimax']])if(control)control.onchange=()=>action('web-set:'+key+':'+(control.checked?'1':'0'));
  if(popupDecensor)popupDecensor.onchange=()=>action('web-set:decensor_artwork_lyrics:'+(popupDecensor.checked?'1':'0'));
  if(floatingDecensor)floatingDecensor.onchange=()=>action('web-set:decensor_floating_lyrics:'+(floatingDecensor.checked?'1':'0'));
  if(popupKaraoke)popupKaraoke.onchange=()=>{const enabled=popupMaster?popupMaster.checked:true;for(const el of [popupConfig,popupEmojiMaxx,popupEmojiMaxxConfig,popupDecensor])if(el)el.disabled=!enabled||!popupKaraoke.checked;action('artwork-karaoke-toggle')};
  if(popupConfig)popupConfig.onclick=()=>action('artwork-karaoke-config');
  if(floatingConfig)floatingConfig.onclick=()=>action('floating-karaoke-config');
  if(popupEmojiMaxxConfig)popupEmojiMaxxConfig.onclick=()=>openExtendedEmojiMaxxConfiguration('artwork');
  if(floatingEmojiMaxxConfig)floatingEmojiMaxxConfig.onclick=()=>openExtendedEmojiMaxxConfiguration('floating');
  // V247 progress layout: style/type is the leftmost control; the illumination
  // enable sits immediately beside its Beat detection selector, followed by the
  // treatment. This makes the dependency visually obvious instead of scattering
  // the checkbox away from the detector it enables.
  const progressStyleControl=progress.querySelector('[data-control-key="progress_style"]'),progressDetectorControl=progress.querySelector('[data-control-key="progress_beat_detector"]'),beatReactiveControl=progress.querySelector('[data-control-key="progress_beat_reactive"]'),progressTreatmentControl=progress.querySelector('[data-control-key="progress_beat_treatment"]'),progressOverlayControl=progress.querySelector('[data-control-key="progress_beat_overlay_mode"]');
  for(const node of [progressStyleControl,beatReactiveControl,progressDetectorControl,progressTreatmentControl,progressOverlayControl])if(node)progress.appendChild(node);
  const progressDemo=document.createElement('label');progressDemo.className='toggle progress-demo-switch';progressDemo.title='Demo: enabled bar, beat illumination, spectral-flux detector, Flash Full treatment, and style 1. Turning it off restores your exact prior settings.';const progressDemoCheck=document.createElement('input');progressDemoCheck.type='checkbox';progressDemoCheck.id='progressDemoToggle';const progressDemoText=document.createElement('span');progressDemoText.textContent='Demo: Style 1 + Spectral Flux + Beat illumination + Flash Full';progressDemo.append(progressDemoCheck,progressDemoText);
  const setProgressDemoLock=locked=>{progressDemoActive=!!locked;const section=document.getElementById('progressSection');if(section)section.classList.toggle('progress-demo-active',progressDemoActive);for(const el of document.querySelectorAll('#progressControls input:not(#progressDemoToggle),#progressControls select,#progressControls button:not(#progressDemoToggle),#progressMasterToggle'))el.disabled=progressDemoActive};
  progressDemoCheck.onchange=async()=>{
    progressDemoCheck.disabled=true;
    if(progressDemoCheck.checked){
      progressDemoSnapshot={progress_bar_enabled:!!latestState.progress_bar_enabled,progress_beat_reactive:!!latestState.progress_beat_reactive,progress_beat_detector:Number(latestState.progress_beat_detector||1),progress_beat_treatment:Number(latestState.progress_beat_treatment||3),progress_style:Number(latestState.progress_style||1)};
      for(const command of ['web-set:progress_bar_enabled:1','web-set:progress_beat_reactive:1','web-set:progress_beat_detector:5','web-set:progress_beat_treatment:3','web-set:progress_style:1'])await action(command);setProgressDemoLock(true);
    }else{
      const old=progressDemoSnapshot;setProgressDemoLock(false);if(old){for(const [key,value] of Object.entries(old))await action('web-set:'+key+':'+(typeof value==='boolean'?(value?1:0):value))}progressDemoSnapshot=null;
    }
    progressDemoCheck.disabled=false;
  };
  if(progressTreatmentControl)progressTreatmentControl.after(progressDemo);else progress.appendChild(progressDemo);
  // V448: explicit Playback rows, matching the requested visual grouping.
  // Row 1: Device → Channels → Speaker Expansion Matrix → Disable speaker expansion.
  // Row 2: Rate/bit depth → Playback speed → Balance.
  // Row 3: External-media pause → loudness matching → automatic resume fade.
  // Row 4: Visualizer input.  Rows remain flex-wrapped for narrow browser widths.
  for(const key of ['output_device','output_rate','output_bit_depth','output_channels','volume','speed_index','balance','locked_bass_reduction_percent','bass_boost_percent','external_media_resume_fade_seconds','inter_track_timing_ms','visualizer_input_source']){
    const node=playback.querySelector('[data-control-key="'+key+'"]');if(node)playback.appendChild(node);
  }
  const rateControl=playback.querySelector('[data-control-key="output_rate"]'),depthControl=playback.querySelector('[data-control-key="output_bit_depth"]');
  if(rateControl&&depthControl){const group=document.createElement('div');group.className='control-item';group.dataset.controlKey='output-format';group.title='Output sample rate and PCM bit depth';const label=document.createElement('label');label.textContent='Rate:';label.title=group.title;const pair=document.createElement('div');pair.style.display='flex';pair.style.gap='6px';pair.style.alignItems='center';const rate=rateControl.querySelector('select'),depth=depthControl.querySelector('select');if(rate){rate.title='Output sample rate';pair.appendChild(rate)}if(depth){depth.title='Output bit depth';pair.appendChild(depth)}group.append(label,pair);rateControl.replaceWith(group);depthControl.remove()}
  const matrixButton=document.createElement('button');matrixButton.id='speakerExpansionMatrixButton';matrixButton.className='secondary-button';matrixButton.textContent='Speaker Expansion Matrix';matrixButton.title='Edit stereo→5.1/7.1/Atmos coefficients and discrete speaker mutes. Applying a multichannel matrix uses PAFPlayer’s native WAVEFORMATEXTENSIBLE speaker-mapped output so mute/value changes reach the intended physical channels.';matrixButton.onclick=openMatrixEditor;playback.appendChild(matrixButton);
  const multiOutLatencyButton=document.createElement('button');multiOutLatencyButton.id='multiOutLatencyButton';multiOutLatencyButton.className='secondary-button multiout-latency-button';multiOutLatencyButton.textContent='Multi-Out Latency';multiOutLatencyButton.title='Align two or more simultaneous output devices with per-endpoint millisecond delay and EXP microphone-assisted acoustic Auto sync.';multiOutLatencyButton.style.display='none';multiOutLatencyButton.onclick=openMultiOutLatency;playback.appendChild(multiOutLatencyButton);setupMultiOutLatencyUI();

  const playbackSection=playback.closest('.section-playback');
  const playbackLayout=document.createElement('div');playbackLayout.id='playbackLayout';playbackLayout.className='playback-layout';
  const makePlaybackRow=id=>{const row=document.createElement('div');row.id=id;row.className='playback-row';playbackLayout.appendChild(row);return row};
  const row1=makePlaybackRow('playbackRow1'),row2=makePlaybackRow('playbackRow2'),row3=makePlaybackRow('playbackRow3'),row4=makePlaybackRow('playbackRow4'),row5=makePlaybackRow('playbackRow5'),row6=makePlaybackRow('playbackRow6'),row7=makePlaybackRow('playbackRow7');
  const playbackNode=key=>playbackSection.querySelector('[data-control-key="'+key+'"]');
  const movePlayback=(row,key)=>{const node=playbackNode(key);if(node)row.appendChild(node)};

  movePlayback(row1,'output_device');
  // Multi-Out Latency is conditionally visible and belongs to the Device cluster.
  row1.appendChild(multiOutLatencyButton);
  movePlayback(row1,'output_channels');
  row1.appendChild(matrixButton);
  movePlayback(row1,'mm_inspired_renderer_enabled');

  movePlayback(row2,'volume');
  const volumeControl=playbackNode('volume');if(volumeControl){volumeControl.style.flex='2 1 560px';const volumeSlider=volumeControl.querySelector('input[type="range"]');if(volumeSlider)volumeSlider.style.minWidth='360px'}
  movePlayback(row2,'output-format');
  movePlayback(row2,'speed_index');
  movePlayback(row2,'balance');

  movePlayback(row3,'bass_boost_enabled');
  movePlayback(row3,'bass_boost_percent');

  movePlayback(row4,'external_media_auto_pause');
  movePlayback(row4,'external_media_loudness_match');
  movePlayback(row4,'external_media_resume_fade_seconds');
  movePlayback(row4,'inter_track_timing_ms');

  movePlayback(row5,'reduce_bass_when_locked');
  movePlayback(row5,'locked_bass_reduction_percent');

  movePlayback(row6,'visualizer_input_source');
  const shuffleLifetime=document.createElement('div');shuffleLifetime.className='control-item';shuffleLifetime.dataset.controlKey='shuffle_expiration_hours';shuffleLifetime.title='Age of a saved history shuffle before PAFPlayer rebuilds it. Zero always rebuilds.';const shuffleLifetimeLabel=document.createElement('label');shuffleLifetimeLabel.htmlFor='shuffleExpirationHours';shuffleLifetimeLabel.textContent='Fresh shuffle after:';const shuffleLifetimeInput=document.createElement('input');shuffleLifetimeInput.id='shuffleExpirationHours';shuffleLifetimeInput.type='number';shuffleLifetimeInput.min='0';shuffleLifetimeInput.max='168';shuffleLifetimeInput.step='0.25';shuffleLifetimeInput.value='72';shuffleLifetimeInput.style.width='6em';shuffleLifetimeInput.onchange=()=>action('web-set:shuffle_expiration_hours:'+shuffleLifetimeInput.value);const shuffleLifetimeUnit=document.createElement('span');shuffleLifetimeUnit.textContent='hours';const shuffleLifetimeValue=document.createElement('span');shuffleLifetimeValue.className='shuffle-lifetime-value';shuffleLifetimeValue.append(shuffleLifetimeInput,shuffleLifetimeUnit);shuffleLifetime.append(shuffleLifetimeLabel,shuffleLifetimeValue);row7.appendChild(shuffleLifetime);
  playbackSection.insertBefore(playbackLayout,document.getElementById('externalMediaStatus'));
  setupMirroredPlayback(playbackLayout);
  const rowsControl=visualizer.querySelector('[data-control-key="visualizer_rows"]'),autoRowsControl=visualizer.querySelector('[data-control-key="visualizer_rows_auto_tallest"]'),truncateControl=visualizer.querySelector('[data-control-key="truncate_visualizer_rows"]');if(rowsControl&&autoRowsControl)rowsControl.appendChild(autoRowsControl);if(rowsControl&&truncateControl)rowsControl.after(truncateControl);
  const refreshConsoleButton=document.createElement('button');refreshConsoleButton.id='refreshConsoleScreenButton';refreshConsoleButton.className='secondary-button';refreshConsoleButton.textContent='↻ Refresh console screen';refreshConsoleButton.title='Force a clean repaint of the terminal HUD and console visualizer';refreshConsoleButton.onclick=()=>action('redraw-ui');visualizer.appendChild(refreshConsoleButton);
  setupArtSaturationAutoslide();
  applyVisualizerLayerEnablement();applyConsoleAlertsEnablement();
  const transport=document.querySelector('.transport');
  const transportShuffle=document.getElementById('transportShuffle'), transportLoop=document.getElementById('transportLoop');
  const wireOrderButton=(node,next,prev,double)=>{if(!node)return;let clicks=0,timer=null;node.onclick=()=>{clicks++;clearTimeout(timer);timer=setTimeout(()=>{if(clicks===1)action(prev);else if(clicks===2)action(double);clicks=0},250)};node.addEventListener('contextmenu',event=>{event.preventDefault();clearTimeout(timer);clicks=0;action(next)})};
  wireOrderButton(transportLoop,'repeat-next','repeat-prev','repeat-double');wireOrderButton(transportShuffle,'shuffle-next','shuffle-prev','shuffle-double');
  for(const [index,[label,name,title]] of [['−','speed-down','Slower'],['+','speed-up','Faster']].entries()){
    const button=document.createElement('button');button.className='wawi '+(name==='speed-up'?'wawi-speed-plus':'wawi-speed-minus');button.textContent=label;button.title=title;
    if(index===0) button.style.marginLeft='16px';
    button.onclick=()=>action(name);transport.appendChild(button);
    button.addEventListener('contextmenu',event=>{event.preventDefault();clearTimeout(button._speedClickTimer);button._speedClicks=(button._speedClicks||0)+1;button._speedClickTimer=setTimeout(()=>{if(button._speedClicks===1)action(name);else {const normal=[...document.querySelectorAll('#ctl-speed_index option')].find(o=>o.textContent==='1×');action('web-set:speed_index:'+(normal?normal.value:'0'))}button._speedClicks=0},250)});
  }
  const speedSource=document.getElementById('ctl-speed_index');
  if(speedSource){
    const speedSelect=document.createElement('select');speedSelect.id='transportSpeedSelect';speedSelect.className='wawi-speed-select';speedSelect.title='Playback speed';
    for(const option of speedSource.options){const copy=document.createElement('option');copy.value=option.value;copy.textContent=option.textContent;speedSelect.appendChild(copy)}
    speedSelect.value=speedSource.value;
    speedSelect.onchange=()=>action('web-set:speed_index:'+speedSelect.value);
    const plus=transport.querySelector('.wawi-speed-plus');
    if(plus)plus.before(speedSelect);else transport.appendChild(speedSelect);
  }
  const volume=document.createElement('input');volume.id='transportVolume';volume.type='range';volume.min='0';volume.max='400';volume.step='5';volume.value='100';volume.title='Volume';volume.style.width='220px';volume.style.marginLeft='16px';
  let volumeTimer=null;volume.oninput=()=>{clearTimeout(volumeTimer);volumeTimer=setTimeout(()=>action('web-set:volume:'+volume.value),80)};
  transport.appendChild(volume);
  const karaokeSpacer=document.createElement('span');karaokeSpacer.style.flex='1';transport.appendChild(karaokeSpacer);
  for(const [label,delta] of [['K−',-2],['K+',2]]){const button=document.createElement('button');button.className='wawi';button.textContent=label;button.title='Adjust karaoke display timing by 0.2 seconds';button.onclick=()=>action('web-set:karaoke_offset_delta:'+delta);transport.appendChild(button)}

  const groups=await (await fetch('/api/actions')).json();
  const host=document.getElementById('controls');
  // V243: the bottom rainbow action area is ONLY for commands that do not
  // already have a first-class control above. Keep /api/actions complete for
  // external clients, but do not render duplicate volume/speed/output/visualizer,
  // Console Karaoke Emojimaxx, art-popup toggle, or Playlist Control actions.
  const skipOtherGroups=new Set(['Playback','Volume / Speed','Output / Visualizer']);
  const skipOtherActions=new Set(['karaoke-previous','karaoke-next','karaoke-emoji-toggle','external-album-art-toggle','force-shuffle-rebuild','playlist-delete-current-web-confirmed','redraw-ui']);
  for(const [groupIndex,group] of groups.entries()){
    if(skipOtherGroups.has(group.name)) continue;
    const uniqueItems=(group.items||[]).filter(item=>!skipOtherActions.has(item.action));
    if(!uniqueItems.length)continue;
    const wrap=document.createElement('div');wrap.className='group';
    const displayName=group.name==='Lyrics / Artwork'?'Artwork Actions':group.name==='Playlist / Metadata'?'Metadata / Maintenance':group.name;
    const heading=document.createElement('h3');heading.textContent=displayName;heading.title=displayName+' controls';wrap.appendChild(heading);if(displayName==='Artwork Actions')wrap.id='artworkActionsSection';if(displayName==='Metadata / Maintenance')wrap.id='metadataMaintenanceSection';if(displayName==='Last.fm')wrap.id='lastFmSection';
    const buttons=document.createElement('div');buttons.className='buttons';
    for(const [buttonIndex,item] of uniqueItems.entries()){
      const b=document.createElement('button');b.id='other-action-'+item.action;b.className='secondary-button other-action-button';b.style.setProperty('--action-hue',String((groupIndex*83+buttonIndex*31)%360));b.textContent=(item.action==='web-view-lastfm-profile'?'↗ ':'⚡ ')+item.label;b.title=item.tooltip||item.label;b.onclick=()=>{if(item.action==='web-view-lastfm-profile')openLastFmProfile();else action(item.action)};buttons.appendChild(b)
    }
    wrap.appendChild(buttons);if(displayName==='Last.fm'){const note=document.createElement('p');note.className='note';note.textContent='The profile button opens your saved Last.fm account. If no username is saved, PAFPlayer asks for one on the player computer. Scrobbling requires Last.fm credentials configured on that computer.';wrap.appendChild(note)}host.appendChild(wrap);
  }
  {const artworkActions=document.getElementById('artworkActionsSection'),artwork=document.getElementById('artworkPopupSection');if(artworkActions&&artwork)artwork.append(...[...artworkActions.children]);artworkActions?.remove();const metadata=document.getElementById('metadataMaintenanceSection'),tags=document.getElementById('tagsSection'),lastFm=document.getElementById('lastFmSection');if(metadata&&tags)tags.after(metadata);if(lastFm&&(metadata||tags))(metadata||tags).after(lastFm)}
}

function progressLyricTimeAt(ratio,duration,sample){
  const position=Math.max(0,Math.min(1,ratio))*duration;
  const sourceOffset=Number(sample.lyricPosition||0)-Number(sample.position||0);
  return Math.max(0,position+sourceOffset+Number(sample.karaokeOffset||0));
}
function progressLyricPreviewAt(timeline,position){
  const empty={text:'',faded:false};
  if(!Array.isArray(timeline)||!Number.isFinite(position)||position<0)return empty;
  let lo=0,hi=timeline.length;
  while(lo<hi){const mid=(lo+hi)>>>1;if(Number(timeline[mid][0])<=position)lo=mid+1;else hi=mid}
  const index=lo-1;
  if(index<0)return empty;
  const current=String(timeline[index][1]??'').trim();
  if(current)return {text:current,faded:false};
  const blankAt=Number(timeline[index][0]);
  if(!Number.isFinite(blankAt)||position-blankAt>5)return empty;
  for(let previous=index-1;previous>=0;previous--){
    const text=String(timeline[previous][1]??'').trim();
    if(text)return {text,faded:true};
  }
  return empty;
}
const progressHost=document.getElementById('progress');
const progressLyricTooltip=document.getElementById('progressLyricTooltip');
function hideProgressLyricTooltip(){progressLyricTooltip.hidden=true}
function showProgressLyricTooltip(event){
  const rect=progressHost.getBoundingClientRect(),sample=webClockSample;
  const duration=Number(sample.duration||0);
  if(!(duration>0)||!(rect.width>0)){hideProgressLyricTooltip();return}
  const ratio=Math.max(0,Math.min(1,(event.clientX-rect.left)/rect.width));
  const position=ratio*duration;
  const preview=progressLyricPreviewAt(webLyricTimeline,progressLyricTimeAt(ratio,duration,sample));
  progressLyricTooltip.querySelector('.preview-time').textContent=fmtTime(position);
  const lyric=progressLyricTooltip.querySelector('.preview-lyric');
  lyric.textContent=preview.text||'';
  lyric.classList.toggle('faded',preview.faded);
  progressLyricTooltip.hidden=false;
  const left=Math.max(8,Math.min(window.innerWidth-progressLyricTooltip.offsetWidth-8,event.clientX-progressLyricTooltip.offsetWidth/2));
  const above=event.clientY-progressLyricTooltip.offsetHeight-12;
  progressLyricTooltip.style.left=left+'px';
  progressLyricTooltip.style.top=(above>=8?above:Math.min(window.innerHeight-progressLyricTooltip.offsetHeight-8,event.clientY+12))+'px';
}
progressHost.addEventListener('pointerenter',showProgressLyricTooltip);
progressHost.addEventListener('pointermove',showProgressLyricTooltip);
progressHost.addEventListener('pointerleave',hideProgressLyricTooltip);
progressHost.addEventListener('pointercancel',hideProgressLyricTooltip);
window.addEventListener('blur',hideProgressLyricTooltip);
document.addEventListener('visibilitychange',()=>{if(document.hidden)hideProgressLyricTooltip()});
progressHost.addEventListener('click',event=>{
  const rect=event.currentTarget.getBoundingClientRect();
  const ratio=Math.max(0,Math.min(1,(event.clientX-rect.left)/Math.max(1,rect.width)));
  const duration=Number(webClockSample.duration||0),now=performance.now();
  if(duration>0){const position=ratio*duration;webSeekPending={position,at:now,trackPath:String(latestState?.track?.path||'')};webClockSample={...webClockSample,position,lyricPosition:position,speed:Number(webClockSample.speed||1),at:now,validUntil:now+4000};
    const bar=document.getElementById('bar'),time=document.getElementById('time');if(bar)bar.style.width=(ratio*100).toFixed(2)+'%';if(time)time.textContent=(webClockSample.paused?'⏸':'▶')+' '+fmtTime(position)+' / '+fmtTime(duration)+'   '+Math.round(ratio*100)+'%';}
  action('web-seek-ratio:'+ratio.toFixed(6));
});

function updateTrackLinks(track,isLocal){
 const pathHost=document.getElementById('path'),download=document.getElementById('trackDownload');
 const pathText=track.path||'';
 if(pathHost.textContent!==pathText)pathHost.textContent=pathText;
 download.hidden=!pathText;
 pathHost.onclick=null;
 if(!pathText){pathHost.removeAttribute('href');pathHost.removeAttribute('download');pathHost.title='';return;}
 pathHost.href=isLocal?'#':'/api/audio/download';
 pathHost.title=isLocal?'Open this track’s folder in Explorer':'Download this audio file';
 if(isLocal){
  pathHost.removeAttribute('download');
  pathHost.onclick=event=>{event.preventDefault();action('web-open-track-folder');};
 }else pathHost.setAttribute('download','');
}
async function tick(){
 try{
  const clockRequestAt=performance.now();
  const response=await fetch('/api/status',{cache:'no-store'});
  const s=await response.json(),clockReceivedAt=performance.now();
  const errorBadge=document.getElementById('sessionErrorBadge'),errorCount=Math.max(0,Number(s.session_error_count||0));if(errorBadge){errorBadge.hidden=!errorCount;errorBadge.textContent='⚠ '+errorCount;errorBadge.onclick=()=>{document.getElementById('choicesFrame')?.scrollIntoView({block:'nearest'});document.querySelector('#configTabs [data-target=\"errorsSection\"]')?.click()};}
  const serverNow=Number(response.headers.get('X-PAF-Server-Time')||0);
  const clockAge=serverNow?Math.max(0,Math.min(2,serverNow-Number(s.lyric_clock_epoch||serverNow)))+(clockReceivedAt-clockRequestAt)/2000:0;
  latestState=s;
  if(typeof s.web_visualizer_enabled==='boolean' && s.web_visualizer_enabled!==webVisualizerEnabled) await setWebVisualizerEnabled(s.web_visualizer_enabled,false);
  if(loadedPlayerVersion===null) loadedPlayerVersion=String(s.version||'');
  else if(String(s.version||'') && String(s.version)!==loadedPlayerVersion){location.reload();return;}
  const m=s.metadata||{},t=s.track||{};
  if(webSeekPending&&webSeekPending.trackPath&&String(t.path||'')!==webSeekPending.trackPath)webSeekPending=null;
  const act=String(m.Act||m.Artist||'').trim();
  const song=String(m.Song||m.Title||t.filename||'Waiting for playback…').trim();
  const original=String(m['Original artist']||m['Original Artist']||'').trim();
  let webTitle=(act?act+' - ':'')+song;
  if(original && (!act || original.toLocaleLowerCase()!==act.toLocaleLowerCase())) webTitle+=' (by '+original+')';
  const songTitleHost=document.getElementById('songTitle');
  if(songTitleHost.textContent!==webTitle){songTitleHost.textContent=webTitle;requestAnimationFrame(fitWebSongTitle);}
  const sharedWindowTitle=String(s.window_title||webTitle||'PAFPlayer');if(document.title!==sharedWindowTitle)document.title=sharedWindowTitle;
  updateTrackLinks(t,response.headers.get('X-PAF-Client-Local')==='1');
  const notice=s.session_notice||{},noticeHost=document.getElementById('sessionNotice');
  const noticeVisible=Boolean(notice.message)&&Number(notice.expires_at_epoch||0)>Date.now()/1000;
  if(noticeHost){noticeHost.textContent=noticeVisible?String(notice.message):'';noticeHost.classList.toggle('visible',noticeVisible);noticeHost.classList.toggle('error',noticeVisible&&String(notice.level||'warning')==='error');}
  renderDetectedUrls(s.urls||[]);
  const clockAdvance=s.playing&&!s.paused?clockAge*Math.max(0,Number(s.speed||1)):0;
  // Status owns metadata even while the newer timeline owns the clock anchor.
  webClockSample={...webClockSample,duration:Number(s.duration_seconds||0),progress:Number(s.progress||0),karaokeOffset:Number(s.karaoke_offset_seconds||0)};
  const statusPosition=Number(s.position_seconds||0)+clockAdvance;
  if(webSeekPending&&Math.abs(statusPosition-webSeekPending.position)<=1.25)webSeekPending=null;
  if(webSeekPending&&clockReceivedAt-webSeekPending.at>3000)webSeekPending=null;
  if(!webSeekPending&&clockReceivedAt-lastTimelineClockAt>500)webClockSample={...webClockSample,position:statusPosition,lyricPosition:Number(s.lyric_position_seconds??s.position_seconds??0)+clockAdvance,speed:Number(s.speed||1),paused:!!s.paused,playing:!!s.playing,at:clockReceivedAt,validUntil:clockReceivedAt+4000};
  webLyricTimeline=Array.isArray(s.lyric_timeline)?s.lyric_timeline:[];
  if(webLyricTimeline.length)scheduledWebLyric(performance.now());
  else if(!spectrumPaused)renderWebLyric(s.lyric||'');
  const pauseButton=document.getElementById('pauseResumeButton');
  if(pauseButton){pauseButton.textContent=s.paused?'▶':'⏸︎';pauseButton.title=s.paused?'Resume':'Pause';}
  updateWebArtTitle();maybeAutoRotateWebArt();const outputDeviceControl=document.querySelector('[data-control-key="output_device"]');if(outputDeviceControl&&outputDeviceControl._setMultiOutputMask)outputDeviceControl._setMultiOutputMask(Number(s.output_devices_mask||1));
  const mediaStatus=document.getElementById('externalMediaStatus');
  if(mediaStatus){
   const playbackNote=s.external_media_auto_paused?'Paused for other media. Press Play to resume now, or wait for it to finish. Pause keeps PAF paused afterward.':Number(s.external_media_fade_remaining||0)>0?'Resuming gently: '+Math.ceil(s.external_media_fade_remaining)+' seconds of fade remaining.':'';
   const detectionNote=s.external_media_monitor_known===false?'Automatic pause monitor: '+(s.external_media_monitor_status||'starting…'):s.external_media_monitor_degraded?'Automatic pause uses Windows audio detection. Media-session status: '+(s.external_media_smtc_error||'unavailable'):'';
   mediaStatus.textContent=[s.external_media_auto_pause?playbackNote:'',s.external_media_auto_pause?detectionNote:'',s.external_media_loudness_match?s.external_media_loudness_status:''].filter(Boolean).join(' ');
  }
  const playState=s.transport_stopped?'Stopped':s.paused?'Paused':s.playing?'Playing':'Stopped';
  const pauseTitle=s.paused&&s.pause_reason?'Paused: '+String(s.pause_reason):'';
  const vol=Number(s.volume??0);const volIcon=vol<=0?'🔇':vol<=35?'🔈':vol<=100?'🔉':'🔊';
  const bal=Number(s.balance??0);const balanceText=bal===0?'Center':Math.abs(bal)+'% '+(bal<0?'Left':'Right');
  const ch=Number(s.output_channels??2);const channelText=ch===12?'Dolby Atmos 7.1.4':ch===7?'7.1':ch===5?'5.1':'Stereo';
  const rateKhz=((Number(s.output_rate_hz||0)/1000)||48).toLocaleString(undefined,{maximumFractionDigits:1});
  const perf=s.visualizer_perf||{};
  const perfFps=Number(perf.fps||0),perfTarget=Number(perf.target_fps||0),perfCpu=Number(perf.cpu_percent||0);
  const perfComponents=perf.components&&typeof perf.components==='object'?perf.components:{};
  const perfHot=Object.entries(perfComponents).sort((a,b)=>Number(b[1]?.total_ms||0)-Number(a[1]?.total_ms||0)).slice(0,4).map(([name,data])=>name+' '+Number(data?.share_percent||0).toFixed(1)+'% / '+Number(data?.avg_ms||0).toFixed(2)+'ms').join('; ');
  const perfTitle='5-second rolling average. Use the visualizer performance control for detailed console attribution.'+(perfHot?' Hot sections: '+perfHot:'')+' CPU: '+perfCpu.toFixed(0)+'%';
  const chips=[
    'Status: '+playState,
    'Last play: '+((m['Last play'])??'Never'),
    volIcon+' Vol: '+vol+'%',
    'Shuffle: '+(s.shuffle?'Yes':'No'),
    'Speed: '+(s.speed??'')+'×',
    'Channels: '+channelText,
    'Out: '+rateKhz+'kHz / '+Number(s.output_bit_depth||16)+' bit'+(m.Bitrate?' • '+m.Bitrate:''),
    'Repeat: '+String(s.repeat_mode_name??(s.loop?'Repeat 1':'Repeat OFF')).replace(/^Repeat\s+/i,''),
    'Balance: '+balanceText
  ];
  if(performance.now()<versionChipUntil) chips.push('Version: '+String(s.version||''));
  const esc=x=>String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
  const perfButton='<button class="chip perf-chip" title="'+esc(perfTitle)+'" onclick="action(\'visualizer-perf-toggle\')">FPS: '+(perfFps?perfFps.toFixed(1):'—')+(perfTarget?' / '+perfTarget.toFixed(0):'')+'</button>';
  const chipsHtml='<span class="chip"'+(pauseTitle?' title="'+esc(pauseTitle)+'"':'')+'>'+esc(chips[0])+'</span>'+perfButton+chips.slice(1).map(x=>'<span class="chip">'+esc(x)+'</span>').join('');
  if(chipsHtml!==lastChipsHtml){document.getElementById('chips').innerHTML=chipsHtml;lastChipsHtml=chipsHtml;}
  if((s.art_generation??0)!==artGeneration){
    artGeneration=s.art_generation??0;
    webArtIndex=0;webArtAutoRotateAt=performance.now()+20000;webBgOverrideIndex=null;webBgMatchedIndex=null;lastWebBackgroundSignature='';
    document.getElementById('art').src='/api/art?g='+artGeneration+'&index=0';
  }
  syncControls(s);syncMirroredPlaybackControls();
  const markLearned=document.getElementById('other-action-mark-song-learned');if(markLearned)markLearned.hidden=!s.claire_integrations_enabled||!!s.learned;
  const editLyr=document.getElementById('editLyrButton'),editKar=document.getElementById('editKarButton');if(editLyr){editLyr.disabled=!s.has_lyr_txt;editLyr.title=s.has_lyr_txt?'Edit plain lyrics sidecar':'No editable plain-lyrics sidecar exists for this track'}if(editKar){editKar.disabled=!s.has_karaoke_sidecars;editKar.title=s.has_karaoke_sidecars?'Edit karaoke timing sidecar':'No editable karaoke sidecar exists for this track'}
  updateWebEmojimaxToggle();
  updateWebBackground();
 }catch(e){}
 setTimeout(tick,document.hidden?Math.max(2000,ms*4):ms);
}


function animateWebClock(now){
  if(now-lastWebClockPaint>=50){
    lastWebClockPaint=now;const sample=webClockSample||{};let pos=Number(sample.position||0),duration=Number(sample.duration||0);
    if(sample.playing&&!sample.paused)pos+=Math.max(0,(Math.min(now,sample.validUntil??now)-Number(sample.at||now))/1000)*Math.max(0,Number(sample.speed||1));
    if(duration>0)pos=Math.max(0,Math.min(duration,pos));else pos=Math.max(0,pos);
    const progress=duration>0?Math.max(0,Math.min(1,pos/duration)):Math.max(0,Math.min(1,Number(sample.progress||0)));
    const bar=document.getElementById('bar');if(bar)bar.style.width=(progress*100).toFixed(2)+'%';
    const indicator=sample.paused?'⏸':'▶',offset=Number(sample.karaokeOffset||0),suffix=offset?'  [karaoke offset: '+(offset>0?'+':'')+offset.toFixed(1)+'s]':'';
    const host=document.getElementById('time');if(host)host.textContent=indicator+' '+fmtTime(pos)+' / '+fmtTime(duration)+'   '+Math.round(progress*100)+'%'+suffix;
  }
  requestAnimationFrame(animateWebClock);
}

async function setWebVisualizerEnabled(enabled,send=true){
  webVisualizerEnabled=!!enabled;const shell=document.getElementById('webVisualizerShell'),toggle=document.getElementById('webVisualizerToggle');if(toggle)toggle.checked=webVisualizerEnabled;if(shell)shell.classList.toggle('off',!webVisualizerEnabled);
  if(!webVisualizerEnabled){spectrumTarget=[];spectrumCurrent=[];const canvas=document.getElementById('visualizer'),ctx=canvas?.getContext?.('2d');if(ctx)ctx.clearRect(0,0,canvas.width,canvas.height)}
  if(send){try{await fetch('/api/web-visualizer',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:webVisualizerEnabled})})}catch(e){}}
}
function setupWebVisualizerToggle(){const toggle=document.getElementById('webVisualizerToggle'),canvas=document.getElementById('visualizer');if(toggle)toggle.onchange=()=>setWebVisualizerEnabled(toggle.checked,true);if(canvas)canvas.ondblclick=()=>setWebVisualizerEnabled(!webVisualizerEnabled,true)}
timelineTick();
async function spectrumTick(){
 if(spectrumTimeline?.source==='track' || !webVisualizerEnabled || document.hidden){setTimeout(spectrumTick,document.hidden?1000:Math.max(250,spectrumMs));return}
 try{
  const r=await fetch('/api/spectrum.raw',{cache:'no-store'});if(r.status===204){spectrumTarget=[]}else if(r.ok){const buffer=await r.arrayBuffer();if(buffer.byteLength)processRawSpectrumBuffer(buffer);else spectrumTarget=[]}
 }catch(e){}
 setTimeout(spectrumTick,spectrumMs);
}

let tagsExpanded=false;
async function toggleAllTags(){
 const button=document.getElementById('expandTagsButton'),host=document.getElementById('tags'),status=document.getElementById('tagsStatus');if(!button||!host)return;
 if(tagsExpanded){tagsExpanded=false;host.replaceChildren();host.style.display='none';button.textContent='Show tags';button.setAttribute('aria-expanded','false');if(status)status.textContent='';return}
 button.disabled=true;if(status)status.textContent='Loading every tag…';
 try{
   const response=await fetch('/api/tags',{cache:'no-store'});if(!response.ok)throw new Error('Could not load tags');const rows=await response.json();host.replaceChildren();
   let artworkRendered=false;
   for(const row of rows){
     const line=document.createElement('div');line.className='tag-row';
     const source=document.createElement('div');source.className='tag-source';source.textContent=row[0]||'';
     const key=document.createElement('div');key.className='tag-key';key.textContent=row[1]||'';
     const value=document.createElement('div');value.className='tag-value';appendLinkified(value,row[2]||'');
     const artworkTag=/\bAPIC\b|\bCOVR\b|COVERART|METADATA[ _-]*BLOCK[ _-]*PICTURE|\bPICTURE\b/i.test(String(row[1]||''));
     if(artworkTag&&!artworkRendered){const image=document.createElement('img');image.className='tag-artwork';image.alt='Embedded artwork for '+String(row[1]||'artwork tag');image.src='/api/art?g='+encodeURIComponent(String(artGeneration||0))+'&index=0';image.onerror=()=>image.remove();value.appendChild(image);artworkRendered=true}
     line.append(source,key,value);host.appendChild(line);
   }
   if(!rows.length)host.textContent='No metadata tags were found for the current track.';
   tagsExpanded=true;host.style.display='block';button.textContent='Hide tags';button.setAttribute('aria-expanded','true');if(status)status.textContent=rows.length+' tag'+(rows.length===1?'':'s')+' shown.';
 }catch(error){if(status)status.textContent=String(error)}finally{button.disabled=false}
}
document.getElementById('expandTagsButton')?.addEventListener('click',toggleAllTags);
new ResizeObserver(resizeCanvas).observe(document.getElementById('visualizer'));
new ResizeObserver(()=>{if(karaokeAutoExpand&&lyricText)requestAnimationFrame(fitKaraokeToDock)}).observe(document.getElementById('lyricDock'));
new ResizeObserver(()=>updateKaraokeReservation()).observe(document.getElementById('lyric'));
window.addEventListener('resize',()=>requestAnimationFrame(()=>{updateKaraokeReservation();fitWebSongTitle()}));
setInterval(()=>updateKaraokeReservation(),500);
async function startWebUi(){
  await loadWebPreferences();
  webKaraokeSettings=loadWebKaraokeSettings();
  setupWebBackgroundConfig();
  await build();setupConfigTabs();
initSpectrumWorker();setupWebVisualizerToggle();const centerVisualizerButton=document.getElementById('floatingLyricsCenterVisualizerButton');if(centerVisualizerButton){centerVisualizerButton.classList.add('web-experimental-button');centerVisualizerButton.textContent='EXP Center Over Visualizer';centerVisualizerButton.title='EXP: Center floating lyrics over the console visualizer (currently does not work)'}resizeCanvas();
  // Give every visible configuration label/control at least a discoverable tooltip.
  document.querySelectorAll('#choicesFrame h3,#choicesFrame label,#choicesFrame button,#choicesFrame select,#choicesFrame input,#choicesFrame summary,#choicesFrame .note,#choicesFrame strong,#matrixModal h2,#matrixModal h3,#matrixModal p,#matrixModal button,#matrixModal input,#matrixModal select').forEach(el=>{if(!el.title){const t=(el.textContent||el.getAttribute('placeholder')||el.getAttribute('aria-label')||el.id||'PAFPlayer control').trim();if(t)el.title=t}});
  tick();spectrumTick();requestAnimationFrame(drawSpectrum);requestAnimationFrame(animateLyric);requestAnimationFrame(animateWebClock);
}
startWebUi();
