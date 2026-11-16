"""Bounded snapshots, no locals, no idle work, and local HTTP access restriction."""
import ast
import inspect
import json
import threading
from types import SimpleNamespace
import unittest
from unittest import mock
import PAFPlayer as app


class StackDiagnosticsTests(unittest.TestCase):
    def test_real_waiting_worker_is_identifiable_without_its_locals(self):
        ready=threading.Event();stop=threading.Event()
        def stalled_fixture_worker():
            private_marker='MUST_NOT_APPEAR_IN_REPORT'
            ready.set();stop.wait(5)
            return private_marker
        worker=threading.Thread(target=stalled_fixture_worker,name='diagnostic-fixture')
        worker.start();ready.wait(2)
        try:
            rows=app.paf_runtime_thread_stacks()
            row=next(row for row in rows if row['name']=='diagnostic-fixture')
            self.assertIn('stalled_fixture_worker',[f['function'] for f in row['stack']])
            self.assertNotIn('MUST_NOT_APPEAR_IN_REPORT',json.dumps(rows))
            self.assertTrue(rows[0]['main'])
            self.assertTrue(all(set(f)=={'file','function','line'} for r in rows for f in r['stack']))
        finally:stop.set();worker.join(3)
        self.assertFalse(worker.is_alive())

    def test_snapshot_limits_threads_depth_and_clears_frame_references(self):
        node=None
        for _ in range(80):
            node=SimpleNamespace(f_code=SimpleNamespace(co_filename='C:/private/folder/worker.py',co_name='work'),f_lineno=123,f_back=node)
        frames={i:node for i in range(100)}
        main_ident=threading.main_thread().ident;frames[main_ident]=node
        with mock.patch.object(app.sys,'_current_frames',return_value=frames):
            rows=app.paf_runtime_thread_stacks()
        self.assertEqual(64,len(rows));self.assertTrue(rows[0]['main'])
        self.assertTrue(all(len(r['stack'])==32 for r in rows))
        self.assertFalse(frames)
        self.assertTrue(all(f['file']=='worker.py' for r in rows for f in r['stack']))

    def test_normal_diagnostics_never_capture_stacks(self):
        with mock.patch.object(app,'paf_runtime_thread_stacks',side_effect=AssertionError('unsolicited sampling')):
            self.assertNotIn('thread_stacks',app.paf_runtime_diagnostics_snapshot())

    def test_requested_snapshot_returns_locations(self):
        with mock.patch.object(app,'paf_runtime_thread_stacks',return_value=[{'fixture':True}]):
            self.assertEqual([{'fixture':True}],app.paf_runtime_diagnostics_snapshot(include_stacks=True)['thread_stacks'])


class LocalRouteTests(unittest.TestCase):
    def route(self,local,query):
        tree=ast.parse(inspect.getsource(app.PAFWebServer))
        branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and
                    ast.unparse(n.test)=='path == "/api/runtime-diagnostics"')
        wrapper=ast.parse('def get(self, path, query):\n    pass').body[0];wrapper.body=[branch]
        capture=mock.Mock(return_value={'ok':True});ns={'paf_runtime_diagnostics_snapshot':capture}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[wrapper],type_ignores=[])),'<actual diagnostic HTTP route>','exec'),ns)
        handler=SimpleNamespace(_client_is_local=lambda:local,_json=mock.Mock())
        ns['get'](handler,'/api/runtime-diagnostics',query)
        return handler,capture

    def test_remote_stack_request_is_denied_before_capture(self):
        h,c=self.route(False,'stacks=1');c.assert_not_called();self.assertEqual(403,h._json.call_args.args[0])

    def test_local_stack_request_and_existing_remote_statistics(self):
        for local,query,enabled in ((True,'stacks=1',True),(True,'stacks=0',False),(False,'',False)):
            h,c=self.route(local,query);c.assert_called_once_with(include_stacks=enabled)
            self.assertEqual(200,h._json.call_args.args[0])


if __name__=='__main__':unittest.main()
