import importlib.util,os,tempfile,unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v661_dj_key',ROOT/'src/PAFPlayer_dj.py')
dj=importlib.util.module_from_spec(spec);spec.loader.exec_module(dj)

class Tests(unittest.TestCase):
 def test_private_key_overrides_stale_environment(self):
  root=Path(tempfile.mkdtemp(prefix='dj-key-test-'));p=root/'private.env'
  p.write_text('OPENAI_API_KEY_OLD=sk-'+('o'*32)+'\nOPENAI_API_KEY="sk-'+('n'*32)+'"\n',encoding='utf8')
  with mock.patch.object(dj,'dj_key_file',return_value=p),mock.patch.dict(os.environ,{'OPENAI_API_KEY':'sk-'+('e'*32)}):
   self.assertEqual('sk-'+('n'*32),dj.openai_key())
 def test_missing_or_invalid_private_key_uses_environment(self):
  root=Path(tempfile.mkdtemp(prefix='dj-key-fallback-'));p=root/'private.env';p.write_text('OPENAI_API_KEY=invalid\n',encoding='utf8')
  with mock.patch.object(dj,'dj_key_file',return_value=p),mock.patch.dict(os.environ,{'OPENAI_API_KEY':'environment-key'}):self.assertEqual('environment-key',dj.openai_key())
  with mock.patch.object(dj,'dj_key_file',return_value=root/'missing'),mock.patch.dict(os.environ,{'OPENAI_API_KEY':'environment-key'}):self.assertEqual('environment-key',dj.openai_key())
if __name__=='__main__':unittest.main()
