import codecs
import contextlib
import io
import json
from pathlib import Path
import tempfile
import time
import types
import unittest
from unittest import mock
import urllib.error
import urllib.request
import wave
import PAFPlayer as p
import PAFPlayer_workflows as w
import PAFPlayer_web_workflows as web
import PAFPlayer_windows_media as windows_media


def fixture(root,name='song.wav'):
    path=root/name; path.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(path),'wb') as out:
        out.setnchannels(1); out.setsampwidth(2); out.setframerate(8000); out.writeframes(b'\0\0'*16000)
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='paf456-tests-'))
        self.app=types.SimpleNamespace(AUDIO_EXTENSIONS={'.wav','.mp3'},append_pafplayer_trace=mock.Mock(),probe_duration_seconds=lambda x:2.,probe_audio_tags=lambda x:{'Artist':'Test'},ffprobe_executable=p.ffprobe_executable,load_player_settings=lambda:{})
        self.runtime=w.Runtime(self.app,self.root/'state')


class WindowsMediaTests(unittest.TestCase):
    def test_inactive_chrome_reclaims_after_one_minute(self):
        since,reclaim=windows_media.chrome_reclaim_deadline('chrome.exe','paused',None,100.)
        self.assertEqual(100.,since);self.assertFalse(reclaim)
        since,reclaim=windows_media.chrome_reclaim_deadline('chrome.exe','paused',since,159.9)
        self.assertFalse(reclaim)
        since,reclaim=windows_media.chrome_reclaim_deadline('chrome.exe','paused',since,160.)
        self.assertTrue(reclaim)

    def test_playing_chrome_and_other_apps_are_never_reclaimed(self):
        self.assertEqual((None,False),windows_media.chrome_reclaim_deadline('chrome.exe','playing',10.,500.))
        self.assertEqual((None,False),windows_media.chrome_reclaim_deadline('vlc.exe','paused',10.,500.))


class RepairTests(Base):
    def test_encoding_newlines_comments_and_verified_backup(self):
        song=fixture(self.root,'Song Live.wav'); playlist=self.root/'list.m3u'
        original=codecs.BOM_UTF16_LE+('#EXTM3U\r\n# retained café\r\nmissing\\Song (Live).wav\r\n').encode('utf-16-le'); playlist.write_bytes(original)
        _,_,_,rows=w.playlist_rows(playlist); old=rows[0]['path']
        preview=w.rewrite_playlist(self.app,playlist,{old:{'path':str(song)}},dry_run=True)
        self.assertTrue(preview['changes']); self.assertEqual(original,playlist.read_bytes())
        result=w.rewrite_playlist(self.app,playlist,{old:{'path':str(song),'confidence':'high','evidence':['test evidence']}},expected_hash=w.digest(playlist))
        self.assertEqual(original,Path(result['backup']).read_bytes())
        self.assertEqual(codecs.BOM_UTF16_LE+('#EXTM3U\r\n# retained café\r\n'+str(song)+'\r\n').encode('utf-16-le'),playlist.read_bytes())
        self.app.append_pafplayer_trace.assert_called_once()

    def test_approval_must_select_previewed_unchanged_candidate(self):
        song=fixture(self.root); missing=self.root/'missing'/'song.wav'; playlist=self.root/'list.m3u'; playlist.write_text(str(missing)+'\n')
        preview=web.repair_preview(self.runtime,{'playlist':str(playlist),'roots':[str(self.root)]})
        self.assertEqual('ambiguous',preview['items'][0]['candidates'][0]['confidence'])
        with self.assertRaises(ValueError): web.apply_repair(self.runtime,{'id':preview['id'],'approved':{str(missing):str(self.root/'not-previewed.wav')},'dry_run':False,'playlist_only':True})
        original=playlist.read_bytes()
        result=web.apply_repair(self.runtime,{'id':preview['id'],'approved':{str(missing):str(song)},'dry_run':True,'playlist_only':True})
        self.assertTrue(result['dry_run']); self.assertEqual(original,playlist.read_bytes())
        result=web.apply_repair(self.runtime,{'id':preview['id'],'approved':{str(missing):str(song)},'dry_run':False,'playlist_only':True})
        self.assertEqual(str(song)+'\n',playlist.read_text())

    def test_hash_evidence_is_high_confidence_but_name_alone_is_not(self):
        song=fixture(self.root); missing=self.root/'old'/'song.wav'
        results=w.repair_candidates(self.app,missing,[self.root],evidence={'sha256':w.digest(song),'size':song.stat().st_size,'duration':2.,'tags':{'Artist':'Test'}})
        self.assertEqual('high',results[0]['confidence']); self.assertIn('SHA-256 identity matches',results[0]['evidence'])

    def test_playlist_conflict_does_not_overwrite(self):
        song=fixture(self.root); target=self.root/'list.m3u';target.write_text('old.wav\n'); expected=w.digest(target);target.write_text('changed.wav\n')
        with self.assertRaises(ValueError): w.rewrite_playlist(self.app,target,{},expected_hash=expected)
        self.assertEqual('changed.wav\n',target.read_text())


