from pathlib import Path
import json
import os
import shutil
import pytest
from image_caption_gender_fixer import imaging
from image_caption_gender_fixer.cli import App,parser,preview_size
from image_caption_gender_fixer.errors import SelectionRequired,IntegrityError
from image_caption_gender_fixer.fs import sha256
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.sessions import Sessions
from image_caption_gender_fixer.transactions import Transactions
from image_caption_gender_fixer.cache import HashCache

ROOT=Path(os.environ.get("ICGF_TEST_INSTALLATION",Path(__file__).resolve().parents[2]))


def make_image(path,text="good boi",photo=False):
    np,cv,Image,Draw,Font,_,_,_=imaging.libraries()
    if photo:
        y,x=np.mgrid[:320,:1100]
        background=np.stack([100+40*np.sin(x/40)+y*.1,120+30*np.sin(y/25)+x*.04,160+30*np.cos((x+y)/50)],axis=2).clip(0,255).astype("uint8")
        image=Image.fromarray(background)
        draw=Draw.Draw(image)
        draw.ellipse((750,30,1050,280),fill=(70,100,45),outline=(30,65,20),width=8)
    else:
        image=Image.new("RGB",(1100,320),"white")
        draw=Draw.Draw(image)
    font=Font.truetype(r"C:\Windows\Fonts\arial.ttf",84)
    draw.text((90,100),text,font=font,fill="white" if photo else "black",stroke_width=1 if photo else 0,stroke_fill="black")
    image.save(path)
    return image


def app_for(tmp_path,extra=(),answers=None):
    state_root=tmp_path/"test-tool-state";state_root.mkdir(exist_ok=True)
    args=parser().parse_intermixed_args(["--new-session","--no-preview",*extra])
    app=App(ROOT,args,ask=(lambda prompt: next(answers)) if answers is not None else None)
    app.sessions=Sessions(state_root)
    app.transactions=Transactions(state_root)
    app.preference_path=state_root/"runtime/state/preferences.json"
    app.cache=HashCache(state_root)
    return app


@pytest.mark.parametrize("extension",["png","jpg"])
def test_real_ocr_render_commit_then_exact_undo(tmp_path,extension):
    source=tmp_path/("source é [1]."+extension)
    make_image(source)
    original_hash=sha256(source)
    app=app_for(tmp_path,answers=iter(["y"]))
    result,code=app.process([str(source)])
    assert code==0,result
    converted=result["results"][0]
    corrected=Path(converted["corrected"])
    assert corrected.exists() and not source.exists()
    history=History(tmp_path);event=history.transactions()[converted["transaction"]]
    assert sha256(tmp_path/event["backup"])==original_hash
    assert imaging.marker(corrected)["transaction"]==event["transaction"]
    restored=app.transactions.undo(tmp_path,event)
    assert sha256(source)==original_hash and Path(restored["archive_path"]).exists()


def test_mandatory_review_and_yes_does_not_bypass(tmp_path):
    source=tmp_path/"review.png";make_image(source);original=sha256(source)
    app=app_for(tmp_path,["--json","--yes"])
    with pytest.raises(SelectionRequired): app.process([str(source)])
    assert sha256(source)==original and not(tmp_path/".history.icgf").exists()
    session=app.sessions.unfinished()[0]
    assert session["items"][0]["state"]=="interrupted"
    assert session["items"][0]["artifacts"]
    assert all(Path(a["path"]).parent==source.parent for a in session["items"][0]["artifacts"])


def test_skip_keeps_source_and_only_session_bookkeeping(tmp_path):
    source=tmp_path/"skip.png";make_image(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter(["s"]))
    result,code=app.process([str(source)])
    assert sha256(source)==original and not(tmp_path/".history.icgf").exists()
    assert result["results"][0]["state"]=="skipped"
    assert not list(tmp_path.glob(".icgf-*.png"))


def test_no_match_does_not_prompt_or_create_folder_sidecars(tmp_path):
    source=tmp_path/"no-match.png";make_image(source,"hello friend")
    def fail(prompt): raise AssertionError("No-match image must not prompt")
    app=app_for(tmp_path);app.ask_callback=fail;app.interactive=True
    result,code=app.process([str(source)])
    assert result["results"][0]["reason"]=="no_substitution"
    assert sorted(p.name for p in tmp_path.iterdir())==["no-match.png","test-tool-state"]


def test_read_only_dry_run_creates_nothing(tmp_path):
    source=tmp_path/"dry.png";make_image(source)
    app=app_for(tmp_path,["--dry-run","--json"])
    before={str(p.relative_to(tmp_path)):p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result,code=app.process([str(source)])
    after={str(p.relative_to(tmp_path)):p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before==after
    assert result["results"][0]["proposed_regions"]==1


def test_actual_photographic_style_repair_stays_level_three(tmp_path):
    source=tmp_path/"texture.png";make_image(source,photo=True)
    app=app_for(tmp_path,["--json","--skip-review-for-confident-ones"])
    with pytest.raises(SelectionRequired): app.process([str(source)])
    assert source.exists() and not(tmp_path/".history.icgf").exists()
    artifacts=app.sessions.unfinished()[0]["items"][0]["artifacts"]
    assert any(a["kind"]=="repair" for a in artifacts)


@pytest.mark.parametrize("alias",["--skip-reivew-for-confident-ones","--skip-review-for-confident-ones"])
def test_aliases_same_gate_and_cannot_bypass_level_two(tmp_path,alias,monkeypatch):
    source=tmp_path/"gate.png";make_image(source)
    real=imaging.proposal
    def force_level_two(*a,**kw):
        proposal=real(*a,**kw);proposal["level"]=2;return proposal
    monkeypatch.setattr(imaging,"proposal",force_level_two)
    app=app_for(tmp_path,["--json",alias])
    with pytest.raises(SelectionRequired): app.process([str(source)])
    assert source.exists()


def test_hidden_history_still_skips_after_folder_rename(tmp_path):
    folder=tmp_path/"initial";folder.mkdir()
    source=folder/"input.png";make_image(source)
    app=app_for(tmp_path,answers=iter(["y"]))
    result,_=app.process([str(source)])
    corrected=Path(result["results"][0]["corrected"])
    # Rename the corrected file as well: exact hash detection must work.
    corrected.rename(folder/"renamed.png")
    renamed=tmp_path/"moved";folder.rename(renamed)
    second=app_for(tmp_path,["--json"])
    result,code=second.process([str(renamed/"renamed.png")])
    assert result["results"][0]["reason"]=="known_corrected"


@pytest.mark.parametrize("columns,rows",[(120,40),(20,8),(1,1),(80,24)])
def test_dynamic_preview_geometry(columns,rows):
    width,height=preview_size(columns,rows)
    assert 1<=width<=columns and 1<=height<=rows
    if rows==40: assert height==28


def test_animated_input_deferred_without_losing_frames(tmp_path):
    _,_,Image,_,_,_,_,_=imaging.libraries()
    path=tmp_path/"animated.gif"
    first=Image.new("RGB",(20,20),"red");second=Image.new("RGB",(20,20),"blue")
    first.save(path,save_all=True,append_images=[second],duration=100,loop=0)
    before=sha256(path)
    with pytest.raises(IntegrityError,match="multiframe"): imaging.decode(path)
    assert sha256(path)==before
