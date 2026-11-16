from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=root/'tests/runs/PAFPlayer_voice_models_v675_candidate.py';target=root/'tests/runs/PAFPlayer_voice_models_v675_candidate_v2.py'
s=source.read_text(encoding='utf8')
def once(a,b):
 global s
 assert s.count(a)==1,(a[:100],s.count(a));s=s.replace(a,b,1)
once("            try:task(selected);events.put(('done','Finished. See the results above.'))", "            try:\n                failures=task(selected)\n                events.put(('done','Finished with errors. See the results above.' if failures else 'Finished. See the results above.'))")
once("    def do_install(selected):\n        for index,model in enumerate(selected):\n            try:reporter('Ready: '+str(install(model,reporter)))\n            except Exception as exc:reporter(CATALOG[model]['name']+' failed: '+str(exc))\n            events.put(('overall',(index+1,len(selected))))", "    def do_install(selected):\n        failures=0\n        for index,model in enumerate(selected):\n            try:reporter('Ready: '+str(install(model,reporter)))\n            except Exception as exc:failures+=1;reporter(CATALOG[model]['name']+' failed: '+str(exc))\n            events.put(('overall',(index+1,len(selected))))\n        return failures")
once("        progress('Comparison folder: '+str(folder))\n        if os.name=='nt':os.startfile(folder)", "        progress('Comparison folder: '+str(folder))\n        events.put(('overall',(len(selected),len(selected))))\n        if os.name=='nt':os.startfile(folder)\n        return sum(row['status']!='ok' for row in results)")
compile(s,str(target),'exec')
with target.open('x',encoding='utf8',newline='') as f:f.write(s)
print('Added honest completion status for errors.')
