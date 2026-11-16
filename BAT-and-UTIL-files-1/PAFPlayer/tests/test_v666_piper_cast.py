import importlib.util
from pathlib import Path
import unittest
from unittest import mock

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v666_cast',root/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)

class Tests(unittest.TestCase):
    def test_default_automatic_piper_cast_uses_both_models(self):
        models=[]
        class Input:
            def write(self,data):pass
            def close(self):pass
        class Process:
            returncode=0
            stdin=Input()
            def __init__(self,args,**kwargs):
                models.append(args[args.index('-m')+1]);Path(args[args.index('-f')+1]).write_bytes(b'x'*50)
            def poll(self):return 0
        opts=dj.settings({'speech_provider':'piper'})
        with mock.patch.object(dj,'dialogue',return_value=([(1,'one'),(2,'two')],'')), \
             mock.patch.object(dj.shutil,'which',return_value=None), \
             mock.patch.object(dj,'ensure_piper',return_value=('piper','woman.onnx')), \
             mock.patch.object(dj,'ensure_piper_male',return_value='man.onnx'), \
             mock.patch.object(dj.subprocess,'Popen',side_effect=Process):
            files,warning=dj.synthesize([{'artist':'a','title':'b'}],opts,lambda s:None,lambda:True)
        self.assertEqual(['woman.onnx','man.onnx'],models);self.assertEqual(2,len(files));self.assertEqual('',warning)

if __name__=='__main__':unittest.main()
