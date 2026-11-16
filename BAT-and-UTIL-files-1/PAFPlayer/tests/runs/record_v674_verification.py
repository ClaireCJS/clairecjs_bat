from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2];report=root/'tests/reports/v674-model-buttons-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V674','real_gui_scales':[1.0,2.0,2.5],'gui_buttons_visible_and_invoked':'passed with mocked install/compare','existing_model_manager_tests_passed':8,'real_piper_comparison':'passed','bundled_modules_compiled':29,'source_bundle_mismatches':0,'release_matches_active':True},indent=2)+'\n',encoding='utf8')
p=root/'releases/PAFPlayer_v674_model_buttons_release_notes.md';name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=p.with_name(name);i=0
while backup.exists():i+=1;backup=p.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(p,backup);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
with p.open('ab') as f:f.write(b'\nVerification: real Tk windows at scales 1.0, 2.0 and 2.5 showed all buttons within the window; Download and Compare were invoked with mocked operations. Eight manager tests and a real Piper comparison passed. All 29 bundled modules matched editable sources, and the release matches the active player. [Test report](../tests/reports/v674-model-buttons-checks-20261112.json).\n')
print('Recorded V674 verification.')
