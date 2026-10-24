import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
import zipfile

import pytest
from image_caption_gender_fixer import maintenance as maint, dependencies as dep
from image_caption_gender_fixer.cli import main, repair_packages
from image_caption_gender_fixer.errors import IntegrityError, UnsafeFilesystem, DependencyUnavailable


def empty_result():
    return {"recycled": [], "retained": [], "would_recycle": [],
            "recycled_bytes": 0, "eligible_bytes": 0}


def download(tmp_path, monkeypatch, relative="environment/wheels/numpy.whl"):
    root = tmp_path / "tool"
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = b"generated setup download for cleanup tests"
    path.write_bytes(payload)
    entry = maint.Download(relative, hashlib.sha256(payload).hexdigest(), "python")
    monkeypatch.setattr(maint, "downloads", lambda: [entry])
    monkeypatch.setattr(maint, "verify_installation", lambda *a: None)
    return root, path, payload


def recycle_into_test_bin(tmp_path, monkeypatch):
    target = tmp_path / "test-bin"
    target.mkdir()
    def recycle(path):
        path.rename(target / path.name)
    monkeypatch.setattr(maint, "recycle", recycle)
    return target


def test_exact_download_is_recycled_once_and_unknown_files_are_preserved(tmp_path, monkeypatch):
    root, path, payload = download(tmp_path, monkeypatch)
    unknown = path.with_name("personal.whl")
    unknown.write_bytes(b"unrelated file")
    recovery = path.with_name("runtime-bundle.zip")
    recovery.write_bytes(b"keep offline repair")
    original = root / "image.jpg"
    original.write_bytes(b"keep original image")
    target = recycle_into_test_bin(tmp_path, monkeypatch)
    result = maint.cleanup_downloads(root)
    assert result["recycled_bytes"] == len(payload) and len(result["recycled"]) == 1
    assert (target / path.name).read_bytes() == payload
    assert unknown.exists() and recovery.exists() and original.exists()
    assert maint.cleanup_downloads(root) == empty_result()


def test_changed_download_is_retained_without_installation_probe(tmp_path, monkeypatch):
    root, path, payload = download(tmp_path, monkeypatch)
    path.write_bytes(payload + b" changed")
    monkeypatch.setattr(maint, "verify_installation", lambda *a: pytest.fail("Changed file must not be eligible"))
    result = maint.cleanup_downloads(root)
    assert not result["recycled"] and "differs" in result["retained"][0]["reason"]
    assert path.exists()


def test_incomplete_installation_keeps_its_setup_download(tmp_path, monkeypatch):
    root, path, _ = download(tmp_path, monkeypatch)
    def failed(*a):
        raise IntegrityError("Installation incomplete")
    monkeypatch.setattr(maint, "verify_installation", failed)
    result = maint.cleanup_downloads(root)
    assert not result["recycled"] and "incomplete" in result["retained"][0]["reason"]
    assert path.exists()


def test_dry_run_reports_bytes_without_recycling(tmp_path, monkeypatch):
    root, path, payload = download(tmp_path, monkeypatch)
    monkeypatch.setattr(maint, "recycle", lambda *a: pytest.fail("Dry run recycled a file"))
    result = maint.cleanup_downloads(root, dry_run=True)
    assert result["eligible_bytes"] == len(payload) and result["recycled_bytes"] == 0
    assert len(result["would_recycle"]) == 1 and path.read_bytes() == payload


def test_recycle_failure_retains_file_without_delete_fallback(tmp_path, monkeypatch):
    root, path, payload = download(tmp_path, monkeypatch)
    def failed(*a):
        raise UnsafeFilesystem("Recycle Bin unavailable")
    monkeypatch.setattr(maint, "recycle", failed)
    result = maint.cleanup_downloads(root)
    assert not result["recycled"] and "Recycle Bin unavailable" in result["retained"][0]["reason"]
    assert path.read_bytes() == payload


def test_noop_recycle_is_detected_and_not_counted_as_space_saved(tmp_path, monkeypatch):
    root, path, _ = download(tmp_path, monkeypatch)
    monkeypatch.setattr(maint, "recycle", lambda *a: True)
    result = maint.cleanup_downloads(root)
    assert result["recycled_bytes"] == 0 and result["retained"] and path.exists()


def test_hard_link_download_is_retained(tmp_path, monkeypatch):
    root, path, payload = download(tmp_path, monkeypatch)
    other = tmp_path / "outside.whl"
    os.link(path, other)
    result = maint.cleanup_downloads(root)
    assert not result["recycled"] and result["retained"]
    assert path.read_bytes() == other.read_bytes() == payload


def test_busy_download_writer_prevents_cleanup(tmp_path, monkeypatch):
    root, path, _ = download(tmp_path, monkeypatch)
    with path.open("r+b"):
        result = maint.cleanup_downloads(root)
    assert result["retained"] and not result["recycled"] and path.exists()


def test_reparse_parent_is_refused(tmp_path, monkeypatch):
    root, path, _ = download(tmp_path, monkeypatch)
    def refused(*a):
        raise UnsafeFilesystem("Reparse-point path refused")
    monkeypatch.setattr(maint, "validate_path", refused)
    result = maint.cleanup_downloads(root)
    assert result["retained"] and not result["recycled"] and path.exists()


def test_real_windows_recycle_works_while_download_is_leased(tmp_path, monkeypatch):
    root, path, payload = download(tmp_path, monkeypatch)
    result = maint.cleanup_downloads(root)
    assert result["recycled_bytes"] == len(payload), result
    assert not path.exists() and not result["retained"]


