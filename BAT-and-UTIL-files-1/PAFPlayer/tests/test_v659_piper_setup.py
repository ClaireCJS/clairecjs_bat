import importlib.util
import io
import json
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
candidate = ROOT / 'src/PAFPlayer_dj.py'
spec = importlib.util.spec_from_file_location('piper_v659', candidate)
dj = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dj)


class SetupTests(unittest.TestCase):
    def test_setup_creates_verified_install_and_reuses_it(self):
        root = Path(tempfile.mkdtemp(prefix='paf-piper-test-'))
        stages = []
        def run(args, folder, valid, timeout=600):
            folder = Path(folder)
            if 'venv' in args:
                python = Path(args[-1]) / ('Scripts/python.exe' if dj.os.name == 'nt' else 'bin/python')
                python.parent.mkdir(parents=True)
                python.write_bytes(b'python')
            elif 'pip' in args:
                exe = folder / 'venv' / ('Scripts/piper.exe' if dj.os.name == 'nt' else 'bin/piper')
                exe.write_bytes(b'piper')
            elif 'piper.download_voices' in args:
                voice = folder / 'voices/en_US-lessac-medium.onnx'
                voice.write_bytes(b'x' * 100)
                voice.with_name(voice.name + '.json').write_text('{}', encoding='utf8')
            else:
                with wave.open(str(folder/'setup-test.wav'), 'wb') as wav:
                    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(22050); wav.writeframes(b'\0\0'*20)
        with mock.patch.object(dj, '_piper_setup_command', side_effect=run) as command:
            result = dj.ensure_piper(stages.append, lambda: True, root)
            self.assertEqual(result, dj.ensure_piper(stages.append, lambda: True, root))
            self.assertEqual(4, command.call_count)
        self.assertTrue(Path(result[0]).is_file())
        self.assertTrue(Path(result[1]).is_file())
        self.assertTrue(any('verifying speech' in stage for stage in stages))

    def test_incomplete_attempt_is_not_reused_and_cancel_does_not_complete(self):
        root = Path(tempfile.mkdtemp(prefix='paf-piper-cancel-'))
        with mock.patch.object(dj, '_piper_setup_command', side_effect=InterruptedError):
            with self.assertRaises(InterruptedError):
                dj.ensure_piper(lambda _: None, lambda: True, root)
        self.assertIsNone(dj.installed_piper(root))
        self.assertEqual(1, len(list(root.glob('install-*'))))

    def test_local_fallback_installs_once_and_uses_configured_voice(self):
        voice=Path(tempfile.mkdtemp(prefix='paf-custom-voice-'))/'custom-voice';voice.write_bytes(b'voice')
        opts = dj.settings({'speech_provider':'piper', 'piper_voices':str(voice)})
        seen = []
        def run(args, **kwargs):
            seen.append(args)
            output=Path(args[args.index('-f')+1]); output.write_bytes(b'x'*100)
            return SimpleNamespace(stdin=io.BytesIO(), poll=lambda:0, returncode=0)
        with mock.patch.object(dj, 'dialogue', return_value=([(1,'a'),(2,'b')],'')), \
             mock.patch.object(dj.shutil, 'which', return_value=None), \
             mock.patch.object(dj, 'ensure_piper', return_value=('auto-piper','auto-voice')) as install, \
             mock.patch.object(dj.subprocess, 'Popen', side_effect=run):
            files, _ = dj.synthesize([{'artist':'a','title':'b'}],opts,lambda _:None,lambda:True)
        self.assertEqual(2,len(files)); self.assertEqual(1,install.call_count)
        self.assertEqual(['auto-piper','auto-piper'],[args[0] for args in seen])
        self.assertTrue(all(args[args.index('-m')+1]==str(voice) for args in seen))

    def test_failure_keeps_dialogue_available(self):
        with mock.patch.object(dj,'dialogue',return_value=([(1,'hello')],'')), \
             mock.patch.object(dj.shutil,'which',return_value=None), \
             mock.patch.object(dj,'ensure_piper',side_effect=dj.PiperSetupError('setup failed')):
            seen=[]
            with self.assertRaises(dj.PiperSetupError):
                dj.synthesize([{'artist':'a','title':'b'}],dj.settings({'speech_provider':'piper'}),lambda _:None,lambda:True,on_dialogue=seen.extend)
            self.assertEqual([(1,'hello')],seen)

if __name__=='__main__': unittest.main()
