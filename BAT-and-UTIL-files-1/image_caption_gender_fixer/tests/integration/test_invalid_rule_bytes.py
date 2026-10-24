from image_caption_gender_fixer.rules import RuleStore


def test_invalid_utf8_record_is_quarantined_without_losing_valid_rules(tmp_path):
    store=RuleStore(tmp_path/".image-gender-fixer.stt")
    first=store.add("king","queen")
    with store.path.open("ab") as output: output.write(b"\xff\xfe\n")
    assert [r.id for r in store.load()]==[first.id] and store.warnings
    second=store.add("duke","duchess")
    assert {r.id for r in store.load()}=={first.id,second.id} and len(store.warnings)==1
