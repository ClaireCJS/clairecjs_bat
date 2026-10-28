// Execute the actual MonkeyMote UI handlers with a small DOM/fetch fixture.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(process.argv[2],'utf8');
const start=source.indexOf(' let mmState=null'),end=source.indexOf(' // Keep the editor',start);
assert(start>=0 && end>start);
const elements=new Map();let choice='cancel',confirmation=false,posts=[];
let state={enabled:true,listening:true,local:true,eligible:true,host:'127.0.0.1',port:19371,clients:2,max_clients:8,token:'fixture'};
function $(id){if(!elements.has(id))elements.set(id,{value:'19371',disabled:false,checked:true,textContent:'',reportValidity(){return true},addEventListener(event,fn){this.close=fn},showModal(){this.returnValue=choice;this.close()}});return elements.get(id)}
const context={$,document:{activeElement:null,hidden:false},setInterval(){},confirm(){return confirmation},fetch:async(url,opts)=>{assert.equal(url,'/api/workflows/monkeymote');if(opts?.method==='POST'){assert.equal(opts.headers['X-PAF-Workflow-Token'],'fixture');const payload=JSON.parse(opts.body);posts.push(payload);state={...state,...payload,listening:payload.enabled??state.enabled}}return {ok:true,json:async()=>({...state})}},Number,Promise,Error};
vm.createContext(context);vm.runInContext(source.slice(start,end),context);
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 await tick();assert.equal($('monkeyMoteEnabled').disabled,false);assert.equal($('monkeyMoteEnabled').checked,true);
 $('monkeyMotePort').value='19372';choice='session';$('monkeyMoteApply').onclick();await tick();
 assert.deepEqual(posts.at(-1),{port:19372,permanent:false,confirm_disable:false});
 $('monkeyMotePort').value='19373';choice='cancel';$('monkeyMoteApply').onclick();await tick();assert.equal(posts.length,1);assert.equal(Number($('monkeyMotePort').value),19372);
 $('monkeyMotePort').value='19373';choice='permanent';$('monkeyMoteApply').onclick();await tick();assert.equal(posts.at(-1).permanent,true);
 confirmation=false;$('monkeyMoteEnabled').onchange({target:{checked:false}});await tick();assert.equal(posts.length,2);assert.equal($('monkeyMoteEnabled').checked,true);
 confirmation=true;$('monkeyMoteEnabled').onchange({target:{checked:false}});await tick();assert.deepEqual(posts.at(-1),{enabled:false,permanent:true,confirm_disable:true});assert.equal($('monkeyMoteEnabled').checked,false);
 $('monkeyMoteEnabled').onchange({target:{checked:true}});await tick();assert.equal(posts.at(-1).enabled,true);
 choice='session';$('monkeyMoteEnabled').onchange({target:{checked:false}});await tick();assert.equal(posts.at(-1).permanent,false);
 console.log('7 UI flows passed: session/save/cancel port; cancel/confirm permanent disable; enable; session disable.');
})().catch(e=>{console.error(e);process.exitCode=1});
