"""V622: visible enqueue placement, owner routing, and saved preference."""
from collections import deque
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

import PAFPlayer as player
import PAFPlayer_instance as instance_module
import PAFPlayer_remote_tray as remote_tray
import PAFPlayer_web_workflows as web
import PAFPlayer_workflows_ui as ui
import PAFPlayer_workflows as workflows


class PlacementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.paths = []
        for name in 'abcde':
            path = root / (name + '.flac')
            path.write_bytes(b'audio')
            self.paths.append(str(path))
        self.runtime = SimpleNamespace(
            app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),
            settings={},queue_history=deque(maxlen=30),log=lambda *_a,**_k: None)

    def edit(self, entries, selected, *, current=None, next_up=None, placement=None):
        state={'entries':entries,'next':next_up or [],'current':current or entries[0],
               'playlist':'test.m3u','shuffled':False}
        revision=web.queue_snapshot(SimpleNamespace(queue_read=lambda: state))['revision']
        payload={'op':'add','paths':selected,'revision':revision}
        if placement is not None: payload['placement']=placement
        return web.calculate_queue_edit(self.runtime,state,payload)

    def test_factory_default_inserts_all_tracks_after_current_in_visible_playlist(self):
        a,b,c,d,e=self.paths
        result=self.edit([a,b,c],[d,e],current=b)
        self.assertEqual([a,b,d,e,c],result['entries'])
        self.assertEqual([d,e],result['next'])

    def test_existing_member_is_moved_after_current_instead_of_hidden_at_end(self):
        a,b,c,d,e=self.paths
        result=self.edit([a,b,c],[a,d],current=c)
        self.assertEqual([b,c,a,d],result['entries'])
        self.assertEqual([a,d],result['next'])
        self.assertEqual(1,result['entries'].count(a))

    def test_existing_member_with_different_path_case_is_not_duplicated(self):
        a,b,c,d,e=self.paths
        spelling=c[:-6]+c[-6:].upper()
        result=self.edit([a,b,c],[spelling],current=b)
        self.assertEqual([a,b,spelling],result['entries'])
        self.assertEqual([spelling],result['next'])

    def test_saved_end_placement_appends_without_immediate_play_next(self):
        a,b,c,d,e=self.paths
        self.runtime.settings['enqueue_placement']='end'
        result=self.edit([a,b,c],[a,d],current=b,next_up=[e])
        self.assertEqual([b,c,a,d],result['entries'])
        self.assertEqual([e],result['next'])

    def test_explicit_flags_override_saved_setting_without_changing_it(self):
        a,b,c,d,e=self.paths
        self.runtime.settings['enqueue_placement']='end'
        self.assertEqual([a,d,b,c],self.edit([a,b,c],[d],placement='after_current')['entries'])
        self.assertEqual('end',self.runtime.settings['enqueue_placement'])
        self.runtime.settings['enqueue_placement']='after_current'
        self.assertEqual([a,b,c,d],self.edit([a,b,c],[d],placement='end')['entries'])
        self.assertEqual('after_current',self.runtime.settings['enqueue_placement'])

    def test_invalid_placement_does_not_edit_history(self):
        with self.assertRaisesRegex(ValueError,'placement'):
            self.edit(self.paths[:2],self.paths[2:3],placement='front')
        self.assertEqual(0,len(self.runtime.queue_history))

    def test_default_and_saved_placement_use_existing_workflow_settings(self):
        app=SimpleNamespace(AUDIO_CATALOG_PRIMARY=Path(r'C:\mp3\lists\everything.m3u'))
        with mock.patch.object(workflows,'read_json',return_value={}):
            runtime=workflows.Runtime(app,Path(self.temp.name)/'settings')
        self.assertEqual('after_current',runtime.settings['enqueue_placement'])
        with mock.patch.object(workflows,'read_json',return_value={'enqueue_placement':'end'}):
            runtime=workflows.Runtime(app,Path(self.temp.name)/'settings')
        self.assertEqual('end',runtime.settings['enqueue_placement'])

    def test_cli_dispatches_explicit_flags_and_keeps_default_unspecified(self):
        with mock.patch.object(remote_tray,'run_enqueue',return_value=0) as run:
            for flag, expected in [('-q',None),('--enqueue',None),('-qa','after_current'),('-qe','end')]:
                self.assertEqual(0,player.main([flag,'Song.flac']))
                if expected is None: run.assert_called_with(['Song.flac'])
                else: run.assert_called_with(['Song.flac'],placement=expected)

    def test_local_cli_routes_placement_to_official_instance(self):
        requests=[]
        class Owner:
            def __init__(self,_runtime): pass
            def acquire(self): return False
            def forward(self,request):
                requests.append(request)
                return {'queued':1,'message':'Queued next'}
        with mock.patch.object(instance_module,'Instance',Owner),mock.patch('PAFPlayer_workflows.get_runtime',return_value=self.runtime):
            self.assertEqual(0,remote_tray.run_enqueue(['Song.flac'],placement='end'))
        self.assertEqual('end',requests[0]['placement'])
        self.assertEqual('path',requests[0]['selectors'][0]['kind'])

    def test_remote_cli_sends_explicit_placement_with_verified_owner_identity(self):
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*_args): self.close()
        class Opener:
            request=None
            def open(self,request,timeout=None):
                self.request=request
                return Response(b'{"ok":true,"queued":1}')
        opener=Opener()
        def setup(server,_address):
            server.url='http://musicbox:666/'
            server.label='musicbox:666'
            server._opener=opener
        with mock.patch.object(remote_tray.RemoteServer,'__init__',autospec=True,side_effect=setup),\
             mock.patch.object(remote_tray.RemoteServer,'hello',return_value=('official-owner',{})):
            self.assertEqual(0,remote_tray.run_enqueue(['--server','musicbox:666','Song.flac'],placement='after_current'))
        body=json.loads(opener.request.data)
        self.assertEqual('official-owner',body['identity'])
        self.assertEqual('after_current',body['placement'])

    def test_owner_applies_its_own_saved_setting_and_explicit_override(self):
        root=Path(self.temp.name)
        self.runtime.root=root
        self.runtime.settings['enqueue_placement']='end'
        self.runtime.queue_read=lambda:{'entries':self.paths[:2],'next':[],
                                        'current':self.paths[0],'playlist':'test.m3u'}
        calls=[]
        self.runtime.queue_bridge=lambda payload:calls.append(payload) or {'revision':'new'}
        owner=instance_module.Instance(self.runtime)
        owner.start()
        try:
            selector={'kind':'path','value':self.paths[2]}
            self.assertEqual(1,owner.forward({'selectors':[selector]})['queued'])
            self.assertEqual('end',calls[-1]['placement'])
            self.assertEqual('Queued at end',owner.forward({'selectors':[selector]})['message'])
            self.assertEqual(1,owner.forward({'selectors':[selector],'placement':'after_current'})['queued'])
            self.assertEqual('after_current',calls[-1]['placement'])
        finally: owner.close()

    def test_web_setting_control_uses_existing_settings_store(self):
        self.assertIn('id="enqueuePlacement"',ui.HTML)
        self.assertIn('enqueue_placement',ui.SCRIPT)
        data=json.dumps({'enqueue_placement':'end'}).encode()
        sent=[]
        handler=SimpleNamespace(command='POST',headers={'Content-Length':str(len(data))},
                                rfile=io.BytesIO(data),connection=SimpleNamespace(settimeout=lambda _x:None),
                                _json=lambda status,value: sent.append((status,value)))
        runtime=SimpleNamespace(settings={'enqueue_placement':'after_current'},save_settings=mock.Mock())
        with mock.patch.object(web,'authorized',return_value=True):
            self.assertTrue(web.handle(handler,SimpleNamespace(workflows=runtime),'/api/workflows/settings'))
        self.assertEqual(200,sent[0][0])
        self.assertEqual('end',runtime.settings['enqueue_placement'])
        runtime.save_settings.assert_called_once_with()


if __name__=='__main__': unittest.main()
