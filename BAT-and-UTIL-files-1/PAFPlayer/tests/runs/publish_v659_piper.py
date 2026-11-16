from pathlib import Path
import datetime, hashlib, shutil
root=Path(__file__).resolve().parents[2]
def replace(path,data,archive):
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');backup=path.with_name(name);i=0
    while backup.exists():
        i+=1;backup=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,backup);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(backup.read_bytes()).digest()
    path.write_text(data,encoding='utf8',newline='');dest=archive/backup.name;i=0
    while dest.exists():
        i+=1;dest=archive/(backup.stem+f' ({i})'+backup.suffix)
    shutil.move(str(backup),str(dest))
def once(text,old,new):
    assert text.count(old)==1,(old[:80],text.count(old))
    return text.replace(old,new,1)
dj=(root/'tests/runs/PAFPlayer_dj_v659_candidate_v2.py').read_text(encoding='utf8')
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True)
idx=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines)
text=once(text,"'2026-11-11-v658-dj-help-commentary'","'2026-11-11-v659-piper-auto-setup'")
text=once(text,"PROGRAM_VERSION                = 'V658'","PROGRAM_VERSION                = 'V659'")
text=once(text,"PROGRAM_RELEASE_LABEL          = 'V658'","PROGRAM_RELEASE_LABEL          = 'V659'")
text=once(text,'placeholder="Blank = first installed model"','placeholder="Blank = smallest installed model"')
text=once(text,'placeholder="Blank = search PATH"','placeholder="Blank = automatic setup"')
old='<p>Local speech requires Piper and one or more voice models; <a href="https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md" target="_blank" rel="noopener">Piper installation and voice downloads</a>. Its installer and selected voice models are downloaded separately; for example, en_US-lessac-medium downloads a 63.2 MB model plus its small JSON configuration; download both files together. Piper and dependencies are additional. PAFPlayer does not overwrite existing installations.</p>'
new='<p>When local speech is needed, PAFPlayer automatically installs Piper and a default voice in private storage if needed. The download includes a 63.2 MB voice model plus Piper and dependencies. Setup runs in the background; existing installations and configured voices are preserved. See <a href="https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md" target="_blank" rel="noopener">Piper voice documentation</a>.</p>'
text=once(text,old,new);compile(dj,'src','exec');compile(text,str(p),'exec')
release=root/'releases/PAFPlayer_v659_piper_auto_setup.py';notes=root/'releases/PAFPlayer_v659_piper_auto_setup_release_notes.md'
assert not release.exists() and not notes.exists()
replace(root/'src/PAFPlayer_dj.py',dj,root/'backups');replace(p,text,root/'releases');release.write_text(text,encoding='utf8',newline='')
test=root/'tests/test_v658_dj_help.py';testtext=test.read_text(encoding='utf8')
testtext=once(testtext,"        with mock.patch.object(dj, 'dialogue', return_value=([(1, 'A little introduction.'), (2, 'Hello!')], '')):","        with mock.patch.object(dj, 'dialogue', return_value=([(1, 'A little introduction.'), (2, 'Hello!')], '')), mock.patch.object(dj.shutil, 'which', return_value=None), mock.patch.object(dj, 'ensure_piper', side_effect=RuntimeError('unavailable')):")
replace(test,testtext,root/'backups')
test=root/'tests/test_v659_piper_setup.py';testtext=test.read_text(encoding='utf8');testtext=once(testtext,"candidate = ROOT / 'tests/runs/PAFPlayer_dj_v659_candidate_v2.py'","candidate = ROOT / 'src/PAFPlayer_dj.py'");replace(test,testtext,root/'backups')
readme=root/'docs/README.md';doc=readme.read_text(encoding='utf8')
doc=once(doc,'Current release: **V658** — AI DJ commentary in Help.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v658_dj_help_commentary_release_notes.md).','Current release: **V659** — automatic Piper setup for AI DJ speech.\n[Release notes, testing, and limitations](../releases/PAFPlayer_v659_piper_auto_setup_release_notes.md).')
doc=once(doc,'If cloud speech fails, local speech requires Piper and one or more downloaded `.onnx` voices plus their matching `.onnx.json` files.','If cloud speech fails, the DJ automatically sets up Piper and a default local voice when needed. Setup downloads Piper and dependencies plus the 63.2 MB voice model in a new private folder under `%LOCALAPPDATA%\\PAFPlayer\\support\\piper`. It runs in the background and verifies a real speech file before marking the install ready. Existing configured executable and voice paths are retained.')
start=doc.index('To set up Piper, follow the [Piper installation and voice-download guide]');end=doc.index('\n\nGenerated commentary WAVs',start)
doc=doc[:start]+'''You can still follow the [Piper installation and voice-download guide](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md) and provide executable and ONNX paths in the web settings. Model licences and accents vary; consult the chosen model’s card. An automatically installed default voice is reused for speakers without configured local voices. A running Ollama server with at least one downloaded model is separately required for local text. Setup failures appear in Help without stopping the music; retry with `#djforce` after correcting the cause. Incomplete setup folders are retained and are not reused.''' + doc[end:]
doc=once(doc,'The tested OpenAI key returned HTTP 401 and Piper was not installed; real speech remains unverified.','Both tested OpenAI keys returned HTTP 401. Piper speech synthesis was verified in an isolated Windows environment using the default voice.')
replace(readme,doc,root/'docs')
changelog=root/'docs/PAFPlayer_changelog.md';doc=changelog.read_text(encoding='utf8');doc=once(doc,'# PAFPlayer changelog\n','# PAFPlayer changelog\n\n## V659 — November 11, 2026\n\nAutomatically install and verify private Piper speech and a default voice when local DJ speech is needed. Existing configured paths are retained; setup runs in the background and keeps incomplete attempts. [Release notes](../releases/PAFPlayer_v659_piper_auto_setup_release_notes.md).\n');replace(changelog,doc,root/'backups')
notes.write_text('''# PAFPlayer V659 — automatic Piper setup

When the DJ needs local speech and Piper or its voice is missing, it creates a separate private environment, downloads Piper and the en_US-lessac-medium voice, and verifies actual speech synthesis. It keeps existing installations, user-selected executable and voice paths, and incomplete attempts. Setup runs in the background; failure leaves generated text visible in Help and does not stop music. The default model download is about 63.2 MB plus Piper and dependencies.

Python 3.10 on Windows uses ONNX Runtime 1.19.0, because the newer version failed to load on the test machine. A real Piper-generated WAV was verified in an isolated environment. OpenAI credentials tested on this machine returned HTTP 401. The editable DJ module matches its single-file bundle; no literal C:\\BAT files were changed.
''',encoding='utf8')
print('Published V659 player, source, release, tests, and documentation.')
