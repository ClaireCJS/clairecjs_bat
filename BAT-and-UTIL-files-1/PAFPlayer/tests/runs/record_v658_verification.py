from pathlib import Path
import datetime, hashlib, json, shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v658-dj-help-checks-20261111.json'
assert not report.exists()
report.write_text(json.dumps({'version':'V658','focused_dj_tests':22,'help_tests':3,'hash_command_tests':7,'source_bundle_mismatches':0,'bundled_modules_compile':28,'release_matches_active':True,'live_ollama':{'model':'qwen3-coder:30b','initial_manual_selection_seconds':78.7,'automatic_selection_bounded_context_seconds':110.3,'sample_track':'synthetic example'},'openai_private_env_current_key':'HTTP 401','piper':'not installed','live_speech':'not verified','literal_c_bat_changes':[]},indent=2)+'\n',encoding='utf-8')
def update(path, before, after, archive):
    value=path.read_text(encoding='utf-8'); assert value.count(before)==1; value=value.replace(before,after,1)
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak'); backup=path.with_name(name); i=0
    while backup.exists():
        i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(value,encoding='utf-8',newline='');dest=archive/backup.name;i=0
    while dest.exists():
        i+=1;dest=archive/(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(dest))
update(root/'docs/README.md','a local Ollama model generated dialogue in about 79 seconds after an earlier request timed out','a local Ollama model generated dialogue in about 79 seconds after an earlier request timed out; a subsequent test using automatic model selection took 110 seconds',root/'docs')
update(root/'releases/PAFPlayer_v658_dj_help_commentary_release_notes.md','A local Ollama model produced real dialogue in approximately 79 seconds after an earlier request timed out.','A local Ollama model produced real dialogue in approximately 79 seconds after an earlier request timed out; the updated automatic selection produced dialogue in 110 seconds. Focused verification: 22 existing DJ tests, three new Help tests, seven command tests, and 28 bundled modules compile; the release copy matches the active player. [Test report](../tests/reports/v658-dj-help-checks-20261111.json).',root/'releases')
print('Recorded live automatic-selection verification and test report.')
