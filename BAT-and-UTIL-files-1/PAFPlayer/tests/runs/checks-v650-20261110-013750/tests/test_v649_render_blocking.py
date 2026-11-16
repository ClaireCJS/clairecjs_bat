"""Reproduce a held library lock and exercise real undo polling/restore logic."""
import ast
import inspect
from pathlib import Path
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

import PAFPlayer as app
import PAFPlayer_workflows as workflows
import PAFPlayer_web_workflows as web


class PresentationLockTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='v649-lock-test-'))
        self.runtime=workflows.Runtime(SimpleNamespace(),self.root/'state')

    def while_library_locked(self,fn):
        done=threading.Event();errors=[]
        def work():
            try:fn()
            except BaseException as e:errors.append(e)
            finally:done.set()
        # Main test thread stands in for a scanner blocked on slow file I/O.
        self.runtime.lock.acquire()
        worker=threading.Thread(target=work)
        try:
            worker.start()
            self.assertTrue(done.wait(1),'Render-facing operation waited behind library I/O')
        finally:self.runtime.lock.release();worker.join(3)
        self.assertFalse(worker.is_alive())
        if errors:raise errors[0]

    def test_lyric_trace_finishes_while_library_lock_is_held(self):
        log=self.root/'trace.log'
        with mock.patch.dict(workflows._runtimes,{id(app):self.runtime}):
            self.while_library_locked(lambda:app._append_pafplayer_diagnostic(log,'TRACE','lyric.updated text=fixture'))
        self.assertEqual(1,self.runtime.sequence)
        self.assertEqual(1,len(self.runtime.events))
        self.assertIn('lyric.updated',log.read_text(encoding='utf-8'))

    def test_hud_publication_and_read_do_not_wait_for_library(self):
        def display():
            self.runtime.note_external_activity('Remote playlist update',seconds=5)
            self.assertEqual('Remote playlist update',self.runtime.hud_activity())
        self.while_library_locked(display)
        with mock.patch.object(workflows.time,'monotonic',return_value=1e30):
            self.assertIsNone(self.runtime.hud_activity())

    def test_log_poll_is_consistent_without_the_library_lock(self):
        self.runtime.events.append(dict(id=1,level='TRACE',category='lyric',message='first'))
        self.runtime.sequence=1
        handler=SimpleNamespace(command='GET',path='/api/workflows/logs?after=0',_json=mock.Mock())
        with mock.patch.object(web,'authorized',return_value=True):
            self.while_library_locked(lambda:self.assertTrue(web.handle(handler,SimpleNamespace(workflows=self.runtime),'/api/workflows/logs')))
        status,data=handler._json.call_args.args
        self.assertEqual(200,status);self.assertEqual(1,data['cursor']);self.assertEqual(1,data['records'][0]['id'])

    def test_concurrent_event_ids_are_unique_and_history_stays_bounded(self):
        log=self.root/'concurrent.log';workers=[]
        with mock.patch.dict(workflows._runtimes,{id(app):self.runtime}):
            for index in range(4):
                worker=threading.Thread(target=lambda: [app._append_pafplayer_diagnostic(log,'TRACE','fixture.event') for _ in range(15)])
                workers.append(worker);worker.start()
            for worker in workers:worker.join(5)
        self.assertFalse(any(w.is_alive() for w in workers))
        self.assertEqual(list(range(1,61)),[x['id'] for x in self.runtime.events])
        self.assertEqual(1000,self.runtime.events.maxlen)


class UndoPollingTests(unittest.TestCase):
    def setUp(self):
        self.play=ast.parse(inspect.getsource(app.play_audio_file)).body[0]
        self.settings={'Volume':100,'ColorStyle':1};self.reads=0
        def current():self.reads+=1;return dict(self.settings)
        def apply(values):self.settings.clear();self.settings.update(values)
        self.ns=dict(current_mode_settings=current,apply_mode_settings=apply,
                     _RUNTIME_SETTINGS_LAST_SNAPSHOT=None,_RUNTIME_SETTINGS_UNDO_STACK=[],
                     RUNTIME_SETTINGS_UNDO_LIMIT=20,playlist_undo_kind_state=[None])
        for name in ('observe_runtime_settings_for_undo','undo_last_runtime_change'):
            fn=next(n for n in self.play.body if isinstance(n,ast.FunctionDef) and n.name==name)
            exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'<production undo>','exec'),self.ns)
        self.ns['observe_runtime_settings_for_undo']()

    def poll(self,action,paused=False):
        name='paused_action' if paused else 'action'
        for node in ast.walk(self.play):
            for _,body in ast.iter_fields(node):
                if not isinstance(body,list):continue
                for i,statement in enumerate(body[:-1]):
                    if (isinstance(statement,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in statement.targets)
                            and isinstance(statement.value,ast.Call) and isinstance(statement.value.func,ast.Name)
                            and statement.value.func.id=='next_owner_action'):
                        following=body[i+1]
                        if isinstance(following,ast.If) and 'observe_runtime_settings_for_undo' in ast.unparse(following):
                            snippet=ast.Module(body=[statement,following],type_ignores=[])
                            self.ns['next_owner_action']=lambda:action
                            exec(compile(ast.fix_missing_locations(snippet),'<production owner poll>','exec'),self.ns)
                            return
        self.fail('Owner poll must observe only real actions')

    def test_idle_playing_and_paused_polls_do_not_read_settings(self):
        baseline=self.reads
        for paused in (False,True):
            for _ in range(25):self.poll(None,paused)
        self.assertEqual(baseline,self.reads)

    def test_changes_and_two_undos_preserve_distinct_snapshots(self):
        self.poll('volume-up');self.settings['Volume']=110
        for _ in range(3):self.poll(None)
        self.poll('color-next');self.settings['ColorStyle']=2
        self.poll('undo',paused=True)
        self.assertEqual((True,False),self.ns['undo_last_runtime_change']())
        self.assertEqual({'Volume':110,'ColorStyle':1},self.settings)
        self.poll('undo')
        self.assertEqual((True,True),self.ns['undo_last_runtime_change']())
        self.assertEqual({'Volume':100,'ColorStyle':1},self.settings)

    def test_direct_undo_captures_latest_change_even_without_another_input(self):
        self.poll('color-next');self.settings['ColorStyle']=3
        self.assertEqual((True,False),self.ns['undo_last_runtime_change']())
        self.assertEqual(1,self.settings['ColorStyle'])


if __name__=='__main__':unittest.main()
