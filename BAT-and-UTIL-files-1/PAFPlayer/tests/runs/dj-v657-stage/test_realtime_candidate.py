import base64,importlib.util,json,os,sys,tempfile,types,unittest,wave
from pathlib import Path
from unittest import mock
path=Path(__file__).parent/'PAFPlayer_dj_candidate_v5.py';spec=importlib.util.spec_from_file_location('dj_voice_test',path);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class Socket:
 def __init__(self):self.messages=[];self.events=iter([{'type':'session.created'},{'type':'response.output_audio.delta','delta':base64.b64encode(b'\0\0'*200).decode()},{'type':'response.done','response':{'status':'completed'}}]);self.closed=False
 def send(self,s):self.messages.append(json.loads(s))
 def recv(self):return json.dumps(next(self.events))
 def close(self):self.closed=True
class RealtimeTests(unittest.TestCase):
 def test_wav_protocol_and_collision(self):
  sock=Socket();fake=types.SimpleNamespace(create_connection=lambda *a,**k:sock);path=Path(tempfile.mkdtemp(prefix='paf-dj-test-'))/'voice.wav'
  with mock.patch.dict(sys.modules,{'websocket':fake}),mock.patch.dict(os.environ,{'OPENAI_API_KEY':'example'}):d.speech_openai('hello','marin','neutral','test-model',path)
  with wave.open(str(path),'rb') as f:self.assertEqual((1,2,24000),(f.getnchannels(),f.getsampwidth(),f.getframerate()))
  self.assertTrue(sock.closed);self.assertEqual('marin',sock.messages[0]['session']['audio']['output']['voice'])
  sock2=Socket();fake.create_connection=lambda *a,**k:sock2
  with mock.patch.dict(sys.modules,{'websocket':fake}),mock.patch.dict(os.environ,{'OPENAI_API_KEY':'example'}):
   with self.assertRaises(FileExistsError):d.speech_openai('hello','marin','neutral','test-model',path)
 def test_current_realtime_voices(self):
  self.assertEqual({'alloy','ash','ballad','coral','echo','sage','shimmer','verse','marin','cedar'},set(d.VOICES))
if __name__=='__main__':unittest.main()
