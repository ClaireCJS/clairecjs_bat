import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tag_setup',ROOT/'src/PAFPlayer_playlist_window.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class DependencyTests(unittest.TestCase):
    def setUp(self):
        self.root=ROOT/'tests/runs'/('v747-'+uuid.uuid4().hex)
        self.roots=patch.object(module,'metadata_package_roots',return_value=[self.root]);self.roots.start()
        self.addCleanup(self.roots.stop)

    def test_existing_runtime_requires_no_download(self):
        sentinel=object()
        with patch('importlib.import_module',return_value=sentinel),patch('urllib.request.urlopen') as download:
            self.assertIs(module.load_mutagen(),sentinel);download.assert_not_called()

    def test_preexisting_completed_cache_remains_available_offline(self):
        folder=self.root/'mutagen-fixture';folder.mkdir(parents=True)
        (folder/'complete').write_text('fixture',encoding='ascii')
        sentinel=object()
        with patch('importlib.import_module',side_effect=[ModuleNotFoundError(name='mutagen'),sentinel]),patch('urllib.request.urlopen') as download:
            self.assertIs(module.load_mutagen(),sentinel);download.assert_not_called()

    def test_incomplete_runtime_never_downloads_at_editor_open(self):
        with patch('importlib.import_module',side_effect=ModuleNotFoundError(name='mutagen')),patch('urllib.request.urlopen') as download:
            with self.assertRaisesRegex(RuntimeError,'bundled runtime/python.exe'):module.load_mutagen(install=True)
            download.assert_not_called()
        self.assertFalse(self.root.exists())
