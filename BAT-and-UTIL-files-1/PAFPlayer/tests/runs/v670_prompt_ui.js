(()=>{
  const $=id=>document.getElementById(id);
  const choice=$('djPromptChoice'), editor=$('djPromptText'), name=$('djPromptName'),
        save=$('djPromptSave'), saveNamed=$('djPromptSaveNamed'), status=$('djPromptStatus');
  let settings=null,builtins={},local=false,token='',previous='',lastChoice='custom';
  function option(value,label){const o=document.createElement('option');o.value=value;o.textContent=label;choice.appendChild(o)}
  function rebuild(selected){
    choice.textContent='';
    option('custom','Restore previous / current prompt');
    option('builtin:original','Original DJ prompt');
    option('builtin:politics','Music and political events');
    for(const item of settings.prompt_presets)option('saved:'+item.name,item.name);
    option('random','Random prompt each conversation');
    choice.value=selected;
    if(choice.value!==selected)choice.value='custom';
    lastChoice=choice.value;
  }
  choice.addEventListener('change',()=>{
    const selected=choice.value;
    if(lastChoice==='custom' && selected!=='custom')previous=editor.value;
    if(selected==='custom')editor.value=previous || editor.value;
    else if(selected.startsWith('builtin:'))editor.value=builtins[selected.slice(8)]||editor.value;
    else if(selected.startsWith('saved:')){
      const preset=settings.prompt_presets.find(p=>p.name===selected.slice(6));if(preset)editor.value=preset.text;
    }
    lastChoice=selected;
    status.textContent=selected==='random'?'A prompt is picked randomly for each conversation.':'Changes are not saved until you click Save prompt settings.';
  });
  async function persist(presets,selected){
    if(!local)throw Error('Change settings on the player computer');
    const payload={prompt_text:editor.value,prompt_previous:previous,prompt_choice:selected,prompt_presets:presets};
    const r=await fetch('/api/workflows/dj',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify(payload)}),d=await r.json();
    if(!r.ok)throw Error(d.error||'Could not save prompt');
    settings=d.settings;previous=settings.prompt_previous;editor.value=settings.prompt_text;rebuild(settings.prompt_choice);
    status.textContent='Prompt settings saved.';
  }
  save.onclick=async()=>{try{await persist(settings.prompt_presets,choice.value)}catch(e){status.textContent=String(e)}};
  saveNamed.onclick=async()=>{
    const label=name.value.trim();
    if(!label){status.textContent='Enter a name for the new prompt.';return}
    if(settings.prompt_presets.some(p=>p.name.toLocaleLowerCase()===label.toLocaleLowerCase())){status.textContent='That name is already in use; choose another name.';return}
    try{await persist([...settings.prompt_presets,{name:label,text:editor.value}],'saved:'+label);name.value=''}catch(e){status.textContent=String(e)}
  };
  async function load(){
    try{
      const r=await fetch('/api/workflows/dj',{cache:'no-store'}),d=await r.json();if(!r.ok)throw Error(d.error||'Unavailable');
      local=!!d.local;token=d.token||sessionStorage.getItem('paf-workflow-token')||'';
      if(!settings){settings=d.settings;builtins=d.prompt_builtins||{};previous=settings.prompt_previous;editor.value=settings.prompt_text;rebuild(settings.prompt_choice)}
      for(const el of [choice,editor,name,save,saveNamed])el.disabled=!local;
      if(!local)status.textContent='Change settings on the player computer.';
    }catch(e){status.textContent=String(e)}
  }
  load();
})();
