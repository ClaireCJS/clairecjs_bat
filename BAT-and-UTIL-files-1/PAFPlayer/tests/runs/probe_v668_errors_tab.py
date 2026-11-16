import importlib.util
from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('v668_browser',root/'PAFPlayer.py')
p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
html=p._paf_web_html();start=html.index('let configTabScrollRaf=0;');end=html.index('function attachChoiceButtons(key)',start);script=html[start:end]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True,args=['--disable-gpu'])
    page=browser.new_page()
    def route(r):
        if r.request.url.endswith('/errors'):r.fulfill(status=200,content_type='text/html',body=p._paf_session_errors_html())
        elif r.request.url.endswith('/api/session-errors'):r.fulfill(status=200,content_type='application/json',body='[{"epoch":1760000000,"filename":"missing.mp3","path":"C:/Music/missing.mp3","reason":"The playlist audio file is missing.","outcome":"Skipping to the next playable track."}]')
        else:r.fulfill(status=200,content_type='text/html',body='<div id="choicesFrame"><div id="configTabs"></div><section id="experimentalSection"><h3>Experimental</h3></section><section id="workflowLogsSection"><h3>Logs</h3></section></div>')
    page.route('**/*',route);page.goto('http://paf-test.local/');page.evaluate('(source)=>eval(source+";organizeControlSections();setupConfigTabs();")',script)
    assert page.locator('#configTabs button').all_text_contents()[-2:]==['Errors','Warnings']
    page.locator('#configTabs button[data-target="errorsSection"]').click()
    page.frame_locator('#errorsSection iframe').locator('.name').wait_for()
    assert page.frame_locator('#errorsSection iframe').locator('.name').inner_text()=='missing.mp3'
    assert 'C:/Music/missing.mp3' in page.frame_locator('#errorsSection iframe').locator('.path').inner_text()
    print('Errors tab displays the live session error list.');browser.close()
