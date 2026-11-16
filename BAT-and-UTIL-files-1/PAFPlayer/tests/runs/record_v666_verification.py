from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v666-dj-force-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V666','focused_tests_passed':65,'bundled_modules_compiled':28,'source_bundle_mismatches':0,'release_matches_active':True,'javascript_blocks_checked':9,'browser_sleep_controls_and_warning':'passed','forced_sleep_generation_and_playback':'passed with mocked providers and playback','piper_second_voice_download_and_selection':'passed with mocked downloads and synthesis','live_second_voice_download':'not tested'},indent=2)+'\n',encoding='utf8')
notes=root/'releases/PAFPlayer_v666_dj_force_release_notes.md'
name=notes.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=notes.with_name(name);i=0
while backup.exists():i+=1;backup=notes.with_name(name[:-4]+f' ({i}).bak')
shutil.copy2(notes,backup);assert hashlib.sha256(notes.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
with notes.open('ab') as f:f.write(b'\nVerification: 65 focused tests passed, including forced generation and playback during sleep and mocked Piper voice download/selection. Twenty-eight bundled modules compiled and matched editable sources; the release matches the active player. Browser sleep controls and warning checks passed. Live download of the second voice was not tested. [Test report](../tests/reports/v666-dj-force-checks-20261112.json).\n')
print('Recorded V666 verification.')
