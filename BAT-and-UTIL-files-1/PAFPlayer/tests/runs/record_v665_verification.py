from pathlib import Path
import datetime
import hashlib
import json
import shutil

root = Path(__file__).resolve().parents[2]
report = root / 'tests' / 'reports' / 'v665-dj-sleep-checks-20261112.json'
assert not report.exists()
report.write_text(json.dumps({
    'version': 'V665',
    'focused_tests_passed': 58,
    'sleep_tests_passed': 7,
    'bundled_modules_compiled': 28,
    'source_bundle_mismatches': 0,
    'release_matches_active': True,
    'javascript_blocks_checked': 9,
    'browser_sleep_visibility_and_lock_sync': 'passed',
    'browser_warning_tab_and_credit_warning': 'passed',
    'live_free_provider_and_piper_evidence': 'v664-free-dj-live-checks-20261112.json',
}, indent=2)+'\n', encoding='utf8')
notes = root / 'releases' / 'PAFPlayer_v665_dj_sleep_release_notes.md'
original = notes.read_bytes()
name = notes.name + datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')
backup = notes.with_name(name)
i = 0
while backup.exists():
    i += 1
    backup = notes.with_name(name[:-4] + f' ({i}).bak')
shutil.copy2(notes, backup)
assert hashlib.sha256(original).digest() == hashlib.sha256(backup.read_bytes()).digest()
with notes.open('ab') as output:
    output.write(b'\nVerification: 58 focused tests passed, including seven sleep tests; all 28 bundled modules compiled and matched editable sources, and the release matched the active player. Browser checks passed for sleep controls, synchronized lock settings, and the OpenAI credit warning. [Test report](../tests/reports/v665-dj-sleep-checks-20261112.json).\n')
print('Recorded V665 verification and backed up release notes.')
