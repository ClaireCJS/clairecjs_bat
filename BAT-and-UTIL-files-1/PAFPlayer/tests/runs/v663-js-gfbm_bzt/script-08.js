(()=>{
const reduce=document.getElementById('steamReduce'),gallery=document.getElementById('steamGallery'),status=document.getElementById('steamStatus');let busy=false,token='',requestSerial=0;
const notice=document.getElementById('steamPlaybackNotice');
let noticeId='',noticeDeadline=0,noticeTimer=0;
function hideNotice(){clearTimeout(noticeTimer);notice.hidden=true;notice.textContent=''}
function showNotice(value,requestAge){
 const id=String(value?.id||''),remaining=Math.max(0,Math.min(10000,Number(value?.remaining_ms||0))-requestAge);
 if(!id||!value.message||!Number.isFinite(remaining)||remaining<=0){hideNotice();return}
 const deadline=performance.now()+remaining;
 if(id!==noticeId){noticeId=id;noticeDeadline=deadline}else{noticeDeadline=Math.min(noticeDeadline,deadline)}
 clearTimeout(noticeTimer);
 if(noticeDeadline<=performance.now()){hideNotice();return}
 notice.textContent=value.message;notice.hidden=false;
 noticeTimer=setTimeout(hideNotice,noticeDeadline-performance.now());
}
document.addEventListener('visibilitychange',()=>{if(!document.hidden){if(performance.now()>=noticeDeadline)hideNotice();refresh()}});
async function request(payload){const r=await fetch('/api/workflows/steam',payload===undefined?{cache:'no-store'}:{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify(payload)});const data=await r.json();if(!r.ok)throw new Error(data.error||r.statusText);return data}
function show(data,requestAge=0){showNotice(data.notice,requestAge);token=data.token||token;reduce.checked=!!data.settings.SteamReduceVisualizerLoad;gallery.checked=!!data.settings.SteamDisableIdleGallery;reduce.disabled=gallery.disabled=!data.local;status.textContent=data.status+(data.games.length?' · '+data.games.join(', '):'')+(!data.local?' · Change these settings on the player computer.':'')}
async function refresh(){if(busy)return;const serial=++requestSerial,started=performance.now();try{const data=await request();if(serial===requestSerial)show(data,performance.now()-started)}catch(e){if(serial===requestSerial)status.textContent=String(e)}}
async function change(key,control){busy=true;++requestSerial;reduce.disabled=gallery.disabled=true;try{show(await request({[key]:control.checked}))}catch(e){status.textContent=String(e)}finally{busy=false;await refresh()}}
reduce.onchange=()=>change('SteamReduceVisualizerLoad',reduce);gallery.onchange=()=>change('SteamDisableIdleGallery',gallery);refresh();setInterval(()=>{if(!document.hidden)refresh()},3000);
})();