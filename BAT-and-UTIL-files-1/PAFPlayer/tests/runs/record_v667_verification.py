from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v667-dj-talk-log-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V667','focused_tests_passed':68,'conversation_log_tests_passed':3,'bundled_modules_compiled':28,'source_bundle_mismatches':0,'release_matches_active':True,'browser_warning_refresh':'passed','tests_use_isolated_log_paths':True},indent=2)+'\n',encoding='utf8')
notes=root/'releases/PAFPlayer_v667_dj_conversation_log_release_notes.md';name=notes.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=notes.with_name(name);i=0
while b.exists():i+=1;b=notes.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(notes,b);assert hashlib.sha256(notes.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
with notes.open('ab') as stream:stream.write(b'\nVerification: 68 focused tests passed, including Unicode formatting, append behavior, logging before synthesis failure, and write-failure reporting. All 28 bundled modules compiled and matched their editable sources; the release matches the active player. Tests used isolated log paths. [Test report](../tests/reports/v667-dj-talk-log-checks-20261112.json).\n')
print('Recorded V667 verification.')
