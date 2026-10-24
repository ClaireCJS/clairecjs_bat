import uuid
from image_caption_gender_fixer.sessions import Sessions
from image_caption_gender_fixer.fs import sha256
from test_recovery import interrupted


def test_partial_atomic_state_staging_does_not_hide_recoverable_journal(tmp_path):
    engine,record,source,stage,backup,corrected=interrupted(tmp_path,1)
    orphan=engine.directory/(".icgf-state-"+str(uuid.uuid4())+".json")
    orphan.write_text('{"partial":',encoding="utf-8")
    engine.recover()
    assert sha256(source)==record["original_hash"] and not backup.exists() and orphan.exists()
    sessions=Sessions(engine.root)
    session=sessions.create([source],"default")
    partial=sessions.directory/(".icgf-state-"+str(uuid.uuid4())+".json")
    partial.write_text('{"partial":',encoding="utf-8")
    assert [s["id"] for s in sessions.unfinished()]==[session["id"]] and not sessions.issues
    assert partial.exists()
