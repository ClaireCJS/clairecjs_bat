import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from image_caption_gender_fixer import cli
from image_caption_gender_fixer.rules import Rule, builtins, transform
from image_caption_gender_fixer.diagnostics import bundle_health
from image_caption_gender_fixer.fs import sha256, state_write

ROOT=Path(os.environ.get("ICGF_TEST_INSTALLATION",Path(__file__).resolve().parents[2]))


def test_normalized_length_tie_prefers_literal_and_reports_intermediate_stages():
    result=transform(" boy ",[Rule(r"\s*boy\s*","regex",mode="regex",id="regex"),Rule("boy","girl",id="literal")])
    assert result["final"]==" girl "
    result=transform("good boi",builtins())
    assert [s["after"] for s in result["stages"]]==["good boy","good girl"]


def test_profile_and_exclusion_administration_is_persistent_and_explicit(tmp_path,monkeypatch,capsys):
    installation=tmp_path/"tool";installation.mkdir()
    images=tmp_path/"images";images.mkdir();monkeypatch.chdir(images)
    assert cli.main(installation,["rules","ignore","boy","--context","king","--profile","project","--json"])==0
    saved=json.loads(capsys.readouterr().out)
    identity=saved["exclusion"]["id"]
    assert cli.main(installation,["rules","explain","boy beside king","--profile","project","--json"])==0
    assert json.loads(capsys.readouterr().out)["final"]=="boy beside king"
    assert cli.main(installation,["rules","disable",identity,"--profile","project","--json"])==0
    capsys.readouterr()
    assert cli.main(installation,["rules","explain","boy beside king","--profile","project","--json"])==0
    assert json.loads(capsys.readouterr().out)["final"]=="girl beside king"
    assert cli.main(installation,["rules","profiles","--json"])==0
    assert "project" in json.loads(capsys.readouterr().out)["profiles"]
    assert cli.main(installation,["preferences","set","global-rules","on","--json"])==0
    assert json.loads(capsys.readouterr().out)["global-rules"] is True


def test_doctor_checks_selected_repaired_tree_and_preserves_old_tree(tmp_path):
    environment=tmp_path/"environment";environment.mkdir()
    original=environment/"packages";original.mkdir()
    (original/"data.bin").write_bytes(b"damaged old package")
    selected=environment/"packages-verified";selected.mkdir()
    (selected/"data.bin").write_bytes(b"verified package")
    state_write(selected/".icgf-ready.json",{"bundle_hash":"fixture"})
    state_write(environment/"metadata/active.json",{"packages":selected.name})
    manifest={"application":"icgf","schema":1,"files":{"packages/data.bin":{"size":len(b"verified package"),"sha256":sha256(selected/"data.bin")}}}
    (environment/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    assert not bundle_health(tmp_path)["errors"]
    assert (original/"data.bin").read_bytes()==b"damaged old package"


def test_supported_abi_failure_and_help_without_packages(tmp_path):
    other=Path(r"C:\Users\ClioC\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
    if not other.is_file(): pytest.skip("Alternate CPython ABI unavailable")
    # Use the staged launcher during development and the installed launcher in
    # the released tests. Its sources are available without private packages.
    staged=Path(__file__).resolve().parents[2]
    launcher=staged/"image_caption_gender_fixer.py" if (staged/"image_caption_gender_fixer.py").is_file() else ROOT/"image_caption_gender_fixer.py"
    result=subprocess.run([str(other),"-B","-I","-S",str(launcher),"doctor","--json"],cwd=tmp_path,capture_output=True,text=True,timeout=30)
    assert result.returncode==30 and json.loads(result.stdout)["required_python"]=="3.10"
    for option in ("--help","--version"):
        result=subprocess.run([str(other),"-B","-I","-S",str(launcher),option,"--json"],cwd=tmp_path,capture_output=True,text=True,timeout=30)
        assert result.returncode==0 and isinstance(json.loads(result.stdout),dict)