def test_python_cleanup_requires_verified_offline_repair_archive(tmp_path):
    environment = tmp_path / "environment"
    (environment / "wheels").mkdir(parents=True)
    archive = environment / "wheels/runtime-bundle.zip"
    archive.write_bytes(b"damaged archive")
    (environment / "manifest.json").write_text(json.dumps({"application": "icgf", "schema": 1,
        "files": {"wheels/runtime-bundle.zip": {"sha256": "0" * 64}}}), encoding="utf-8")
    with pytest.raises(IntegrityError, match="repair archive"):
        maint.verify_installation(tmp_path, "python")


def test_ocr_cleanup_rejects_global_install_as_private_replacement(tmp_path, monkeypatch):
    monkeypatch.setattr(dep, "native", lambda *a: {"path": str(tmp_path / "global/tesseract.exe")})
    with pytest.raises(IntegrityError, match="private Tesseract"):
        maint.verify_installation(tmp_path, "ocr")


def test_startup_processing_performs_cleanup_and_preserves_json(tmp_path, monkeypatch, capsys):
    root, path, payload = download(tmp_path, monkeypatch)
    recycle_into_test_bin(tmp_path, monkeypatch)
    images = tmp_path / "empty-images"
    images.mkdir()
    assert main(root, [str(images), "--new-session", "--json"]) == 11
    result = json.loads(capsys.readouterr().out)
    assert result["setup_cleanup"]["recycled_bytes"] == len(payload) and not path.exists()


@pytest.mark.parametrize("args", [
    ["--help", "--json"], ["--version", "--json"], ["preferences", "show", "--json"],
    ["doctor", "--json"], ["environment", "status", "--json"], ["--dry-run", "--json"],
])
def test_read_only_startup_commands_do_not_cleanup(tmp_path, monkeypatch, args):
    monkeypatch.setattr(maint, "cleanup_downloads", lambda *a, **k: pytest.fail("Read-only command cleaned files"))
    monkeypatch.setattr(dep, "status", lambda *a: {})
    installation = tmp_path / "tool"
    installation.mkdir()
    images = tmp_path / "empty-images"
    images.mkdir()
    monkeypatch.chdir(images)
    assert main(installation, args) in (0, 11, 40)
    assert not list(installation.iterdir()) and not list(images.iterdir())


def test_explicit_cleanup_command_and_dry_run(tmp_path, monkeypatch, capsys):
    root, path, payload = download(tmp_path, monkeypatch)
    recycle_into_test_bin(tmp_path, monkeypatch)
    assert main(root, ["environment", "cleanup", "--dry-run", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["setup_cleanup"]["eligible_bytes"] == len(payload)
    assert path.exists()
    assert main(root, ["environment", "cleanup", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["setup_cleanup"]["recycled_bytes"] == len(payload)
    assert not path.exists()


@pytest.mark.parametrize("successful", [True, False])
def test_ocr_installation_only_cleans_after_success(tmp_path, monkeypatch, successful):
    payload = b"generated fake installer; not executable"
    monkeypatch.setattr(dep, "TESS_INSTALLER_HASH", hashlib.sha256(payload).hexdigest())
    archive = tmp_path / "environment/staging" / ("tesseract-" + dep.TESS_VERSION + ".nupkg")
    archive.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive, "x") as zipped:
        zipped.writestr("tools/tesseract-ocr-w64-setup-" + dep.TESS_VERSION + ".exe", payload)
    monkeypatch.setattr(dep.shutil, "which", lambda name: "fake-7z.exe")
    monkeypatch.setattr(dep.subprocess, "run", lambda *a, **k: SimpleNamespace(
        returncode=0, stdout="eng\n" if successful else "fra\n", stderr=""))
    monkeypatch.setattr(dep, "native", lambda *a: {"path": "fake-tesseract.exe"})
    monkeypatch.setattr(dep, "fetch", lambda *a: None)
    calls = []
    monkeypatch.setattr(maint, "cleanup_downloads", lambda *a, **k: calls.append(k["groups"]) or empty_result())
    if successful:
        dep.install_ocr(tmp_path, lambda question: True)
        assert calls == [("ocr",)]
    else:
        with pytest.raises(DependencyUnavailable):
            dep.install_ocr(tmp_path, lambda question: True)
        assert not calls


@pytest.mark.parametrize("successful", [True, False])
def test_private_package_repair_only_cleans_after_verification(tmp_path, monkeypatch, successful):
    payload = b"# generated package fixture\n"
    archive = tmp_path / "environment/wheels/runtime-bundle.zip"
    archive.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive, "x") as zipped:
        zipped.writestr("numpy/__init__.py", payload)
    expected = hashlib.sha256(archive.read_bytes()).hexdigest()
    (tmp_path / "environment/manifest.json").write_text(json.dumps({"files": {
        "wheels/runtime-bundle.zip": {"sha256": expected},
        "packages/numpy/__init__.py": {"sha256": hashlib.sha256(payload).hexdigest()}}}), encoding="utf-8")
    monkeypatch.setattr(dep, "status", lambda *a: {"packages": {"numpy": {"error": "fixture"}}})
    def verify(*a, **k):
        if not successful:
            raise subprocess.CalledProcessError(1, "fixture probe")
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(subprocess, "run", verify)
    calls = []
    monkeypatch.setattr(maint, "cleanup_downloads", lambda *a, **k: calls.append(k["groups"]) or empty_result())
    app = SimpleNamespace(root=tmp_path, confirm=lambda prompt: True, diagnostics=lambda text: None)
    if successful:
        assert repair_packages(app)
        assert calls == [("python",)]
    else:
        with pytest.raises(subprocess.CalledProcessError):
            repair_packages(app)
        assert not calls and not (tmp_path / "environment/metadata/active.json").exists()
    assert archive.exists()
