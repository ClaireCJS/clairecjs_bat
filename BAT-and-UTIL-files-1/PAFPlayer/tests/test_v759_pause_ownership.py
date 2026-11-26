import inspect,threading,time,unittest
from pathlib import Path
from unittest.mock import Mock
import PAFPlayer as app
from PAFPlayer_playback_focus import PlaybackFocus

class PauseOwnershipTests(unittest.TestCase):
    def player(self,paused):
        enqueue=Mock();state=[paused]
        focus=PlaybackFocus(Path('tests/runs'),state,enqueue,pause=app.WEB_PAUSE,resume=app.WEB_PLAY,guarded=True)
        return focus,state,enqueue
    def request_pause(self,focus,owner):
        results=[]
        thread=threading.Thread(target=lambda:results.append(focus.handle({'owner':owner,'action':'pause'})))
        thread.start();deadline=time.monotonic()+2;action=None
        while action is None and time.monotonic()<deadline:
            action=focus.pop_action();time.sleep(.001)
        self.assertEqual(app.WEB_PAUSE,action);focus.paused[0]=True
        thread.join(2);self.assertFalse(thread.is_alive());self.assertEqual([{'ok':True}],results)
    def release(self,focus,owner):focus.handle({'owner':owner,'action':'release'})
    def test_prepaused_main_never_receives_play(self):
        focus,state,enqueue=self.player(True)
        focus.handle({'owner':'preview','action':'pause'})
        self.assertFalse(focus.restore);self.assertIsNone(focus.pop_action())
        self.release(focus,'preview')
        self.assertTrue(state[0]);self.assertIsNone(focus.pop_action());enqueue.assert_not_called()
    def test_prepaused_stays_paused_with_multiple_previews_and_expiry(self):
        focus,state,enqueue=self.player(True)
        for owner in ('one','two'):focus.handle({'owner':owner,'action':'pause'})
        self.release(focus,'one')
        focus.leases.clear();focus.restore_if_free()
        self.assertTrue(state[0]);self.assertIsNone(focus.pop_action());enqueue.assert_not_called()
    def test_playing_main_resumes_only_after_last_preview(self):
        focus,state,enqueue=self.player(False);self.request_pause(focus,'one')
        focus.handle({'owner':'two','action':'pause'});self.release(focus,'one')
        self.assertIsNone(focus.pop_action());self.assertTrue(state[0])
        self.release(focus,'two');self.assertEqual(app.WEB_PLAY,focus.pop_action())
        self.assertTrue(focus.begin_resume());self.assertFalse(state[0]);enqueue.assert_not_called()
    def test_new_preview_cancels_stale_queued_resume(self):
        focus,state,_=self.player(False);self.request_pause(focus,'one');self.release(focus,'one')
        self.assertTrue(focus.pending_resume)
        focus.handle({'owner':'two','action':'pause'})
        self.assertIsNone(focus.pop_action());self.assertTrue(state[0])
        self.release(focus,'two');self.assertEqual(app.WEB_PLAY,focus.pop_action())
    def test_manual_pause_or_stop_revokes_resume_ownership(self):
        for action in (app.WEB_PAUSE,app.WEB_STOP):
            with self.subTest(action=action):
                focus,state,_=self.player(False);self.request_pause(focus,'one')
                focus.observe_action(action,True,toggle=app.PAUSE_TOGGLE,stop=app.WEB_STOP)
                self.release(focus,'one');self.assertIsNone(focus.pop_action());self.assertTrue(state[0])
    def test_manual_pause_cancels_pending_restore(self):
        focus,state,_=self.player(False);self.request_pause(focus,'one');self.release(focus,'one')
        focus.observe_action(app.WEB_PAUSE,True)
        self.assertIsNone(focus.pop_action());self.assertTrue(state[0])
    def test_stale_play_and_auto_resume_cannot_restart_held_player(self):
        focus,state,_=self.player(True);focus.handle({'owner':'one','action':'pause'})
        for action in (app.WEB_PLAY,app.EXTERNAL_MEDIA_RESUME,app.PAUSE_TOGGLE):
            self.assertIsNone(focus.guard_action(action,True,toggle=app.PAUSE_TOGGLE,external_resume=app.EXTERNAL_MEDIA_RESUME))
        self.assertFalse(focus.begin_resume());self.assertTrue(state[0])
    def test_lease_between_restore_selection_and_commit_still_blocks(self):
        focus,state,_=self.player(False);self.request_pause(focus,'one');self.release(focus,'one')
        self.assertEqual(app.WEB_PLAY,focus.pop_action())
        focus.handle({'owner':'two','action':'pause'})
        self.assertFalse(focus.begin_resume());self.assertTrue(state[0])
    def test_late_pause_after_resume_intent_requires_actual_pause_ack(self):
        focus,state,_=self.player(False);self.assertTrue(focus.begin_resume())
        self.request_pause(focus,'one');self.assertTrue(state[0])
    def test_audio_owner_hooks_and_bundle_parity(self):
        main=inspect.getsource(app.main);play=inspect.getsource(app.play_audio_file)
        for text in ('guarded=True',):self.assertIn(text,main)
        for text in ('playback_focus.pop_action()','playback_focus.observe_action(','playback_focus.guard_action(','playback_focus.begin_resume()'):self.assertIn(text,play)
        self.assertEqual(Path('src/PAFPlayer_playback_focus.py').read_text(encoding='utf-8-sig'),app._PAF_BUNDLED_SOURCES['PAFPlayer_playback_focus'])

if __name__=='__main__':unittest.main()
