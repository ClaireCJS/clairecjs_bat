import importlib.util,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v662_browser_probe',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
html=p._paf_web_html();start=html.index('let configTabScrollRaf=0;');end=html.index('function attachChoiceButtons(key)',start)
script=html[start:end]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True,args=['--disable-gpu'])
 page=browser.new_page()
 page.set_content('<div id="choicesFrame"><div id="configTabs"></div><section id="experimentalSection"><h3>Experimental</h3></section><section id="workflowLogsSection"><h3>Logs</h3></section></div>')
 result=page.evaluate('(source)=>{eval(source+";organizeControlSections();setupConfigTabs();");return {tabs:[...document.querySelectorAll("#configTabs button")].map(x=>x.textContent),last:document.querySelector("#choicesFrame").lastElementChild.id,warning:document.getElementById("djWarningsContent")?.textContent}}',script)
 print(result)
 assert result['tabs'][-1]=='Warnings' and result['last']=='warningsSection'
 browser.close()
