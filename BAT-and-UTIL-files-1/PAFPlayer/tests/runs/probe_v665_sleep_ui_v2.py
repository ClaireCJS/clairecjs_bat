import importlib.util,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v665_sleep_ui',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_dj as d
html=p._paf_web_html();scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',html,re.I|re.S)
script=next(s for s in scripts if "const $=x=>document.getElementById('dj_'+x)" in s)
keys=list(d.DEFAULTS);checkboxes={'enabled','gemini_free_confirmed','sleep_when_locked'}
controls=[]
for k in keys:
 if k=='sleep_time':controls.append('<select id="dj_sleep_time"><option value="never">never</option><option value="01:00">1am</option></select>')
 elif k=='wake_time':controls.append('<select id="dj_wake_time"><option value="sunrise">sunrise</option><option value="07:00">7am</option></select>')
 else:controls.append(f'<input id="dj_{k}" type="'+('checkbox' if k in checkboxes else 'text')+'">')
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True,args=['--disable-gpu'])
 page=browser.new_page();page.set_content(''.join(controls)+'<div id="djSleepScheduleDetails" hidden></div><div id="djSunriseZipDetails" hidden></div><input type="checkbox" id="djLockScreenSleep"><button id="dj_save"></button><p id="dj_status"></p><div id="djWarningsContent"></div>')
 page.evaluate('''settings=>{window.saved={...settings};window.patches=[];window.fetch=async(url,opt)=>{if(opt&&opt.method==='POST'){let p=JSON.parse(opt.body);window.patches.push(p);Object.assign(window.saved,p)}return {ok:true,json:async()=>({local:true,token:'test',settings:window.saved,warnings:[]})}}}''',d.settings())
 page.add_script_tag(content=script);page.wait_for_function("!document.getElementById('dj_sleep_when_locked').disabled")
 assert page.eval_on_selector('#djSleepScheduleDetails','e=>e.hidden')
 page.select_option('#dj_sleep_time','01:00');assert not page.eval_on_selector('#djSleepScheduleDetails','e=>e.hidden');assert not page.eval_on_selector('#djSunriseZipDetails','e=>e.hidden')
 assert page.input_value('#dj_sunrise_zip')=='22312'
 page.select_option('#dj_wake_time','07:00');assert page.eval_on_selector('#djSunriseZipDetails','e=>e.hidden')
 page.check('#dj_sleep_when_locked');page.wait_for_function("document.getElementById('djLockScreenSleep').checked")
 page.uncheck('#djLockScreenSleep');page.wait_for_function("!document.getElementById('dj_sleep_when_locked').checked")
 patches=page.evaluate('window.patches');assert patches[-2:]==[{'sleep_when_locked':True},{'sleep_when_locked':False}]
 print('Sleep/wake/ZIP visibility and bidirectional lock-setting synchronization passed.')
 browser.close()
