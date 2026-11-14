"""Shared progress imports work even if the package initializer cannot load."""
import importlib
from pathlib import Path
import site
import sys
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class ProgressDiscoveryTests(unittest.TestCase):
    def test_search_includes_root_bat_script_cwd_and_site_directories(self):
        with mock.patch.object(site, "getsitepackages", return_value=["C:/synthetic-site"]), mock.patch.object(site, "getusersitepackages", return_value="C:/synthetic-user-site"):
            paths = audit.progress_library_search_dirs()
        for root in (Path("C:/"), Path("C:/BAT"), audit._SCRIPT_DIR, Path.cwd(), Path("C:/synthetic-site"), Path("C:/synthetic-user-site")):
            for folder in (root, root / "clairecjs_util", root / "clairecjs_utils"):
                self.assertIn(folder, paths)

    def test_installed_package_is_preferred(self):
        module = mock.Mock()
        with mock.patch.object(importlib, "import_module", return_value=module):
            self.assertEqual(audit.load_shared_progress_library([]), (module.progress_bar, module.rainbow_hex, module.spaced_unit))

    def test_leaf_fallback_bypasses_broken_initializer_and_bad_candidate(self):
        root = Path(tempfile.mkdtemp(prefix="audit-progress-import-"))
        bad = root / "bad"
        good = root / "clairecjs_util"
        bad.mkdir()
        good.mkdir()
        (bad / "claire_progressbar.py").write_text("raise RuntimeError('broken copy')", encoding="utf-8")
        (good / "__init__.py").write_text("raise RuntimeError('optional dependency missing')", encoding="utf-8")
        (good / "claire_progressbar.py").write_text("def progress_bar(**kw): return 'shared'\ndef rainbow_hex(p): return '#123456'\ndef spaced_unit(u): return ' ' + u\n", encoding="utf-8")
        old_path = list(sys.path)
        with mock.patch.object(importlib, "import_module", side_effect=ImportError("initializer failed")):
            progress, rainbow, unit = audit.load_shared_progress_library([bad, good])
        self.assertEqual(progress(), "shared")
        self.assertEqual(rainbow(0), "#123456")
        self.assertEqual(unit("files"), " files")
        self.assertEqual(sys.path, old_path)

    def test_real_bat_shared_library_loads_without_package_initializer(self):
        folder = Path("C:/BAT/clairecjs_utils")
        if not (folder / "claire_progressbar.py").is_file():
            self.skipTest("Shared BAT library not installed")
        with mock.patch.object(importlib, "import_module", side_effect=ImportError("forced package failure")):
            functions = audit.load_shared_progress_library([folder])
        self.assertTrue(all(callable(function) for function in functions))
        with functions[0](total=1, description="Import test", enabled=False):
            pass

    def test_diagnostics_retain_real_import_reason(self):
        with mock.patch.object(importlib, "import_module", side_effect=ImportError("missing optional dependency")):
            with self.assertRaisesRegex(ImportError, "missing optional dependency"):
                audit.load_shared_progress_library([])
