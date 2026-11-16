import importlib.util,json,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v663_warning_refresh',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
html=p._paf_web_html();scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',html,re.I|re.S)
script=next(s for s in scripts if "const $=x=>document.getElementById('dj_'+x)" in s)
keys=['enabled','history','interval','seconds','speakers','women','men','text_provider','text_model','ollama_model','speech_provider','speech_model','voices','accent','piper_executable','piper_voices','gemini_free_confirmed']
inputs=''.join(f'<input id="dj_{k}" type="'+('checkbox' if k in ('enabled','gemini_free_confirmed') else 'text')+'">' for k in keys)
payload={'local':True,'token':'test','settings':{k:False if k in ('enabled','gemini_free_confirmed') else '' for k in keys},'warnings':['OpenAI API credit balance was exhausted at the last check.']}
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True,args=['--disable-gpu'])
 page=browser.new_page();page.set_content(inputs+'<button id="dj_save"></button><p id="dj_status"></p><div id="djWarningsContent"></div>')
 page.evaluate('(payload)=>{window.fetch=async()=>({ok:true,json:async()=>payload})}',payload)
 page.add_script_tag(content=script)
 page.wait_for_function("document.querySelector('#djWarningsContent').textContent.includes('credit balance was exhausted')")
 print('Warnings tab received current credit warning from DJ status.')
 browser.close()
