import ast,hashlib,importlib.util,json,os,re,subprocess,sys
from datetime import datetime
from pathlib import Path
root=Path(__file__).resolve().parents[3];stage=Path(__file__).parent;env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');checks=[]
for label,args in [('dj tests',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_v657_dj*.py','-q']),('command tests',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_v656_hash*.py','-q']),('baseline comparison',[sys.executable,str(stage/'compare_regressions.py')])]:
 r=subprocess.run(args,cwd=root,env=env,text=True,encoding='utf8',errors='replace',capture_output=True,timeout=120);checks.append({'name':label,'returncode':r.returncode,'output':(r.stdout+r.stderr)[-3000:]})
 if r.returncode:raise RuntimeError(label+' failed')
source=(root/'PAFPlayer.py').read_text(encoding='utf8');compile(source,'PAFPlayer.py','exec');tree=ast.parse(source);bundles={}
for n in tree.body:
 if isinstance(n,ast.Assign):
  for t in n.targets:
   if isinstance(t,ast.Name) and t.id=='_PAF_BUNDLED_SOURCES':bundles.update(ast.literal_eval(n.value))
   elif isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES':bundles[ast.literal_eval(t.slice)]=ast.literal_eval(n.value)
for name,content in bundles.items():
 compile(content,name,'exec');paths=[x for x in [root/'src'/f'{name}.py',root/'lockscreen'/'src'/f'{name}.py',root/'screensaver'/'src'/f'{name}.py',root/'lockscreen'/f'{name.removeprefix("PAFPlayer_")}.py'] if x.is_file()]
 assert len(paths)==1 and paths[0].read_text(encoding='utf8')==content,name
spec=importlib.util.spec_from_file_location('paf_verify_release',root/'PAFPlayer.py');app=importlib.util.module_from_spec(spec);sys.modules[spec.name]=app;spec.loader.exec_module(app)
scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',app._paf_web_html(),re.S)
for script in scripts:
 result=subprocess.run([r'C:\Program Files\nodejs\node.exe','--check','-'],input=script,text=True,encoding='utf8',capture_output=True,timeout=15);assert result.returncode==0,result.stderr
report={'version':app.PROGRAM_VERSION,'sha256':hashlib.sha256((root/'PAFPlayer.py').read_bytes()).hexdigest(),'bundle_count':len(bundles),'javascript_count':len(scripts),'checks':checks,'live_text':'Unavailable: URLError in sandbox and elevated attempt','live_piper':'Not installed; prior Windows speech probes failed','literal_c_bat_changes':[]}
path=root/'tests/reports'/('v657-dj-checks-'+datetime.now().strftime('%Y%m%d-%H%M%S')+'.json')
with path.open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print('Report',path,'bundles',len(bundles),'JS blocks',len(scripts),'sha256',report['sha256'])
