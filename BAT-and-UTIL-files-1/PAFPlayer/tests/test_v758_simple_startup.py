import ast,inspect,json,os,threading,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import PAFPlayer as app
from PAFPlayer_playback_focus import PlaybackFocus
from test_v755_preview_focus import FocusTests

class StartupTests(unittest.TestCase):
    setUp=FocusTests.setUp
    tearDown=FocusTests.tearDown
    player=FocusTests.player
    def test_many_dead_registrations_do_not_connect(self):
        preview=self.player(True)
        for index in range(18):
            (preview.root/('dead-%02d.json'%index)).write_text(json.dumps({'pid':2147483000,'port':1,'token':'expired'}),encoding='utf-8')
        with patch.object(preview,'process_alive',return_value=False),patch.object(preview,'request',side_effect=AssertionError('Dead PID must never be contacted')):
            started=time.monotonic();preview.claim();elapsed=time.monotonic()-started
        self.assertLess(elapsed,.5)
        self.assertEqual(18,len(list((preview.root/'retired').glob('dead-*.json'))))
        self.assertEqual([],preview.peers)
    def test_process_liveness_detects_self_and_absent_pid(self):
        self.assertTrue(PlaybackFocus.process_alive(os.getpid()))
        self.assertFalse(PlaybackFocus.process_alive(2147483000))
        for invalid in (None,False,-1,0,'100'):
            self.assertFalse(PlaybackFocus.process_alive(invalid))
    def test_overlapping_startups_give_newest_preview_priority(self):
        main=self.player();older=self.player(True);pause_started=threading.Event();allow_older=threading.Event();errors=[]
        request=older.request
        def delayed(peer,payload,**kwargs):
            result=request(peer,payload,**kwargs)
            if payload['action']=='pause':
                pause_started.set();allow_older.wait(4)
            return result
        def claim():
            try:older.claim()
            except BaseException as exc:errors.append(exc)
        with patch.object(older,'request',side_effect=delayed):
            worker=threading.Thread(target=claim,daemon=True);worker.start()
            try:
                self.assertTrue(pause_started.wait(2))
                newer=self.player(True);newer.claim()
                self.assertTrue(older.paused[0]);self.assertTrue(main.paused[0])
                allow_older.set();time.sleep(.05)
                self.assertTrue(worker.is_alive())
                newer.release();worker.join(3)
                self.assertFalse(worker.is_alive());self.assertFalse(errors)
                self.assertFalse(older.paused[0]);self.assertTrue(main.paused[0])
                older.release();self.assertFalse(main.paused[0])
            finally:allow_older.set()
    def test_preview_initial_and_persisted_pause_state_are_isolated(self):
        tree=ast.parse(inspect.getsource(app.main))
        assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='playback_paused_state' for t in n.targets))
        env={'simple_instance':True,'persisted_settings':{'PlaybackPaused':1}}
        value=eval(compile(ast.Expression(assignment.value),'<preview-state>','eval'),env)
        self.assertEqual([False],value)
        expression=next(value for node in ast.walk(tree) if isinstance(node,ast.Dict) for key,value in zip(node.keys,node.values) if isinstance(key,ast.Constant) and key.value=='PlaybackPaused' and isinstance(value,ast.IfExp))
        env.update(playback_paused_state=[False],external_media_controller=SimpleNamespace(auto_paused=False))
        self.assertEqual(1,eval(compile(ast.Expression(expression),'<saved-state>','eval'),env))
    def test_focus_trace_never_exposes_authentication(self):
        main=self.player();preview=self.player(True);trace=Mock();preview.trace=trace
        preview.claim();preview.release()
        text=repr(trace.call_args_list)
        self.assertIn('preview.focus.ready',text)
        self.assertNotIn(main.token,text);self.assertNotIn(preview.token,text)
    def test_retire_preserves_both_collision_files(self):
        preview=self.player(True);old=preview.root/'stale.json';old.write_text('old',encoding='utf-8');preview.retire(old)
        old.write_text('new',encoding='utf-8');preview.retire(old)
        self.assertEqual('old',(preview.root/'retired/stale.json').read_text())
        self.assertEqual('new',(preview.root/'retired/stale (1).json').read_text())
    def test_new_bundle_matches_module(self):
        self.assertEqual(Path('src/PAFPlayer_playback_focus.py').read_text(encoding='utf-8-sig'),app._PAF_BUNDLED_SOURCES['PAFPlayer_playback_focus'])

if __name__=='__main__':unittest.main()
