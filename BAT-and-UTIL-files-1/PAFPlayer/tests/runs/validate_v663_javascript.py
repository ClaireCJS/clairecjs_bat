import importlib.util,re,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v663_javascript_probe',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
html=p._paf_web_html();scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',html,re.I|re.S)
folder=Path(tempfile.mkdtemp(prefix='v663-js-',dir=str(root/'tests/runs')))
for index,script in enumerate(scripts,1):
 path=folder/f'script-{index:02}.js';path.write_text(script,encoding='utf8')
 result=subprocess.run(['node','--check',str(path)],capture_output=True,text=True)
 if result.returncode:
  print('Script',index,'failed:',result.stderr);raise SystemExit(1)
print('JavaScript blocks passed syntax checks:',len(scripts))
