from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v661-dj-private-key-checks-20261111.json';assert not report.exists()
report.write_text(json.dumps({'version':'V661','key_loading_tests':2,'dj_diagnostics_tests':6,'piper_setup_tests':4,'help_tests':3,'existing_dj_tests':22,'command_tests':7,'compiled_bundled_modules':28,'source_bundle_mismatches':0,'release_matches_active':True,'private_key_loaded':True,'private_key_differs_from_inherited_environment':True,'openai_models_http_status':200,'openai_text_http_status':429,'openai_text_error_code':'credit_balance_exhausted','openai_speech':'failed; not verified','local_fallback':'Ollama and Piper verified in V660','literal_c_bat_changes':{'C:\\BAT\\private.env':'modified','C:\\BAT\\private.env.bak.202611111906.replaced-by-chatgpt.bak':'created'}},indent=2)+'\n',encoding='utf8')
def update(path,a,b,archive):
 data=path.read_text(encoding='utf8');assert data.count(a)==1;data=data.replace(a,b,1)
 name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=path.with_name(name);i=0
 while backup.exists():i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(path,backup);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
 path.write_text(data,encoding='utf8',newline='');dest=archive/backup.name;i=0
 while dest.exists():i+=1;dest=archive/(backup.stem+f' ({i})'+backup.suffix)
 shutil.move(str(backup),str(dest))
notes=root/'releases/PAFPlayer_v661_dj_private_key_release_notes.md'
a='A verified backup of the prior private environment file was created before the file was updated.'
b='A verified backup of the prior private environment file was created before the file was updated. Two key-loading tests, six DJ diagnostic and playback tests, and 36 existing Piper, Help, DJ, and command tests passed. All 28 bundled modules compiled and the release matched the active player. [Test report](../tests/reports/v661-dj-private-key-checks-20261111.json).'
update(notes,a,b,root/'releases')
readme=root/'docs/README.md'
a='Both tested OpenAI keys returned HTTP 401. A live local Ollama-to-Piper test generated six speech files in about 54 seconds, and a muted FFplay check succeeded.'
b='The newer service key authenticated, but an OpenAI text request returned HTTP 429 `credit_balance_exhausted`; cloud speech remains unverified. A live local Ollama-to-Piper test generated six speech files in about 54 seconds, and a muted FFplay check succeeded.'
update(readme,a,b,root/'docs')
print('Recorded private-key loading and account credit results.')
