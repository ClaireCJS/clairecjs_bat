import math
import pytest
from image_caption_gender_fixer.rules import Rule,builtins,transform,RuleStore
from image_caption_gender_fixer.newspaper_columns import newspaper,compare_columns,display_width,ANSI

CASES=[('another man','a man',400),('my hubby','my wife',300),('he has no idea','she has no idea',300),
       ('not with his cock','not with her cock',300),('hubby','wifey',6),('not with his','not with her',150),
       ('tease him','tease her',150),('tying him','tying her',150),('his little','her little',150),('keep him','keep her',150)]

@pytest.mark.parametrize('before,after,priority',CASES)
def test_requested_rule_and_priority(before,after,priority):
    rules=builtins();rule=next(r for r in rules if r.before==before)
    assert rule.after==after and rule.priority==priority
    assert transform(before,rules)['final']==after
    assert transform(before.upper(),rules)['final']==after.upper()

def test_another_man_is_terminal_but_nearby_man_still_changes():
    result=transform('Another man and man near a real man.',builtins())
    assert result['final']=='A man and woman near a real man.'
    assert result['edits'][0]['before']=='Another man' and result['edits'][0]['after']=='A man'
    assert not any(t['before']=='a man' for t in result['trace'])

@pytest.mark.parametrize('phrase',['real man','Real man','REAL MAN','rEaL mAn'])
def test_whitelist_preserves_case_and_blocks_lower_inner_rule(phrase):
    assert transform(phrase+'...',builtins())['final']==phrase+'...'
    assert transform(phrase,builtins())['edits']==[]

def test_protection_survives_rule_store_and_asdict_roundtrip(tmp_path):
    from dataclasses import asdict
    rule=Rule('another man','a man',400,id='custom',protect=True)
    store=RuleStore(tmp_path/'rules.stt');store.append('rule',rule=asdict(rule))
    assert store.load()[0].protect
    assert transform('another man',store.load()+[Rule('man','woman',10,id='lower')])['final']=='a man'
    with pytest.raises(Exception):Rule('a','b',protect=1).validate()

def test_existing_builtin_ids_and_cascade_stay_stable():
    assert [(r.id,r.before) for r in builtins()[:7]]==[(f'builtin-{i}',p) for i,p in enumerate(['boi','good boy','boy','man','husband','real man','his wife'])]
    assert transform('good boi and my hubby',builtins())['final']=='good girl and my wife'

@pytest.mark.parametrize('width',[8,40,80,120,240])
def test_newspaper_keeps_all_lines_in_down_then_across_order(width):
    lines=[f'L{i:02}' for i in range(60)]
    rows=newspaper('\n'.join(lines),width=width,height=12)
    assert all(display_width(row)<=width for row in rows)
    cells=[row.split('  │  ') for row in rows]
    reconstructed=[]
    for col in range(max(len(row) for row in cells)):
        reconstructed.extend(row[col].strip() for row in cells if col<len(row) and row[col].strip())
    assert reconstructed==lines
    if width>=120:assert len(rows)<=12

@pytest.mark.parametrize('width',[40,80,120,240])
def test_comparison_keeps_corresponding_sentences_colored_and_bounded(width):
    old='\n'.join('Old sentence '+str(i) for i in range(50))
    new='\n'.join('New sentence '+str(i) for i in range(50))
    text=compare_columns(old,new,width=width,height=15,enabled=True)
    assert '\x1b[92m' in text and '\x1b[93m' in text
    assert all(display_width(row)<=width for row in text.splitlines())
    assert all(('Old sentence '+str(i)) in text and ('New sentence '+str(i)) in text for i in range(50))
    if width>=120:assert '  │  ' in text

def test_wide_combining_unicode_and_control_text_are_safe():
    text='界界 cafe\u0301 '+('word '*30)+'\x1b[2J\rEND'
    rows=newspaper(text,width=40,height=10)
    assert all(display_width(row)<=40 for row in rows)
    assert '\x1b' not in '\n'.join(rows) and '\\x1b[2J\\x0dEND' in '\n'.join(rows)
    assert display_width('界e\u0301')==3
