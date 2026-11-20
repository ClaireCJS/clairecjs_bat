import contextlib
import io
from pathlib import Path
import unittest
from unittest import mock

import PAFPlayer as p
import PAFPlayer_dj
from test_v657_dj_playback import Monitor, Process, FakeDJ

ROOT=Path(__file__).resolve().parents[1]

class SimpleSplashTests(unittest.TestCase):
    def run_preview(self, simple):
        clock=[100.0];calls=[0];dj=FakeDJ();dj.prepared=False;dj.validate_upcoming=lambda *_args:None
        def action():
            calls[0]+=1;clock[0]+=.1
            return p.STOP if calls[0]>=3 else None
        coordinator=p.PAFExternalPlaybackCoordinator(Monitor());coordinator.filter_action(None,False,0)
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(mock.patch.object(PAFPlayer_dj,'get_controller',return_value=dj))
            stack.enter_context(mock.patch.object(p,'paf_workflows',return_value=object()))
            stack.enter_context(mock.patch.object(p,'_CONSOLE_TITLE_STARTUP_SHOWN',False))
            splash=stack.enter_context(mock.patch.object(p,'console_title_splash',return_value='SPLASH-MARKER'))
            write=stack.enter_context(mock.patch.object(p,'write_console'))
            for name in ('update_lastfm_now_playing_async','append_pafplayer_trace','record_local_play_history','write_now_playing_files','start_background_audio_health_check','save_player_setting_value','set_console_title','scrobble_track_async','playlist_history_mark_played','save_spectrum_timeline_cache'):
                if hasattr(p,name): stack.enter_context(mock.patch.object(p,name))
            result=p.play_audio_file(ROOT/'tests/runs/dj-v657-stage/test-tone.wav',ffplay=Path('ffplay.exe'),duration_probe=lambda _:60,key_action_reader=action,process_factory=lambda *a,**kw:Process(),monotonic=lambda:clock[0],sleeper=lambda _:None,install_signal_handlers=False,drcs_visualizer=False,sixel_visualizer=False,lyrics_display=False,looping=False,now_playing_targets=[],manage_winamp=False,external_media_controller=coordinator,visualizer_input_source_state=[0],attribute_management_enabled=False,theory_modes={13,36},simple_mode=simple)
            return result,splash.call_count,[str(c.args[0]) for c in write.call_args_list if c.args]
    def test_simple_never_paints_startup_splash(self):
        result,count,output=self.run_preview(True)
        self.assertEqual('stopped',result);self.assertEqual(0,count);self.assertFalse(any('SPLASH-MARKER' in line for line in output))
    def test_normal_playback_still_paints_startup_splash(self):
        result,count,output=self.run_preview(False)
        self.assertEqual('stopped',result);self.assertGreater(count,0);self.assertTrue(any('SPLASH-MARKER' in line for line in output))
if __name__=='__main__':unittest.main()
