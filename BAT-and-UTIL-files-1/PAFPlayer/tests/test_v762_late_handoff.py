import unittest
from unittest.mock import patch
import PAFPlayer as app
import PAFPlayer_memory_audio
from test_v657_dj_playback import Process
from test_v742_simple_splash import SimpleSplashTests

class HandoffTests(unittest.TestCase):
    def run_case(self, *, buffered=True, primed=True, starts=True, claim_fails=False, stale_pause=False):
        events=[];original=app.play_audio_file;state=[stale_pause]
        class Focus:
            claimed=False
            def start(self):events.append('register')
            def claim(self):
                events.append('claim')
                if claim_fails:raise RuntimeError('focus rejected')
                self.claimed=True;state[0]=False
            def pop_action(self):return None
            def observe_action(self,*args,**kwargs):pass
            def guard_action(self,action,*args,**kwargs):return action
            def begin_resume(self):return True
        focus=Focus()
        class Renderer(Process):
            def wait_primed(self):events.append('primed');return primed
            def start_output(self):events.append('audible');return starts
        renderer=Renderer()
        def legacy(*args,**kwargs):events.append('legacy-launch');return Process()
        def launch(*args,**kwargs):
            events.append('renderer-created')
            self.assertTrue(kwargs['hold_for_handoff'])
            self.assertNotIn('claim',events)
            return renderer,[]
        calls=[0]
        def action():
            calls[0]+=1
            if stale_pause and calls[0]==1:self.assertTrue(renderer.running,'Old startup pause latch stopped the primed renderer')
            return app.STOP if calls[0]>=3 else None
        def invoke(*args,**kwargs):
            kwargs.update(smooth_audio_renderer_enabled=False,playback_focus=focus,process_factory=legacy,mm_inspired_renderer_state=[buffered],output_channels_state=[5 if buffered else 2],trim_edge_silence=False,replaygain_probe=lambda *_:app.calculate_replaygain_info({},'off'),initially_paused=stale_pause,paused_state=state,key_action_reader=action)
            return original(*args,**kwargs)
        with patch.object(app,'play_audio_file',side_effect=invoke),patch.object(app.subprocess,'Popen',legacy),patch.object(app,'launch_matrixmixer_inspired_renderer',side_effect=launch),patch.object(PAFPlayer_memory_audio.MemoryAudioSource,'try_open',return_value=None),patch.object(app,'probe_audio_tags',return_value={}),patch.object(app,'probe_audio_raw_tags',return_value={}),patch.object(app,'probe_audio_stream_layout',return_value=(2,'stereo')),patch.object(app,'find_clairecjs_dependency',return_value=None),patch.object(app,'record_pafplayer_runtime_warning'),patch.object(app,'retire_live_audio_names',return_value=[]):
            if claim_fails or not starts:
                with self.assertRaises(RuntimeError):SimpleSplashTests().run_preview(True)
                self.assertFalse(renderer.running)
            else:
                result,_,_=SimpleSplashTests().run_preview(True);self.assertEqual('stopped',result)
        return events
    def test_buffered_audio_prepares_before_pausing_other_players(self):
        events=self.run_case()
        self.assertLess(events.index('renderer-created'),events.index('primed'))
        self.assertLess(events.index('primed'),events.index('claim'))
        self.assertLess(events.index('claim'),events.index('audible'))
        self.assertNotIn('legacy-launch',events)
    def test_legacy_focus_is_acquired_immediately_before_launch(self):
        events=self.run_case(buffered=False)
        self.assertEqual(['claim','legacy-launch'],[v for v in events if v in ('claim','legacy-launch')])
    def test_failed_preparation_waits_until_fallback_is_ready_to_launch(self):
        events=self.run_case(primed=False)
        self.assertNotIn('audible',events)
        self.assertLess(events.index('primed'),events.index('claim'))
        self.assertEqual(['claim','legacy-launch'],events[-2:])
    def test_focus_failure_does_not_release_output_or_launch_fallback(self):
        events=self.run_case(claim_fails=True)
        self.assertNotIn('audible',events);self.assertNotIn('legacy-launch',events)
    def test_output_start_failure_does_not_launch_a_second_decoder(self):
        events=self.run_case(starts=False)
        self.assertNotIn('legacy-launch',events)
    def test_pause_while_preparing_does_not_replay_a_stale_pause_latch(self):
        self.run_case(stale_pause=True)

if __name__=='__main__':unittest.main()
