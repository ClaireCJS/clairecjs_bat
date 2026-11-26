import ast
import inspect
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import threading
import time
import PAFPlayer as app
from PAFPlayer_playback_focus import PlaybackFocus

class FocusTests(unittest.TestCase):
    def setUp(self):
        self.fixture=Path(tempfile.mkdtemp(prefix='v755-focus-',dir=Path('tests/runs').resolve()))
        self.players=[]
    def tearDown(self):
        for player in reversed(self.players): player.close()
        # Fixtures are preserved under tests/runs; no user files are deleted.
    def player(self, preview=False, paused=False):
        state=[paused];actions=[]
        def action(value):
            actions.append(value);state[0]=value==app.WEB_PAUSE;return True
        p=PlaybackFocus(self.fixture,state,action,preview=preview,pause=app.WEB_PAUSE,resume=app.WEB_PLAY)
        p.actions=actions;p.start();self.players.append(p);return p
    def test_main_and_other_preview_pause_then_restore_in_order(self):
        main=self.player();a=self.player(True)
        a.claim();self.assertTrue(main.paused[0])
        b=self.player(True);b.claim()
        self.assertTrue(main.paused[0]);self.assertTrue(a.paused[0]);self.assertFalse(b.paused[0])
        b.release();self.assertFalse(a.paused[0]);self.assertTrue(main.paused[0])
        a.release();self.assertFalse(main.paused[0])
    def test_originally_paused_player_remains_paused(self):
        main=self.player(paused=True);a=self.player(True);a.claim();a.release()
        self.assertTrue(main.paused[0]);self.assertNotIn(app.WEB_PLAY,main.actions)
    def test_out_of_order_exit_does_not_resume_main_under_new_preview(self):
        main=self.player();a=self.player(True);a.claim();b=self.player(True);b.claim()
        a.release();self.assertTrue(main.paused[0]);b.release();self.assertFalse(main.paused[0])
    def test_expired_owner_restores_previous_state(self):
        main=self.player();main.handle({'owner':'crashed','action':'pause'})
        with main.lock:
            main.leases.clear();main.restore_if_free()
        self.assertFalse(main.paused[0])
    def test_idempotent_claim_and_refresh(self):
        main=self.player();a=self.player(True);a.claim();a.claim()
        self.assertEqual(1,len(main.leases))
        self.assertTrue(main.handle({'owner':a.identity,'action':'refresh'})['ok'])
        a.release();self.assertEqual(1,main.actions.count(app.WEB_PLAY))
    def test_listener_rejects_wrong_token(self):
        main=self.player()
        with self.assertRaises(urllib.error.HTTPError):
            main.request({'port':main.server.server_port,'token':'wrong'}, {'owner':'outsider','action':'pause'})
        self.assertFalse(main.paused[0])
    def test_claim_failure_releases_prior_peers(self):
        main=self.player();a=self.player(True)
        original=a.request
        def request(peer,payload,**kwargs):
            if payload['action']=='pause':
                original(peer,payload,**kwargs);return {'ok':False}
            return original(peer,payload,**kwargs)
        with patch.object(a,'request',side_effect=request):
            with self.assertRaises(RuntimeError):a.claim()
        self.assertFalse(main.paused[0])
    def test_waits_for_real_transport_queue_ack_even_without_web_server(self):
        server=app.PAFWebServer(enabled=False,host='127.0.0.1',port=0)
        state=[False]
        main=PlaybackFocus(self.fixture,state,server.enqueue_action,pause=app.WEB_PAUSE,resume=app.WEB_PLAY)
        main.start();self.players.append(main)
        preview=self.player(True);errors=[]
        def claim():
            try:preview.claim()
            except BaseException as exc:errors.append(exc)
        worker=threading.Thread(target=claim);worker.start()
        deadline=time.monotonic()+3;action=None
        while action is None and time.monotonic()<deadline:
            action=server.pop_action();time.sleep(.01)
        self.assertEqual(app.WEB_PAUSE,action)
        self.assertTrue(worker.is_alive())
        state[0]=True;worker.join(3)
        self.assertFalse(worker.is_alive());self.assertFalse(errors)
        preview.release();self.assertEqual(app.WEB_PLAY,server.pop_action())
        server.close()

    def test_one_bottom_safety_row_and_bundle_parity(self):
        self.assertEqual(1,app.TERMINAL_BOTTOM_RESERVE_TRIM_ROWS)
        for rows in (20,24,30,48):
            origin=app.stable_viewport_ui_origin(rows,rows-1,1)
            self.assertEqual(rows-1,origin+rows-2)
        source=Path('src/PAFPlayer_playback_focus.py').read_text(encoding='utf-8-sig')
        self.assertEqual(source,app._PAF_BUNDLED_SOURCES['PAFPlayer_playback_focus'])
    def test_claim_before_decoder_and_main_cleanup(self):
        source=inspect.getsource(app.play_audio_file)
        self.assertLess(source.index('playback_focus.claim()'),source.index('process = process_factory(command'))
        source=inspect.getsource(app.main)
        self.assertIn('playback_focus=playback_focus',source)
        self.assertIn('playback_focus.close()',source)

if __name__=='__main__':unittest.main()
