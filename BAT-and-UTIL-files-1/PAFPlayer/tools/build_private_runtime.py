"""Build PAFPlayer's app-local Windows CPython runtime with Tcl/Tk support."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.12.10"
INSTALLER = f"python-{VERSION}-amd64.exe"
URL = f"https://www.python.org/ftp/python/{VERSION}/{INSTALLER}"
MAX_INSTALLER_BYTES = 40 * 1024 * 1024


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def build(destination: Path, *, python_installer: Path | None = None) -> None:
    if sys.platform != "win32":
        raise RuntimeError("Build this private runtime on 64-bit Windows.")
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"Refusing to replace existing runtime: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stamp = __import__("datetime").datetime.now().strftime("%Y%m%d%H%M%S")
    stage = destination.with_name(f".{destination.name}.stage-{stamp}")
    if stage.exists():
        raise FileExistsError(f"Preserving existing runtime staging folder: {stage}")
    stage.mkdir()
    runtime_stage = stage
    installer_cache = runtime_stage / "downloads" / "python-installer"
    installer_cache.mkdir(parents=True, exist_ok=True)
    installer = installer_cache / INSTALLER
    if not installer.exists():
        if python_installer is not None:
            shutil.copy2(python_installer, installer)
        else:
            with urlopen(URL, timeout=45) as response, installer.open("xb") as output:
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > MAX_INSTALLER_BYTES:
                        raise ValueError("Python installer exceeded the size limit")
                    output.write(chunk)
    elif python_installer is not None and digest(installer) != digest(python_installer):
        raise FileExistsError(f"A different installer is already preserved at {installer}")
    runtime_stage = stage
    result = subprocess.run([
        str(installer), "/quiet", "InstallAllUsers=0", f"TargetDir={runtime_stage}",
        "Include_launcher=0", "Include_tcltk=1", "Include_pip=1",
        "Include_test=0", "Include_doc=0", "Include_dev=1", "PrependPath=0",
        "Shortcuts=0", "AssociateFiles=0",
    ], check=False, timeout=300)
    if result.returncode:
        raise RuntimeError(f"Python installer returned code {result.returncode}; staging kept at {stage}")
    python = runtime_stage / "python.exe"
    site = runtime_stage / "Lib" / "site-packages"
    if not python.is_file() or not (runtime_stage / "DLLs" / "_tkinter.pyd").is_file():
        raise RuntimeError(f"Private Python installation is missing python.exe or Tk support; staging kept at {stage}")
    subprocess.run([
        str(python), "-m", "pip", "install", "--disable-pip-version-check",
        "--no-cache-dir", "--only-binary=:all:", "--target", str(site),
        "-r", str(ROOT / "requirements-core.txt"),
    ], check=True)
    result = subprocess.run([str(python), "-c",
                             "import tkinter, numpy, PIL, send2trash, requests, mutagen; "
                             "tkinter.Tk().destroy(); print('private runtime imports OK')"],
                            check=True, capture_output=True, text=True)
    if "private runtime imports OK" not in result.stdout:
        raise RuntimeError(f"Private runtime import verification failed; staging kept at {stage}")
    (runtime_stage / "runtime-manifest.json").write_text(json.dumps({
        "python": VERSION,
        "architecture": "win_amd64",
        "requirements": (ROOT / "requirements-core.txt").read_text(encoding="utf-8"),
        "python_installer": INSTALLER,
        "python_installer_sha256": digest(installer),
    }, indent=2) + "\n", encoding="utf-8")
    stage.rename(destination)
    print(f"Built private Python runtime: {destination}")
    print(result.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "runtime")
    parser.add_argument("--python-installer", type=Path,
                        help="use an already-downloaded official Python installer")
    args = parser.parse_args()
    try:
        build(args.output, python_installer=args.python_installer)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Private runtime build failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
