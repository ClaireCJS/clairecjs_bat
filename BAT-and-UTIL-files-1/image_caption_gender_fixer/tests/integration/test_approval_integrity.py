from pathlib import Path
import pytest
from image_caption_gender_fixer.transactions import Transactions
from image_caption_gender_fixer.errors import IntegrityError
from image_caption_gender_fixer.fs import sha256, identity
from test_transactions import prepared


def test_changed_approved_stage_is_refused_before_any_original_rename(tmp_path):
    root,folder,source,stage,tx=prepared(tmp_path)
    expected=sha256(stage);original=sha256(source)
    stage.write_bytes(b"generated alteration after approval")
    with pytest.raises(IntegrityError,match="staging output changed"):
        Transactions(root).commit(source,stage,original,tx,"rules","default",[],expected_identity=identity(source),expected_stage_hash=expected)
    assert sha256(source)==original and not(folder/".history.icgf").exists()


def test_identical_content_with_changed_source_identity_is_refused(tmp_path):
    root,folder,source,stage,tx=prepared(tmp_path)
    original=source.read_bytes();expected=identity(source)
    preserved=source.with_name("preserved-original.jpg")
    source.rename(preserved)
    source.write_bytes(original)
    with pytest.raises(IntegrityError,match="Source identity"):
        Transactions(root).commit(source,stage,sha256(source),tx,"rules","default",[],expected_identity=expected)
    assert source.read_bytes()==preserved.read_bytes()==original and stage.exists()
