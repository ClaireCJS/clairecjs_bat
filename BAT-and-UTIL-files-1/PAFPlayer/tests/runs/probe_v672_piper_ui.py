import importlib.util,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v672_piper_ui',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
html=p._paf_web_html();scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',html,re.I|re.S)
script=next(s for s in scripts if "getElementById('djPiperDetails')" in s)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True,args=['--disable-gpu'])
 page=browser.new_page();page.set_content('<pre id="djPiperDetails"></pre><button id="djPiperSetup"></button><p id="djPiperSetupStatus"></p>')
 payload={'local':True,'token':'test','piper_setup_running':False,'piper_auto_executable':'C:/piper.exe','piper_auto_voices':['C:/voice.onnx'],'piper_missing_paths':['C:/old.onnx']}
 page.evaluate('''state=>{window.saved=state;window.posted=null;window.fetch=async(url,opt)=>{if(opt&&opt.method==='POST')window.posted=JSON.parse(opt.body);return {ok:true,json:async()=>window.saved}}}''',payload)
 page.add_script_tag(content=script);page.wait_for_function("document.querySelector('#djPiperDetails').textContent.includes('C:/voice.onnx')")
 assert 'C:/old.onnx' in page.locator('#djPiperDetails').inner_text();assert not page.locator('#djPiperSetup').is_disabled()
 page.click('#djPiperSetup');page.wait_for_function('window.posted!==null');assert page.evaluate('window.posted')=={'setup_piper':True}
 print('Detected paths, missing-path warning, and Piper setup retry button passed.');browser.close()
