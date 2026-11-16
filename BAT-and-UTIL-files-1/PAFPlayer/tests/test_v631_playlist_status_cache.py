"""V631 queue status reads remain responsive while file checks run."""
from pathlib import Path
import threading
import time
from types import SimpleNamespace
import unittest
import uuid
from unittest import mock

import PAFPlayer as player
import PAFPlayer_web_workflows as web
from PAFPlayer_workflows import recycle


def identity(path):
    return str(path).casefold()


class PlaylistStatusCacheTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).parent/'runs'/('v631-status-'+uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.addCleanup(lambda: recycle(self.root))
        self.song=self.root/'song.flac';self.song.write_bytes(b'audio')
        self.runtime=SimpleNamespace(missing_playlist_cache=None)

    def wait_for(self,cache,order,source,removed=()):
        present={identity(x) for x in order}
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            result=cache.read(self.runtime,order,source,present,set(removed),identity)
            if cache._cached_key is not None and cache._cached_key==cache._latest_key:
                return result
            time.sleep(.01)
        self.fail('queue status worker did not finish')

    def test_first_read_does_not_wait_for_filesystem(self):
        entered=threading.Event();release=threading.Event()
        def slow_scan(*_args):
            entered.set();release.wait(3);return []
        cache=web.PlaylistStatusCache(refresh_seconds=10)
        with mock.patch.object(web,'missing_playlist_paths',side_effect=slow_scan):
            started=time.monotonic()
            self.assertEqual(((),()),cache.read(self.runtime,[self.song],None,{identity(self.song)},set(),identity))
            self.assertLess(time.monotonic()-started,.25)
            self.assertTrue(entered.wait(1))
            started=time.monotonic()
            cache.read(self.runtime,[self.song],None,{identity(self.song)},set(),identity)
            self.assertLess(time.monotonic()-started,.25)
            release.set()
            self.wait_for(cache,[self.song],None)

    def test_repeated_reads_reuse_cached_file_status(self):
        cache=web.PlaylistStatusCache(refresh_seconds=60)
        with mock.patch.object(web,'missing_playlist_paths',return_value=[]) as scan:
            self.wait_for(cache,[self.song],None)
            self.assertEqual(1,scan.call_count)
            with mock.patch.object(Path,'is_file',side_effect=AssertionError('unexpected file stat')):
                for _ in range(30):
                    self.assertEqual(((),()),cache.read(self.runtime,[self.song],None,{identity(self.song)},set(),identity))
            self.assertEqual(1,scan.call_count)

    def test_membership_change_and_invalidation_schedule_refresh(self):
        cache=web.PlaylistStatusCache(refresh_seconds=60)
        other=self.root/'missing.flac'
        with mock.patch.object(web,'missing_playlist_paths',return_value=[]) as scan:
            self.wait_for(cache,[self.song],None)
            self.assertEqual(((),(str(other),)),self.wait_for(cache,[self.song,other],None))
            self.assertEqual(2,scan.call_count)
            cache.invalidate()
            cache.read(self.runtime,[self.song,other],None,{identity(self.song),identity(other)},set(),identity)
            deadline=time.monotonic()+3
            while scan.call_count<3 and time.monotonic()<deadline: time.sleep(.01)
            self.assertEqual(3,scan.call_count)

    def test_playlist_candidate_cache_rechecks_file_presence(self):
        missing=self.root/'later.flac'
        playlist=self.root/'list.m3u'
        playlist.write_text(str(missing)+'\n',encoding='utf-8')
        self.assertEqual([str(missing)],web.missing_playlist_paths(self.runtime,playlist))
        missing.write_bytes(b'audio')
        self.assertEqual([],web.missing_playlist_paths(self.runtime,playlist))

    def test_queue_edit_uses_known_missing_without_statting_all_entries(self):
        state={'entries':[str(self.song),'missing.flac'],'next':[],
               'current':str(self.song),'playlist':'list.m3u',
               'missing':['missing.flac'],'shuffled':False,'reason':'playlist order'}
        revision=web.queue_revision(state)
        runtime=SimpleNamespace(queue_history=[],log=lambda *_args,**_kwargs:None)
        with mock.patch.object(Path,'is_file',side_effect=AssertionError('unexpected file stat')):
            result=web.calculate_queue_edit(runtime,state,{'op':'remove','paths':[str(self.song)],'revision':revision})
        self.assertEqual(['missing.flac'],result['entries'])
        self.assertEqual(['missing.flac'],result['missing'])

    def test_missing_status_refresh_does_not_invalidate_queue_edit_revision(self):
        state={'entries':[str(self.song)],'next':[],'current':str(self.song),
               'playlist':'list.m3u','missing':[],'shuffled':False,'reason':'playlist order'}
        before=web.queue_revision(state)
        refreshed=dict(state,missing=[str(self.song)],reason='status refreshed')
        self.assertEqual(before,web.queue_revision(refreshed))
        refreshed['entries'].append('other.flac')
        self.assertNotEqual(before,web.queue_revision(refreshed))


if __name__=='__main__': unittest.main()
