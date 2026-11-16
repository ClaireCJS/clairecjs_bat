from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2];report=root/'tests/reports/v673-voice-model-manager-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V673','focused_tests_passed':32,'manager_tests_passed':8,'real_tk_window':'passed','real_piper_comparison':'two WAV samples and results JSON passed','kokoro_qwen_install_and_comparison':'mocked; real downloads and synthesis not tested','bundled_modules_compiled':29,'source_bundle_mismatches':0,'release_matches_active':True,'models_automatically_selected_for_download':False},indent=2)+'\n',encoding='utf8')
notes=root/'releases/PAFPlayer_v673_voice_models_release_notes.md';name=notes.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=notes.with_name(name);i=0
while backup.exists():i+=1;backup=notes.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(notes,backup);assert hashlib.sha256(notes.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
with notes.open('ab') as f:f.write(b'\nVerification: 32 focused tests passed. The real Tk window opened and a real Piper run produced two comparison WAVs and results JSON. Kokoro and Qwen installation and comparison paths were mocked; their real downloads and synthesis were not tested. All 29 bundled modules compiled and matched editable sources; the release matches the active player. [Test report](../tests/reports/v673-voice-model-manager-checks-20261112.json).\n')
print('Recorded V673 verification.')
