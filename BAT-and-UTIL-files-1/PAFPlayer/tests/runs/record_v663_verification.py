from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v663-dj-free-providers-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V663','boundary_test':1,'free_provider_and_warning_tests':6,'private_key_tests':2,'dj_diagnostic_playback_tests':6,'piper_setup_tests':4,'help_tests':3,'existing_dj_tests':22,'command_tests':7,'compiled_bundled_modules':28,'source_bundle_mismatches':0,'release_matches_active':True,'javascript_blocks_checked':9,'browser_warning_tab_order':'passed','browser_warning_refresh':'passed','real_local_fallback':{'openai_exhaustion':'simulated without network spending','ollama_and_piper':'actual local inference and synthesis','speech_files':6,'credit_warning':'present','initial_120s_timeout':'failed; raised to 600s'},'openrouter_live':'not verified; no key','gemini_live':'not verified; no key; free-tier confirmation required','actual_credit_warning_seeded':True,'literal_c_bat_changes':[]},indent=2)+'\n',encoding='utf8')
def update(path,a,b,archive):
 data=path.read_text(encoding='utf8');assert data.count(a)==1,(a,data.count(a));data=data.replace(a,b,1)
 name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=path.with_name(name);i=0
 while backup.exists():i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(path,backup);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
 path.write_text(data,encoding='utf8',newline='');dest=archive/backup.name;i=0
 while dest.exists():i+=1;dest=archive/(backup.stem+f' ({i})'+backup.suffix)
 shutil.move(str(backup),str(dest))
notes=root/'releases/PAFPlayer_v663_dj_between_tracks_release_notes.md'
a='Track transport and modal Help behavior remain unchanged. V662 adds OpenRouter/Gemini text fallbacks and the OpenAI credit warning.'
b='Track transport and modal Help behavior remain unchanged. V662 adds OpenRouter/Gemini text fallbacks and the OpenAI credit warning. A browser probe verified that Warnings is the last tab and displays the credit warning; a real local Ollama/Piper run after simulated OpenAI credit exhaustion generated six WAVs. The first run exceeded the former 120-second limit, so the local timeout was raised to 600 seconds. The hosted free providers have not been verified live because their API keys are not configured. [Test report](../tests/reports/v663-dj-free-providers-checks-20261112.json).'
update(notes,a,b,root/'releases')
readme=root/'docs/README.md'
a='Local model loading and generation can take minutes.';b='Local model loading and generation can take minutes; the background request allows up to ten minutes.'
update(readme,a,b,root/'docs')
print('Recorded browser, fallback, track-boundary, and provider verification.')
