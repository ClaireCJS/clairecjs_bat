import contextlib,importlib.util,io,unittest
from pathlib import Path
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('dj_between_fixture',HERE/'test_v657_dj_playback.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);p=base.p
import PAFPlayer_dj

class Tests(unittest.TestCase):
 def test_automatic_job_ready_mid_song_waits_until_next_track(self):
  dj=base.FakeDJ();dj.prepared=False;clock=[100.];commands=[];stage=[0]
  def factory(command,**kwargs):commands.append(command);return base.Process()
  def first_action():
   clock[0]+=1
   if clock[0]>145:raise AssertionError('first track did not finish')
   if stage[0]==0:stage[0]=1;dj.prepared=True;return None
   if stage[0]==1:
    self.assertFalse(dj.played);stage[0]=2;return p.NEXT_FILE
   return None
  def second_action():
   clock[0]+=1
   if clock[0]>180:raise AssertionError('second track did not finish')
   if dj.played and stage[0]==2:stage[0]=3;dj.play_done=True;return None
   if stage[0]==3 and len(commands)>=3:return p.STOP
   return None
  coordinator=p.PAFExternalPlaybackCoordinator(base.Monitor());coordinator.filter_action(None,False,0)
  def run(reader):
   return p.play_audio_file(HERE/'runs/dj-v657-stage/test-tone.wav',ffplay=Path('ffplay.exe'),duration_probe=lambda _:60,key_action_reader=reader,process_factory=factory,monotonic=lambda:clock[0],sleeper=lambda _:None,install_signal_handlers=False,drcs_visualizer=False,sixel_visualizer=False,lyrics_display=False,looping=False,now_playing_targets=[],initially_paused=False,paused_state=[False],manage_winamp=False,external_media_controller=coordinator,visualizer_input_source_state=[0],attribute_management_enabled=False,theory_modes={13,36})
  with contextlib.ExitStack() as stack:
   stack.enter_context(contextlib.redirect_stdout(io.StringIO()));stack.enter_context(mock.patch.object(PAFPlayer_dj,'get_controller',return_value=dj));stack.enter_context(mock.patch.object(p,'paf_workflows',return_value=object()))
   for name in ('update_lastfm_now_playing_async','append_pafplayer_trace','record_local_play_history','write_now_playing_files','start_background_audio_health_check','save_player_setting_value','set_console_title','scrobble_track_async','playlist_history_mark_played','save_spectrum_timeline_cache'):
    if hasattr(p,name):stack.enter_context(mock.patch.object(p,name))
   stack.enter_context(mock.patch.object(p,'LASTFM_SCROBBLING',False,create=True))
   first=run(first_action);self.assertEqual(p.NEXT_FILE,first);self.assertFalse(dj.played)
   second=run(second_action)
  self.assertEqual('stopped',second);self.assertTrue(dj.played);self.assertEqual(3,len(commands))

if __name__=='__main__':unittest.main()
