import importlib.util,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('v676_player',root/'PAFPlayer.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_wav_menu as menu
import PAFPlayer_dj as dj
class Tests(unittest.TestCase):
 def test_send_to_running_player(self):
  folder=Path(tempfile.mkdtemp());wav=folder/'a.wav';wav.write_bytes(b'WAVE')
  instance=mock.Mock();instance.acquire.return_value=False;instance.forward.return_value={'ok':True};spawn=mock.Mock()
  self.assertEqual('queued',menu.queue_or_play(wav,runtime=object(),script=root/'PAFPlayer.py',instance_factory=lambda _:instance,spawn=spawn))
  self.assertEqual(str(wav.resolve()),instance.forward.call_args.args[0]['selectors'][0]['value']);spawn.assert_not_called();instance.close.assert_called_once()
 def test_start_player_when_no_instance(self):
  folder=Path(tempfile.mkdtemp());wav=folder/'a.wav';wav.write_bytes(b'WAVE');instance=mock.Mock();instance.acquire.return_value=True;spawn=mock.Mock()
  self.assertEqual('launched',menu.queue_or_play(wav,runtime=object(),script=root/'PAFPlayer.py',instance_factory=lambda _:instance,spawn=spawn))
  self.assertIn(str(wav.resolve()),spawn.call_args.args[0]);instance.close.assert_called_once()
 def test_failure_does_not_start_duplicate(self):
  folder=Path(tempfile.mkdtemp());wav=folder/'a.wav';wav.write_bytes(b'WAVE');instance=mock.Mock();instance.acquire.return_value=False;instance.forward.side_effect=ValueError('no listener');spawn=mock.Mock()
  with self.assertRaises(ValueError):menu.queue_or_play(wav,runtime=object(),script=root/'PAFPlayer.py',instance_factory=lambda _:instance,spawn=spawn)
  spawn.assert_not_called()
 def test_dj_request_contains_lyrics_and_not_local_path(self):
  options=dj.settings({'text_provider':'auto'});options['_new_track_count']=1
  response={'output':[{'content':[{'type':'output_text','text':'[{"speaker":1,"text":"A lyric."}]'}]}]}
  with mock.patch.object(dj,'openai_key',return_value='fake'),mock.patch.object(dj,'post_json',return_value=response) as send:
   dj.dialogue([{'artist':'Artist','title':'Title','lyrics':'the lyric','_path':'private/path'}],options)
  args=send.call_args.args;self.assertIn('the lyric',args[1]['input']);self.assertNotIn('private/path',args[1]['input']);self.assertIn('Never invent personal experiences',args[1]['instructions'])
 def test_command_quotes_file_placeholder(self):self.assertTrue(menu.command_for('player.py',python='python.exe').endswith('"%1"'))
if __name__=='__main__':unittest.main()
