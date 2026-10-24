from pathlib import Path
import hashlib
import zipfile
from types import SimpleNamespace
import pytest
from image_caption_gender_fixer import dependencies as dep
from image_caption_gender_fixer.errors import DependencyUnavailable,SelectionRequired


def test_missing_ocr_asks_and_decline_does_not_download(tmp_path,monkeypatch):
    monkeypatch.setattr(dep,"native",lambda *a:None)
    asked=[]
    with pytest.raises(DependencyUnavailable): dep.require_ocr(tmp_path,True,False,lambda question:asked.append(question) or False)
    assert len(asked)==1 and "cannot proceed" in asked[0] and "Chocolatey" in asked[0]


@pytest.mark.parametrize("dry,interactive",[(True,True),(False,False)])
def test_no_install_in_dry_run_or_noninteractive(tmp_path,monkeypatch,dry,interactive):
    monkeypatch.setattr(dep,"native",lambda *a:None)
    def forbidden(*a): raise AssertionError("prompt/install forbidden")
    with pytest.raises((DependencyUnavailable,SelectionRequired)): dep.require_ocr(tmp_path,interactive,dry,forbidden)


def test_private_installer_flow_with_mocked_download_extract_and_verification(tmp_path,monkeypatch):
    payload=b"generated fake installer; never executed"
    monkeypatch.setattr(dep,"TESS_INSTALLER_HASH",hashlib.sha256(payload).hexdigest())
    archive=tmp_path/"environment/staging"/("tesseract-"+dep.TESS_VERSION+".nupkg")
    archive.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive,"w") as f:
        f.writestr("tools/tesseract-ocr-w64-setup-"+dep.TESS_VERSION+".exe",payload)
    monkeypatch.setattr(dep.shutil,"which",lambda name:"fake-7z.exe" if name=="7z" else None)
    calls=[]
    def fake_run(command,**kw):
        calls.append(command)
        return SimpleNamespace(returncode=0,stdout="List of available languages\neng\n",stderr="")
    monkeypatch.setattr(dep.subprocess,"run",fake_run)
    monkeypatch.setattr(dep,"native",lambda *a:{"path":"fake-tesseract.exe","version":"tesseract verified"})
    fetched=[]
    monkeypatch.setattr(dep,"fetch",lambda url,path,expected:fetched.append((url,path,expected)))
    result=dep.install_ocr(tmp_path,lambda question:True)
    assert result["path"]=="fake-tesseract.exe"
    assert any("--list-langs" in c for c in calls)
    assert len(fetched)==1 and dep.ENGLISH_COMMIT in fetched[0][0]
