from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v672-dj-variety-piper-checks-20261112.json';assert not report.exists()
report.write_text(json.dumps({'version':'V672','focused_tests_passed':82,'dj_variety_tests_passed':4,'piper_setup_tests_passed':6,'piper_existing_install_real_synthesis':'passed, 22050 Hz','browser_piper_setup':'passed','browser_prompt_and_sleep_controls':'passed','bundled_modules_compiled':28,'source_bundle_mismatches':0,'javascript_blocks_checked':11,'release_matches_active':True,'recent_dialogue_memory':'current session only','live_provider_with_new_context':'not tested'},indent=2)+'\n',encoding='utf8')
def append_note(p,text):
 name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=p.with_name(name);i=0
 while backup.exists():i+=1;backup=p.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(p,backup);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
 with p.open('ab') as f:f.write(text.encode('utf8'))
append_note(root/'releases/PAFPlayer_v671_dj_variety_release_notes.md','\nV672 regression checks include the DJ variety tests. Recent conversation memory lasts for the current player session. [Test report](../tests/reports/v672-dj-variety-piper-checks-20261112.json).\n')
append_note(root/'releases/PAFPlayer_v672_piper_startup_release_notes.md','\nVerification: 82 focused tests passed; browser checks covered Piper setup, prompt and sleep controls. The existing local Piper installation synthesized real audio at 22050 Hz. Eleven JavaScript blocks and 28 bundled modules passed checks; the release matches the active player. The new context was not tested against a live text provider. [Test report](../tests/reports/v672-dj-variety-piper-checks-20261112.json).\n')
print('Recorded V671 and V672 verification.')
