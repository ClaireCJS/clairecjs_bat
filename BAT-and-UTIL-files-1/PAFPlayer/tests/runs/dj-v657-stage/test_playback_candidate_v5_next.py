import contextlib,importlib.util,io,sys,threading,unittest
from pathlib import Path
from unittest import mock
root=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('paf_candidate_dj',Path(__file__).parent/'PAFPlayer_candidate_v6.py');p=importlib.util.module_from_spec(spec);sys.modules[spec.name]=p;spec.loader.exec_module(p)
import PAFPlayer_dj
class Monitor:
 def snapshot(self,now):return {'known':True,'active':()}
class Process:
 def __init__(self):self.running=True
 def poll(self):return None if self.running else 0
 def terminate(self):self.running=False
 kill=terminate
 def wait(self,timeout=None):self.running=False;return 0
class FakeDJ:
 def __init__(self):self.lock=threading.RLock();self.error='';self.notice='';self.stage='';self.forced=False;self.play_done=False;self.prepared=True;self.played=False;self.cancelled=False
 def due(self):return self.prepared
 def take(self):self.prepared=False;self.forced=False;return ['test.wav']
 def play(self,files,exe):self.played=True;return True
 def cancel_request(self):self.cancelled=True;self.forced=False;self.prepared=False
 def cancel_playback(self):pass
 def track_changed(self):pass
 def record(self,*args,**kwargs):pass
class PlaybackTests(unittest.TestCase):
 def run_case(self,manual_pause,initial=False,skip=False):
  dj=FakeDJ();dj.forced=initial;clock=[100.];paused=[initial];commands=[];once=[False]
  def factory(command,**kwargs):commands.append(command);return Process()
  def action():
   clock[0]+=1
   if clock[0]>130:raise AssertionError('Mock playback did not finish')
   if paused[0] and not once[0]:
    if initial and not dj.played:return None
    once[0]=True
    if skip:return p.NEXT_FILE
    if manual_pause:return p.WEB_PAUSE
    dj.play_done=True;return None
   if ((manual_pause or initial) and once[0]) or len(commands)>=2:return p.STOP
   return None
  coordinator=p.PAFExternalPlaybackCoordinator(Monitor());coordinator.filter_action(None,False,0)
  fixture=Path(__file__).parent/'test-tone.wav'
  with contextlib.ExitStack() as stack:
   stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
   stack.enter_context(mock.patch.object(PAFPlayer_dj,'get_controller',return_value=dj))
   stack.enter_context(mock.patch.object(p,'paf_workflows',return_value=object()))
   for name in ('update_lastfm_now_playing_async','append_pafplayer_trace','record_local_play_history','write_now_playing_files','start_background_audio_health_check','save_player_setting_value','set_console_title','scrobble_track_async','playlist_history_mark_played','save_spectrum_timeline_cache'):
    if hasattr(p,name):stack.enter_context(mock.patch.object(p,name))
   stack.enter_context(mock.patch.object(p,'LASTFM_SCROBBLING',False,create=True))
   result=p.play_audio_file(fixture,ffplay=Path('ffplay.exe'),duration_probe=lambda _:60,key_action_reader=action,process_factory=factory,monotonic=lambda:clock[0],sleeper=lambda _:None,install_signal_handlers=False,drcs_visualizer=False,sixel_visualizer=False,lyrics_display=False,looping=False,now_playing_targets=[],initially_paused=initial,paused_state=paused,manage_winamp=False,external_media_controller=coordinator,visualizer_input_source_state=[0],attribute_management_enabled=False,theory_modes={13,36})
  return result,dj,commands,paused
 def test_dj_resumes_after_completion(self):
  result,dj,commands,paused=self.run_case(False);self.assertEqual('stopped',result);self.assertTrue(dj.played);self.assertEqual(2,len(commands))
 def test_user_pause_prevents_automatic_resume(self):
  result,dj,commands,paused=self.run_case(True);self.assertEqual('stopped',result);self.assertTrue(dj.cancelled);self.assertEqual(1,len(commands))
 def test_forced_playback_while_paused_never_resumes_music(self):
  result,dj,commands,paused=self.run_case(False,initial=True);self.assertEqual('stopped',result);self.assertTrue(dj.played);self.assertEqual(1,len(commands))
 def test_skip_stops_commentary_without_restart(self):
  result,dj,commands,paused=self.run_case(False,skip=True);self.assertEqual(p.NEXT_FILE,result);self.assertTrue(dj.cancelled);self.assertEqual(1,len(commands))
if __name__=='__main__':unittest.main()
