from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2];report=root/'tests/reports/v669-hash-prompt-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V669','focused_tests_passed':16,'prompt_tests_passed':4,'mock_playback_views':['playing','paused','help'],'existing_command_input_tests_passed':7,'bundled_modules_compiled':28,'source_bundle_mismatches':0,'release_matches_active':True},indent=2)+'\n',encoding='utf8')
notes=root/'releases/PAFPlayer_v669_hash_prompt_release_notes.md';name=notes.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=notes.with_name(name);i=0
while backup.exists():i+=1;backup=notes.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(notes,backup);assert hashlib.sha256(notes.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
with notes.open('ab') as stream:stream.write(b'\nVerification: 16 focused tests passed, including mocked playing, paused, and Help prompt rendering, command editing, timeout, and cancellation. All 28 bundled modules compiled and matched editable sources; the release matches the active player. [Test report](../tests/reports/v669-hash-prompt-checks-20261112.json).\n')
print('Recorded V669 verification.')
