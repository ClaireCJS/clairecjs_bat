"""V623: visible regex resolution and confirmed owner-side enqueue previews."""
from collections import deque
import contextlib
import io
import json
from pathlib import Path
import threading
import unittest
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import PAFPlayer as player
import PAFPlayer_instance as instance_module
import PAFPlayer_remote_tray as tray
import PAFPlayer_workflows as workflows


class PreviewTests(unittest.TestCase):
    def test_match_listing_groups_folders_and_colors_each_filename(self):
        paths=[r'C:\Music\One\A.flac',r'C:\Music\Two\B.flac',r'C:\Music\One\C.flac']
        listing=tray.format_enqueue_matches(paths,color=True)
        self.assertEqual(1,listing.count(r'C:\Music\One'))
        self.assertEqual(1,listing.count(r'C:\Music\Two'))
        self.assertEqual(3,listing.count('\x1b[38;2;'))
        self.assertIn('  3. ',listing)
        self.assertEqual(1,tray.format_enqueue_matches(paths,limit=2).count(r'C:\Music\One'))

    def test_owner_preview_is_read_only_one_use_and_rechecks_media(self):
        track=r'C:\Music\Artist\Song.flac'
        runtime=SimpleNamespace(lock=threading.RLock(),app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),
                                catalog_paths=lambda:[track],queue_bridge=mock.Mock())
        with mock.patch.object(workflows,'supported_file',return_value=True):
            preview=workflows.prepare_enqueue_preview(runtime,[{'kind':'regex','pattern':'Artist.*Song'}])
            runtime.queue_bridge.assert_not_called()
            self.assertEqual([track],preview['matches'])
            self.assertEqual([track],workflows.consume_enqueue_preview(runtime,preview['preview_token']))
            with self.assertRaisesRegex(ValueError,'expired'):
                workflows.consume_enqueue_preview(runtime,preview['preview_token'])
            other=workflows.prepare_enqueue_preview(runtime,[{'kind':'regex','pattern':'Song'}])
        with self.assertRaisesRegex(ValueError,'changed or disappeared'):
            workflows.consume_enqueue_preview(runtime,other['preview_token'])
        runtime.queue_bridge.assert_not_called()

    def test_local_ipc_previews_without_mutating_then_commits_once(self):
        track=r'C:\Music\Rudy\Bowl of Cherries.flac'
        calls=[];descriptor={}
        runtime=SimpleNamespace(root=Path(r'C:\PAFPlayer-preview-test'),lock=threading.RLock(),
                                app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),settings={'enqueue_placement':'end'},
                                catalog_paths=lambda:[track],
                                queue_read=lambda:{'entries':[],'next':[],'current':None,'playlist':'test.m3u'},
                                queue_bridge=lambda payload:calls.append(payload) or {'revision':'new'},
                                log=lambda *_a,**_k:None)
        owner=instance_module.Instance(runtime)
        with mock.patch.object(instance_module,'write_json',side_effect=lambda _path,value: descriptor.update(value)),\
             mock.patch.object(instance_module,'read_json',return_value=descriptor),\
             mock.patch.object(instance_module,'supported_file',return_value=True),\
             mock.patch.object(workflows,'supported_file',return_value=True):
            owner.start()
            try:
                preview=owner.forward({'selectors':[{'kind':'regex','pattern':'rudy.*bowl.of.cherr'}],
                                       'preview_only':True})
                self.assertEqual([track],preview['matches'])
                self.assertEqual([],calls)
                receipt=owner.forward({'preview_token':preview['preview_token'],'placement':'after_current'})
                self.assertEqual(1,receipt['queued'])
                self.assertEqual([track],calls[0]['paths'])
                self.assertEqual('after_current',calls[0]['placement'])
            finally: owner.close()

    def test_cli_regex_prints_progress_and_results_before_commit(self):
        requests=[]
        class Owner:
            def __init__(self,_runtime): pass
            def acquire(self): return False
            def forward(self,request,*,timeout=60):
                requests.append(request)
                if request.get('preview_only'):
                    return {'ok':True,'matches':[r'C:\Music\Rudy\Bowl of Cherries.flac'],
                            'preview_token':'x'*32,'count':1}
                return {'ok':True,'queued':1,'message':'Queued next'}
        output=io.StringIO()
        with mock.patch.object(instance_module,'Instance',Owner),\
             mock.patch.object(workflows,'get_runtime',return_value=object()),\
             contextlib.redirect_stdout(output):
            self.assertEqual(0,tray.run_enqueue(['rudy.*bowl.of.cherr']))
        self.assertIn('Searching the official player library',output.getvalue())
        self.assertIn('Search matched 1 track',output.getvalue())
        self.assertIn('Bowl of Cherries.flac',output.getvalue())
        self.assertEqual('preview_token',next(iter(requests[1])))

    def test_large_preview_requires_confirmation_before_commit(self):
        requests=[]
        paths=[rf'C:\Music\Album\Track {i:02}.flac' for i in range(21)]
        class Owner:
            def __init__(self,_runtime): pass
            def acquire(self): return False
            def forward(self,request,*,timeout=60):
                requests.append(request)
                if request.get('preview_only'):
                    return {'ok':True,'matches':paths,'preview_token':'x'*32,'count':len(paths)}
                return {'ok':True,'queued':len(paths),'message':'Queued next'}
        with mock.patch.object(instance_module,'Instance',Owner),\
             mock.patch.object(workflows,'get_runtime',return_value=object()),\
             mock.patch.object(tray,'confirm_enqueue_matches',return_value=False),\
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1,tray.run_enqueue(['re:Track.*']))
        self.assertEqual(1,len(requests))
        with mock.patch.object(instance_module,'Instance',Owner),\
             mock.patch.object(workflows,'get_runtime',return_value=object()),\
             mock.patch.object(tray,'confirm_enqueue_matches',return_value=True),\
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0,tray.run_enqueue(['re:Track.*'],placement='end'))
        self.assertEqual('end',requests[-1]['placement'])
        self.assertEqual('x'*32,requests[-1]['preview_token'])

    def test_noninteractive_large_preview_does_not_queue(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertFalse(tray.confirm_enqueue_matches(21,stdin=io.StringIO()))
        terminal=SimpleNamespace(isatty=lambda:True)
        self.assertFalse(tray.confirm_enqueue_matches(21,input_fn=lambda _prompt:'',stdin=terminal))
        self.assertTrue(tray.confirm_enqueue_matches(21,input_fn=lambda _prompt:'y',stdin=terminal))
        self.assertEqual('list',tray.confirm_enqueue_matches(21,input_fn=lambda _prompt:'L',stdin=terminal))

    def test_interrupt_during_large_match_confirmation_never_commits(self):
        requests=[]
        class Owner:
            def __init__(self,_runtime): pass
            def acquire(self): return False
            def forward(self,request,*,timeout=60):
                requests.append(request)
                return {'ok':True,'matches':[rf'C:\Music\Track {i}.flac' for i in range(21)],
                        'preview_token':'x'*32,'count':21}
        with mock.patch.object(instance_module,'Instance',Owner),\
             mock.patch.object(workflows,'get_runtime',return_value=object()),\
             mock.patch.object(tray,'confirm_enqueue_matches',side_effect=KeyboardInterrupt),\
             contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(1,tray.run_enqueue(['re:Track']))
        self.assertEqual(1,len(requests))

    def test_remote_preview_and_commit_keep_same_owner_identity(self):
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*_args): self.close()
        class Opener:
            def __init__(self): self.requests=[]
            def open(self,request,timeout=None):
                self.requests.append((request,timeout))
                if len(self.requests)==1:
                    return Response(json.dumps({'ok':True,'matches':[r'D:\Music\Song.flac'],
                                                'preview_token':'x'*32,'count':1}).encode())
                return Response(b'{"ok":true,"queued":1,"message":"Queued next"}')
        opener=Opener()
        def setup(server,_address):
            server.url='http://musicbox:666/'
            server.label='musicbox:666'
            server._opener=opener
        with mock.patch.object(tray.RemoteServer,'__init__',autospec=True,side_effect=setup),\
             mock.patch.object(tray.RemoteServer,'hello',return_value=('official-v623',{})),\
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0,tray.run_enqueue(['--server','musicbox:666','re:Song']))
        preview=json.loads(opener.requests[0][0].data)
        commit=json.loads(opener.requests[1][0].data)
        self.assertEqual('official-v623',preview['identity'])
        self.assertEqual('official-v623',commit['identity'])
        self.assertEqual('x'*32,commit['preview_token'])
        self.assertEqual(120,opener.requests[0][1])

    def test_remote_http_preview_does_not_edit_and_token_commits_once(self):
        track=r'C:\Music\Artist\Song.flac'
        web=player.PAFWebServer(host='127.0.0.1',port=0)
        runtime=web.workflows
        old=(getattr(runtime,'instance',None),runtime.queue_read,runtime.queue_bridge,
             dict(getattr(runtime,'enqueue_previews',{})))
        calls=[]
        runtime.instance=SimpleNamespace(identity='official-v623',owns=lambda:True)
        runtime.queue_read=lambda:{'entries':[],'next':[],'current':None,'playlist':'test.m3u'}
        runtime.queue_bridge=lambda payload:calls.append(payload) or {'revision':'new'}
        runtime.enqueue_previews={}
        def post(payload):
            body=json.dumps(payload).encode()
            return urlopen(Request(web.url.rstrip('/')+'/api/remote-enqueue',data=body,
                                   headers={'Content-Type':'application/json'}),timeout=5)
        try:
            with mock.patch.object(workflows,'enqueue_selectors',return_value=[track]),\
                 mock.patch.object(workflows,'supported_file',return_value=True):
                self.assertTrue(web.start())
                with post({'identity':'official-v623','selectors':[{'kind':'regex','pattern':'Song'}],
                           'preview_only':True}) as response:
                    preview=json.load(response)
                self.assertEqual([track],preview['matches'])
                self.assertEqual([],calls)
                commit={'identity':'official-v623','preview_token':preview['preview_token'],
                        'placement':'end'}
                with self.assertRaises(HTTPError) as wrong:
                    post(dict(commit,identity='wrong'))
                self.assertEqual(409,wrong.exception.code)
                self.assertEqual([],calls)
                with post(commit) as response:
                    self.assertEqual(1,json.load(response)['queued'])
                self.assertEqual([track],calls[0]['paths'])
                self.assertEqual('end',calls[0]['placement'])
                with self.assertRaises(HTTPError) as reused:
                    post(commit)
                self.assertEqual(400,reused.exception.code)
                self.assertEqual(1,len(calls))
        finally:
            web.close()
            runtime.instance,runtime.queue_read,runtime.queue_bridge,previous=old
            runtime.enqueue_previews=previous


if __name__=='__main__': unittest.main()