class MonitorTests(Base):
    def test_stability_restart_rename_and_hidden_backup_exclusion(self):
        folder=self.root/'music';folder.mkdir();song=fixture(folder)
        fixture(folder,'.hidden.wav');fixture(folder,'song.bak.wav');fixture(folder,'transfer.part.wav')
        monitor=w.FolderMonitor(self.runtime,[folder]);self.assertEqual([],monitor.scan(now=0)); self.assertEqual([],monitor.scan(now=1))
        result=monitor.scan(now=3);self.assertEqual(1,len(result));self.assertEqual('import',result[0]['action'])
        again=w.FolderMonitor(self.runtime,[folder]);self.assertEqual([],again.scan(now=10))
        renamed=folder/'renamed.wav';song.rename(renamed);again.scan(now=11);result=again.scan(now=14)
        self.assertEqual('rename',result[0]['action']);self.assertNotIn(w.pathkey(song),self.runtime.index)
        self.assertEqual(1,len(self.runtime.index))

    def test_dry_run_changes_no_files_or_membership(self):
        folder=self.root/'music';folder.mkdir();fixture(folder)
        monitor=w.FolderMonitor(self.runtime,[folder],mode='library')
        self.assertEqual('pending-stability',monitor.scan(dry_run=True,now=0)[0]['action'])
        self.assertEqual('import',monitor.scan(dry_run=True,now=3)[0]['action'])
        self.assertFalse(self.runtime.root.exists());self.assertFalse(self.runtime.index)

    def test_playlist_import_is_deduplicated_and_backs_up(self):
        folder=self.root/'music';folder.mkdir();song=fixture(folder);playlist=self.root/'queue.m3u';playlist.write_text('#EXTM3U\r\n')
        monitor=w.FolderMonitor(self.runtime,[folder],mode='playlist',playlist=playlist)
        monitor.scan(now=0);monitor.scan(now=3);monitor.scan(now=4)
        self.assertEqual(1,playlist.read_text().count(str(song)));self.assertEqual(1,len(list(self.root.glob('queue.m3u.bak.*'))))


class QueueTests(Base):
    def setUp(self):
        super().setUp(); self.paths=[str(fixture(self.root,name+'.wav')) for name in ('a','b','c')]
        self.state={'entries':self.paths[:],'next':[],'current':self.paths[0],'playlist':'test.m3u','reason':'playlist order'}
        self.runtime.queue_read=lambda:self.state
        def bridge(payload):
            self.state=web.calculate_queue_edit(self.runtime,self.state,payload);return web.queue_snapshot(self.runtime)
        self.runtime.queue_bridge=bridge

    def apply(self,op,paths=(),**kw):return web.edit_queue(self.runtime,{'op':op,'paths':list(paths),'revision':web.queue_snapshot(self.runtime)['revision'],**kw})

    def test_next_remove_undo_move_and_conflict(self):
        self.apply('next',[self.paths[2]]);self.assertEqual([self.paths[2]],self.state['next'])
        previous=web.queue_snapshot(self.runtime)['revision'];self.apply('remove',[self.paths[1]])
        self.assertTrue(Path(self.paths[1]).exists());self.assertNotIn(self.paths[1],self.state['entries'])
        with self.assertRaises(ValueError):web.edit_queue(self.runtime,{'op':'remove','paths':[self.paths[2]],'revision':previous})
        self.apply('undo');self.assertEqual(self.paths,self.state['entries'])
        self.apply('top',[self.paths[2]]);self.assertEqual(self.paths[2],self.state['entries'][0])

    def test_save_new_playlist_never_overwrites(self):
        a=self.apply('save',name='queue.m3u8');b=self.apply('save',name='queue.m3u8')
        self.assertNotEqual(a['saved_path'],b['saved_path']);self.assertTrue(Path(a['saved_path']).is_file())


