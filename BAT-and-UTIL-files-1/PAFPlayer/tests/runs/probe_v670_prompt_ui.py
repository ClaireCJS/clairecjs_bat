import importlib.util,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v670_ui',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_dj as dj
html=p._paf_web_html();scripts=re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>',html,re.I|re.S)
script=next(s for s in scripts if "const choice=$('djPromptChoice')" in s)
start=html.index('let configTabScrollRaf=0;');end=html.index('function attachChoiceButtons(key)',start);tabs=html[start:end]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True,args=['--disable-gpu'])
 page=browser.new_page()
 page.set_content('<div id="choicesFrame"><div id="configTabs"></div><section id="experimentalSection"><h3>Experimental</h3><div id="djSettings"></div></section></div>')
 page.evaluate('(source)=>eval(source+";organizeControlSections();setupConfigTabs();")',tabs)
 assert page.locator('#configTabs button[data-target="aiDjSection"]').count()==1
 assert page.locator('#aiDjSection #djSettings').count()==1
 page.set_content('<select id="djPromptChoice"></select><textarea id="djPromptText"></textarea><input id="djPromptName"><button id="djPromptSave"></button><button id="djPromptSaveNamed"></button><p id="djPromptStatus"></p>')
 payload={'settings':dj.settings(),'prompt_builtins':dj.BUILTIN_PROMPTS,'local':True,'token':'test'}
 page.evaluate('''payload=>{window.state=payload;window.fetch=async(url,opt)=>{if(opt&&opt.method==='POST'){Object.assign(window.state.settings,JSON.parse(opt.body));window.patches=(window.patches||0)+1}return {ok:true,json:async()=>window.state}}}''',payload)
 page.add_script_tag(content=script);page.wait_for_function("document.querySelector('#djPromptText').value.length>0")
 assert page.input_value('#djPromptText')==dj.ORIGINAL_DJ_PROMPT
 page.fill('#djPromptText','My original prompt')
 page.select_option('#djPromptChoice','builtin:politics');assert 'political' in page.input_value('#djPromptText').lower()
 page.select_option('#djPromptChoice','custom');assert page.input_value('#djPromptText')=='My original prompt'
 page.select_option('#djPromptChoice','builtin:politics');page.click('#djPromptSave');page.wait_for_function("document.getElementById('djPromptStatus').textContent.includes('saved')")
 assert page.evaluate('window.state.settings.prompt_previous')=='My original prompt'
 page.set_content('<select id="djPromptChoice"></select><textarea id="djPromptText"></textarea><input id="djPromptName"><button id="djPromptSave"></button><button id="djPromptSaveNamed"></button><p id="djPromptStatus"></p>')
 page.add_script_tag(content=script);page.wait_for_function("document.querySelector('#djPromptText').value.length>0")
 assert page.input_value('#djPromptChoice')=='builtin:politics'
 page.select_option('#djPromptChoice','custom');assert page.input_value('#djPromptText')=='My original prompt'
 page.select_option('#djPromptChoice','random');page.click('#djPromptSave');page.wait_for_function("window.state.settings.prompt_choice==='random'")
 page.fill('#djPromptText','My new prompt');page.fill('#djPromptName','My style');page.click('#djPromptSaveNamed');page.wait_for_function("window.state.settings.prompt_presets.length===1")
 assert page.evaluate('window.state.settings.prompt_presets[0].text')=='My new prompt'
 page.fill('#djPromptName','MY STYLE');page.click('#djPromptSaveNamed');assert 'already in use' in page.locator('#djPromptStatus').inner_text()
 print('Dedicated DJ tab, editable prompts, restore, random, and saved presets passed.');browser.close()
