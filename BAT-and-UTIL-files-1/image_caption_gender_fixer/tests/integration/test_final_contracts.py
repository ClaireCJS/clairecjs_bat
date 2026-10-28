import json
import os
from pathlib import Path
import subprocess
import sys
import pytest
from image_caption_gender_fixer import cli, imaging
from image_caption_gender_fixer.rules import builtins, transform
from image_caption_gender_fixer.fs import sha256
from test_images import app_for, make_image

ROOT=Path(os.environ.get("ICGF_TEST_INSTALLATION",Path(__file__).resolve().parents[2]))


def test_phrase_and_occurrence_exclusions_protect_original_cascade_span():
    assert transform("good boi and boi",builtins(),[{"phrase":"good boi"}])["final"]=="good boi and girl"
    assert transform("good boi and boi",builtins(),[{"occurrence":[0,8]}])["final"]=="good boi and girl"


def test_end_of_options_and_exact_product_suffix():
    args=cli.parser().parse_intermixed_args(["--","--verbose"])
    assert args.items==["--verbose"] and not args.verbose
    assert cli.product_name("a-gendeerfixed (2).png")
    assert not cli.product_name("a-gendeerfixed-example.png")


def test_explain_uses_read_only_analysis_and_detects_product_markers(tmp_path,capsys):
    source=tmp_path/"explain.png";make_image(source)
    args=cli.parser().parse_intermixed_args(["--json"])
    app=cli.App(ROOT,args)
    before={p:p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    result,code=cli.administrative(app,"explain",[str(source)])
    assert code==0 and result["would_process"] and result["confidence_provisional"] and result["review_required"]
    assert before=={p:p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    image,metadata=imaging.decode(source)
    marked=tmp_path/"renamed-product.png"
    imaging.save_image(image,metadata,marked,"baf707da-f755-4c26-9bdf-40eec88728d6",sha256(source),"rules")
    result,code=cli.administrative(app,"explain",[str(marked)])
    assert code==0 and result["ambiguous"] and not result["would_process"]


def test_unsupported_animation_has_deferred_result_and_resumable_state(tmp_path):
    _,_,Image,_,_,_,_,_=imaging.libraries()
    source=tmp_path/"animation.gif"
    Image.new("RGB",(20,20),"red").save(source,save_all=True,append_images=[Image.new("RGB",(20,20),"blue")],loop=0,duration=100)
    original=sha256(source)
    app=app_for(tmp_path,["--json"])
    result,code=app.process([str(source)])
    assert code==10 and result["results"][0]["state"]=="deferred"
    assert sha256(source)==original and app.sessions.unfinished()


def test_repair_restart_preserves_interactive_terminal(tmp_path,monkeypatch):
    source=tmp_path/"restart.png";make_image(source)
    app=app_for(tmp_path)
    app.interactive=True;app.ask_callback=None
    monkeypatch.setattr(cli,"repair_packages",lambda app:True)
    captured=[]
    def restart(mode,executable,arguments):
        captured.append((mode,executable,arguments));return 21
    monkeypatch.setattr(cli.os,"spawnv",restart)
    with pytest.raises(SystemExit) as exit: app.process([str(source)])
    assert exit.value.code==21 and captured[0][0]==os.P_WAIT
    assert "--resume" in captured[0][2] and source.exists()


def test_plain_launcher_isolates_before_shadowable_standard_library_imports(tmp_path):
    staged=Path(__file__).resolve().parents[2]
    launcher=staged/"image_caption_gender_fixer.py" if (staged/"image_caption_gender_fixer.py").is_file() else ROOT/"image_caption_gender_fixer.py"
    shadow=tmp_path/"shadow";shadow.mkdir()
    (shadow/"json.py").write_text('raise RuntimeError("Unrelated PYTHONPATH json module was loaded")',encoding="utf-8")
    env=dict(os.environ,PYTHONPATH=str(shadow))
    result=subprocess.run([sys.executable,str(launcher),"--version","--json"],cwd=tmp_path,env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0 and json.loads(result.stdout)["version"]=="0.3.0"
