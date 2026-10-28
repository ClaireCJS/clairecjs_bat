import pytest
from image_caption_gender_fixer.rules import Rule,RuleStore,builtins,transform,reject_cycles
from image_caption_gender_fixer.errors import IntegrityError


@pytest.mark.parametrize("source,expected",[("boi","girl"),("good boi","good girl"),("good boy","good girl"),("man","woman"),("husband","wife"),("woman","woman"),("BOI","GIRL"),("Boi","Girl"),("a good boy!","a good girl!"),("human manpower","human manpower")])
def test_seeded_cascade(source,expected):
    assert transform(source,builtins())["final"]==expected


def test_cascade_provenance_and_phrase_precedence():
    result=transform("good boi",builtins())
    assert [t["rule"] for t in result["trace"]]==["builtin-0","builtin-1"]
    assert result["edits"]==[{"start":0,"end":8,"before":"good boi","after":"good girl"}]
    assert any(s["rule"]=="builtin-2" for s in result["shadowed"])


def test_generated_text_not_reprocessed_at_same_priority():
    result=transform("cat",[Rule("cat","dog",10,id="a"),Rule("dog","wolf",10,id="b")])
    assert result["final"]=="dog"


def test_literal_precedes_regex_and_folder_precedes_default():
    rules=[Rule("boy","A",10,id="regex",mode="regex"),Rule("boy","B",10,id="literal"),Rule("boy","C",10,id="folder",scope="folder",user=True)]
    assert transform("boy",rules)["final"]=="C"


def test_leftmost_overlap():
    rules=[Rule("a b","x",10,id="a"),Rule("b c","y",10,id="b")]
    assert transform("a b c",rules)["final"]=="x c"


def test_casefold_unicode_and_punctuation():
    assert transform("STRASSE",[Rule("straße","weg",id="unicode")])["final"]=="WEG"
    assert transform("good, boy",[Rule("good boy","friend",id="punct",punctuation="flex")])["final"]=="friend"


@pytest.mark.parametrize("rules",[[Rule("a","b"),Rule("b","a")],[Rule("a","b"),Rule("b","c"),Rule("c","a")]])
def test_cycle_rejected(rules):
    with pytest.raises(IntegrityError): reject_cycles(rules)


def test_regex_is_bounded():
    with pytest.raises(IntegrityError): transform("a"*100000+"!",[Rule("(a+)+$","x",mode="regex",id="bad")])


def test_ignored_phrase_and_occurrence():
    assert transform("boy boy",builtins(),[{"phrase":"boy"}])["final"]=="boy boy"
    assert transform("boy boy",builtins(),[{"occurrence":[0,3]}])["final"]=="boy girl"


def test_rule_store_reports_bad_record_and_keeps_valid(tmp_path):
    path=tmp_path/".image-gender-fixer.stt"
    store=RuleStore(path)
    rule=store.add("king","queen",20)
    with path.open("a") as out: out.write("{bad json}\n")
    loaded=store.load()
    assert loaded[0].id==rule.id and store.warnings
    store.append("disable",id=rule.id)
    assert not store.load()[0].enabled


def test_profiles(tmp_path):
    store=RuleStore(tmp_path/".image-gender-fixer.stt")
    store.add("king","queen",profile="custom")
    assert not store.load("default")
    assert store.load("custom")[0].after=="queen"
