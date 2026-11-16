import importlib.util,io,sys,tempfile,threading,time,unittest
from pathlib import Path
from unittest import mock
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v675_player',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_voice_models as m

class Reporter:
 def __init__(self):self.messages=[];self.downloads=[];self.lines=[]
 def __call__(self,value):self.messages.append(value)
 def output(self,value):self.lines.append(value)
 def bytes(self,name,done,total,speed):self.downloads.append((name,done,total,speed))

class Response:
 def __init__(self,actual=25000,claimed=25000):self.stream=io.BytesIO(b'x'*actual);self.headers={'Content-Length':str(claimed)}
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,n):return self.stream.read(n)

class Tests(unittest.TestCase):
 def test_subprocess_output_is_visible_before_process_exits(self):
  got=threading.Event();lines=[];done=threading.Event()
  class Progress:
   def output(self,line):lines.append(line);got.set()
  code="import sys,time;print('Downloading 10%',flush=True);time.sleep(1.0);print('Download done',flush=True)"
  def worker():
   try:m.run_command([sys.executable,'-u','-c',code],progress=Progress(),timeout=10)
   finally:done.set()
  thread=threading.Thread(target=worker);thread.start()
  self.assertTrue(got.wait(3));self.assertFalse(done.is_set());self.assertIn('Downloading 10%',lines)
  thread.join(5);self.assertTrue(done.is_set());self.assertIn('Download done',lines)

 def test_direct_download_reports_real_bytes_and_total(self):
  folder=Path(tempfile.mkdtemp(prefix='paf-progress-test-'));r=Reporter()
  def command(args,**kwargs):
   if 'venv' in args:
    py=m.python_in(kwargs['cwd']);py.parent.mkdir(parents=True);py.write_bytes(b'python')
  with mock.patch.object(m,'run_command',side_effect=command),mock.patch.object(m.urllib.request,'urlopen',side_effect=lambda *a,**kw:Response()):
   m.install('kokoro',progress=r,root=folder)
  for name in ('kokoro-v1.0.onnx','voices-v1.0.bin'):
   relevant=[v for v in r.downloads if v[0]==name];self.assertTrue(relevant)
   self.assertEqual((25000,25000),relevant[-1][1:3])

 def test_truncated_download_is_not_reported_installed(self):
  folder=Path(tempfile.mkdtemp(prefix='paf-progress-truncated-'));r=Reporter()
  def command(args,**kwargs):
   if 'venv' in args:
    py=m.python_in(kwargs['cwd']);py.parent.mkdir(parents=True);py.write_bytes(b'python')
  with mock.patch.object(m,'run_command',side_effect=command),mock.patch.object(m.urllib.request,'urlopen',side_effect=lambda *a,**kw:Response(12000,25000)):
   with self.assertRaisesRegex(RuntimeError,'Incomplete'):m.install('kokoro',progress=r,root=folder)
  self.assertIsNone(m.installed('kokoro',folder))

 def test_output_redacts_url_queries(self):
  lines=[]
  m.run_command([sys.executable,'-u','-c',"print('https://example.com/file?token=secret')"],progress=lines.append,timeout=10)
  self.assertTrue(lines);self.assertNotIn('secret',' '.join(lines));self.assertIn('[redacted]',' '.join(lines))
if __name__=='__main__':unittest.main()
