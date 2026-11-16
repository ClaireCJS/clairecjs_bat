import contextlib
import importlib.util
import io
from pathlib import Path
import unittest
from unittest import mock

here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('v669_playback_fixture',here/'test_v657_dj_playback.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base);p=base.p
import PAFPlayer_dj

class Tests(unittest.TestCase):
    def test_prompt_state_edit_timeout_and_cancel(self):
        e=p.PAFHashCommandEntry();self.assertIsNone(p.hash_command_prompt(e))
        e.feed('#',0);self.assertEqual('#▌',p.hash_command_prompt(e))
        e.feed('D',.1);e.feed('j',.2);self.assertEqual('#Dj▌',p.hash_command_prompt(e))
        e.feed('\b',.3);self.assertEqual('#D▌',p.hash_command_prompt(e))
        self.assertEqual('d',e.expire(1.8));self.assertIsNone(p.hash_command_prompt(e))
        e.feed('#',2);e.feed('x',2.1);e.feed('\x1b',2.2);self.assertIsNone(p.hash_command_prompt(e))

    def run_player(self,paused=False,help_open=False):
        dj=base.FakeDJ();dj.prepared=False;clock=[100.];sequence=list('#djx\b\x1b');writes=[];step=[0]
        entry=p.PAFHashCommandEntry()
        def action():
            clock[0]+=.1
            if clock[0]>110:raise AssertionError('mock playback did not stop')
            if help_open and step[0]==0:step[0]+=1;return p.HELP_OVERLAY
            if sequence:
                entry.feed(sequence.pop(0),clock[0]);return None
            if help_open and step[0]==1:step[0]+=1;return p.DISMISS_OVERLAY
            return p.STOP
        coordinator=p.PAFExternalPlaybackCoordinator(base.Monitor());coordinator.filter_action(None,False,0)
        with contextlib.ExitStack() as stack:
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(mock.patch.object(p,'_HASH_COMMAND_ENTRY',entry))
            stack.enter_context(mock.patch.object(p,'write_console',side_effect=lambda text:writes.append(text)))
            stack.enter_context(mock.patch.object(PAFPlayer_dj,'get_controller',return_value=dj))
            stack.enter_context(mock.patch.object(p,'paf_workflows',return_value=object()))
            for name in ('update_lastfm_now_playing_async','append_pafplayer_trace','record_local_play_history','write_now_playing_files','start_background_audio_health_check','save_player_setting_value','set_console_title','scrobble_track_async','playlist_history_mark_played','save_spectrum_timeline_cache'):
                if hasattr(p,name):stack.enter_context(mock.patch.object(p,name))
            stack.enter_context(mock.patch.object(p,'LASTFM_SCROBBLING',False,create=True))
            result=p.play_audio_file(here/'runs/dj-v657-stage/test-tone.wav',ffplay=Path('ffplay.exe'),duration_probe=lambda _:60,key_action_reader=action,process_factory=lambda *a,**kw:base.Process(),monotonic=lambda:clock[0],sleeper=lambda _:None,install_signal_handlers=False,drcs_visualizer=False,sixel_visualizer=False,lyrics_display=False,looping=False,now_playing_targets=[],initially_paused=paused,paused_state=[paused],manage_winamp=False,external_media_controller=coordinator,visualizer_input_source_state=[0],attribute_management_enabled=False,theory_modes={13,36})
        self.assertEqual('stopped',result);self.assertIsNone(entry.buffer)
        output=''.join(writes)
        for prompt in ('#▌','#d▌','#dj▌','#djx▌'):self.assertIn(prompt,output)
        self.assertGreaterEqual(output.count('#dj▌'),2)

    def test_prompt_visible_during_playback(self):self.run_player()
    def test_prompt_visible_while_paused(self):self.run_player(paused=True)
    def test_prompt_visible_over_help(self):self.run_player(help_open=True)

if __name__=='__main__':unittest.main()
