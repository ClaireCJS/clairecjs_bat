"""Create the shipped package-repair archive without pip or network access."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent
target = ROOT / "wheels/runtime-bundle.zip"
packages = ROOT / "packages"
with zipfile.ZipFile(target, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for member in sorted(packages.rglob("*")):
        if member.is_file() and "__pycache__" not in member.parts and not member.name.endswith(".pyc"):
            archive.write(member, member.relative_to(packages).as_posix())
with zipfile.ZipFile(target) as archive:
    bad = archive.testzip()
    if bad:
        raise RuntimeError("Repair archive failed CRC verification: " + bad)
    print("Offline repair archive:", len(archive.infolist()), "files;", target.stat().st_size, "bytes")
