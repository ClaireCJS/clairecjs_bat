"""Focused lock-screen and related tray regressions with isolated, retained fixtures."""
from pathlib import Path
import datetime
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
MODULES = ("test_v505_lockscreen_package", "test_v508_lockscreen_installer",
           "test_v509_lockscreen_release", "test_PAFPlayer_v499_tray",
           "test_v503_tray_track_details", "test_v504_tray_machine")

def child(stage):
    sys.path.insert(0, str(ROOT))
    os.chdir(stage)
    for key in ("TEMP", "TMP", "LOCALAPPDATA", "APPDATA"):
        os.environ[key] = str(stage)
    os.environ["PLAY_AUDIO_FILE_HISTORY_DB"] = str(stage / "history.sqlite3")
    for key in tuple(os.environ):
        if key.startswith("LASTFM_") or key == "PAFPLAYER_DISCORD_WEBHOOK":
            os.environ.pop(key)
    tempfile.tempdir = str(stage)
    sys.path.insert(0, str(ROOT / 'tests'))
    from run_PAFPlayer_tests import install_guards
    install_guards(stage)
    suite = unittest.TestSuite()
    for name in MODULES:
        spec = importlib.util.spec_from_file_location(name, ROOT / "tests" / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    spec = importlib.util.spec_from_file_location('test_managed_publisher', ROOT / 'lockscreen/testing/test_managed_publisher.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"tests": result.testsRun, "failures": len(result.failures),
                      "errors": len(result.errors), "skipped": len(result.skipped)}))
    return 0 if result.wasSuccessful() else 1

def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    stage = ROOT / "lockscreen" / "archive" / "staging" / ("regression-staging-" + stamp)
    stage.mkdir(parents=True)
    report = ROOT / "tests" / "reports" / ("v530-regressions-" + stamp + ".txt")
    with report.open("xb") as log:
        result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--child", str(stage)],
                                stdout=log, stderr=subprocess.STDOUT, timeout=180)
    print(report.read_text(encoding="utf-8"))
    print("Report:", report)
    return result.returncode

if __name__ == "__main__":
    raise SystemExit(child(Path(sys.argv[2])) if len(sys.argv) > 1 and sys.argv[1] == "--child" else main())
