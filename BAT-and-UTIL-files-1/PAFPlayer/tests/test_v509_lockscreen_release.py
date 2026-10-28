"""Regression checks for the V509 Windows 10 Release package."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "lockscreen" / "dist" / "PAFPlayerLockScreen_v509_x64.msix"
FOUNDATION = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP = "http://schemas.microsoft.com/appx/manifest/uap/windows10"


class LockScreenReleaseTests(unittest.TestCase):
    def test_release_package_has_native_entry_point_and_lockscreen_contract(self):
        with zipfile.ZipFile(PACKAGE) as archive:
            names = set(archive.namelist())
            self.assertIn("PAFPlayerLockScreen.exe", names)
            self.assertIn("PAFPlayerLockScreen.dll", names)
            self.assertNotIn("entrypoint/PAFPlayerLockScreen.exe", names)
            manifest = ET.fromstring(archive.read("AppxManifest.xml"))
            identity = manifest.find(f"{{{FOUNDATION}}}Identity")
            self.assertEqual(identity.get("Version"), "509.0.0.0")
            app = manifest.find(f"{{{FOUNDATION}}}Applications/{{{FOUNDATION}}}Application")
            self.assertEqual(app.get("Executable"), "PAFPlayerLockScreen.exe")
            self.assertEqual(app.get("EntryPoint"), "PAFPlayerLockScreen.App")
            visual = app.find(f"{{{UAP}}}VisualElements")
            self.assertEqual(visual.find(f"{{{UAP}}}LockScreen").get("Notification"),
                             "badgeAndTileText")
            deps = {item.get("Name") for item in manifest.findall(
                f"{{{FOUNDATION}}}Dependencies/{{{FOUNDATION}}}PackageDependency")}
            self.assertEqual(deps, {
                "Microsoft.VCLibs.140.00",
                "Microsoft.NET.Native.Framework.2.2",
                "Microsoft.NET.Native.Runtime.2.2",
            })


if __name__ == "__main__":
    unittest.main()
