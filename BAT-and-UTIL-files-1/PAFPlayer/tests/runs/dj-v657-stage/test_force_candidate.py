import contextlib,importlib.util,io,sys,unittest
from pathlib import Path
from unittest import mock
h=Path(__file__).parent;sp=importlib.util.spec_from_file_location('dj_playback_fixture',h/'test_playback_final.py');base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base);p=base.p
import PAFPlayer_dj
class DJ(base.FakeDJ):
 def __init__(self):super().__init__();self.prepared=False;self.options={'enabled':False};self.requests=0
 def start(self,forced=False,current=None):self.requests+=1;self.forced=True;self.prepared=True;return True
class Tests(unittest.TestCase):
 def test_force_command_in_paused_player_stays_paused(self):
  dj=DJ();clock=[100.];paused=[True];commands=[];sent=[False];finished=[False]
  def factory(command,**kwargs):commands.append(command);return base.Process()
  def action():
   clock[0]+=1
   if clock[0]>130:raise AssertionError('did not finish')
   if paused[0] and not sent[0]:sent[0]=True;return p._HASH_COMMAND_PREFIX+'djforce'
   if dj.played and not finished[0]:finished[0]=True;dj.play_done=True;return None
   if finished[0]:return p.STOP
   return None
  coordinator=p.PAFExternalPlaybackCoordinator(base.Monitor());coordinator.filter_action(None,False,0)
  with contextlib.ExitStack() as stack:
   stack.enter_context(contextlib.redirect_stdout(io.StringIO()));stack.enter_context(mock.patch.object(PAFPlayer_dj,'get_controller',return_value=dj));stack.enter_context(mock.patch.object(p,'paf_workflows',return_value=object()))
   for name in ('update_lastfm_now_playing_async','append_pafplayer_trace','record_local_play_history','write_now_playing_files','start_background_audio_health_check','save_player_setting_value','set_console_title','scrobble_track_async','playlist_history_mark_played','save_spectrum_timeline_cache'):
    if hasattr(p,name):stack.enter_context(mock.patch.object(p,name))
   stack.enter_context(mock.patch.object(p,'LASTFM_SCROBBLING',False,create=True))
   result=p.play_audio_file(h/'test-tone.wav',ffplay=Path('ffplay.exe'),duration_probe=lambda _:60,key_action_reader=action,process_factory=factory,monotonic=lambda:clock[0],sleeper=lambda _:None,install_signal_handlers=False,drcs_visualizer=False,sixel_visualizer=False,lyrics_display=False,looping=False,now_playing_targets=[],initially_paused=True,paused_state=paused,manage_winamp=False,external_media_controller=coordinator,visualizer_input_source_state=[0],attribute_management_enabled=False,theory_modes={13,36})
  self.assertEqual('stopped',result);self.assertEqual(1,dj.requests);self.assertTrue(dj.played);self.assertEqual(1,len(commands))
if __name__=='__main__':unittest.main()
