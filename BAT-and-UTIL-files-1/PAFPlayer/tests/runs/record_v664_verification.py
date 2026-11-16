from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v664-free-dj-live-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V664','focused_tests':51,'bundled_modules_compiled':28,'source_bundle_mismatches':0,'release_matches_active':True,'openrouter_key_auth_http':200,'openrouter_free_account':True,'gemini_key_auth_http':200,'google_project_user_confirmed_free_tier':True,'gemini_free_setting_persisted':True,'real_end_to_end':{'openrouter_free_and_piper':{'wav_files':4,'elapsed_seconds':16.5},'gemini_native_and_piper':{'wav_files':2,'elapsed_seconds':9.5}},'earlier_gemini_model':'404 unavailable to new users; updated to gemini-3.5-flash-lite','openai_credit_warning':'last verified balance exhausted','literal_c_bat_changes':{'C:\\BAT\\private.env':'modified','C:\\BAT\\private.env.bak.202611120207.replaced-by-chatgpt.bak':'created'}},indent=2)+'\n',encoding='utf8')
def update(path,a,b,archive):
 s=path.read_text(encoding='utf8');assert s.count(a)==1;s=s.replace(a,b,1)
 name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');bpath=path.with_name(name);i=0
 while bpath.exists():i+=1;bpath=path.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(path,bpath);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(bpath.read_bytes()).digest()
 path.write_text(s,encoding='utf8',newline='');dest=archive/bpath.name;i=0
 while dest.exists():i+=1;dest=archive/(bpath.stem+f' ({i})'+bpath.suffix)
 shutil.move(str(bpath),str(dest))
notes=root/'releases/PAFPlayer_v664_gemini_native_release_notes.md'
a='Live tests using synthetic metadata generated two dialogue turns each through OpenRouter’s free router and the confirmed free-tier Gemini project.'
b='Live end-to-end tests with synthetic metadata generated four valid speech files through OpenRouter’s free router and two through the confirmed free-tier Gemini project, both using Piper. The project’s free-tier confirmation was saved in the player settings. Fifty-one focused tests passed; 28 bundled modules compiled and the release matched the active file. [Test report](../tests/reports/v664-free-dj-live-checks-20261112.json).'
update(notes,a,b,root/'releases')
readme=root/'docs/README.md';a='The newer service key authenticated, but an OpenAI text request returned HTTP 429 `credit_balance_exhausted`; cloud speech remains unverified.'
b='The newer OpenAI service key authenticated, but an OpenAI text request returned HTTP 429 `credit_balance_exhausted`; OpenAI speech remains unverified. Live free-tier OpenRouter and Gemini dialogue plus Piper speech passed with synthetic track metadata.'
update(readme,a,b,root/'docs')
print('Recorded live free-provider and Piper verification.')
