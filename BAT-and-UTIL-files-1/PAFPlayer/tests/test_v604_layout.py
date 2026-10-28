"""V604 layout and bundled-source regression checks; no live player launch."""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent if HERE.name == "tests" else HERE


def bundled_sources() -> dict[str, str]:
    tree = ast.parse((ROOT / "PAFPlayer.py").read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "_PAF_BUNDLED_SOURCES":
                result.update(ast.literal_eval(node.value))
            elif (isinstance(target, ast.Subscript)
                  and isinstance(target.value, ast.Name)
                  and target.value.id == "_PAF_BUNDLED_SOURCES"):
                result[ast.literal_eval(target.slice)] = ast.literal_eval(node.value)
    return result


class LayoutTests(unittest.TestCase):
    def setUp(self):
        if not (ROOT / "src").is_dir():
            self.skipTest("source-layout check runs against the real project, not a flattened test stage")

    def test_one_root_python_and_one_user_document(self):
        self.assertEqual([path.name for path in ROOT.glob("*.py")], ["PAFPlayer.py"])
        self.assertEqual(sorted(path.name for path in ROOT.glob("*.md")),
                         ["AGENTS.md", "PAFPlayer.md"])
        self.assertIn("docs/README.md", (ROOT / "PAFPlayer.md").read_text(encoding="utf-8"))
        self.assertFalse(list(ROOT.glob("*.bak.*")))

    def test_editable_modules_equal_single_file_bundle(self):
        bundled = bundled_sources()
        sources = sorted((ROOT / "src").glob("PAFPlayer_*.py"))
        self.assertEqual(len(sources), 20)
        for path in sources:
            with self.subTest(module=path.stem):
                self.assertEqual(path.read_text(encoding="utf-8"), bundled[path.stem])

    def test_integration_roots_are_current(self):
        screen = ROOT / "screensaver"
        self.assertTrue((screen / "PAFPlayer.scr").is_file())
        self.assertTrue((screen / "src" / "PAFPlayer_screensaver.cs").is_file())
        self.assertFalse(list(screen.glob("*.py")))
        self.assertFalse(list(screen.glob("*.cs")))
        lock = ROOT / "lockscreen"
        self.assertTrue((lock / "PAFPlayerLockScreen.csproj").is_file())
        self.assertTrue((lock / "dist").is_dir())
        self.assertFalse(list(lock.glob("regression-staging-*")))
        self.assertFalse(list(lock.glob("test-build-*")))
        self.assertFalse(list(lock.glob("build-v*")))
        self.assertFalse(list(lock.glob("publish_v*.py")))


if __name__ == "__main__":
    unittest.main()
