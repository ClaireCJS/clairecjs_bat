"""Real process lifetime and Windows junction regressions; generated data only."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
from image_caption_gender_fixer import cli
from image_caption_gender_fixer.errors import UnsafeFilesystem
from image_caption_gender_fixer.fs import validate_path

INSTALLATION=Path(os.environ.get('ICGF_TEST_INSTALLATION',Path(__file__).resolve().parents[2]))
SOURCE_ROOT=Path(__file__).resolve().parents[2]


def fake_tool(folder):
    folder.mkdir()
    launcher=SOURCE_ROOT/'image_caption_gender_fixer.py'
    if not launcher.exists(): launcher=INSTALLATION/'image_caption_gender_fixer.py'
    shutil.copy2(launcher,folder/'image_caption_gender_fixer.py')
    package=folder/'src/image_caption_gender_fixer';package.mkdir(parents=True)
    (package/'__init__.py').write_text('',encoding='utf-8')
    (package/'cli.py').write_text('import json,time\nfrom pathlib import Path\ndef main(root):\n time.sleep(.6)\n Path(root,"child-finished").write_text("finished")\n print(json.dumps({"state":"finished"}))\n return 21\n',encoding='utf-8')
    return folder/'image_caption_gender_fixer.py'


@pytest.mark.parametrize('via_batch',[False,True])
def test_calling_process_waits_and_returns_child_status(tmp_path,via_batch):
    tool=tmp_path/'image_caption_gender_fixer'
    launcher=fake_tool(tool)
    if via_batch:
        wrapper=SOURCE_ROOT/'image-caption-gender-fixer.bat'
        if not wrapper.exists(): wrapper=INSTALLATION.parent/'image-caption-gender-fixer.bat'
        shutil.copy2(wrapper,tmp_path/wrapper.name)
        alias=SOURCE_ROOT/'icgf.bat'
        if not alias.exists(): alias=INSTALLATION.parent/'icgf.bat'
        shutil.copy2(alias,tmp_path/alias.name)
        command=[os.environ.get('COMSPEC',r'C:\Windows\System32\cmd.exe'),'/d','/c',str(tmp_path/'icgf.bat')]
    else: command=[sys.executable,str(launcher)]
    process=subprocess.Popen(command,cwd=tmp_path,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                             env=dict(os.environ,ICGF_PYTHON=sys.executable))
    code=process.wait(timeout=30)
    # communicate() also waits for inherited pipe handles, and used to hide
    # execv's early parent exit. Inspect state immediately after wait instead.
    finished_before_parent_exit=(tool/'child-finished').exists()
    stdout,stderr=process.communicate(timeout=30)
    assert finished_before_parent_exit,'The caller exited while its worker was still running'
    assert code==21,(code,stdout,stderr)
    assert json.loads(stdout.decode('utf-8'))['state']=='finished'


def junction(alias,target):
    result=subprocess.run([os.environ.get('COMSPEC',r'C:\Windows\System32\cmd.exe'),'/d','/c',
                           'mklink','/J',str(alias),str(target)],capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr


def test_explicit_directory_junction_resolves_and_deduplicates(tmp_path):
    physical=tmp_path/'physical';physical.mkdir()
    source=physical/'caption.png';source.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
    alias=tmp_path/'alias';junction(alias,physical)
    root=tmp_path/'tool';root.mkdir()
    app=cli.App(root,cli.parser().parse_intermixed_args(['--json']))
    assert app.discover([str(alias)])==[source]
    assert app.discover([str(alias/'*'),str(source)])==[source]
    assert validate_path(alias/'future.png')==physical/'future.png'
    # Recursive scans still skip junction children, avoiding cycles/escape.
    junction(physical/'loop',physical)
    app.args.recursive=True
    assert app.discover([str(alias)])==[source]


def test_junction_does_not_bypass_installation_target_refusal(tmp_path):
    root=tmp_path/'tool';root.mkdir()
    alias=tmp_path/'tool-alias';junction(alias,root)
    with pytest.raises(UnsafeFilesystem,match='installation'):
        validate_path(alias,root)


def test_linked_image_and_unknown_reparse_provider_still_refused(tmp_path,monkeypatch):
    from image_caption_gender_fixer import fs
    source=tmp_path/'linked.png';source.write_bytes(b'generated fixture')
    real=fs.reparse
    monkeypatch.setattr(fs,'reparse',lambda path:Path(path)==source or real(path))
    with pytest.raises(UnsafeFilesystem,match='Reparse'):
        validate_path(source)
