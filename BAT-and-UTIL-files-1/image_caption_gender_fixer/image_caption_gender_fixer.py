#!/usr/bin/env python3
"""Standard-library-only launcher; dependencies travel with this directory."""
import sys

sys.dont_write_bytecode = True

import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Restart before importing application/dependency code. Ignore user site packages,
# .pth hooks, PYTHONPATH and global packages when running the actual application.
if not sys.flags.no_site or not sys.flags.isolated:
    os.execv(sys.executable, [sys.executable, "-I", "-S", str(ROOT / Path(__file__).name), *sys.argv[1:]])

os.environ.setdefault("OMP_THREAD_LIMIT", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
_packages = "packages"
_active = ROOT / "environment" / "metadata" / "active.json"
if _active.exists():
    try:
        _selection = json.loads(_active.read_text(encoding="utf-8"))
        _packages = _selection["packages"]
        if _selection.get("application") != "icgf" or _selection.get("schema") != 1 or not _packages.startswith("packages-") or Path(_packages).name != _packages or ":" in _packages:
            raise ValueError("Invalid private package selection")
        _ready = json.loads((ROOT / "environment" / _packages / ".icgf-ready.json").read_text(encoding="utf-8"))
        if _ready.get("application") != "icgf" or _ready.get("schema") != 1:
            raise ValueError("Private package environment was not verified")
    except (OSError, ValueError, KeyError, TypeError):
        if not any(a in sys.argv for a in ("--help", "--version")):
            print(json.dumps({"state":"failed","error":"Invalid/unready package selection; inspect environment metadata."}))
            raise SystemExit(40)
        _packages = "packages"
sys.path.insert(0, str(ROOT / "environment" / _packages))
sys.path.insert(0, str(ROOT / "src"))
_dll_handles = []
if os.name == "nt":
    for _relative in ("environment/" + _packages + "/" + suffix for suffix in (".dlls", "numpy.libs", "PIL", "cv2")):
        _directory = ROOT / _relative
        if _directory.is_dir():
            _dll_handles.append(os.add_dll_directory(str(_directory)))

from image_caption_gender_fixer.cli import main

if __name__ == "__main__":
    raise SystemExit(main(ROOT))
