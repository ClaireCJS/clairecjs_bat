from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):
    assert s.count(a)==1,(a[:100],s.count(a));return s.replace(a,b,1)
def replace(path,data,archive):
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=path.with_name(name);n=0
    while b.exists():n+=1;b=path.with_name(name[:-4]+f' ({n}).bak')
    shutil.copy2(path,b);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    path.write_text(data,encoding='utf8',newline='');dest=archive/b.name;n=0
    while dest!=b and dest.exists():n+=1;dest=archive/(b.stem+f' ({n})'+b.suffix)
    if dest!=b:shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_dj.py';s=src.read_text(encoding='utf8')
anchor='def synthesize(history,opts,stage,valid,on_dialogue=None):'
new='''def ensure_piper_male(auto_exe, stage, valid, root=None):
    """Download a second default voice to a unique folder; reuse completed downloads."""
    base = Path(root) if root is not None else piper_support_root()
    for folder in sorted(base.glob('male-voice-*')) if base.is_dir() else ():
        voice = folder / 'en_US-ryan-medium.onnx'
        config = voice.with_name(voice.name + '.json')
        if (folder / 'complete').is_file() and voice.is_file() and voice.stat().st_size > 44 and config.is_file():
            return str(voice)
    if not valid(): raise InterruptedError()
    try:
        base.mkdir(parents=True, exist_ok=True)
        folder = Path(tempfile.mkdtemp(prefix='male-voice-', dir=str(base)))
        python = Path(auto_exe).parent / ('python.exe' if os.name == 'nt' else 'python')
        if not python.is_file(): raise PiperSetupError('Piper Python environment is unavailable')
        stage('Installing Piper: downloading second voice')
        _piper_setup_command([str(python), '-m', 'piper.download_voices', '--data-dir', str(folder), 'en_US-ryan-medium'], folder, valid)
        voice = folder / 'en_US-ryan-medium.onnx'; config = voice.with_name(voice.name + '.json')
        if not voice.is_file() or voice.stat().st_size <= 44 or not config.is_file(): raise PiperSetupError('Piper second voice download was incomplete')
        with config.open('r', encoding='utf8') as stream: json.load(stream)
        if not valid(): raise InterruptedError()
        with (folder / 'complete').open('x', encoding='utf8') as stream: stream.write('en_US-ryan-medium\\n')
        return str(voice)
    except (InterruptedError, PiperSetupError): raise
    except (OSError, ValueError) as exc: raise PiperSetupError('Piper second voice setup failed') from exc


'''+anchor
s=once(s,anchor,new)
old='''                exe = exe or auto_exe
                voices = voices or [auto_voice]
            if path.exists():'''
new='''                exe = exe or auto_exe
                if not voices:
                    voices = [auto_voice]
                    if opts['men'] and opts['speakers'] > 1:
                        try: voices.append(ensure_piper_male(auto_exe, stage, valid))
                        except PiperSetupError:
                            warning=(warning+'; ' if warning else '')+'Second Piper voice unavailable; using one local voice'
            if path.exists():'''
s=once(s,old,new);compile(s,str(src),'exec')
p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1;lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(s)+'\n';text=''.join(lines);compile(text,str(p),'exec')
release=root/'releases/PAFPlayer_v666_dj_force.py';readme=root/'docs/README.md';docs=readme.read_text(encoding='utf8')
docs=once(docs,'Piper uses the configured voice models; its automatic installation currently provides one voice, so configure two Piper voice models for distinct local voices.','Piper uses configured voice models when provided; otherwise it automatically installs its default voices, including a second voice for the default cast. If the second voice cannot be downloaded, it falls back to one voice and reports a warning.')
notes=root/'releases/PAFPlayer_v666_dj_force_release_notes.md';nt=notes.read_text(encoding='utf8')
nt=once(nt,'The automatic Piper installation currently includes one voice model; configure two models for distinct local voices.','For the default cast, Piper automatically downloads a second voice when needed; if unavailable, it uses the first voice and reports a warning. Explicitly configured voice models remain unchanged.')
replace(src,s,root/'backups');replace(p,text,root/'releases');replace(release,text,root/'releases');replace(readme,docs,root/'docs');replace(notes,nt,root/'releases')
print('Added on-demand second Piper voice with verified backups.')
