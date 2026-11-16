import unittest
from types import SimpleNamespace
from pathlib import Path
from dj_pipeline import synthesize
class PipelineTests(unittest.TestCase):
 def test_openai_success(self):
  calls=[]
  def voice(text,name,path):calls.append((text,name));path.write_bytes(b'audio')
  result=synthesize([{'artist':'A','title':'B'}],SimpleNamespace(speakers=2),ollama_model='m',piper_command=[],piper_models=[],openai_text=lambda h,s:[(1,'hello'),(2,'hi')],openai_voice=voice)
  self.assertEqual(2,len(result['files']));self.assertNotEqual(calls[0][1],calls[1][1]);self.assertEqual([],result['warnings'])
 def test_cloud_fallback_once(self):
  count=[]
  def fail(*args):count.append(1);raise RuntimeError('secret should not be shown')
  def run(args,**kwargs):Path(args[args.index('-f')+1]).write_bytes(b'0'*100);return SimpleNamespace(returncode=0)
  result=synthesize([{'artist':'A','title':'B'}],SimpleNamespace(speakers=2),ollama_model='m',piper_command=['piper'],piper_models=['model'],openai_text=fail,ollama_text=lambda *x:[(1,'a'),(2,'b')],openai_voice=fail,run=run)
  self.assertEqual(2,len(result['files']));self.assertEqual(2,len(count));self.assertNotIn('secret',str(result))
 def test_no_piper_is_visible(self):
  def fail(*args):raise RuntimeError('failed')
  with self.assertRaisesRegex(RuntimeError,'Piper'):
   synthesize([{'title':'B'}],SimpleNamespace(speakers=1),ollama_model='m',piper_command=[],piper_models=[],openai_text=lambda *x:[(1,'a')],openai_voice=fail)
if __name__=='__main__':unittest.main()
