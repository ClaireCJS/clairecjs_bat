import importlib.util
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('v665_warning_refresh', root / 'PAFPlayer.py')
player = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = player
spec.loader.exec_module(player)
import PAFPlayer_dj as dj

scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', player._paf_web_html(), re.I | re.S)
script = next(s for s in scripts if "const $=x=>document.getElementById('dj_'+x)" in s)
controls = ''.join(f'<input id="dj_{k}" type="'+('checkbox' if k in ('enabled', 'gemini_free_confirmed', 'sleep_when_locked') else 'text')+'">' for k in dj.DEFAULTS)
with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True, args=['--disable-gpu'])
    page = browser.new_page()
    page.set_content(controls+'<div id="djSleepScheduleDetails"></div><div id="djSunriseZipDetails"></div><input id="djLockScreenSleep" type="checkbox"><button id="dj_save"></button><p id="dj_status"></p><div id="djWarningsContent"></div>')
    payload = {'local': True, 'token': 'test', 'settings': dj.settings(), 'warnings': ['OpenAI API credit balance was exhausted at the last check.']}
    page.evaluate('(payload)=>{window.fetch=async()=>({ok:true,json:async()=>payload})}', payload)
    page.add_script_tag(content=script)
    page.wait_for_function("document.querySelector('#djWarningsContent').textContent.includes('credit balance was exhausted')")
    print('Warnings tab displays the current credit warning.')
    browser.close()
