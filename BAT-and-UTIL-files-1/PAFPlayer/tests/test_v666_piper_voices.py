import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v666_piper',root/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)

class Tests(unittest.TestCase):
    def test_second_voice_download_is_cached(self):
        base=Path(tempfile.mkdtemp(prefix='paf-male-test-'))
        bindir=base/'bin';bindir.mkdir();exe=bindir/'piper';exe.touch()
        (bindir/('python.exe' if dj.os.name=='nt' else 'python')).touch()
        calls=[]
        def download(args,cwd,valid):
            calls.append(args)
            (cwd/'en_US-ryan-medium.onnx').write_bytes(b'x'*50)
            (cwd/'en_US-ryan-medium.onnx.json').write_text(json.dumps({}),encoding='utf8')
        with mock.patch.object(dj,'_piper_setup_command',side_effect=download):
            first=dj.ensure_piper_male(str(exe),lambda s:None,lambda:True,base)
            second=dj.ensure_piper_male(str(exe),lambda s:None,lambda:True,base)
        self.assertEqual(first,second);self.assertEqual(len(calls),1)
        self.assertIn('en_US-ryan-medium',calls[0])

    def test_incomplete_download_reports_setup_error(self):
        base=Path(tempfile.mkdtemp(prefix='paf-male-fail-'));exe=base/'piper';exe.touch()
        (base/('python.exe' if dj.os.name=='nt' else 'python')).touch()
        with mock.patch.object(dj,'_piper_setup_command'):
            with self.assertRaises(dj.PiperSetupError):dj.ensure_piper_male(str(exe),lambda s:None,lambda:True,base)

if __name__=='__main__':unittest.main()
