import ctypes
import json
import os
from pathlib import Path
import pytest
from image_caption_gender_fixer.cli import App,parser,main,undo_images
from image_caption_gender_fixer.errors import UnsafeFilesystem,SelectionRequired
from image_caption_gender_fixer.fs import hide,is_network,reparse


def fake_png(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n"+b"generated-discovery-only")
    return path


def app(tmp_path,extra=()):
    root=tmp_path/"installation";root.mkdir(exist_ok=True)
    return App(root,parser().parse_intermixed_args(["--json",*extra]))


def test_literal_wildcards_and_overlapping_arguments_deduplicate(tmp_path):
    source=fake_png(tmp_path/"space é [1]'s.png")
    other=fake_png(tmp_path/"second.bin")
    instance=app(tmp_path)
    paths=instance.discover([str(tmp_path/"*"),str(source),str(source)])
    assert set(paths)=={source,other}


def test_recursive_opt_in_and_product_exclusion(tmp_path):
    source=fake_png(tmp_path/"first.png")
    second=fake_png(tmp_path/"child"/"second.png")
    fake_png(tmp_path/"first-gendeerfixed.png")
    fake_png(tmp_path/".icgf-pretend-proposal.png")
    assert app(tmp_path).discover([str(tmp_path)])==[source]
    assert set(app(tmp_path,["--recursive"]).discover([str(tmp_path)]))=={source,second}


def test_hidden_opt_in(tmp_path):
    source=fake_png(tmp_path/"hidden.png");hide(source)
    assert not app(tmp_path).discover([str(source)])
    assert app(tmp_path,["--include-hidden"]).discover([str(source)])==[source]


def test_installation_is_not_process_target(tmp_path):
    instance=app(tmp_path)
    with pytest.raises(UnsafeFilesystem): instance.discover([str(instance.root)])


def test_hard_links_deduplicate_by_file_identity(tmp_path):
    source=fake_png(tmp_path/"one.png")
    linked=tmp_path/"two.png";os.link(source,linked)
    paths=app(tmp_path).discover([str(source),str(linked)])
    assert len(paths)==1 and source.stat().st_nlink==2


def test_network_detection_and_refusal(tmp_path,monkeypatch):
    assert is_network(Path(r"\\server\share\image.png"))
    source=fake_png(tmp_path/"source.png")
    monkeypatch.setattr("image_caption_gender_fixer.cli.is_network",lambda p:True)
    with pytest.raises(UnsafeFilesystem): app(tmp_path).discover([str(source)])
    assert app(tmp_path,["--allow-network"]).discover([str(source)])==[source]


def test_json_help_version_and_invalid_arguments(tmp_path,capsys):
    assert main(tmp_path,["--help","--json"])==0
    assert "help" in json.loads(capsys.readouterr().out)
    assert main(tmp_path,["--version","--json"])==0
    assert "version" in json.loads(capsys.readouterr().out)
    assert main(tmp_path,["--unknown-option","--json"])==64
    assert json.loads(capsys.readouterr().out)["state"]=="failed"


def test_read_only_preferences_do_not_create_state(tmp_path,capsys):
    assert main(tmp_path,["preferences","show","--json"])==0
    assert json.loads(capsys.readouterr().out)["undo-corrected"]=="ask"
    assert list(tmp_path.iterdir())==[]
    assert main(tmp_path,["preferences","set","undo-corrected","recycle","--dry-run","--json"])==0
    assert list(tmp_path.iterdir())==[]


def test_confident_spellings_and_conflicting_undo_options():
    assert parser().parse_intermixed_args(["--skip-reivew-for-confident-ones"]).skip_confident
    assert parser().parse_intermixed_args(["--skip-review-for-confident-ones"]).skip_confident
    from image_caption_gender_fixer.cli import ArgumentsError
    with pytest.raises(ArgumentsError): parser().parse_intermixed_args(["--keep-undo-archives","--recycle-undo-archives"])
