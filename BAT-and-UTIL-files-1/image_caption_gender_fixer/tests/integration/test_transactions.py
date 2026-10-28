import json
from pathlib import Path
import uuid
import pytest
from image_caption_gender_fixer import transactions
from image_caption_gender_fixer.transactions import Transactions
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.fs import sha256,available,source_lease,folder_lock,recycle
from image_caption_gender_fixer.errors import IntegrityError,UnsafeFilesystem,RecoverableFailure


def prepared(tmp_path):
    root=tmp_path/"tool";root.mkdir()
    folder=tmp_path/"images";folder.mkdir()
    source=folder/"original.jpg";source.write_bytes(b"original image bytes\0"*512)
    tx=str(uuid.uuid4());stage=folder/(".icgf-"+tx+"-proposal.jpg");stage.write_bytes(b"corrected image bytes"*256)
    return root,folder,source,stage,tx


def test_real_windows_commit_and_undo_restores_exact_bytes(tmp_path):
    root,folder,source,stage,tx=prepared(tmp_path)
    expected=sha256(source)
    event=Transactions(root).commit(source,stage,expected,tx,"rules","default",[])
    assert not source.exists() and (folder/event["corrected"]).exists()
    assert sha256(folder/event["backup"])==expected
    result=Transactions(root).undo(folder,event)
    assert sha256(source)==expected and Path(result["archive_path"]).exists()
    assert History(folder).recognize(expected)[0]=="previously_undone"


def test_output_collision_preserves_both(tmp_path):
    root,folder,source,stage,tx=prepared(tmp_path)
    occupied=folder/"original-genderfixed.jpg";occupied.write_bytes(b"unrelated")
    event=Transactions(root).commit(source,stage,sha256(source),tx,"rules","default",[])
    assert occupied.read_bytes()==b"unrelated" and event["corrected"]=="original-genderfixed (1).jpg"


def test_changed_source_refused(tmp_path):
    root,folder,source,stage,tx=prepared(tmp_path);expected=sha256(source);source.write_bytes(b"changed")
    with pytest.raises(IntegrityError): Transactions(root).commit(source,stage,expected,tx,"rules","default",[])
    assert source.read_bytes()==b"changed" and stage.exists()


def test_history_commit_failure_rolls_back_original(tmp_path,monkeypatch):
    root,folder,source,stage,tx=prepared(tmp_path);expected=sha256(source)
    def fail(*a,**k): raise OSError("injected history append failure")
    monkeypatch.setattr(History,"append",fail)
    with pytest.raises(OSError): Transactions(root).commit(source,stage,expected,tx,"rules","default",[])
    assert sha256(source)==expected and stage.exists()


def test_occupied_original_refuses_undo(tmp_path):
    root,folder,source,stage,tx=prepared(tmp_path);engine=Transactions(root)
    event=engine.commit(source,stage,sha256(source),tx,"rules","default",[])
    source.write_bytes(b"new user file")
    with pytest.raises(UnsafeFilesystem): engine.undo(folder,event)
    assert source.read_bytes()==b"new user file"


def test_modified_corrected_archive_flagged_and_retained(tmp_path):
    root,folder,source,stage,tx=prepared(tmp_path);engine=Transactions(root)
    event=engine.commit(source,stage,sha256(source),tx,"rules","default",[])
    (folder/event["corrected"]).write_bytes(b"user edited corrected")
    result=engine.undo(folder,event)
    assert result["changed_corrected"] and Path(result["archive_path"]).read_bytes()==b"user edited corrected"


def test_folder_lock_contention_is_real_windows_lock(tmp_path):
    with folder_lock(tmp_path):
        with pytest.raises(UnsafeFilesystem):
            with folder_lock(tmp_path): pass


def test_windows_recycle_generated_disposable_file(tmp_path):
    path=tmp_path/"explicitly-disposable-recycle-test.txt";path.write_text("generated test only")
    recycle(path)
    assert not path.exists()


def test_available_names_number_before_final_extension(tmp_path):
    path=tmp_path/"image.jpg.bak";path.write_text("one")
    (tmp_path/"image.jpg (1).bak").write_text("two")
    assert available(path).name=="image.jpg (2).bak"
