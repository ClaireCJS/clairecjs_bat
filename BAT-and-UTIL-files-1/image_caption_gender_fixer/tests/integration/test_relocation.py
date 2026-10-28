"""Exercise launcher-relative resources from an unrelated working directory."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "image_caption_gender_fixer.py"


def isolated_environment():
    env = os.environ.copy()
    env["PATH"] = str(Path(env.get("SystemRoot", r"C:\Windows")) / "System32")
    env["PYTHONPATH"] = str(Path(env.get("TEMP", r"C:\Temp")) / "icgf-nonexistent-global-packages")
    return env


def launch(cwd, *arguments):
    return subprocess.run(
        [sys.executable, "-B", "-I", "-S", str(LAUNCHER), *arguments],
        cwd=cwd, env=isolated_environment(), capture_output=True, text=True,
        encoding="utf-8", timeout=60, check=True,
    )


def test_resources_resolve_from_tool_root_with_minimal_path(tmp_path):
    result = json.loads(launch(tmp_path, "environment", "status", "--json").stdout)
    assert result["english_fast"]
    for tool in ("tesseract", "magick"):
        assert Path(result["native"][tool]["path"]).is_relative_to(ROOT / "environment")
    for package in result["packages"].values():
        assert "error" not in package, package
        assert Path(package["path"]).is_relative_to(ROOT / "environment")
    assert list(tmp_path.iterdir()) == []


def test_root_stays_minimal_after_read_only_commands(tmp_path):
    before = {p.name for p in ROOT.iterdir() if p.is_file()}
    assert before == {"image_caption_gender_fixer.py", "README.md"}
    assert "help" in json.loads(launch(tmp_path, "--help", "--json").stdout)
    doctor = json.loads(launch(tmp_path, "doctor", "--json").stdout)
    assert Path(doctor["root"]) == ROOT
    assert not doctor["unexpected_items"] and not doctor["missing_root_files"]
    assert {p.name for p in ROOT.iterdir() if p.is_file()} == before
    assert not (ROOT / "__pycache__").exists()
    assert not (ROOT / ".pytest_cache").exists()
    assert list(tmp_path.iterdir()) == []


def test_private_paf_renderer_is_available_without_global_tools(tmp_path):
    result=json.loads(launch(tmp_path,"doctor","--json").stdout)
    assert result['preview']['available']
    assert result['preview']['renderer']=='pafplayer-dual-preview'
    assert Path(result['preview']['module']).is_relative_to(ROOT/'src')


def test_offline_package_archive_matches_manifest():
    import hashlib
    import zipfile
    manifest = json.loads((ROOT / "environment/manifest.json").read_text(encoding="utf-8"))
    archive = ROOT / "environment/wheels/runtime-bundle.zip"
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == manifest["files"]["wheels/runtime-bundle.zip"]["sha256"]
    with zipfile.ZipFile(archive) as zipped:
        for member in zipped.infolist():
            if not member.is_dir():
                assert hashlib.sha256(zipped.read(member)).hexdigest() == manifest["files"]["packages/" + member.filename]["sha256"]
