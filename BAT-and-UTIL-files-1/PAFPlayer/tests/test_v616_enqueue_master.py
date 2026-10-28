"""V616 short enqueue spelling and background everything.m3u creation."""
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

import PAFPlayer as player
from PAFPlayer_remote_tray import parse_enqueue_arguments
from PAFPlayer_workflows import Runtime, build_master_playlist, enqueue_selectors


class ShortEnqueueAndMasterTests(unittest.TestCase):
    def test_short_and_long_cli_dispatch_the_same_unquoted_regex(self):
        import PAFPlayer_remote_tray as tray
        pattern='metallica.*justice'
        _,selectors=parse_enqueue_arguments([pattern])
        self.assertEqual([{'kind':'regex','pattern':pattern}],selectors)
        with mock.patch.object(tray,'run_enqueue',return_value=17) as enqueue:
            self.assertEqual(17,player.main(['-q',pattern]))
            self.assertEqual(17,player.main(['--enqueue',pattern]))
        self.assertEqual([mock.call([pattern]),mock.call([pattern])],enqueue.call_args_list)

    def test_missing_master_build_is_background_and_regex_searches_result(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw)/'music';root.mkdir()
            album=root/'Metallica'/'And Justice for All';album.mkdir(parents=True)
            target=album/'Blackened.flac';target.write_bytes(b'audio')
            (root/'Other.flac').write_bytes(b'other')
            (root/'ignore.txt').write_text('not audio')
            master=root/'lists'/'everything.m3u'
            runtime=Runtime.__new__(Runtime)
            runtime.app=SimpleNamespace(AUDIO_CATALOG_PRIMARY=master,AUDIO_CATALOG_LIBRARY_ROOT=root,
                                        AUDIO_EXTENSIONS={'.flac'})
            runtime.settings={'library_roots':[]};runtime.index={};runtime.queue_read=None
            runtime.lock=threading.RLock();runtime.log=lambda *_args,**_kw: None
            queued=[];runtime.submit=lambda fn: queued.append(fn)
            self.assertTrue(runtime.ensure_master_playlist())
            self.assertFalse(master.exists())
            self.assertEqual(1,len(queued))
            self.assertFalse(runtime.ensure_master_playlist())
            # Missing filelists are optional: configured roots remain searchable
            # while their background master-playlist build is pending.
            self.assertEqual([str(target)],enqueue_selectors(runtime,[{'kind':'regex','pattern':'metallica.*justice'}]))
            self.assertEqual({'created':True,'count':2},queued.pop()())
            self.assertFalse(runtime.master_build_pending)
            text=master.read_text(encoding='utf-8')
            self.assertTrue(text.startswith('#EXTM3U\n'))
            self.assertIn(str(target),text)
            self.assertNotIn('ignore.txt',text)
            self.assertEqual([str(target)],enqueue_selectors(runtime,[{'kind':'regex','pattern':'metallica.*justice'}]))
            runtime.master_build_pending=True
            with self.assertRaisesRegex(ValueError,'no indexed matches yet'):
                enqueue_selectors(runtime,[{'kind':'regex','pattern':'nonexistent.*album'}])

    def test_existing_master_is_never_rewritten(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw);master=root/'everything.m3u'
            master.write_bytes(b'#EXTM3U\n# hand curated\n')
            before=master.read_bytes()
            self.assertEqual({'created':False,'count':0},build_master_playlist(master,[root],{'.flac'}))
            self.assertEqual(before,master.read_bytes())
            self.assertFalse(list(root.glob('*.building')))
            self.assertFalse(list(root.glob('*.bak.*')))

    def test_no_root_cannot_create_misleading_empty_master(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw)
            with self.assertRaisesRegex(ValueError,'No existing music-library root'):
                build_master_playlist(root/'lists'/'everything.m3u',[root/'missing'],{'.flac'})
            self.assertFalse((root/'lists'/'everything.m3u').exists())
            runtime=Runtime.__new__(Runtime)
            runtime.app=SimpleNamespace(AUDIO_CATALOG_PRIMARY=root/'lists'/'everything.m3u',
                                        AUDIO_CATALOG_LIBRARY_ROOT=root/'missing',AUDIO_EXTENSIONS={'.flac'})
            runtime.settings={'library_roots':[]};runtime.lock=threading.RLock()
            events=[];queued=[]
            runtime.log=lambda event,**fields: events.append((event,fields))
            runtime.submit=lambda fn: queued.append(fn)
            self.assertTrue(runtime.ensure_master_playlist())
            with self.assertRaisesRegex(ValueError,'No existing music-library root'):
                queued.pop()()
            self.assertEqual('library.master-build-error',events[-1][0])
            self.assertFalse(runtime.master_build_pending)


if __name__=='__main__': unittest.main()
