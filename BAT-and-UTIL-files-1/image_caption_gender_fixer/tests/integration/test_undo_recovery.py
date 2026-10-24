import json
from pathlib import Path
import pytest
from image_caption_gender_fixer import cli
from image_caption_gender_fixer.fs import archive_name, available, move, sha256
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.transactions import Transactions
from image_caption_gender_fixer.errors import RecoverableFailure
from test_transactions import prepared


@pytest.mark.parametrize("boundary",["prepared","archived","restored","history"])
def test_real_undo_recovery_at_each_durable_boundary(tmp_path,boundary):
    root,folder,source,stage,tx=prepared(tmp_path)
    engine=Transactions(root)
    original=sha256(source)
    event=engine.commit(source,stage,original,tx,"rules","default",[])
    corrected=folder/event["corrected"];backup=folder/event["backup"]
    archive=available(archive_name(corrected))
    record=dict(engine.event_values(event),operation="undo",folder=str(folder),
                archive=archive.name,archive_hash=sha256(corrected),changed_corrected=False)
    engine.save(record,"undo_prepared")
    if boundary in ("archived","restored","history"):
        move(corrected,archive)
    if boundary in ("restored","history"):
        move(backup,source)
    if boundary=="history":
        History(folder).append("undone",**engine.event_values(record),archive=archive.name,
                               archive_hash=record["archive_hash"],changed_corrected=False)
    engine.recover()
    assert not engine.pending() and engine.recover()==[]
    if boundary in ("prepared","archived"):
        assert not source.exists() and backup.exists() and corrected.exists() and not archive.exists()
        assert sha256(backup)==original
        assert History(folder).transactions()[tx]["event"]=="committed"
    else:
        assert sha256(source)==original and archive.exists() and not backup.exists()
        assert History(folder).transactions()[tx]["event"]=="undone"


def test_explicit_backup_preserves_even_a_corrupt_history_tail(tmp_path,capsys):
    root,folder,source,stage,tx=prepared(tmp_path)
    engine=Transactions(root)
    engine.commit(source,stage,sha256(source),tx,"rules","default",[])
    history=folder/".history.icgf"
    with history.open("ab") as output: output.write(b'{"partial":')
    original=history.read_bytes()
    assert cli.main(root,["history","backup",str(folder),"--json"])==0
    report=json.loads(capsys.readouterr().out)
    assert Path(report["path"]).read_bytes()==original and history.read_bytes()==original
