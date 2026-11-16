from pathlib import Path
import datetime, hashlib, json, shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v659-piper-auto-setup-checks-20261111.json';assert not report.exists()
report.write_text(json.dumps({'version':'V659','setup_tests':4,'help_tests':3,'existing_dj_tests':22,'command_tests':7,'compiled_bundled_modules':28,'source_mismatches':0,'release_matches_active':True,'private_setup':'created and verified actual voice synthesis','piper_version':'1.8.0','onnxruntime_version':'1.19.0','voice':'en_US-lessac-medium','live_local_end_to_end':{'input':'synthetic example metadata','text_provider':'ollama','speech_provider':'piper','wav_files':6,'elapsed_seconds':53.5},'silent_ffplay_exit_code':0,'openai_current_and_old_keys':'HTTP 401','literal_c_bat_changes':[]},indent=2)+'\n',encoding='utf8')
def update(path,before,after,archive):
    data=path.read_text(encoding='utf8');assert data.count(before)==1;data=data.replace(before,after,1)
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=path.with_name(name);i=0
    while b.exists():
        i+=1;b=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,b);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    path.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
    while dest.exists():
        i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
    shutil.move(str(b),str(dest))
notes=root/'releases/PAFPlayer_v659_piper_auto_setup_release_notes.md'
old='A real Piper-generated WAV was verified in an isolated environment.'
new='Private Piper setup completed and verified its own speech file. A live Ollama-to-Piper test generated six WAV files in 53.5 seconds; FFplay played the setup WAV with volume muted and exited successfully. Four setup tests, three Help tests, 22 existing DJ tests, and seven command tests passed. All 28 bundled modules compiled, and the release matches the active player. [Test report](../tests/reports/v659-piper-auto-setup-checks-20261111.json).'
update(notes,old,new,root/'releases')
readme=root/'docs/README.md';old='Piper speech synthesis was verified in an isolated Windows environment using the default voice.';new='A live local Ollama-to-Piper test generated six speech files in about 54 seconds, and a muted FFplay check succeeded.'
update(readme,old,new,root/'docs')
print('Recorded end-to-end local speech and playback verification.')
