import ast,re,subprocess,sys,types
from pathlib import Path
root=Path(__file__).resolve().parents[3]; tree=ast.parse((root/'PAFPlayer.py').read_text(encoding='utf8')); modules={}
for node in tree.body:
 if not isinstance(node,ast.Assign):continue
 for target in node.targets:
  if isinstance(target,ast.Name) and target.id=='_PAF_BUNDLED_SOURCES':modules.update(ast.literal_eval(node.value))
  elif isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id=='_PAF_BUNDLED_SOURCES':modules[ast.literal_eval(target.slice)]=ast.literal_eval(node.value)
sys.path.insert(0,str(root/'src'))
web=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_paf_web_html')
html=max((n.value for n in ast.walk(web) if isinstance(n,ast.Constant) and isinstance(n.value,str)),key=len)
for name in ('PAFPlayer_workflows_ui','PAFPlayer_screensaver','PAFPlayer_lockscreen','PAFPlayer_tray','PAFPlayer_steam'):
 module=types.ModuleType('build_check_'+name);module.__file__=str(root/(name+'.py'));sys.modules[module.__name__]=module
 exec(compile(modules[name],name,'exec'),vars(module));augment=getattr(module,'augment',None) or getattr(module,'augment_html',None)
 if augment:html=augment(html)
scripts=re.findall(r'<script[^>]*>(.*?)</script>',html,re.S)
for code in scripts:
 r=subprocess.run([r'C:\Program Files\nodejs\node.exe','--check','-'],input=code,text=True,encoding='utf8',capture_output=True,timeout=15)
 if r.returncode:raise RuntimeError(r.stderr)
print('JavaScript blocks checked:',len(scripts))
