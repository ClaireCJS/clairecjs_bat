"""V615 remote enqueue resolves on the official player, never on the client drive."""
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest import mock
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import PAFPlayer as player
from PAFPlayer_workflows import Runtime, enqueue_selectors
from PAFPlayer_instance import Instance
from PAFPlayer_remote_tray import parse_enqueue_arguments, run_enqueue, RemoteServer


class Response(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *_args): self.close()


class EnqueueTests(unittest.TestCase):
    def runtime(self, root):
        runtime=Runtime.__new__(Runtime)
        runtime.app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'},
                                    AUDIO_CATALOG_PRIMARY=root/'everything.m3u')
        runtime.root=root
        runtime.index={}
        runtime.settings={'library_roots':[]}
        runtime.lock=threading.RLock()
        runtime.queue_read=None
        runtime.log=lambda *_args,**_kw: None
        return runtime

    def test_regex_master_playlist_and_no_catalog_error(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw)
            player_file=root/'Artist'/'Blame.flac'
            player_file.parent.mkdir()
            player_file.write_bytes(b'audio')
            runtime=self.runtime(root)
            with self.assertRaisesRegex(ValueError,'matched no songs'):
                enqueue_selectors(runtime,[{'kind':'regex','pattern':'Blame'}])
            (root/'everything.m3u').write_text(str(player_file)+'\n',encoding='utf-8')
            self.assertEqual([str(player_file)],enqueue_selectors(runtime,[{'kind':'regex','pattern':r'Artist/.+\.flac$'}]))
            with self.assertRaisesRegex(ValueError,'matched no songs'):
                enqueue_selectors(runtime,[{'kind':'regex','pattern':'NeverHere'}])

    def test_remote_drive_letter_hint_and_ambiguous_name(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw)
            songs=[]
            for artist in ('One','Two'):
                path=root/artist/'Blame.flac';path.parent.mkdir();path.write_bytes(b'one!' if artist=='One' else b'twoooo');songs.append(path)
            runtime=self.runtime(root)
            runtime.index={str(path):{'path':str(path)} for path in songs}
            with self.assertRaisesRegex(ValueError,'Ambiguous'):
                enqueue_selectors(runtime,[{'kind':'path','value':r'Q:\Blame.flac'}])
            self.assertEqual([str(songs[1])],enqueue_selectors(runtime,[{'kind':'path','value':r'Q:\Two\Blame.flac'}]))
            self.assertEqual([str(songs[0])],enqueue_selectors(runtime,[{'kind':'path','value':r'X:\Blame.flac','size':4}]))

    def test_playlist_neighbor_index_is_persisted(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw);album=root/'Artist'/'Album';album.mkdir(parents=True)
            used=album/'Used.flac';used.write_bytes(b'used')
            sibling=root/'Artist'/'Other'/'Found.flac';sibling.parent.mkdir();sibling.write_bytes(b'found')
            other=root/'AnotherArtist'/'Other.flac';other.parent.mkdir();other.write_bytes(b'other')
            runtime=self.runtime(root)
            runtime.app.AUDIO_CATALOG_LIBRARY_ROOT=root
            runtime.submit=lambda fn: fn()
            runtime.observe_playlist(root/'list.m3u',[used])
            self.assertIn(str(sibling),runtime.catalog_paths())
            self.assertIn(str(other),runtime.catalog_paths())
            self.assertTrue((root/'library.json').is_file())

    def test_cli_identifies_regex_but_not_plain_filename(self):
        address,items=parse_enqueue_arguments(['--server','musicbox:666','Blame.flac','Track (Live).flac','re:^Artist/.+\\.flac$','.*Girl.*'])
        self.assertEqual('musicbox:666',address)
        self.assertEqual(['path','path','regex','regex'],[item['kind'] for item in items])
        with self.assertRaisesRegex(ValueError,'needs a value'):
            parse_enqueue_arguments(['--regex'])

    def test_remote_post_is_bound_to_verified_owner(self):
        class Opener:
            def __init__(self): self.request=None
            def open(self,request,timeout=None):
                self.request=request
                return Response(b'{"ok":true,"queued":1}')
        opener=Opener()
        with mock.patch.object(RemoteServer,'hello',return_value=('official-abc',{})), \
             mock.patch.object(RemoteServer,'_read'):
            with mock.patch.object(RemoteServer,'__init__',autospec=True) as init:
                def setup(server,address):
                    server.url='http://musicbox:666/';server.label='musicbox:666';server._opener=opener
                init.side_effect=setup
                self.assertEqual(0,run_enqueue(['--server','musicbox:666','Blame.flac']))
        self.assertEqual('/api/remote-enqueue',opener.request.full_url.rsplit(':666',1)[1])
        body=json.loads(opener.request.data)
        self.assertEqual('official-abc',body['identity'])
        self.assertEqual('Blame.flac',body['selectors'][0]['value'])

    def test_http_queues_only_through_official_queue_bridge(self):
        with tempfile.TemporaryDirectory() as raw:
            path=Path(raw)/'V615-only-track.flac';path.write_bytes(b'audio')
            web=player.PAFWebServer(host='127.0.0.1',port=0)
            runtime=web.workflows
            old=(getattr(runtime,'instance',None),runtime.index,runtime.queue_read,runtime.queue_bridge,
                 runtime.settings.get('music_library_playlist'))
            old_master=player.AUDIO_CATALOG_PRIMARY
            player.AUDIO_CATALOG_PRIMARY=Path(raw)/'missing.m3u'
            runtime.settings['music_library_playlist']=str(Path(raw)/'missing.m3u')
            calls=[]
            runtime.instance=SimpleNamespace(identity='official-v615',owns=lambda: True)
            runtime.index={str(path):{'path':str(path)}}
            runtime.queue_read=lambda: {'entries':[],'next':[],'current':None,'playlist':None}
            runtime.queue_bridge=lambda payload: calls.append(payload) or {'revision':'after'}
            try:
                self.assertTrue(web.start())
                def post(identity):
                    data=json.dumps({'identity':identity,'selectors':[{'kind':'path','value':r'Z:\Artist\V615-only-track.flac'}]}).encode()
                    return urlopen(Request(web.url.rstrip('/')+'/api/remote-enqueue',data=data,
                                           headers={'Content-Type':'application/json'}),timeout=5)
                with self.assertRaises(HTTPError) as wrong:
                    post('wrong-owner')
                self.assertEqual(409,wrong.exception.code)
                self.assertFalse(calls)
                ownership=iter((True,False))
                runtime.instance=SimpleNamespace(identity='official-v615',owns=lambda: next(ownership))
                with self.assertRaises(HTTPError) as changed:
                    post('official-v615')
                self.assertEqual(409,changed.exception.code)
                self.assertFalse(calls)
                runtime.instance=SimpleNamespace(identity='official-v615',owns=lambda: True)
                with post('official-v615') as response:
                    self.assertEqual(1,json.load(response)['queued'])
                self.assertEqual('add',calls[0]['op'])
                self.assertEqual([str(path)],calls[0]['paths'])
            finally:
                web.close()
                runtime.instance,runtime.index,runtime.queue_read,runtime.queue_bridge,old_library=old
                if old_library is None: runtime.settings.pop('music_library_playlist',None)
                else: runtime.settings['music_library_playlist']=old_library
                player.AUDIO_CATALOG_PRIMARY=old_master

    def test_loopback_handoff_resolves_on_owner_and_uses_queue(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); track=root/'Owner-only.flac';track.write_bytes(b'audio')
            calls=[]
            runtime=SimpleNamespace(root=root,app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'}),
                                    catalog_paths=lambda:[str(track)],
                                    queue_read=lambda:{'entries':[],'next':[],'current':None,'playlist':None},
                                    queue_bridge=lambda payload:calls.append(payload) or {'revision':'after'})
            owner=Instance(runtime)
            owner.start()
            try:
                answer=owner.forward({'selectors':[{'kind':'path','value':r'Z:\Other\Owner-only.flac'}]})
                self.assertEqual(1,answer['queued'])
                self.assertEqual([str(track)],calls[0]['paths'])
            finally: owner.close()


if __name__=='__main__': unittest.main()
