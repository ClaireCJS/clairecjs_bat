from pathlib import Path
import uuid
import pytest
from image_caption_gender_fixer.transactions import Transactions
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.fs import sha256,move,backup_name,available,now
from image_caption_gender_fixer.errors import RecoverableFailure,IntegrityError


def interrupted(tmp_path,step):
    folder=tmp_path/"images";folder.mkdir()
    root=tmp_path/"tool";root.mkdir()
    tx=str(uuid.uuid4())
    source=folder/"original.png";source.write_bytes(b"generated original"*100)
    stage=folder/(".icgf-"+tx+"-proposal.png");stage.write_bytes(b"generated corrected"*100)
    backup=available(backup_name(source));corrected=folder/"original-gendeerfixed.png"
    record={"operation":"convert","transaction":tx,"folder":str(folder),"original":source.name,
            "stage":stage.name,"backup":backup.name,"corrected":corrected.name,"original_hash":sha256(source),
            "corrected_hash":sha256(stage),"rules_fingerprint":"r","profile":"default","program_version":"test"}
    engine=Transactions(root);engine.save(record,"prepared")
    if step>=1: move(source,backup)
    if step>=2: move(stage,corrected)
    if step>=3: History(folder).append("committed",**engine.event_values(record))
    return engine,record,source,stage,backup,corrected


@pytest.mark.parametrize("step",[0,1,2])
def test_real_recovery_rolls_back_each_uncommitted_boundary(tmp_path,step):
    engine,record,source,stage,backup,corrected=interrupted(tmp_path,step)
    engine.recover()
    assert source.exists() and sha256(source)==record["original_hash"]
    assert not backup.exists() and not corrected.exists() and stage.exists()
    assert engine.pending()==[] and engine.recover()==[]


def test_recovery_reconciles_committed_history_without_rollback(tmp_path):
    engine,record,source,stage,backup,corrected=interrupted(tmp_path,3)
    engine.recover()
    assert not source.exists() and corrected.exists() and backup.exists()
    assert engine.pending()==[]
    assert len(History(source.parent).records)==2


def test_recovery_preserves_occupied_original_and_backup(tmp_path):
    engine,record,source,stage,backup,corrected=interrupted(tmp_path,1)
    source.write_bytes(b"unrelated new user file")
    with pytest.raises(RecoverableFailure): engine.recover()
    assert source.read_bytes()==b"unrelated new user file" and sha256(backup)==record["original_hash"]


def test_partial_history_tail_blocks_recovery_without_losing_originals(tmp_path):
    engine,record,source,stage,backup,corrected=interrupted(tmp_path,3)
    history=History(source.parent)
    with history.path.open("ab") as f: f.write(b'{"incomplete":')
    with pytest.raises(IntegrityError): engine.recover()
    assert sha256(backup)==record["original_hash"] and corrected.exists()


def test_acknowledged_write_failure_after_visible_history_retains_published_files(tmp_path,monkeypatch):
    engine,record,source,stage,backup,corrected=interrupted(tmp_path,0)
    original=History.append
    def after_append(self,*a,**kw):
        original(self,*a,**kw)
        raise OSError("injected flush acknowledgement failure")
    monkeypatch.setattr(History,"append",after_append)
    with pytest.raises(RecoverableFailure):
        engine.commit(source,stage,record["original_hash"],record["transaction"],"r","default",[])
    assert not source.exists() and corrected.exists() and backup.exists()
