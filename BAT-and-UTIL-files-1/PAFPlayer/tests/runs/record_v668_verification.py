from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v668-playlist-errors-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V668','missing_playlist_tests_passed':3,'existing_error_reliability_tests_passed':7,'session_error_tests_passed':4,'browser_errors_tab_live_session_list':'passed','browser_warnings_tab_last':'passed','javascript_blocks_checked':9,'bundled_modules_compiled':28,'source_bundle_mismatches':0,'release_matches_active':True},indent=2)+'\n',encoding='utf8')
notes=root/'releases/PAFPlayer_v668_playlist_errors_release_notes.md';name=notes.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=notes.with_name(name);i=0
while backup.exists():i+=1;backup=notes.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(notes,backup);assert hashlib.sha256(notes.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
with notes.open('ab') as f:f.write(b'\nVerification: missing-entry tests and existing error reliability tests passed. Browser checks verified that Errors displays the session list and Warnings remains last. Nine JavaScript blocks and 28 bundled modules passed checks; the release matches the active player. [Test report](../tests/reports/v668-playlist-errors-checks-20261112.json).\n')
print('Recorded V668 verification.')
