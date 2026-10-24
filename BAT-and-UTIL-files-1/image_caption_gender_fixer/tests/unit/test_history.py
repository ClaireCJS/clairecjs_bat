import ctypes
import json
import uuid
import pytest
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.errors import IntegrityError


def record():
    return dict(transaction=str(uuid.uuid4()),original="photo.jpg",corrected="photo-gendeerfixed.jpg",backup="photo.jpg.bak.202610231200.replaced-by-chatgpt.bak",original_hash="a"*64,corrected_hash="b"*64,rules_fingerprint="c"*64)


def test_no_history_merely_for_inspection(tmp_path):
    assert History(tmp_path).records==[]
    assert list(tmp_path.iterdir())==[]


def test_hidden_relative_history_survives_folder_rename(tmp_path):
    folder=tmp_path/"before";folder.mkdir()
    entry=record();History(folder).append("committed",**entry)
    assert ctypes.windll.kernel32.GetFileAttributesW(str(folder/".history.icgf"))&2
    renamed=tmp_path/"renamed";folder.rename(renamed)
    known,event=History(renamed).recognize("a"*64)
    assert known=="known_original" and event["transaction"]==entry["transaction"]
    assert "before" not in (renamed/".history.icgf").read_text()


def test_idempotent_append_and_undo(tmp_path):
    event=record();history=History(tmp_path)
    history.append("committed",**event);history.append("committed",**event)
    assert len(history.records)==2
    history.append("undone",**event,archive="kept.bak")
    assert History(tmp_path).recognize("a"*64)[0]=="previously_undone"
    assert History(tmp_path).recognize("b"*64)[0]=="known_corrected"


@pytest.mark.parametrize("damage",[b'{"partial":',b"nonsense\n"])
def test_partial_or_corrupt_tail_keeps_prefix_but_refuses_mutation(tmp_path,damage):
    history=History(tmp_path);entry=record();history.append("committed",**entry)
    with history.path.open("ab") as f: f.write(damage)
    loaded=History(tmp_path)
    assert len(loaded.records)==2 and loaded.tail_error
    with pytest.raises(IntegrityError): loaded.append("undone",**entry)


def test_reordered_duplicate_and_changed_records_detected(tmp_path):
    history=History(tmp_path);history.append("committed",**record())
    lines=history.path.read_bytes().splitlines(keepends=True)
    with history.path.open("r+b") as damaged:
        damaged.write(b"".join(reversed(lines)))
        damaged.truncate()
    assert History(tmp_path).tail_error


def test_unrelated_canonical_file_preserved(tmp_path):
    path=tmp_path/".history.icgf";path.write_text("user data\n")
    with pytest.raises(IntegrityError): History(tmp_path).append("committed",**record())
    assert path.read_text()=="user data\n"
