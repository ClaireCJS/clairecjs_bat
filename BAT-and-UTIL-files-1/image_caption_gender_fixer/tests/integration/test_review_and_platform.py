import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

import pytest
from image_caption_gender_fixer import cli, imaging, transactions
from image_caption_gender_fixer.errors import IntegrityError
from image_caption_gender_fixer.errors import SelectionRequired, UnsafeFilesystem, RecoverableFailure
from image_caption_gender_fixer.fs import sha256, folder_lock, hide
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.rules import Rule, builtins, transform
from test_images import app_for, make_image
from test_recovery import interrupted

ROOT=Path(os.environ.get("ICGF_TEST_INSTALLATION",Path(__file__).resolve().parents[2]))


def test_post_render_ocr_correction_rerenders_without_saving_rules(tmp_path,monkeypatch):
    source=tmp_path/"ocr.png";make_image(source)
    real=imaging.ocr;initial=[True]
    def ocr(*args,**kwargs):
        lines=real(*args,**kwargs)
        if initial[0]:
            initial[0]=False
            for line in lines:
                line["text"]=line["text"].replace("boi","boy")
                for word in line["words"]: word.text=word.text.replace("boi","boy")
        return lines
    monkeypatch.setattr(imaging,"ocr",ocr)
    app=app_for(tmp_path,answers=iter(["1","good boi","invalid-box","","nan","0"]))
    proposals=[]
    def review(source,proposal,regions):
        proposals.append({"trace":list(proposal["trace"]),"stage":proposal["stage"]})
        return "o" if len(proposals)==1 else "a"
    app.review=review
    result,code=app.process([str(source)])
    assert code==0 and len(proposals)==2
    assert all(step["rule"]!="builtin-0" for step in proposals[0]["trace"])
    assert any(step["rule"]=="builtin-0" for step in proposals[1]["trace"])
    assert not(tmp_path/".image-gender-fixer.stt").exists()


def test_repair_comparison_artifacts_are_adjacent_owned_and_recycled(tmp_path):
    source=tmp_path/"compare.png";make_image(source);before=sha256(source)
    app=app_for(tmp_path,answers=iter(["b","1","telea","s"]))
    result,code=app.process([str(source)])
    assert code==10 and sha256(source)==before and not(tmp_path/".history.icgf").exists()
    assert not list(tmp_path.glob(".icgf-*.png"))
    assert app.sessions.load(result["session"])["items"][0]["artifacts"]==[]


def test_detected_face_prevents_confident_review_bypass(tmp_path,monkeypatch):
    source=tmp_path/"face-warning.png";make_image(source)
    monkeypatch.setattr(imaging,"scene_faces",lambda image:[(0,0,image.width,image.height)])
    real=imaging.proposal;observed=[]
    def proposal(*a,**k):
        value=real(*a,**k);observed.append(value);return value
    monkeypatch.setattr(imaging,"proposal",proposal)
    app=app_for(tmp_path,["--json","--skip-review-for-confident-ones"])
    with pytest.raises(SelectionRequired): app.process([str(source)])
    assert observed[0]["level"]==3
    assert any("face" in w for d in observed[0]["diagnostics"] for w in d["warnings"])
    assert source.exists()


def test_bundled_face_classifier_runs_locally():
    _,_,Image,_,_,_,_,_=imaging.libraries()
    assert imaging.scene_faces(Image.new("RGB",(200,200),"white"))==[]


@pytest.mark.parametrize("command",["outline -1","mask 100000","tracking nan","rotation inf","shadow 0,0,-1","extend left 999999"])
def test_extreme_visual_controls_are_rejected(command):
    region=imaging.Region("boy","girl",(0,0,40,20),99,[],[])
    with pytest.raises((cli.ArgumentsError,ValueError)):
        cli.adjust(region,command,(300,200))


def test_growth_cascade_is_bounded():
    # Construct a valid size-bounded rule whose repeated matches would create
    # excessive output, rather than allocating an exponential cascade.
    rules=[Rule("a","word "*800,100,id="bounded")]
    with pytest.raises(IntegrityError,match="bounded output"):
        transform("a "*100,rules)


def test_changed_corrected_archive_is_kept_even_with_recycle_flag(tmp_path):
    source=tmp_path/"changed.png";make_image(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter(["a"]))
    result,code=app.process([str(source)]);assert code==0
    corrected=Path(result["results"][0]["corrected"])
    with corrected.open("ab") as output: output.write(b"generated later edit")
    changed=sha256(corrected)
    undo=app_for(tmp_path,["--json","--recycle-undo-archives"])
    result,code=cli.undo_images(undo,[str(corrected)])
    assert code==0 and sha256(source)==original
    record=result["results"][0]
    assert record["archive_disposition"]=="kept" and sha256(record["archive_path"])==changed


def test_format_signature_controls_corrected_extension(tmp_path):
    source=tmp_path/"wrong.jpg"
    original=tmp_path/"original.png";make_image(original);original.rename(source)
    app=app_for(tmp_path,answers=iter(["a"]))
    result,code=app.process([str(source)]);assert code==0
    corrected=Path(result["results"][0]["corrected"])
    assert corrected.name=="wrong-gendeerfixed.png"
    _,_,Image,_,_,_,_,_=imaging.libraries()
    with Image.open(corrected) as image: assert image.format=="PNG"


def test_state_volume_capacity_failure_precedes_original_rename(tmp_path,monkeypatch):
    source=tmp_path/"capacity.png";make_image(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter(["a"]))
    real=transactions.capacity
    def capacity(folder,needed):
        if Path(folder).is_relative_to(app.transactions.root): raise UnsafeFilesystem("Generated state-volume capacity failure")
        return real(folder,needed)
    monkeypatch.setattr(transactions,"capacity",capacity)
    result,code=app.process([str(source)])
    assert code==50 and sha256(source)==original and not(tmp_path/".history.icgf").exists()


def test_recovery_rejects_changed_files_despite_committed_history(tmp_path):
    engine,record,source,stage,backup,corrected=interrupted(tmp_path,3)
    corrected.write_bytes(b"generated external change")
    with pytest.raises(RecoverableFailure): engine.recover()
    assert backup.exists() and corrected.read_bytes()==b"generated external change" and engine.pending()


def test_os_releases_stale_folder_lock_after_process_death(tmp_path):
    code='import sys,os;from pathlib import Path;sys.path.insert(0,sys.argv[1]);from image_caption_gender_fixer.fs import folder_lock;p=Path(sys.argv[2]);\nwith folder_lock(p):\n print("ready",flush=True);sys.stdin.buffer.read(1);os._exit(99)'
    child=subprocess.Popen([sys.executable,"-B","-I","-S","-c",code,str(ROOT/"src"),str(tmp_path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        assert child.stdout.readline().strip()==b"ready"
        with pytest.raises(UnsafeFilesystem):
            with folder_lock(tmp_path): pass
        child.communicate(input=b"x",timeout=10)
        assert child.returncode==99
        with folder_lock(tmp_path): pass
    finally:
        if child.poll() is None: child.terminate();child.wait(timeout=10)


def test_real_long_unicode_path_commit_and_undo(tmp_path):
    folder=tmp_path
    while len(str(folder))<275:
        folder=folder/("long-é-"+uuid.uuid4().hex[:16])
    folder.mkdir(parents=True)
    source=folder/"source [é].png";make_image(source)
    original=sha256(source)
    app=app_for(tmp_path,answers=iter(["a"]))
    result,code=app.process([str(source)])
    assert code==0,result
    event=next(iter(History(folder).transactions().values()))
    app.transactions.undo(folder,event)
    assert sha256(source)==original
