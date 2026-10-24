"""Developer-only, explicit bundle preparation. No imports of the application."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / "environment"


def digest(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(f.read()).hexdigest()


def copy_new(source, dest):
    source, dest = Path(source), Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if digest(source) != digest(dest):
            raise RuntimeError("Existing bundle member differs; preserve it: " + str(dest))
        return
    with source.open("rb") as src, dest.open("xb") as out:
        shutil.copyfileobj(src, out)
    if digest(source) != digest(dest):
        raise RuntimeError("Copy verification failed")


def tree(source, target):
    source = Path(source)
    for item in source.rglob("*"):
        if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc":
            copy_new(item, Path(target) / item.relative_to(source))


def download(url, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path
    request = urllib.request.Request(url, headers={"User-Agent": "ICGF-approved-dependency-bundler/0.1"})
    with urllib.request.urlopen(request, timeout=90) as response, path.open("xb") as out:
        shutil.copyfileobj(response, out)
    return path


def existing():
    source = Path(r"C:\ProgramData\anaconda3\Lib\site-packages")
    names = ["PIL", "pytest", "_pytest", "tqdm", "regex", "pluggy", "packaging", "iniconfig", "tomli", "exceptiongroup", "colorama"]
    for name in names:
        tree(source / name, ENV / "packages" / name)
    for pattern in ["pillow-*.dist-info", "Pillow-*.dist-info", "pytest-*.dist-info", "tqdm-*.dist-info", "regex-*.dist-info", "pluggy-*.dist-info", "packaging-*.dist-info", "iniconfig-*.dist-info", "tomli-*.dist-info", "exceptiongroup-*.dist-info", "colorama-*.dist-info"]:
        for metadata in source.glob(pattern):
            tree(metadata, ENV / "packages" / metadata.name)
    copy_new(Path(r"C:\clairecjs_utils\claire_progressbar.py"), ENV / "packages" / "clairecjs_utils" / "claire_progressbar.py")
    print("Existing Python dependencies copied and SHA-256 verified.")


def python_wheels():
    # Run only after explicit consent. Download wheels, validate against PyPI's
    # published SHA-256, then extract locally without touching global Python.
    specifications = [("numpy", "1.26.4"), ("opencv-python-headless", "4.10.0.84")]
    for name, version in specifications:
        with urllib.request.urlopen(f"https://pypi.org/pypi/{name}/{version}/json", timeout=60) as response:
            metadata = json.load(response)
        wheels = [x for x in metadata["urls"] if x["filename"].endswith("win_amd64.whl") and ("cp310-cp310" in x["filename"] if name == "numpy" else "cp37-abi3" in x["filename"])]
        if len(wheels) != 1:
            raise RuntimeError("Expected one compatible Windows wheel")
        entry = wheels[0]
        wheel = download(entry["url"], ENV / "wheels" / entry["filename"])
        if digest(wheel) != entry["digests"]["sha256"]:
            raise RuntimeError("Published wheel SHA-256 mismatch")
        with zipfile.ZipFile(wheel) as archive:
            for member in archive.infolist():
                relative = Path(member.filename)
                if relative.is_absolute() or ".." in relative.parts:
                    raise RuntimeError("Unsafe wheel member")
                if member.is_dir():
                    continue
                dest = ENV / "packages" / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                payload = archive.read(member)
                if dest.exists():
                    if dest.read_bytes() != payload:
                        raise RuntimeError("Conflicting wheel member: " + str(relative))
                else:
                    with dest.open("xb") as out:
                        out.write(payload)
        print(entry["filename"], entry["digests"]["sha256"])


def tess_package():
    archive = download("https://community.chocolatey.org/api/v2/package/tesseract/5.5.3.20260724", ENV / "staging" / "tesseract.5.5.3.20260724.nupkg")
    with zipfile.ZipFile(archive) as package:
        print(package.read("tools/chocolateyinstall.ps1").decode("utf-8-sig"))


def manifest():
    files = {}
    for item in ENV.rglob("*"):
        if item.is_file() and item.name not in ("manifest.json", "requirements.lock") and "staging" not in item.parts and "__pycache__" not in item.parts:
            files[str(item.relative_to(ENV)).replace("\\", "/")] = {"size": item.stat().st_size, "sha256": digest(item)}
    target = ENV / "manifest.json"
    with target.open("x", encoding="utf-8") as f:
        optional = [name for name in files if name.startswith("wheels/") and name.endswith(".whl")]
        json.dump({"application": "icgf", "schema": 1, "python": "3.10", "architecture": "AMD64", "optional_files": optional, "files": files}, f, indent=2)
    print(len(files), "bundle members verified")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["existing", "python-wheels", "tesseract-package", "manifest"])
    action = parser.parse_args().action
    {"existing": existing, "python-wheels": python_wheels, "tesseract-package": tess_package, "manifest": manifest}[action]()
