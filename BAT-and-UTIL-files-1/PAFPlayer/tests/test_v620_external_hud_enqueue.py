"""V620: direct enqueue, remembered library source, and external HUD activity."""
import contextlib
import io
import json
from pathlib import Path
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

import PAFPlayer as player
import PAFPlayer_workflows as workflows
import PAFPlayer_instance as instance_module
import PAFPlayer_web_workflows as web_workflows
import PAFPlayer_workflows_ui as workflows_ui
from PAFPlayer_remote_tray import enqueue_receipt


class EnqueueAndHudTests(unittest.TestCase):
    def test_double_dash_q_is_not_regex_abbreviation(self):
        import PAFPlayer_remote_tray as remote_tray
        with mock.patch.object(remote_tray, 'run_enqueue', return_value=17) as enqueue:
            self.assertEqual(17, player.main(['--q', 'Song.flac']))
        enqueue.assert_called_once_with(['Song.flac'])

    def test_receipt_explains_existing_and_new_playlist_members(self):
        receipt=enqueue_receipt({'message':'Queued next','queued':2,
                                 'added_to_playlist':1,'already_in_playlist':1})
        self.assertEqual('Queued next — 2 tracks (1 new playlist entry; 1 already in playlist).',receipt)

    def test_owner_acknowledges_two_queued_but_only_one_new_membership(self):
        old=r'C:\Music\Already Here.flac';new=r'C:\Music\New Track.flac'
        state={'entries':[old],'next':[],'current':old,'playlist':'test.m3u'}
        runtime=SimpleNamespace(root=Path(r'C:\PAFPlayer-test-owner'),
                                app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),
                                queue_read=lambda: state,
                                queue_bridge=lambda payload: {'revision':'after'},
                                log=lambda *_args,**_kw: None)
        owner=instance_module.Instance(runtime)
        descriptor={}
        def remember(_path,value): descriptor.update(value)
        try:
            with mock.patch.object(instance_module,'write_json',side_effect=remember), \
                 mock.patch.object(instance_module,'read_json',return_value=descriptor), \
                 mock.patch.object(instance_module,'supported_file',return_value=True):
                owner.start()
                result=owner.forward({'paths':[old,new]})
        finally:
            owner.close()
        self.assertEqual(2,result['queued'])
        self.assertEqual(1,result['already_in_playlist'])
        self.assertEqual(1,result['added_to_playlist'])

    def test_owner_waits_for_queue_during_brief_startup(self):
        track=r'C:\Music\Ready Soon.flac'
        runtime=SimpleNamespace(root=Path(r'C:\PAFPlayer-test-startup'),
                                app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),
                                queue_read=lambda: {'entries':[],'next':[],'current':None,'playlist':None},
                                queue_bridge=None,log=lambda *_args,**_kw: None)
        owner=instance_module.Instance(runtime)
        descriptor={}
        timer=threading.Timer(.15,lambda: setattr(runtime,'queue_bridge',lambda payload: {'revision':'ready'}))
        try:
            with mock.patch.object(instance_module,'write_json',side_effect=lambda _path,value: descriptor.update(value)), \
                 mock.patch.object(instance_module,'read_json',return_value=descriptor), \
                 mock.patch.object(instance_module,'supported_file',return_value=True):
                owner.start();timer.start()
                result=owner.forward({'paths':[track]})
        finally:
            timer.join(timeout=1)
            owner.close()
        self.assertEqual(1,result['queued'])

    def test_exact_existing_path_needs_no_library_scan(self):
        track=Path(r'C:\Music\Artist\Song.flac')
        runtime=SimpleNamespace(app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),
                                catalog_paths=mock.Mock(side_effect=AssertionError('catalog scanned')))
        with mock.patch.object(workflows, 'supported_file', return_value=True):
            result=workflows.enqueue_selectors(runtime,[{'kind':'path','value':str(track)}],allow_direct=True)
        self.assertEqual([str(track.resolve())],result)
        runtime.catalog_paths.assert_not_called()

    def test_missing_filelist_warns_and_uses_available_catalog(self):
        track=Path(r'C:\Music\Artist\Blame.flac')
        runtime=SimpleNamespace(app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),
                                music_library_playlist_path=lambda: Path(r'Z:\missing\filelist.txt'),
                                catalog_paths=lambda: [str(track)])
        output=io.StringIO()
        with mock.patch.object(instance_module, 'supported_file', return_value=True), contextlib.redirect_stdout(output):
            result=instance_module.resolve_request(runtime,[],regex='Blame')
        self.assertEqual([str(track.resolve())],result['paths'])
        self.assertIn('workflow warning',output.getvalue())

    def test_missing_filelist_is_warning_for_enqueue_filename_lookup(self):
        track=Path(r'C:\Music\Artist\Blame.flac')
        runtime=SimpleNamespace(app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),
                                music_library_playlist_path=lambda: Path(r'Z:\missing\filelist.txt'),
                                catalog_paths=lambda: [str(track)])
        output=io.StringIO()
        with mock.patch.object(workflows, 'supported_file', return_value=True), contextlib.redirect_stdout(output):
            result=workflows.enqueue_selectors(runtime,[{'kind':'path','value':'Blame.flac'}])
        self.assertEqual([str(track)],result)
        self.assertIn('enqueue warning',output.getvalue())

    def test_missing_filelist_searches_music_roots(self):
        track=Path(r'C:\Music\Artist\Blame.flac')
        runtime=workflows.Runtime.__new__(workflows.Runtime)
        runtime.app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}, AUDIO_CATALOG_LIBRARY_ROOT=Path(r'C:\Music'))
        runtime.settings={'library_roots':[],'music_library_playlist':r'Z:\missing\everything.m3u'}
        runtime.index={};runtime.queue_read=None;runtime.lock=threading.RLock()
        with mock.patch.object(Path,'is_dir',return_value=True), \
             mock.patch.object(workflows,'scan_media',return_value=[track]) as scan, \
             mock.patch.object(workflows,'supported_file',return_value=True):
            self.assertEqual([str(track)],runtime.catalog_paths())
        scan.assert_called_once()

    def test_library_path_is_a_persistent_workflow_setting(self):
        runtime=workflows.Runtime.__new__(workflows.Runtime)
        runtime.app=SimpleNamespace(AUDIO_CATALOG_PRIMARY=Path(r'C:\mp3\lists\everything.m3u'))
        runtime.root=Path(r'C:\PAFPlayer-workflow-test')
        runtime.settings={}
        self.assertEqual(Path(r'C:\mp3\lists\everything.m3u'),runtime.music_library_playlist_path())
        runtime.settings['music_library_playlist']=r'D:\Music\lists\all.m3u'
        self.assertEqual(Path(r'D:\Music\lists\all.m3u'),runtime.music_library_playlist_path())
        with mock.patch.object(workflows,'write_json') as write:
            runtime.save_settings()
        write.assert_called_once_with(runtime.root/'settings.json',runtime.settings)
        self.assertIn('workflowLibraryPlaylist',workflows_ui.HTML)
        self.assertIn('music_library_playlist',workflows_ui.SCRIPT)

    def test_web_control_saves_library_path_through_existing_settings_api(self):
        path=Path.cwd()/'tests'/'test-library.m3u'
        payload=json.dumps({'music_library_playlist':str(path)}).encode()
        sent=[]
        handler=SimpleNamespace(command='POST',headers={'Content-Length':str(len(payload))},
                                rfile=io.BytesIO(payload),connection=SimpleNamespace(settimeout=lambda _x: None),
                                _json=lambda status,value: sent.append((status,value)))
        runtime=SimpleNamespace(settings={},save_settings=mock.Mock())
        owner=SimpleNamespace(workflows=runtime)
        with mock.patch.object(web_workflows,'authorized',return_value=True):
            self.assertTrue(web_workflows.handle(handler,owner,'/api/workflows/settings'))
        self.assertEqual(200,sent[0][0])
        self.assertEqual(str(path.resolve()),runtime.settings['music_library_playlist'])
        runtime.save_settings.assert_called_once_with()

    def test_external_queue_edit_is_reported_without_paths(self):
        runtime=SimpleNamespace(queue_bridge=mock.Mock(return_value={'revision':'new'}),
                                note_external_activity=mock.Mock())
        payload={'op':'add','paths':[r'C:\Private\Song.flac']}
        self.assertEqual({'revision':'new'},web_workflows.edit_queue(runtime,payload,source='another PAFPlayer'))
        runtime.note_external_activity.assert_called_once_with('Enqueued 1 track via another PAFPlayer')

    def test_hud_activity_expires(self):
        runtime=workflows.Runtime.__new__(workflows.Runtime)
        runtime.lock=threading.RLock();runtime._hud_activity=None
        with mock.patch.object(workflows.time,'monotonic',side_effect=[100.,101.,106.]):
            runtime.note_external_activity(' Queued   2 tracks ',seconds=5)
            self.assertEqual('Queued 2 tracks',runtime.hud_activity())
            self.assertIsNone(runtime.hud_activity())


if __name__=='__main__': unittest.main()
