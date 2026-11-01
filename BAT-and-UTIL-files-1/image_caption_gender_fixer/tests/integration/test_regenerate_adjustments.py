"""Regeneration retains per-region visual choices and rendered appearance."""
from copy import deepcopy
from pathlib import Path
import pytest
from PIL import Image
import numpy as np
from image_caption_gender_fixer import imaging
from image_caption_gender_fixer.caption_editor import caption_regions,preserve_adjustments
from image_caption_gender_fixer.cli import adjust
from image_caption_gender_fixer.errors import IntegrityError
from image_caption_gender_fixer.rules import Rule
from image_caption_gender_fixer.fs import sha256
from test_images import app_for,make_image


def line(text,y=10):
    words=[];offset=0;x=10
    for text_word in text.split(' '):
        width=len(text_word)*12
        words.append(imaging.Word(text_word,(x,y,x+width,y+25),99,offset,offset+len(text_word)))
        offset+=len(text_word)+1;x+=width+12
    return {'text':text,'words':words}


def initial(lines):
    return imaging.regions(lines,[Rule('boy','girl',id='boy'),Rule('man','woman',id='man')])[0]


def test_noop_regenerate_keeps_geometry_nested_settings_trace_and_skips():
    lines=[line('man greets boy')];previous=initial(lines)
    previous[0].settings={'box':(1,2,70,30),'dx':4,'scale':.7,'font':'chosen.ttf',
        'mask_sides':{'left':3},'protected':[(200,20,250,50)],'repair':'telea',
        'move_squeeze':True,'fit_retry':2,'foreground':(1,2,3,255)}
    previous[1].skipped=True
    text=imaging.full_captions(lines,previous)['proposed'];snapshot=deepcopy(previous)
    rebuilt,_=caption_regions(lines,text,previous)
    assert rebuilt==snapshot and rebuilt is not previous and rebuilt[0] is not previous[0]
    rebuilt[0].settings['mask_sides']['left']=99;rebuilt[0].settings['protected'].append((1,1,2,2))
    assert previous==snapshot


def test_edit_keeps_independent_styles_on_the_same_line_and_original_word_boxes():
    lines=[line('man greets boy')];previous=initial(lines)
    previous[0].settings={'dx':12,'foreground':(10,20,30,255)}
    previous[1].settings={'scale':.8,'repair':'gradient','mask_sides':{'right':2}}
    rebuilt,_=caption_regions(lines,'lady greets friend',previous)
    assert imaging.full_captions(lines,rebuilt)['proposed']=='lady greets friend'
    assert len(rebuilt)==2
    assert [r.settings for r in rebuilt]==[r.settings for r in previous]
    assert [r.box for r in rebuilt]==[r.box for r in previous]
    assert [r.after for r in rebuilt]==['lady','friend']


@pytest.mark.parametrize('text',[
    'kind friend','kind girl today','very kind girl','kind girl!',
    'kind lovely friend today','kind','girl','a friend','kind, girl',
    'a completely rewritten caption','kind girl\nwith friends',
])
def test_caption_edits_preserve_settings_without_dropping_words(text):
    lines=[line('kind boy')];previous=initial(lines)
    previous[0].settings={'dx':7,'scale':.85,'rotation':2,'repair':'navier','mask_sides':{'up':4}}
    rebuilt,_=caption_regions(lines,text,previous)
    assert imaging.full_captions(lines,rebuilt)['proposed']==' '.join(text.splitlines())
    assert any(r.settings==previous[0].settings for r in rebuilt)


def test_adjustments_do_not_leak_across_lines_and_can_be_reset():
    lines=[line('kind boy'),line('kind boy',60)];previous=initial(lines)
    previous[0].settings={'scale':.7};previous[1].settings={'dx':15}
    rebuilt,_=caption_regions(lines,'kind friend\nkind pal',previous)
    assert [r.settings for r in rebuilt]==[{'scale':.7},{'dx':15}]
    adjust(rebuilt[0],'reset',(500,150))
    repeated,_=caption_regions(lines,'kind friend\nkind companion',rebuilt)
    assert repeated[0].settings=={} and repeated[1].settings=={'dx':15}


def test_rule_rebuild_copies_existing_settings_and_leaves_new_unrelated_rule_unstyled():
    lines=[line('kind boy greets friends')];previous=initial(lines)
    previous[0].settings={'foreground':(0,128,255,255),'mask_sides':{'right':2}}
    new,_=imaging.regions(lines,[Rule('boy','lady'),Rule('friends','neighbors')])
    rebuilt=preserve_adjustments(new,previous)
    assert rebuilt[0].settings==previous[0].settings and rebuilt[1].settings=={}
    rebuilt[0].settings['mask_sides']['right']=8
    assert previous[0].settings['mask_sides']['right']==2 and not new[0].settings


