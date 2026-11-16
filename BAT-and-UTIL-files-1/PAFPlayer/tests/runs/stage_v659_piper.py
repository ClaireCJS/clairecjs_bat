from pathlib import Path

root = Path(__file__).resolve().parents[2]
src = (root/'src/PAFPlayer_dj.py').read_text(encoding='utf-8')
def once(text, before, after):
    assert text.count(before)==1, (before, text.count(before))
    return text.replace(before,after,1)
src=once(src,'import subprocess\n','import subprocess\nimport sys\n')
anchor='def synthesize(history,opts,stage,valid,on_dialogue=None):\n'
helper='''class PiperSetupError(RuntimeError):
    """A safe, user-facing Piper setup error without subprocess output."""


def piper_support_root():
    base = os.environ.get('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Local')
    return Path(base) / 'PAFPlayer' / 'support' / 'piper'


def installed_piper(root=None):
    root = Path(root) if root is not None else piper_support_root()
    if not root.is_dir(): return None
    for folder in sorted(root.glob('install-*'), reverse=True):
        exe = folder / 'venv' / ('Scripts/piper.exe' if os.name == 'nt' else 'bin/piper')
        voice = folder / 'voices' / 'en_US-lessac-medium.onnx'
        config = voice.with_name(voice.name + '.json')
        if (folder / 'complete').is_file() and exe.is_file() and voice.is_file() and voice.stat().st_size > 44 and config.is_file():
            return str(exe), str(voice)
    return None


def _piper_setup_command(args, cwd, valid, timeout=600):
    if not valid(): raise InterruptedError()
    try:
        process = subprocess.Popen(args, cwd=str(cwd), stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    except OSError as exc:
        raise PiperSetupError('Piper setup could not start; check Python and permissions') from exc
    deadline = time.monotonic() + timeout
    try:
        while process.poll() is None:
            if not valid() or time.monotonic() >= deadline:
                process.terminate()
                try: process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill(); process.wait(timeout=3)
                if not valid(): raise InterruptedError()
                raise PiperSetupError('Piper setup timed out; check the network and try again')
            time.sleep(.1)
        if process.returncode:
            raise PiperSetupError('Piper setup failed; check Python, network access, and free space')
    finally:
        if process.poll() is None: process.terminate()


def ensure_piper(stage, valid, root=None):
    """Install Piper and one voice in a unique private folder, or reuse a completed set."""
    existing = installed_piper(root)
    if existing: return existing
    if not valid(): raise InterruptedError()
    base = Path(root) if root is not None else piper_support_root()
    try:
        base.mkdir(parents=True, exist_ok=True)
        folder = Path(tempfile.mkdtemp(prefix='install-', dir=str(base)))
        voices = folder / 'voices'; voices.mkdir()
        venv = folder / 'venv'
        python = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        stage('Installing Piper: creating isolated environment')
        _piper_setup_command([sys.executable, '-m', 'venv', str(venv)], folder, valid)
        stage('Installing Piper: downloading packages')
        _piper_setup_command([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir', 'piper-tts'], folder, valid)
        stage('Installing Piper: downloading voice')
        _piper_setup_command([str(python), '-m', 'piper.download_voices', '--data-dir', str(voices), 'en_US-lessac-medium'], folder, valid)
        exe = venv / ('Scripts/piper.exe' if os.name == 'nt' else 'bin/piper')
        voice = voices / 'en_US-lessac-medium.onnx'
        config = voice.with_name(voice.name + '.json')
        if not exe.is_file() or not voice.is_file() or voice.stat().st_size <= 44 or not config.is_file():
            raise PiperSetupError('Piper setup did not produce a complete voice')
        with config.open('r', encoding='utf8') as stream: json.load(stream)
        if not valid(): raise InterruptedError()
        with (folder / 'complete').open('x', encoding='utf8') as stream: stream.write('piper-tts; en_US-lessac-medium\\n')
        return str(exe), str(voice)
    except (InterruptedError, PiperSetupError):
        raise
    except (OSError, ValueError) as exc:
        raise PiperSetupError('Piper setup failed; check Python, network access, and free space') from exc


'''
src=once(src,anchor,helper+anchor)
src=once(src,"            if not exe or not voices: raise RuntimeError('Piper executable and voice model paths are required for local speech')", "            if not exe or not voices:\n                auto_exe, auto_voice = ensure_piper(stage, valid)\n                exe = exe or auto_exe\n                voices = voices or [auto_voice]")
src=once(src,"                        self.error=('DJ speech failed; text is available in Help. Check OpenAI and Piper settings' if published else 'DJ text generation failed; check OpenAI and Ollama settings')", "                        self.error=(str(exc) if isinstance(exc, PiperSetupError) else ('DJ speech failed; text is available in Help. Check OpenAI and Piper settings' if published else 'DJ text generation failed; check OpenAI and Ollama settings'))")
compile(src,'candidate','exec')
out=root/'tests/runs/PAFPlayer_dj_v659_candidate.py'
assert not out.exists();out.write_text(src,encoding='utf-8')
print(out)
