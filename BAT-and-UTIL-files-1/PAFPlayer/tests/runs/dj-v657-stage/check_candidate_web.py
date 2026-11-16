import importlib.util,re,subprocess,sys
from pathlib import Path
p=Path(__file__).parent/'PAFPlayer_candidate_v4.py';spec=importlib.util.spec_from_file_location('paf_web_candidate',p);m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
html=m._paf_web_html();scripts=re.findall(r'<script\b[^>]*>(.*?)</script>',html,re.S)
for code in scripts:
 r=subprocess.run([r'C:\Program Files\nodejs\node.exe','--check','-'],input=code,text=True,encoding='utf8',capture_output=True,timeout=15)
 if r.returncode:raise RuntimeError(r.stderr)
print(len(scripts),'JavaScript blocks passed')
