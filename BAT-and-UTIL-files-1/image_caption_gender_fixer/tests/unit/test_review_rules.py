from dataclasses import replace
import pytest
from image_caption_gender_fixer.rules import Rule,RuleStore,builtins,transform
from image_caption_gender_fixer.rule_editor import validate_payload,move_rule,ordered
from image_caption_gender_fixer.caption_editor import caption_regions
from image_caption_gender_fixer.imaging import Word,full_captions
from image_caption_gender_fixer.presentation import comparison,prompt,Initializing

@pytest.mark.parametrize('text',['real man','Real man','REAL MAN','rEaL mAn'])
def test_identity_rule_reserves_original_span_and_preserves_case(text):
    r=transform(text+' and man with his wife',builtins())
    assert r['final']==text+' and woman with her wife'
    assert not any(e['start']<len(text) for e in r['edits'])

def test_same_priority_identity_wins_longest_and_no_repeated_state_error():
    rules=[Rule('Real man','real man',10,id='protect'),Rule('man','woman',10,id='inner')]
    assert transform('Real man and man',rules)['final']=='Real man and woman'

def test_saved_rule_and_priority_order_are_one_append_and_reload(tmp_path):
    payload={'before':'queen','after':'leader','priority':150}
    result,new=validate_payload(payload,builtins(),'work')
    result,index=move_rule(result,next(i for i,r in enumerate(result) if r.id==new.id),1)
    new=next(r for r in result if r.id==new.id)
    store=RuleStore(tmp_path/'.image-gender-fixer.stt');store.save_order(result,new,'work')
    assert len(store.path.read_text().splitlines())==1
    loaded=store.load('work');assert loaded[0].priority==new.priority
    assert store.priorities['builtin-0']==next(r.priority for r in result if r.id=='builtin-0')
    assert not store.load('default') and not store.priorities

def test_edited_caption_reuses_geometry_and_full_text_is_already_available():
    lines=[{'text':s,'words':[Word(s,(10,10+i*40,230,40+i*40),96,0,len(s))]} for i,s in enumerate(['Hello good boy','Another sentence'])]
    regions,protected=caption_regions(lines,'Hello good friend\nAnother sentence')
    assert len(regions)==1 and regions[0].box==lines[0]['words'][0].box
    assert full_captions(lines,regions)['proposed']=='Hello good friend\nAnother sentence'
    assert len(protected)==2

def test_caption_line_insertions_are_mapped_without_retyping_or_losing_words():
    lines=[{'text':'Hello there','words':[Word('Hello there',(0,0,100,20),99,0,11)]}]
    regions,_=caption_regions(lines,'Hello\nmy dear friend')
    assert regions[0].after=='Hello my dear friend'

def test_side_by_side_uses_color_and_stays_within_width():
    import re
    output=comparison('Old line\nsame','New line\nsame',width=100,enabled=True)
    assert '\x1b[92m' in output and '\x1b[93m' in output
    assert all(len(re.sub(r'\x1b\[[0-9;]*m','',s))<=100 for s in output.splitlines())
    assert 'ENTER=skip' in prompt('[s]kip: ','s')


def test_startup_status_replaces_one_line_and_clear_leaves_no_ansi_in_nonterminal(monkeypatch):
    import io,os
    from image_caption_gender_fixer import presentation
    stream=io.StringIO();monkeypatch.setattr(presentation.sys,'stderr',stream)
    monkeypatch.setattr(presentation.shutil,'get_terminal_size',lambda *a,**k:os.terminal_size((70,25)))
    status=Initializing(True);status.update('Loading packages');status.update('Hashing source images 4/50');status.clear()
    output=stream.getvalue();assert output.count('\r\x1b[2K')==3 and '\n' not in output and not status.visible
    stream.seek(0);stream.truncate();quiet=Initializing(False);quiet.update('silent');quiet.clear();assert stream.getvalue()==''


def test_his_wife_preserves_each_words_capitalization():
    assert transform('His wife and HIS WIFE',builtins())['final']=='Her wife and HER WIFE'