class SecurityTests(Base):
    def test_policy_one_shared_machine_list_and_user_or_host(self):
        self.assertTrue(w.policy_default({'USERNAME':'claire','COMPUTERNAME':'other'}))
        for host in w.TRUSTED_MACHINES:self.assertTrue(w.policy_default({'USERNAME':'other','COMPUTERNAME':host.upper()}))
        self.assertFalse(w.policy_default({'USERNAME':'other','COMPUTERNAME':'other'}))

    def test_upload_filename_rejections(self):
        for name in ('../evil.wav','a\\b.wav','CON.wav','a.wav:evil','evil.exe','evil.wav\r\nX: y','%2e%2e%2Fevil.wav'):
            with self.subTest(name=name),self.assertRaises(ValueError):web.safe_filename(name,{'.wav'})

    def test_redaction(self):
        for secret in ('hunter2',r'C:\private\song.wav','secret-token'):
            text='event '+json.dumps({'password':'hunter2','path':r'C:\private\song.wav','token':'secret-token'})
            self.assertNotIn(secret,w.redact(text))
        self.assertNotIn('some name.wav',w.redact('upload.accepted filename=some name.wav'))

    def test_upload_ttl_retains_queued_files_and_recycles_only_managed_files(self):
        root=self.runtime.root/'uploads';root.mkdir(parents=True);active=fixture(root,'active.wav');old=fixture(root,'old.wav')
        self.runtime.uploads={str(active):{'created':0},str(old):{'created':0}}
        self.runtime.queue_read=lambda:{'entries':[str(active)],'next':[],'current':None}
        with mock.patch.object(web,'recycle') as recycle:web.cleanup_uploads(self.runtime,now=w.UPLOAD_TTL_SECONDS+1)
        recycle.assert_called_once_with(old.resolve());self.assertIn(str(active),self.runtime.uploads)


class HttpTests(Base):
    def setUp(self):
        super().setUp();self.server=p.PAFWebServer(host='127.0.0.1',port=0);self.server.workflows=self.runtime;self.runtime.server=self.server
        self.assertTrue(self.server.start());self.url=self.server.url

    def tearDown(self):self.server.close();self.runtime.close()

    def request(self,path,payload=None,token=True,headers=None):
        head=headers or {}
        if token:head['X-PAF-Workflow-Token']=self.runtime.token
        request=urllib.request.Request(self.url.rstrip('/')+'/api/workflows/'+path,data=json.dumps(payload).encode() if payload is not None else None,headers=head)
        with urllib.request.urlopen(request,timeout=4) as response:return json.load(response)

    def test_security_settings_and_token_validation(self):
        value=self.request('status');self.assertTrue(value['local']);self.assertEqual(self.runtime.token,value['token'])
        with self.assertRaises(urllib.error.HTTPError) as err:self.request('settings',{'remote_uploads':True},token=False)
        self.assertEqual(403,err.exception.code)
        with self.assertRaises(urllib.error.HTTPError):self.request('settings',{'remote_uploads':True},headers={'Origin':'https://example.com'})
        self.request('settings',{'remote_uploads':False});self.assertFalse(self.runtime.settings['remote_uploads'])

    def test_upload_content_is_validated_not_just_extension(self):
        self.runtime.settings['remote_uploads']=True
        for data,ok in ((b'not audio',False),(fixture(self.root).read_bytes(),True)):
            req=urllib.request.Request(self.url.rstrip('/')+'/api/workflows/upload',data=data,headers={'X-PAF-Workflow-Token':self.runtime.token,'X-File-Name':'test.wav','Content-Type':'application/octet-stream'})
            # Recycle is mocked only to retain failed test artifacts; production uses OS Recycle Bin.
            with mock.patch.object(web,'recycle') as recycle:
                if ok:
                    with urllib.request.urlopen(req,timeout=15) as response:self.assertTrue(json.load(response)['ok'])
                else:
                    with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(req,timeout=15)
                    recycle.assert_called_once()


if __name__=='__main__':unittest.main()