def test_conflicting_adjustments_are_not_silently_replaced_when_text_is_merged():
    lines=[line('man boy')];previous=initial(lines)
    previous[0].settings={'dx':4};previous[1].settings={'dx':20};saved=deepcopy(previous)
    new,_=imaging.regions(lines,[Rule('man boy','person')])
    with pytest.raises(IntegrityError,match='different visual adjustments'):
        preserve_adjustments(new,previous)
    assert previous==saved


def test_adjust_menu_then_caption_repair_and_rule_regeneration_keeps_rendered_color(tmp_path,monkeypatch):
    source=tmp_path/'neutral.png';make_image(source,'kind boy');original=sha256(source)
    app=app_for(tmp_path,answers=iter(['m','18,3','c','#0088ff','s']))
    seen=[];last_pixels=[];expected={'dx':18,'dy':3,'foreground':(0,136,255,255),'scale':.95}
    def review(path,proposal,regions):
        assert not proposal.get('blocked') and sha256(source)==original
        seen.append((proposal['transaction'],deepcopy(regions)))
        number=len(seen)
        if number<=3:return 'v'
        assert all(regions[0].settings[k]==v for k,v in expected.items())
        if number==4:return {'action':'edit_caption','text':'kind friend'}
        if number==5:return {'action':'repair_mode','mode':'gradient','source':str(path),'text':'kind friend today'}
        if number==6:return {'action':'add_rule','payload':{'before':'today','after':'tomorrow','priority':200}}
        assert regions[0].settings['repair']=='gradient'
        if number==7:
            last_pixels.append(np.array(Image.open(proposal['stage']).convert('RGB')))
            return {'action':'edit_caption','text':'kind friend tomorrow'}
        assert number==8 and imaging.full_captions(app.caption_lines,regions)['proposed']=='kind friend tomorrow'
        pixels=np.array(Image.open(proposal['stage']).convert('RGB'))
        assert np.array_equal(last_pixels[0],pixels)
        assert np.count_nonzero((pixels[:,:,0]<30)&(pixels[:,:,1]>100)&(pixels[:,:,1]<165)&(pixels[:,:,2]>225))>200
        assert proposal['diagnostics'][0]['repair']=='gradient'
        return 'a'
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert code==0 and len(seen)==8 and len({t for t,_ in seen})==8
    assert Path(result['results'][0]['corrected']).is_file()


def test_rule_regeneration_before_manual_caption_keeps_adjustment(tmp_path,monkeypatch):
    source=tmp_path/'neutral.png';make_image(source,'kind boy')
    app=app_for(tmp_path,answers=iter(['m','8,2']));seen=[]
    def review(path,proposal,regions):
        seen.append(deepcopy(regions))
        if len(seen)==1:return 'v'
        if len(seen)==2:return {'action':'add_rule','payload':{'before':'boy','after':'friend','priority':200}}
        assert regions[0].after=='friend' and regions[0].settings=={'dx':8,'dy':2}
        return 's'
    monkeypatch.setattr(app,'review',review)
    _,code=app.process([str(source)])
    assert code==10 and len(seen)==3


def test_next_image_starts_with_its_own_settings(tmp_path,monkeypatch):
    first=tmp_path/'first.png';second=tmp_path/'second.png'
    make_image(first,'kind boy');make_image(second,'friendly boy')
    app=app_for(tmp_path,answers=iter(['s']));seen=[]
    def review(path,proposal,regions):
        seen.append(path)
        if len(seen)==1:return 'v'
        if len(seen)==2:
            assert regions[0].settings=={'scale':.95}
            return {'action':'edit_caption','text':imaging.full_captions(app.caption_lines,regions)['proposed']}
        if len(seen)==3:
            assert regions[0].settings=={'scale':.95};return 's'
        assert path==second and not regions[0].settings
        return 's'
    monkeypatch.setattr(app,'review',review)
    _,code=app.process([str(first),str(second)])
    assert code==10 and seen==[first,first,first,second]


def test_rule_that_would_merge_conflicting_styles_is_refused_before_saving(tmp_path,monkeypatch,capsys):
    source=tmp_path/'neutral.png';make_image(source,'man boy')
    app=app_for(tmp_path,answers=iter([]));seen=[]
    def review(path,proposal,regions):
        seen.append(deepcopy(regions))
        if len(seen)==1:
            assert len(regions)==2
            regions[0].settings={'scale':.9};regions[1].settings={'scale':.8}
            return {'action':'add_rule','payload':{'before':'man boy','after':'person','priority':600}}
        assert [r.settings for r in regions]==[{'scale':.9},{'scale':.8}]
        return 's'
    monkeypatch.setattr(app,'review',review)
    _,code=app.process([str(source)])
    assert code==10 and len(seen)==2
    assert not (tmp_path/'.image-gender-fixer.stt').exists()
    assert 'different visual adjustments' in capsys.readouterr().err
