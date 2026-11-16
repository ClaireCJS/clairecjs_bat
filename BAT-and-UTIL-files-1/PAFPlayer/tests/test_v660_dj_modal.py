import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('dj_modal_fixture',HERE/'test_v657_dj_playback.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
p=base.p
import PAFPlayer_dj

class DJ(base.FakeDJ):
    def __init__(self):
        super().__init__();self.prepared=False;self.dismissed=False;self.early_take=False
    def take(self):
        if not self.dismissed:self.early_take=True
        return super().take()

class Tests(unittest.TestCase):
    def test_ready_job_waits_for_help_to_close_then_plays_and_resumes(self):
        dj=DJ();clock=[100.];paused=[False];commands=[];step=[0]
        def factory(command,**kwargs):commands.append(command);return base.Process()
        def action():
            clock[0]+=1
            if clock[0]>145:raise AssertionError('playback did not finish')
            if step[0]==0:step[0]=1;return p.HELP_OVERLAY
            if step[0]==1:step[0]=2;dj.prepared=True;dj.forced=True;return None
            if step[0]==2:
                self.assertFalse(dj.played);self.assertFalse(dj.early_take)
                dj.dismissed=True;step[0]=3;return p.DISMISS_OVERLAY
            if dj.played and step[0]==3:step[0]=4;dj.play_done=True;return None
            if step[0]==4 and len(commands)>=2:return p.STOP
            return None
        coordinator=p.PAFExternalPlaybackCoordinator(base.Monitor());coordinator.filter_action(None,False,0)
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(mock.patch.object(PAFPlayer_dj,'get_controller',return_value=dj))
            stack.enter_context(mock.patch.object(p,'paf_workflows',return_value=object()))
            for name in ('update_lastfm_now_playing_async','append_pafplayer_trace','record_local_play_history','write_now_playing_files','start_background_audio_health_check','save_player_setting_value','set_console_title','scrobble_track_async','playlist_history_mark_played','save_spectrum_timeline_cache'):
                if hasattr(p,name):stack.enter_context(mock.patch.object(p,name))
            stack.enter_context(mock.patch.object(p,'LASTFM_SCROBBLING',False,create=True))
            result=p.play_audio_file(HERE/'runs/dj-v657-stage/test-tone.wav',ffplay=Path('ffplay.exe'),duration_probe=lambda _:60,key_action_reader=action,process_factory=factory,monotonic=lambda:clock[0],sleeper=lambda _:None,install_signal_handlers=False,drcs_visualizer=False,sixel_visualizer=False,lyrics_display=False,looping=False,now_playing_targets=[],initially_paused=False,paused_state=paused,manage_winamp=False,external_media_controller=coordinator,visualizer_input_source_state=[0],attribute_management_enabled=False,theory_modes={13,36})
        self.assertEqual('stopped',result);self.assertTrue(dj.played)
        self.assertFalse(dj.early_take);self.assertEqual(2,len(commands))

if __name__=='__main__':unittest.main()
