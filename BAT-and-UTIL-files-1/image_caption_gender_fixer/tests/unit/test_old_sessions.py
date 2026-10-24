import pytest
from pathlib import Path
from image_caption_gender_fixer.cli import App,parser
from image_caption_gender_fixer.errors import SelectionRequired
from image_caption_gender_fixer.fs import sha256
from PIL import Image


def old_jobs(tmp_path,answers=None,json_mode=False):
    root=tmp_path/"tool";root.mkdir()
    images=tmp_path/"images";images.mkdir()
    source=images/"original.png";Image.new("RGB",(10,10),"purple").save(source)
    args=parser().parse_intermixed_args(["--yes"]+(["--json"] if json_mode else []))
    app=App(root,args,ask=(lambda prompt:next(answers)) if answers is not None else None)
    first=app.sessions.create([source],"default")
    second=app.sessions.create([source],"conservative")
    return app,source,first,second


def test_multiple_old_jobs_require_explicit_choice_even_with_yes(tmp_path):
    app,source,first,second=old_jobs(tmp_path,json_mode=True)
    with pytest.raises(SelectionRequired) as error: app.select_session([source])
    assert {s["id"] for s in error.value.context["sessions"]}=={first["id"],second["id"]}
    assert len(app.sessions.list())==2 and source.exists()


@pytest.mark.parametrize("choice",["resume","inspect_then_new","forget_then_new","new"])
def test_old_job_menu_preserves_sources_and_unselected_jobs(tmp_path,choice):
    answers=iter([])
    app,source,first,second=old_jobs(tmp_path,answers=answers)
    sequence={"resume":["r",second["id"]],"inspect_then_new":["i",first["id"],"n"],
              "forget_then_new":["t",first["id"],"y","n"],"new":["n"]}[choice]
    replies=iter(sequence);app.ask_callback=lambda prompt:next(replies)
    original=sha256(source)
    selected=app.select_session([source])
    ids={s["id"] for s in app.sessions.list()}
    assert sha256(source)==original and second["id"] in ids
    assert not(source.parent/".history.icgf").exists()
    if choice=="resume": assert selected["id"]==second["id"] and len(ids)==2
    elif choice=="forget_then_new": assert first["id"] not in ids and len(ids)==2
    else: assert first["id"] in ids and len(ids)==3
