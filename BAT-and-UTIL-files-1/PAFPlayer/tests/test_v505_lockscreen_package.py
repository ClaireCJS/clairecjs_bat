"""Regression checks against the distributable Windows 10 lock-screen package."""
import struct
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "releases" / "PAFPlayer_v505_lockscreen_x64.msix"
FOUNDATION = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP = "http://schemas.microsoft.com/appx/manifest/uap/windows10"


class LockScreenPackageTests(unittest.TestCase):
    def test_signed_package_declares_detailed_status_and_background_task(self):
        with zipfile.ZipFile(PACKAGE) as archive:
            manifest = ET.fromstring(archive.read("AppxManifest.xml"))
            identity = manifest.find(f"{{{FOUNDATION}}}Identity")
            self.assertEqual(identity.get("Name"), "ClaireCJS.PAFPlayer.LockScreen")
            self.assertEqual(identity.get("Version"), "505.0.0.0")
            application = manifest.find(f"{{{FOUNDATION}}}Applications/{{{FOUNDATION}}}Application")
            visual = application.find(f"{{{UAP}}}VisualElements")
            self.assertTrue(visual.find(f"{{{UAP}}}DefaultTile").get("Wide310x150Logo"))
            lock = visual.find(f"{{{UAP}}}LockScreen")
            self.assertEqual(lock.get("Notification"), "badgeAndTileText")
            badge = archive.read(lock.get("BadgeLogo").replace("\\", "/"))
            self.assertEqual(struct.unpack(">II", badge[16:24]), (24, 24))
            task = application.find(f"{{{FOUNDATION}}}Extensions/{{{FOUNDATION}}}Extension")
            self.assertEqual(task.get("Category"), "windows.backgroundTasks")
            self.assertEqual(task.find(f"{{{FOUNDATION}}}BackgroundTasks/{{{FOUNDATION}}}Task").get("Type"), "timer")
            ids = [item.get("ActivatableClassId") for item in manifest.iter()
                   if item.tag.endswith("ActivatableClass")]
            self.assertIn(task.get("EntryPoint"), ids)

    def test_package_contains_background_component_and_no_private_key(self):
        with zipfile.ZipFile(PACKAGE) as archive:
            names = archive.namelist()
            self.assertIn("PAFPlayerLockScreen.BackgroundTasks.winmd", names)
            self.assertIn("PAFPlayerLockScreen.exe", names)
            self.assertFalse(any(name.casefold().endswith((".pfx", ".p12", ".key")) for name in names))


if __name__ == "__main__":
    unittest.main()
