from pathlib import Path
root=Path(__file__).resolve().parents[2]
src=(root/'tests/runs/PAFPlayer_dj_v659_candidate.py').read_text(encoding='utf-8')
def once(s, old, new):
    assert s.count(old)==1, (old, s.count(old))
    return s.replace(old,new,1)
old="        _piper_setup_command([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir', 'piper-tts'], folder, valid)"
new="""        packages = ['piper-tts']
        if os.name == 'nt' and sys.version_info[:2] == (3, 10):
            packages.append('onnxruntime==1.19.0')
        _piper_setup_command([str(python), '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir', *packages], folder, valid)"""
src=once(src,old,new)
old="        with config.open('r', encoding='utf8') as stream: json.load(stream)\n        if not valid(): raise InterruptedError()"
new="""        with config.open('r', encoding='utf8') as stream: json.load(stream)
        stage('Installing Piper: verifying speech')
        smoke = folder / 'setup-test.wav'
        _piper_setup_command([str(exe), '-m', str(voice), '-f', str(smoke), '--', 'Piper speech setup is ready.'], folder, valid, timeout=120)
        try:
            with wave.open(str(smoke), 'rb') as wav:
                if wav.getnframes() <= 0: raise ValueError('Empty speech')
        except (OSError, ValueError, wave.Error) as exc:
            raise PiperSetupError('Piper setup could not verify speech on this computer') from exc
        if not valid(): raise InterruptedError()"""
src=once(src,old,new)
old="        with self.lock:return {'settings':dict(self.options),'stage':self.stage if self.forced else '',"
new="        with self.lock:\n            private = installed_piper()\n            return {'settings':dict(self.options),'stage':self.stage if self.forced else '',"
src=once(src,old,new)
src=once(src,"'piper_available':bool((self.options['piper_executable'] and Path(self.options['piper_executable']).is_file()) or shutil.which('piper')),", "'piper_available':bool((self.options['piper_executable'] and Path(self.options['piper_executable']).is_file()) or shutil.which('piper') or private),")
src=once(src,"'piper_voices_found':sum(Path(x.strip()).is_file() for x in self.options['piper_voices'].splitlines() if x.strip())}", "'piper_voices_found':sum(Path(x.strip()).is_file() for x in self.options['piper_voices'].splitlines() if x.strip()) + (1 if private and not self.options['piper_voices'].strip() else 0)}")
compile(src,'candidate','exec'); out=root/'tests/runs/PAFPlayer_dj_v659_candidate_v2.py';assert not out.exists();out.write_text(src,encoding='utf-8');print(out)
