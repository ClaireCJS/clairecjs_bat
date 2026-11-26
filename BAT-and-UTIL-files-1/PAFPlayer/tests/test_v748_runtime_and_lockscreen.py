import hashlib
import io
import json
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import uuid

import PAFPlayer as app
import PAFPlayer_runtime_paths as paths
import PAFPlayer_remote_lockscreen as remote
import PAFPlayer_lockscreen as lock
import PAFPlayer_lockscreen_payload as payload
import PAFPlayer_ffmpeg_setup as ffmpeg
import PAFPlayer_model_storage as storage

ROOT=Path(__file__).resolve().parents[1]

class RuntimeAndLockScreenTests(unittest.TestCase):
    def stage(self):
        directory=ROOT/'tests/runs'/('v748-'+uuid.uuid4().hex)
        directory.mkdir(parents=True)
        return directory

    def test_all_flat_claire_scripts_are_moved_and_collisions_preserved(self):
        directory=self.stage();dest=directory/'runtime/clairecjs_utils';dest.mkdir(parents=True)
        (dest/'claire_anything.py').write_text('existing',encoding='utf-8')
        for name in ('claire_anything.py','claire_console.py','claire_custom_helper.py'):
            (directory/name).write_text('legacy',encoding='utf-8')
        moved=paths.migrate_flat_helpers(directory)
        self.assertEqual(len(moved),3)
        self.assertEqual(list(directory.glob('claire_*.py')),[])
        self.assertEqual((dest/'claire_anything.py').read_text(),'existing')
        self.assertEqual((dest/'legacy/claire_anything.py').read_text(),'legacy')
        self.assertEqual(paths.migrate_flat_helpers(directory),[])

    def test_download_bootstrap_writes_only_runtime_and_reuses_existing(self):
        directory=self.stage();target=directory/'runtime/clairecjs_utils'
        with patch.object(app,'helper_directory',return_value=target),patch('urllib.request.urlopen',return_value=io.BytesIO(b'API_VERSION = 1\n')) as download:
            self.assertTrue(app._download_missing_claire_helper('claire_fixture'))
            self.assertEqual((target/'claire_fixture.py').read_bytes(),b'API_VERSION = 1\n')
            self.assertEqual(list(directory.glob('claire_*.py')),[])
            with patch.object(app,'_claire_helper_available',return_value=True):
                self.assertTrue(app._download_missing_claire_helper('claire_fixture'))
            self.assertEqual(download.call_count,1)

    def test_installation_payload_extracts_under_runtime_with_verified_hashes(self):
        directory=self.stage()
        with patch.object(paths,'runtime_root',return_value=directory/'runtime'):
            extracted=lock.embedded_installer_root()
        self.assertTrue(extracted.is_relative_to(directory/'runtime'))
        for file in extracted.rglob('*'):
            if file.name in payload.PAYLOAD_SHA256:
                self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),payload.PAYLOAD_SHA256[file.name])
        self.assertTrue((extracted/'dist/v531/PAFPlayerLockScreen_v531_x64.msix').is_file())

    def test_default_download_locations_stay_in_runtime(self):
        self.assertTrue(ffmpeg.support_root().is_relative_to(paths.runtime_root()))
        with patch.object(storage.os,'environ',{}),patch.object(storage,'preference_path',return_value=self.stage()/'absent.json'):
            self.assertTrue(storage.preferred_root().is_relative_to(paths.runtime_root()))

    def test_transient_network_gap_uses_cached_cues_but_expires(self):
        server=SimpleNamespace(_lock=threading.RLock(),connected=False,owner_identity='',clock_offset=0,
            _last_verified_at=100,_last_verified_identity='owner',
            _state={'program':'PAFPlayer','version':'V748','playing':True,'paused':False,
                    'lyric_clock_epoch':100,'lyric_position_seconds':1,'duration_seconds':180,
                    'lyric_timeline':[[0,'First'],[6,'Second']]})
        with patch.object(remote.time,'monotonic',return_value=110):
            state=remote.status_payload(server,'lease','owner',now=110)['state']
            self.assertEqual(state['position_seconds'],11)
            self.assertEqual(state['lyric'],'Second')
        with patch.object(remote.time,'monotonic',return_value=116):
            self.assertIsNone(remote.status_payload(server,'lease','owner',now=116))
        with patch.object(remote.time,'monotonic',return_value=110):
            self.assertIsNone(remote.status_payload(server,'lease','different',now=110))

    def test_new_companion_is_required_for_upgrade(self):
        self.assertEqual(lock.EMBEDDED_INSTALL_VERSION,'531.0.0.0')
        self.assertIn('PAFPlayerLockScreen_v531_x64.msix',payload.PAYLOAD_SHA256)

    def test_optional_loopback_installer_targets_runtime(self):
        directory=self.stage();backend=object()
        with patch.object(app,'paf_runtime_root',return_value=directory/'runtime'), \
             patch.object(app,'AUTO_INSTALL_PYAUDIO_WPATCH',True), \
             patch.object(app,'_LIVE_INPUT_BACKEND_INSTALL_ATTEMPTED',False), \
             patch.object(app.sys,'argv',['paf.py']), \
             patch.object(app.importlib,'import_module',side_effect=[ImportError(),ImportError(),backend]), \
             patch.object(app.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
            self.assertIs(app._ensure_pyaudiowpatch(),backend)
        command=run.call_args.args[0]
        target=Path(command[command.index('--target')+1])
        self.assertTrue(target.is_relative_to(directory/'runtime'))
        self.assertTrue((target/'complete').is_file())
        self.assertTrue(Path(run.call_args.kwargs['env']['TEMP']).is_relative_to(directory/'runtime'))

    def test_first_party_recovery_preserves_numbered_collisions(self):
        folder=self.stage()/'runtime/clairecjs_utils';folder.mkdir(parents=True)
        (folder/'claire_audio_processing.py').write_text('old file',encoding='utf-8')
        with patch.dict(app.sys.modules), \
             patch.object(app,'_CLAIRECJS_IMPORTED_MODULES',{}), \
             patch.object(app,'find_clairecjs_dependency',return_value=None), \
             patch.object(app,'_prompt_clairecjs_download_location',return_value=folder), \
             patch('urllib.request.urlopen',return_value=io.BytesIO(b'CLAIRE_AUDIO_PROCESSING_VERSION = "V2"\n')):
            recovered=app.ensure_clairecjs_dependency('claire_audio_processing')
            self.assertIsNotNone(recovered)
        self.assertEqual((folder/'claire_audio_processing.py').read_text(),'old file')
        self.assertTrue((folder/'claire_audio_processing (1).py').is_file())
