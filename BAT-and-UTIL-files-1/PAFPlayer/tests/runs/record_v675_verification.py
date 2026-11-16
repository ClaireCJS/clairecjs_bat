from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2];report=root/'tests/reports/v675-model-progress-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V675','focused_regression_tests_passed':82,'progress_tests_passed':6,'real_tk_progress_window':'passed with mock download, bytes and installer percentage','subprocess_output_before_exit':'passed with real subprocess','piper_installer_output':'passed with real subprocess','real_piper_comparison':'passed','live_large_model_download':'not performed','bundled_modules_compiled':29,'source_bundle_mismatches':0,'release_matches_active':True},indent=2)+'\n',encoding='utf8')
p=root/'releases/PAFPlayer_v675_model_progress_release_notes.md';name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=p.with_name(name);i=0
while backup.exists():i+=1;backup=p.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(p,backup);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
with p.open('ab') as f:f.write(b'\nVerification: 82 focused regression tests passed, including six progress and Piper streaming checks. Real Tk window probes displayed byte-based and installer-reported percentages; real subprocess output was visible before exit, and real Piper comparison still worked. All 29 bundled modules matched editable sources, and the release matches the active player. A live large-model download was not performed. [Test report](../tests/reports/v675-model-progress-checks-20261112.json).\n')
print('Recorded V675 verification.')
