"""Acceptance regressions using generated images and isolated local state."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import uuid

import pytest
from image_caption_gender_fixer import imaging, cli, dependencies
from image_caption_gender_fixer.diagnostics import bundle_health
from image_caption_gender_fixer.errors import IntegrityError, RenderBlocked, RecoverableFailure
from image_caption_gender_fixer.fs import sha256, identity, state_write, recycle
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.rules import RuleStore, builtins, transform
from image_caption_gender_fixer.sessions import Sessions
from test_images import make_image, app_for

ROOT=Path(os.environ.get("ICGF_TEST_INSTALLATION",Path(__file__).resolve().parents[2]))


def test_context_exclusion_requires_both_phrase_and_context():
    ignored=[{"phrase":"boy","context":"king"}]
    assert transform("boy near queen",builtins(),ignored)["final"]=="girl near queen"
    assert transform("king near boy and man",builtins(),ignored)["final"]=="king near boy and woman"


def test_regions_preserve_whole_line_exclusion_context():
    words=[imaging.Word("boy",(0,0,30,20),99,0,3),imaging.Word("king",(40,0,80,20),99,4,8),
           imaging.Word("man",(90,0,130,20),99,9,12)]
    regions,_=imaging.regions([{"text":"boy king man","words":words}],builtins(),[{"phrase":"boy","context":"king"}])
    assert [(r.before,r.after) for r in regions]==[("man","woman")]


def test_ignore_ids_profiles_toggles_and_scope_filtering(tmp_path):
    store=RuleStore(tmp_path/".image-gender-fixer.stt")
    digest="a"*64
    item=store.add_ignore("project",phrase="boy",image_hash=digest)
    store.append("disable",id=item["id"],profile="project")
    assert store.load("default")==[] and not store.ignores
    store.load("project",digest)
    assert transform("boy",builtins(),store.ignores)["final"]=="girl"
    store.load("project","b"*64)
    assert not store.warnings and not store.ignores
    assert "project" in store.profiles()


def test_rule_append_preserves_unrelated_file_and_quarantines_partial_tail(tmp_path):
    foreign=tmp_path/"foreign.stt"
    foreign.write_text('{"personal":"notes"}',encoding="utf-8")
    before=foreign.read_bytes()
    with pytest.raises(IntegrityError): RuleStore(foreign).add("king","queen")
    assert foreign.read_bytes()==before
    store=RuleStore(tmp_path/".image-gender-fixer.stt")
    store.add("king","queen")
    with store.path.open("a",encoding="utf-8") as out: out.write('{"interrupted":')
    store.add("duke","duchess")
    assert len(store.load())==2 and len(store.warnings)==1


def test_global_exclusion_applies_without_enabling_global_substitutions(tmp_path):
    source=tmp_path/"images";source.mkdir()
    installation=tmp_path/"tool";installation.mkdir()
    global_store=RuleStore(installation/"runtime/state/global-rules.stt","global")
    global_store.add("king","queen")
    global_store.add_ignore(phrase="boy")
    app=cli.App(installation,cli.parser().parse_args(["--json"]))
    rules,store=app.rules(source)
    assert transform("boy king",rules,store.ignores)["final"]=="boy king"
    state_write(app.preference_path,{"undo-corrected":"ask","global-rules":True})
    rules,store=app.rules(source)
    assert transform("boy king",rules,store.ignores)["final"]=="boy queen"


def test_blocked_render_offers_adjustment_and_cannot_be_approved(tmp_path,monkeypatch):
    source=tmp_path/"blocked.png";make_image(source);original=sha256(source)
    real=imaging.render_region
    def blocked(image,region,protected):
        if region.after=="good girl": raise RenderBlocked("Generated no-fit condition")
        return real(image,region,protected)
    monkeypatch.setattr(imaging,"render_region",blocked)
    app=app_for(tmp_path,answers=iter(["a","v","0","1","wording girl","a"]))
    result,code=app.process([str(source)])
    assert code==0,result
    event=next(iter(History(tmp_path).transactions().values()))
    assert sha256(tmp_path/event["backup"])==original


def test_real_impossible_fit_produces_no_unsafe_stage(tmp_path):
    _,_,Image,Draw,Font,_,_,_=imaging.libraries()
    source=tmp_path/"tiny.png"
    image=Image.new("RGBA",(120,60),"white")
    Draw.Draw(image).text((5,8),"boy",font=Font.truetype(r"C:\Windows\Fonts\arial.ttf",22),fill="black")
    image.save(source)
    decoded,metadata=imaging.decode(source)
    word=imaging.Word("boy",(5,12,45,35),99,0,3)
    region=imaging.Region("boy","W"*300,word.box,99,[word],[])
    proposal=imaging.proposal(source,decoded,metadata,[region],[word.box],ROOT,"unused",sha256(source),"rules")
    assert proposal["blocked"] and proposal["stage"] is None and not proposal["artifacts"]
    assert [p.name for p in tmp_path.iterdir()]==[source.name]


def test_cancel_is_resumable_and_then_commits_with_fresh_approval(tmp_path):
    source=tmp_path/"cancel.png";make_image(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter(["c"]))
    result,code=app.process([str(source)])
    assert code==20 and sha256(source)==original and not(tmp_path/".history.icgf").exists()
    pending=app.sessions.unfinished()
    assert len(pending)==1 and pending[0]["items"][0]["state"]=="canceled"
    resumed=app_for(tmp_path,answers=iter(["a"]))
    resumed.args.resume=pending[0]["id"];resumed.args.new_session=False
    result,code=resumed.process([])
    assert code==0 and result["results"][0]["state"]=="committed"
    event=next(iter(History(tmp_path).transactions().values()))
    assert sha256(tmp_path/event["backup"])==original


def test_one_composite_approval_for_multiple_regions(tmp_path):
    _,_,Image,Draw,Font,_,_,_=imaging.libraries()
    source=tmp_path/"multiple.png"
    image=Image.new("RGB",(1100,320),"white")
    painter=Draw.Draw(image);font=Font.truetype(r"C:\Windows\Fonts\arial.ttf",70)
    painter.text((70,100),"boi",font=font,fill="black")
    painter.text((650,100),"man",font=font,fill="black")
    image.save(source)
    app=app_for(tmp_path);calls=[]
    def approve(source,proposal,regions):
        calls.append(proposal)
        assert len(proposal["diagnostics"])==2 and Path(proposal["stage"]).is_file()
        return "a"
    app.review=approve
    result,code=app.process([str(source)])
    assert code==0 and len(calls)==1 and len(History(tmp_path).transactions())==1


def test_lossless_alpha_icc_dpi_and_unaffected_pixels(tmp_path):
    np,_,Image,Draw,Font,_,_,_=imaging.libraries()
    from PIL import ImageCms
    source=tmp_path/"alpha.png"
    image=Image.new("RGBA",(900,200),(40,80,120,90))
    draw=Draw.Draw(image);font=Font.truetype(r"C:\Windows\Fonts\arial.ttf",48)
    box=draw.textbbox((40,60),"good boi",font=font)
    draw.text((40,60),"good boi",font=font,fill=(255,255,255,255))
    profile=ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    image.save(source,icc_profile=profile,dpi=(144,144))
    decoded,metadata=imaging.decode(source)
    word=imaging.Word("good boi",box,99,0,8)
    region=imaging.Region("good boi","good girl",box,99,[word],[])
    corrected,diagnostic,_=imaging.render_region(decoded,region,[box])
    affected=diagnostic["affected"]
    mask=np.ones((decoded.height,decoded.width),dtype=bool)
    mask[affected[1]:affected[3],affected[0]:affected[2]]=False
    assert np.array_equal(np.array(decoded)[mask],np.array(corrected)[mask])
    output=tmp_path/"stage.png"
    imaging.save_image(corrected,metadata,output,str(uuid.uuid4()),sha256(source),"rules")
    with Image.open(output) as saved:
        assert saved.info["icc_profile"]==profile
        assert saved.info["dpi"][0]==pytest.approx(144,abs=.1)
        assert np.array_equal(np.array(saved)[mask],np.array(decoded)[mask])


def test_orientation_is_baked_once_with_updated_dimensions(tmp_path):
    _,_,Image,_,_,ImageOps,_,_=imaging.libraries()
    source=tmp_path/"rotated.jpg"
    image=Image.new("RGB",(400,160),"orange")
    exif=Image.Exif();exif[274]=6;exif[40962]=400;exif[40963]=160
    image.save(source,exif=exif)
    original=sha256(source)
    decoded,metadata=imaging.decode(source)
    assert decoded.size==(160,400)
    output=tmp_path/"oriented.jpg"
    imaging.save_image(decoded,metadata,output,str(uuid.uuid4()),original,"rules")
    with Image.open(output) as saved:
        assert saved.size==(160,400) and saved.getexif()[274]==1
        assert saved.getexif()[40962]==160 and saved.getexif()[40963]==400
        assert ImageOps.exif_transpose(saved).size==saved.size
    assert sha256(source)==original


@pytest.mark.parametrize("edge",["left","right","top","bottom"])
def test_fully_styled_text_fits_at_each_edge_or_blocks_safely(edge):
    _,_,Image,Draw,Font,_,_,_=imaging.libraries()
    image=Image.new("RGBA",(300,160),"white")
    draw=Draw.Draw(image);font=Font.truetype(r"C:\Windows\Fonts\arial.ttf",24)
    bounds=draw.textbbox((0,0),"boy",font=font)
    x=0 if edge=="left" else 300-bounds[2] if edge=="right" else 80
    y=-bounds[1] if edge=="top" else 160-bounds[3] if edge=="bottom" else 50
    box=draw.textbbox((x,y),"boy",font=font)
    draw.text((x,y),"boy",font=font,fill="black")
    word=imaging.Word("boy",box,99,0,3)
    region=imaging.Region("boy","girl",box,99,[word],[],{"outline":2,"shadow":(2,2),"blur":1})
    try:
        result,diagnostic,_=imaging.render_region(image,region,[box])
    except RenderBlocked:
        assert edge in ("right","bottom")
    else:
        x1,y1,x2,y2=diagnostic["affected"]
        assert 0<=x1<x2<=300 and 0<=y1<y2<=160 and result.size==image.size


def test_bundle_doctor_hashes_and_optional_downloads_are_read_only(tmp_path):
    environment=tmp_path/"environment";environment.mkdir()
    content=environment/"data.bin";content.write_bytes(b"package data")
    manifest={"application":"icgf","schema":1,"optional_files":["wheels/old.whl"],"files":{
        "data.bin":{"size":len(content.read_bytes()),"sha256":sha256(content)},
        "wheels/old.whl":{"size":1,"sha256":"a"*64}}}
    (environment/"manifest.json").write_text(json.dumps(manifest),encoding="utf-8")
    before={str(p):p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result=bundle_health(tmp_path)
    assert result["checked"]==1 and result["optional_absent"]==["wheels/old.whl"] and not result["errors"]
    assert before=={str(p):p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    content.write_bytes(b"modified data")
    assert bundle_health(tmp_path)["errors"]


def test_unexpected_crash_log_excludes_ocr_and_target_paths(tmp_path,monkeypatch,capsys):
    installation=tmp_path/"tool";installation.mkdir()
    private="Secret OCR text that must never be logged"
    def fail(*a): raise RuntimeError(private)
    monkeypatch.setattr(cli.App,"process",fail)
    assert cli.main(installation,["--json","--new-session"])==50
    result=json.loads(capsys.readouterr().out)
    assert result["exception_type"]=="RuntimeError" and "crash_report" in result
    logs="".join(p.read_text(encoding="utf-8") for p in (installation/"runtime").rglob("*") if p.is_file())
    assert private not in logs and str(tmp_path) not in logs


def test_json_review_selection_has_session_and_transaction_ids(tmp_path,monkeypatch,capsys):
    source=tmp_path/"review.png";make_image(source)
    app=app_for(tmp_path,["--json"])
    monkeypatch.setattr(cli,"App",lambda *a,**k:app)
    installation=tmp_path/"command-tool";installation.mkdir()
    assert cli.main(installation,[str(source),"--json"])==21
    result=json.loads(capsys.readouterr().out)
    assert result["session"] and result["transaction"] and "good boi" not in json.dumps(result)
    assert source.exists() and not(tmp_path/".history.icgf").exists()


def test_forgetting_session_preserves_committed_outputs_rules_and_preferences(tmp_path):
    source=tmp_path/"first.png";make_image(source)
    app=app_for(tmp_path,answers=iter(["a"]))
    result,code=app.process([str(source)]);assert code==0
    corrected=Path(result["results"][0]["corrected"])
    event=next(iter(History(tmp_path).transactions().values()))
    backup=tmp_path/event["backup"]
    second=tmp_path/"pending.png";make_image(second,"hello friend")
    session=app.sessions.load(result["session"])
    artifact=tmp_path/(".icgf-"+str(uuid.uuid4())+"-proposal.png")
    artifact.write_bytes(b"generated owned preview")
    session["items"].append({"path":str(second),"hash":sha256(second),"state":"pending","artifacts":[
        {"path":str(artifact),"hash":sha256(artifact),"identity":identity(artifact)[:2],"kind":"proposal"}]})
    app.sessions.save(session)
    RuleStore(tmp_path/".image-gender-fixer.stt").add("king","queen")
    state_write(app.preference_path,{"undo-corrected":"keep","global-rules":False})
    protected=[corrected,backup,tmp_path/".history.icgf",tmp_path/".image-gender-fixer.stt",app.preference_path,second]
    before={p:sha256(p) for p in protected}
    app.sessions.abandon(session,[])
    assert all(sha256(p)==digest for p,digest in before.items())
    assert not artifact.exists() and not(app.sessions.directory/(session["id"]+".json")).exists()


def test_corrupt_session_is_retained_and_reported(tmp_path):
    source=tmp_path/"source.txt";source.write_text("generated",encoding="utf-8")
    sessions=Sessions(tmp_path)
    valid=sessions.create([source],"default")
    corrupt=sessions.directory/(str(uuid.uuid4())+".json")
    corrupt.write_text('{"partial":',encoding="utf-8")
    assert [s["id"] for s in sessions.unfinished()]==[valid["id"]]
    assert sessions.issues and corrupt.read_text(encoding="utf-8")=='{"partial":'


def test_real_offline_package_repair_and_relocation(tmp_path,monkeypatch):
    installation=tmp_path/"repair-tool"
    wheels=installation/"environment/wheels";wheels.mkdir(parents=True)
    shutil.copyfile(ROOT/"environment/wheels/runtime-bundle.zip",wheels/"runtime-bundle.zip")
    shutil.copyfile(ROOT/"environment/manifest.json",installation/"environment/manifest.json")
    monkeypatch.setattr(dependencies,"status",lambda *a,**k:{"packages":{"numpy":{"error":"generated missing environment"}}})
    app=SimpleNamespace(root=installation,confirm=lambda question:True,diagnostics=lambda message:None)
    assert cli.repair_packages(app)
    selection=json.loads((installation/"environment/metadata/active.json").read_text(encoding="utf-8"))
    packages=installation/"environment"/selection["packages"]
    assert (packages/".icgf-ready.json").exists()
    relocated=tmp_path/"moved-repair-tool";installation.rename(relocated)
    code='import sys,os,json;from pathlib import Path;r=Path(sys.argv[1]);s=json.loads((r/"environment/metadata/active.json").read_text());p=r/"environment"/s["packages"];sys.path.insert(0,str(p));h=[os.add_dll_directory(str(p/n)) for n in ("numpy.libs","PIL","cv2",".dlls") if (p/n).exists()];import numpy,cv2;assert Path(numpy.__file__).is_relative_to(p);assert cv2.imencode(".png",numpy.zeros((2,2,3),dtype=numpy.uint8))[0]'
    subprocess.run([sys.executable,"-B","-I","-S","-c",code,str(relocated)],check=True,capture_output=True,timeout=60)
    recycle(relocated)
    assert not relocated.exists()
