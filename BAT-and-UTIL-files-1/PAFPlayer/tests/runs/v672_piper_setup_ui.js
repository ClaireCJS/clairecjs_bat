(()=>{
 const details=document.getElementById('djPiperDetails'),button=document.getElementById('djPiperSetup'),status=document.getElementById('djPiperSetupStatus');
 let local=false,token='';
 async function refresh(){
  try{
   const r=await fetch('/api/workflows/dj',{cache:'no-store'}),d=await r.json();if(!r.ok)throw Error(d.error||'Unavailable');
   local=!!d.local;token=d.token||sessionStorage.getItem('paf-workflow-token')||'';button.disabled=!local||d.piper_setup_running;
   details.textContent=[d.piper_auto_executable?'Automatic Piper: '+d.piper_auto_executable:'Automatic Piper has not been installed yet.',...(d.piper_auto_voices||[]).map(v=>'Automatic voice: '+v),...(d.piper_missing_paths||[]).map(v=>'Configured path not found: '+v)].join('\n');
   status.textContent=d.piper_setup_error||d.piper_setup_stage||(d.piper_auto_executable?'Automatic Piper is ready.':'Piper setup starts automatically when the AI DJ is enabled.');
  }catch(e){status.textContent=String(e)}
 }
 button.onclick=async()=>{
  button.disabled=true;
  try{const r=await fetch('/api/workflows/dj',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify({setup_piper:true})}),d=await r.json();if(!r.ok)throw Error(d.error||'Setup could not start');status.textContent='Starting free Piper setup…';await refresh()}
  catch(e){status.textContent=String(e);button.disabled=!local}
 };
 refresh();setInterval(()=>{if(!document.hidden)refresh()},4000);
})();
