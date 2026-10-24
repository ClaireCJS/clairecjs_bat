"""Recycle recognized setup downloads only after their replacements verify."""
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys

from .errors import ICGFError, IntegrityError
from .fs import reparse, recycle, sha256, source_lease, validate_path


@dataclass(frozen=True)
class Download:
    relative: str
    sha256: str
    group: str


def downloads():
    from .dependencies import TESS_VERSION, TESS_INSTALLER_HASH
    package_hash = "d59129139ae1b2b8abd0474b4526670e3907e81718dc0ae3a2b9fd4ae0805967"
    entries = [
        Download("environment/wheels/numpy-1.26.4-cp310-cp310-win_amd64.whl",
                 "b97fe8060236edf3662adfc2c633f56a08ae30560c56310562cb4f95500022d5", "python"),
        Download("environment/wheels/opencv_python_headless-4.10.0.84-cp37-abi3-win_amd64.whl",
                 "afcf28bd1209dd58810d33defb622b325d3cbe49dcd7a43a902982c33e5fad05", "python"),
    ]
    for filename in (f"tesseract.{TESS_VERSION}.nupkg", f"tesseract-{TESS_VERSION}.nupkg"):
        entries.append(Download("environment/staging/" + filename, package_hash, "ocr"))
    for filename in (f"tesseract-ocr-w64-setup-{TESS_VERSION}.exe", f"tesseract-{TESS_VERSION}.exe"):
        entries.append(Download("environment/staging/" + filename, TESS_INSTALLER_HASH, "ocr"))
    return entries


def package_directory(root):
    packages = root / "environment/packages"
    active = root / "environment/metadata/active.json"
    if active.exists():
        selection = json.loads(active.read_text(encoding="utf-8"))
        name = selection["packages"]
        if (selection.get("application") != "icgf" or selection.get("schema") != 1
                or not isinstance(name, str) or not name.startswith("packages-")
                or Path(name).name != name or ":" in name):
            raise IntegrityError("Invalid private package selection; setup downloads retained.")
        packages = root / "environment" / name
        ready = json.loads((packages / ".icgf-ready.json").read_text(encoding="utf-8"))
        if ready.get("application") != "icgf" or ready.get("schema") != 1:
            raise IntegrityError("Private packages are not ready; setup downloads retained.")
    return validate_path(packages)


def verify_installation(root, group):
    """Read-only probes; never download, install, or trust global replacements."""
    if group == "python":
        manifest = json.loads((root / "environment/manifest.json").read_text(encoding="utf-8"))
        if manifest.get("application") != "icgf" or manifest.get("schema") != 1:
            raise IntegrityError("Package manifest is invalid.")
        archive = validate_path(root / "environment/wheels/runtime-bundle.zip")
        expected = manifest["files"]["wheels/runtime-bundle.zip"]["sha256"]
        if sha256(archive) != expected:
            raise IntegrityError("Offline package-repair archive did not verify.")
        packages = package_directory(root)
        code = '''import sys,os
sys.dont_write_bytecode=True
from pathlib import Path
p=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(p))
handles=[os.add_dll_directory(str(p/n)) for n in ("numpy.libs","PIL","cv2",".dlls") if (p/n).is_dir()]
import numpy,cv2
assert all(Path(m.__file__).resolve().is_relative_to(p) for m in (numpy,cv2))
assert numpy.__version__ == "1.26.4" and cv2.__version__ == "4.10.0"
ok,data=cv2.imencode(".png",numpy.zeros((2,2,3),dtype=numpy.uint8))
assert ok and len(data)>0
'''
        result = subprocess.run([sys.executable, "-B", "-I", "-S", "-c", code, str(packages)],
                                capture_output=True, text=True, timeout=45)
        if result.returncode:
            raise IntegrityError("Private NumPy/OpenCV verification failed; setup downloads retained.")
    elif group == "ocr":
        from .dependencies import native, ENGLISH_HASH
        found = native(root, "tesseract")
        if not found or not Path(found["path"]).resolve().is_relative_to((root / "environment/tools").resolve()):
            raise IntegrityError("A working private Tesseract installation was not found.")
        data = validate_path(root / "environment/tessdata/eng.traineddata")
        if sha256(data) != ENGLISH_HASH:
            raise IntegrityError("Bundled English OCR data did not verify.")
        result = subprocess.run([found["path"], "--tessdata-dir", str(data.parent), "--list-langs"],
                                capture_output=True, text=True, timeout=20)
        if result.returncode or "eng" not in result.stdout.split():
            raise IntegrityError("Private Tesseract/English verification failed.")
    else:
        raise ValueError("Unknown setup-download group.")


def cleanup_downloads(root, groups=("python", "ocr"), dry_run=False):
    """No broad directory cleanup; preserve changed, busy, or unverified files."""
    root = Path(os.path.abspath(root))
    result = {"recycled": [], "retained": [], "would_recycle": [],
              "recycled_bytes": 0, "eligible_bytes": 0}
    readiness = {}
    for entry in downloads():
        if entry.group not in groups:
            continue
        path = root / entry.relative
        if not os.path.lexists(path):
            continue
        item = {"path": str(path)}
        try:
            # Fixed filename allowlist, checked parent paths, one ordinary file.
            # The downloader's write handle blocks this lease until it finishes.
            validate_path(path)
            if not path.is_file() or reparse(path) or path.stat().st_nlink != 1:
                raise IntegrityError("Setup download is not a single ordinary file.")
            with source_lease(path):
                item["bytes"] = path.stat().st_size
                if sha256(path) != entry.sha256:
                    raise IntegrityError("Download differs from the recognized setup archive.")
                if entry.group not in readiness:
                    try:
                        verify_installation(root, entry.group)
                        readiness[entry.group] = None
                    except (ICGFError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
                        readiness[entry.group] = str(error)
                if readiness[entry.group]:
                    raise IntegrityError(readiness[entry.group])
                result["eligible_bytes"] += item["bytes"]
                if dry_run:
                    result["would_recycle"].append(item)
                else:
                    recycle(path)
                    if os.path.lexists(path):
                        raise IntegrityError("Recycle Bin did not remove the download; no deletion fallback.")
                    result["recycled"].append(item)
                    result["recycled_bytes"] += item["bytes"]
        except (ICGFError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
            result["retained"].append(dict(item, reason=str(error)))
    return result


def report_cleanup(result, emit=None):
    emit = emit or (lambda text: print(text, file=sys.stderr))
    if result["recycled"]:
        emit(f"Setup cleanup: recycled {len(result['recycled'])} downloads "
             f"({result['recycled_bytes']:,} bytes); installed packages and offline repair archive kept.")
    for item in result["retained"]:
        emit("Setup download retained: " + item["path"] + ": " + item["reason"])
