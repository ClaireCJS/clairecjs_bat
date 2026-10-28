"""V628 missing-filelist lookup starts near the invoking command folder."""
from pathlib import Path
import threading
import unittest
import uuid
from types import SimpleNamespace
from unittest import mock

import PAFPlayer as player
import PAFPlayer_remote_tray as tray
import PAFPlayer_workflows as workflows


class OutwardLibrarySearchTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(__file__).parent/'runs'/('v628-'+uuid.uuid4().hex)
        self.root.mkdir(parents=True)
        self.addCleanup(lambda: workflows.recycle(self.root))
        self.current=self.root/'Artist'/'Album'
        self.current.mkdir(parents=True)
        self.near=self.current/'Current.flac'
        self.near.write_bytes(b'current')
        self.sibling=self.root/'Artist'/'Other'/'Wanted.flac'
        self.sibling.parent.mkdir(parents=True)
        self.sibling.write_bytes(b'wanted')
        self.runtime=workflows.Runtime.__new__(workflows.Runtime)
        self.runtime.app=SimpleNamespace(AUDIO_EXTENSIONS={'.flac'},
                                         AUDIO_CATALOG_PRIMARY=self.root/'missing.m3u')
        self.runtime.settings={'library_roots':[]}
        self.runtime.index={}
        self.runtime.lock=threading.RLock()
        self.runtime.queue_read=None

    def test_scan_starts_in_current_folder_then_parent_sibling(self):
        found=list(workflows.scan_media_outward(self.current,{'.flac'}))
        self.assertEqual(self.near,found[0])
        self.assertIn(self.sibling,found)
        self.assertEqual(1,found.count(self.near))

    def test_regex_and_filename_resolve_without_master_filelist(self):
        regex={'kind':'regex','pattern':'Other/.*Wanted','origin_dir':str(self.current)}
        path={'kind':'path','value':r'Z:\Other\Wanted.flac','origin_dir':str(self.current)}
        self.assertEqual([str(self.sibling)],workflows.enqueue_selectors(self.runtime,[regex]))
        self.assertEqual([str(self.sibling)],workflows.enqueue_selectors(self.runtime,[path]))

    def test_existing_filelist_skips_outward_scan(self):
        master=self.runtime.app.AUDIO_CATALOG_PRIMARY
        master.write_text(str(self.near)+'\n',encoding='utf-8')
        with mock.patch.object(workflows,'scan_media_outward',side_effect=AssertionError('unneeded')):
            self.assertEqual([str(self.near)],self.runtime.catalog_paths(search_from=self.current,include_outward=True))

    def test_indexed_match_skips_outward_scan(self):
        self.runtime.index={str(self.near):{'path':str(self.near)}}
        with mock.patch.object(workflows,'scan_media_outward',side_effect=AssertionError('unneeded')):
            found=workflows.enqueue_selectors(self.runtime,[{'kind':'regex','pattern':'Current'}])
        self.assertEqual([str(self.near)],found)

    def test_cli_sends_launch_folder_to_owner(self):
        requests=[]
        class Owner:
            def __init__(self,_runtime): pass
            def acquire(self): return False
            def forward(self,request,**_kwargs):
                requests.append(request)
                return {'ok':True,'queued':1,'message':'Queued next'}
        import PAFPlayer_instance as instance
        with mock.patch.object(instance,'Instance',Owner), \
             mock.patch.object(workflows,'get_runtime',return_value=object()), \
             mock.patch.object(tray.Path,'cwd',return_value=self.current):
            self.assertEqual(0,tray.run_enqueue(['Current.flac']))
        self.assertEqual(str(self.current),requests[0]['selectors'][0]['origin_dir'])

    def test_existing_direct_file_needs_no_library_search(self):
        with mock.patch.object(self.runtime,'catalog_paths',side_effect=AssertionError('unneeded')):
            self.assertEqual([str(self.near)],workflows.enqueue_selectors(
                self.runtime,[{'kind':'path','value':str(self.near)}],allow_direct=True))


if __name__=='__main__': unittest.main()
