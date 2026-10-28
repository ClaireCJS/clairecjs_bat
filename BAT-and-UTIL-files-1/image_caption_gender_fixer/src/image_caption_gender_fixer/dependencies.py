"""Offline selection and explicitly consented dependency installation."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
import zipfile

from .errors import DependencyUnavailable, SelectionRequired, IntegrityError

TESS_VERSION = "5.5.3.20260724"
TESS_INSTALLER_HASH = "bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4"
ENGLISH_COMMIT = "923915d4ced2a7235221788285785a29c4a42d4a"
ENGLISH_HASH = "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2"


def native(root, name):
    root = Path(root)
    candidates = [root / "environment" / "tools" / name / (name + ".exe")]
    candidates += list((root / "environment" / "tools").glob(name + "*/" + name + ".exe"))
    found = shutil.which(name)
    if found:
        candidates.append(Path(found))
    common = {"tesseract": [r"C:\Program Files\Tesseract-OCR\tesseract.exe"],
              "magick": [r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"]}
    candidates += [Path(p) for p in common.get(name, [])]
    for candidate in candidates:
        if candidate.is_file():
            try:
                result = subprocess.run([str(candidate), "-version" if name == "magick" else "--version"],
                                        capture_output=True, timeout=20, text=True, encoding="utf-8", errors="replace")
                output = (result.stdout + result.stderr).strip()
                if result.returncode == 0 and name.casefold() in output.casefold():
                    return {"path": str(candidate), "version": output.splitlines()[0]}
            except (OSError, subprocess.TimeoutExpired):
                pass
    return None


def status(root, imports=False, notify=None):
    native_tools={}
    for name in ('tesseract','magick'):
        if notify:notify('Checking '+name+' executable…')
        native_tools[name]=native(root,name)
    result = {"native": native_tools,
              "english_fast": (Path(root) / "environment/tessdata/eng.traineddata").is_file()}
    if imports:
        result["packages"] = {}
        for name in ("PIL", "numpy", "cv2", "regex", "pytest", "tqdm", "clairecjs_utils.claire_progressbar"):
            try:
                if notify:notify("Loading private package "+name+"…")
                module = importlib.import_module(name)
                result["packages"][name] = {"version": getattr(module, "__version__", None), "path": module.__file__}
            except Exception as error:
                result["packages"][name] = {"error": str(error)}
    return result


def fetch(url, path, expected):
    path = Path(path)
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() == expected:
            return path
        raise IntegrityError("Existing dependency download differs; preserve it and inspect.")
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "ICGF-approved-dependency-installer/0.1"})
    with urllib.request.urlopen(request, timeout=120) as response, path.open("xb") as output:
        shutil.copyfileobj(response, output)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise IntegrityError("Dependency SHA-256 verification failed; do not execute it.")
    return path


def install_ocr(root, ask):
    root = Path(root)
    seven = shutil.which("7z")
    for candidate in (Path(r"C:\Program Files\7-Zip\7z.exe"),):
        if candidate.exists():
            seven = str(candidate)
    bundled_seven=root/"environment/tools/7zip/7z.exe"
    if bundled_seven.is_file(): seven=str(bundled_seven)
    destination=root/"environment/tools"/("tesseract-"+TESS_VERSION)
    method=("Extract the verified portable files privately to "+str(destination)+" (about 102 MB unpacked). "
            if seven else "Use the installed Chocolatey manager for a system Tesseract installation; administrator rights may be required. ")
    plan=(f"Required: Tesseract OCR {TESS_VERSION}, Chocolatey package source "
          f"https://community.chocolatey.org/api/v2/package/tesseract/{TESS_VERSION} (26,535,576 bytes), "
          f"plus official English tessdata_fast from https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{ENGLISH_COMMIT}/eng.traineddata "
          f"(4,113,088 bytes) into {root/'environment/tessdata'}. "+method+
          "Payload hashes will be verified. Image correction cannot proceed without the missing OCR dependencies. "
          "Allow these dependency downloads and installation? [y/N] ")
    if not ask(plan):
        raise DependencyUnavailable("Required OCR installation declined; no image processing performed.")
    if seven:
        archive_path = root / "environment/staging" / ("tesseract-" + TESS_VERSION + ".nupkg")
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if not archive_path.exists():
            request = urllib.request.Request("https://community.chocolatey.org/api/v2/package/tesseract/" + TESS_VERSION,
                                             headers={"User-Agent": "ICGF-approved-dependency-installer/0.1"})
            with urllib.request.urlopen(request, timeout=120) as response, archive_path.open("xb") as output:
                shutil.copyfileobj(response, output)
        installer = archive_path.with_suffix(".exe")
        with zipfile.ZipFile(archive_path) as archive:
            member = "tools/tesseract-ocr-w64-setup-" + TESS_VERSION + ".exe"
            payload = archive.read(member)
        if hashlib.sha256(payload).hexdigest() != TESS_INSTALLER_HASH:
            raise IntegrityError("Pinned OCR payload checksum mismatch; installation refused.")
        if not installer.exists():
            with installer.open("xb") as output:
                output.write(payload)
        elif hashlib.sha256(installer.read_bytes()).hexdigest() != TESS_INSTALLER_HASH:
            raise IntegrityError("Existing OCR installer differs; retained.")
        destination = root / "environment/tools" / ("tesseract-" + TESS_VERSION)
        subprocess.run([seven, "x", str(installer), "-o" + str(destination), "-aos", "-y", "-xr!$PLUGINSDIR"],
                       check=True, capture_output=True, timeout=180)
    else:
        choco = shutil.which("choco")
        if not choco:
            raise DependencyUnavailable("Neither archive extraction nor a trusted package manager is available; no unverified installer executed.")
        subprocess.run([choco, "install", "tesseract", "--version=" + TESS_VERSION, "--yes", "--no-progress"],
                       check=True, timeout=600)
    fetch("https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/" + ENGLISH_COMMIT + "/eng.traineddata",
          root / "environment/tessdata/eng.traineddata", ENGLISH_HASH)
    found = native(root, "tesseract")
    if not found:
        raise DependencyUnavailable("OCR setup finished without a verified executable; installation not successful.")
    probe = subprocess.run([found["path"], "--tessdata-dir", str(root / "environment/tessdata"), "--list-langs"],
                           capture_output=True, text=True, timeout=20)
    if probe.returncode or "eng" not in probe.stdout.split():
        raise DependencyUnavailable("Installed English OCR data did not verify.")
    from .maintenance import cleanup_downloads, report_cleanup
    report_cleanup(cleanup_downloads(root, groups=("ocr",)))
    return found


def require_ocr(root, interactive, dry_run, ask):
    found = native(root, "tesseract")
    if found and (Path(root) / "environment/tessdata/eng.traineddata").is_file():
        return found
    if dry_run:
        raise DependencyUnavailable("Dry run needs Tesseract and English fast OCR data; installation is disabled.")
    if not interactive:
        raise SelectionRequired("Required OCR dependencies are missing; run environment repair interactively to approve installation.")
    return install_ocr(root, ask)
