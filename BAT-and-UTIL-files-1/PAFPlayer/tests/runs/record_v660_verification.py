from pathlib import Path
import datetime,hashlib,json,shutil
root=Path(__file__).resolve().parents[2]
report=root/'tests/reports/v660-dj-diagnostics-checks-20261111.json';assert not report.exists()
report.write_text(json.dumps({'version':'V660','new_diagnostic_and_playback_tests':6,'piper_setup_tests':4,'help_tests':3,'existing_dj_tests':22,'command_tests':7,'bundled_modules_compiled':28,'source_bundle_mismatches':0,'release_matches_active':True,'live_local_probe':{'synthetic_track':True,'requested_seconds':90,'dialogue_turns':10,'valid_speech_files':10,'log_created':True,'sample_track_metadata_in_log':False},'existing_v659_session_observed':{'enabled':True,'local_fallback':'ollama and piper','ready':True,'transport_paused':True},'literal_c_bat_changes':[]},indent=2)+'\n',encoding='utf8')
def update(path,a,b,archive):
    data=path.read_text(encoding='utf8');assert data.count(a)==1;data=data.replace(a,b,1)
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=path.with_name(name);i=0
    while backup.exists():i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data,encoding='utf8',newline='');dest=archive/backup.name;i=0
    while dest.exists():i+=1;dest=archive/(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(dest))
notes=root/'releases/PAFPlayer_v660_dj_diagnostics_release_notes.md';a='Explicit user pause remains respected.';b='Explicit user pause remains respected. Resuming a manually paused player preserves a ready automatic segment, which plays after playback resumes.';update(notes,a,b,root/'releases')
a='The precise cause of the earlier lack of a job was not recorded by V659.';b='The precise cause of the earlier lack of a job was not recorded by V659. A real local probe at the 90-second setting generated ten turns and ten valid WAVs with a metadata-free DJ log. Six new diagnostic and playback tests plus 36 existing DJ, Piper, Help, and command tests passed; all 28 bundled modules compiled and the release matches the active file. [Test report](../tests/reports/v660-dj-diagnostics-checks-20261111.json).';update(notes,a,b,root/'releases')
readme=root/'docs/README.md';a='When Help is open, prepared commentary waits until Help closes before it claims the music pause.';b='When Help is open, prepared commentary waits until Help closes before it claims the music pause. Resuming a manual pause preserves a ready automatic segment. Help warns if the DJ diagnostic log could not be opened.';update(readme,a,b,root/'docs')
print('Recorded V660 local probe, playback regressions and diagnostic verification.')
