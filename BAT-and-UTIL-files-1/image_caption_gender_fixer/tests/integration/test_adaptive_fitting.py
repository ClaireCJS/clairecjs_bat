"""Previously exhausted fits succeed through measured parameter selection."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import pytest
from PIL import Image,ImageDraw,ImageFont
from image_caption_gender_fixer import imaging,smart_fitting,fit_search
from image_caption_gender_fixer.errors import RenderBlocked
from image_caption_gender_fixer.fs import sha256
from test_images import app_for

FONT=r'C:\Windows\Fonts\arial.ttf'


@pytest.fixture
def style(monkeypatch):
    monkeypatch.setattr(imaging,'estimate',lambda *args:dict(foreground=(0,0,0,255),background=(255,255,255),
        background_alpha=255,texture=0,font=FONT,size=24,font_score=1,font_candidates=[]))
    monkeypatch.setattr('image_caption_gender_fixer.ocr_quality.panels',lambda image:[])
    return ImageFont.truetype(FONT,24)


def isolated_word(font,settings=None):
    image=Image.new('RGBA',(100,140),'white');box=(20,60,60,88)
    ImageDraw.Draw(image).text((20,55),'cat',font=font,fill='black')
    word=imaging.Word('cat',box,99,0,3)
    region=imaging.Region('cat','sleepy kittens',box,99,[word],[],settings=deepcopy(settings or {}),line_index=0,ocr_span=(0,3))
    return image,[dict(text='cat',words=[word])],region,[box]


def full_context(font):
    text='one two cat four five six seven eight nine'
    image=Image.new('RGBA',(800,140),'white');draw=ImageDraw.Draw(image);words=[];offset=0;x=20
    for token in text.split():
        width=round(draw.textlength(token,font=font));box=(x,60,x+width,88)
        words.append(imaging.Word(token,box,99,offset,offset+len(token)))
        draw.text((x,55),token,font=font,fill='black');offset+=len(token)+1;x+=width+6
    word=words[2]
    region=imaging.Region('cat','a tremendously long sequence of replacement wording',word.box,99,[word],[],
        line_index=0,ocr_span=(word.start,word.end))
    return image,[dict(text=text,words=words)],region,[w.box for w in words]


def blocked_old_passes(image,lines,region,protected):
    for level in (1,2):
        candidate=replace(region,settings=dict(region.settings,move_squeeze=True,fit_retry=level))
        with pytest.raises(RenderBlocked,match='cannot fit safely'):
            imaging._render_fitting_pass(image,candidate,protected,lines,[region])


@pytest.mark.parametrize('settings',[{}, {'dy':25}, {'foreground':(0,128,255,255),'tracking':0,'font':FONT}])
def test_measured_width_uses_nearby_caption_space_when_all_fixed_passes_fail(style,settings):
    image,lines,region,protected=isolated_word(style,settings);before=image.tobytes();saved=deepcopy(region)
    blocked_old_passes(image,lines,region,protected)
    result,rendered,blocked=smart_fitting.render_plan(image,[region],protected,lines)
    assert blocked is None and len(rendered)==1
    diagnostic=rendered[0][1];fit=diagnostic['adaptive_parameters']
    assert fit and diagnostic['automatic_fit'] and diagnostic['level']>=2
    assert diagnostic['text_bounds'][2]-diagnostic['text_bounds'][0]>region.box[2]-region.box[0]
    assert diagnostic['horizontal_scale']>=fit_search.MIN_WIDTH
    assert fit['variants']<=fit_search.MAX_TRIALS
    lane=imaging.caption_lane(image,region,lines);a,b,c,d=diagnostic['text_bounds']
    assert lane[0]<=a<c<=lane[2] and lane[1]<=b<d<=lane[3]
    assert region==saved and image.tobytes()==before and result.tobytes()!=before
    if 'font' in settings:assert fit['font']==settings['font'] and fit['tracking']==settings['tracking']


def test_full_line_context_is_tried_without_moving_one_word_to_another_row(style):
    image,lines,region,protected=full_context(style);original=deepcopy(region)
    blocked_old_passes(image,lines,region,protected)
    result,rendered,blocked=smart_fitting.render_plan(image,[region],protected,lines)
    assert blocked is None
    diagnostic=rendered[0][1];context=diagnostic['fit_context']
    assert context['words_per_side']>2 and context['before']==lines[0]['text']
    assert context['after']=='one two a tremendously long sequence of replacement wording four five six seven eight nine'
    assert diagnostic['text_bounds'][1]>=56 and diagnostic['text_bounds'][3]<=92
    assert imaging.full_captions(lines,[region])['proposed']==context['after'] and region==original


def test_vertical_alignment_uses_free_space_inside_tall_ocr_box(style):
    image=Image.new('RGBA',(160,120),'white');draw=ImageDraw.Draw(image)
    protected_logo=(0,0,160,48);draw.rectangle((0,0,159,47),fill='#197a9c')
    box=(40,30,100,70);draw.text((40,48),'cat',font=style,fill='black')
    word=imaging.Word('cat',box,99,0,3);region=imaging.Region('cat','dog',box,99,[word],[],line_index=0,ocr_span=(0,3))
    lines=[dict(text='cat',words=[word])];protected=[box,protected_logo]
    blocked_old_passes(image,lines,region,protected)
    result,rendered,blocked=smart_fitting.render_plan(image,[region],protected,lines)
    assert not blocked
    diagnostic=rendered[0][1]
    assert diagnostic['adaptive_parameters']['dy']>=18
    assert diagnostic['text_bounds'][1]>=48 and diagnostic['text_bounds'][3]<=76
    assert result.crop(protected_logo).tobytes()==image.crop(protected_logo).tobytes()


def test_manual_box_is_a_real_limit_and_visual_choices_are_not_reset(style):
    image,lines,region,protected=isolated_word(style)
    region.settings={'box':region.box,'font':FONT,'foreground':(0,128,255,255),'shadow':(2,2),'repair':'fill'}
    saved=deepcopy(region);before=image.tobytes()
    _,_,blocked=smart_fitting.render_plan(image,[region],protected,lines)
    assert blocked and blocked['fit_exhausted'] and 'Automatic limits reached' in blocked['reason']
    assert region==saved and image.tobytes()==before


def test_context_cannot_consume_another_substitution_and_other_lines_stay_intact(style):
    image,lines,region,protected=full_context(style)
    word=lines[0]['words'][0]
    other=imaging.Region(word.text,'first',word.box,99,[word],[],line_index=0,ocr_span=(word.start,word.end),settings={'repair':'gradient'})
    contexts=fit_search._contexts(region,lines,[region,other])
    assert all(word.box not in [w.box for w in item.words] for item,count in contexts)
    lower=(0,102,image.width,130)
    ImageDraw.Draw(image).rectangle(lower,fill='#e28a20')
    result,_,_=smart_fitting.render_plan(image,[region],protected+[lower],lines)
    assert result.crop(lower).tobytes()==image.crop(lower).tobytes()


def test_detected_panel_still_prevents_text_from_spilling_into_photo(style,monkeypatch):
    image,lines,region,protected=isolated_word(style)
    panel=(8,0,72,140);monkeypatch.setattr('image_caption_gender_fixer.ocr_quality.panels',lambda image:[panel])
    result,rendered,blocked=smart_fitting.render_plan(image,[region],protected,lines)
    assert not blocked
    bounds=rendered[0][1]['text_bounds'];assert panel[0]<=bounds[0]<bounds[2]<=panel[2]
    assert result.crop((72,0,100,140)).tobytes()==image.crop((72,0,100,140)).tobytes()


def test_impossible_caption_is_bounded_and_does_not_write_artifacts(style,tmp_path,monkeypatch):
    image,lines,region,protected=isolated_word(style);region.after='W'*150
    source=tmp_path/'neutral.png';image.save(source);digest=sha256(source)
    monkeypatch.setattr(imaging,'scene_faces',lambda image:[])
    proposal=imaging.proposal(source,image,dict(format='PNG',info={},exif=Image.Exif()),[region],protected,
        tmp_path,'unused',digest,'rules',caption_lines=lines)
    assert proposal['blocked']['fit_exhausted'] and proposal['blocked']['fit_trials']>0
    assert proposal['stage'] is None and not proposal['artifacts'] and sha256(source)==digest
    cfg=dict(region.settings,_fit_lane=imaging.caption_lane(image,region,lines))
    chosen,trials,info=fit_search.select_fit(replace(region,settings=cfg),imaging.estimate(image,region),[],cfg['_fit_lane'])
    assert chosen is None and trials<=fit_search.MAX_TRIALS


def test_first_proposal_automatically_uses_measured_fit_and_waits_for_approval(style,tmp_path,monkeypatch):
    image,lines,region,protected=isolated_word(style);source=tmp_path/'neutral.png';image.save(source);digest=sha256(source)
    app=app_for(tmp_path,answers=iter([]));reviews=[]
    monkeypatch.setattr(app,'ocr_lines',lambda *args,**kwargs:(lines,False))
    monkeypatch.setattr(imaging,'regions',lambda *args:([region],protected))
    monkeypatch.setattr(imaging,'scene_faces',lambda image:[])
    monkeypatch.setattr(imaging,'ocr',lambda *args,**kwargs:[dict(text=region.after)])
    def review(path,proposal,regions):
        assert not proposal.get('blocked') and proposal['diagnostics'][0]['adaptive_parameters']
        assert proposal['level']>=2 and not (tmp_path/'.history.icgf').exists() and sha256(source)==digest
        reviews.append(proposal);return 'a'
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert code==0 and len(reviews)==1 and Path(result['results'][0]['corrected']).is_file()
    assert region.settings=={}



def test_optional_context_repair_failure_keeps_a_valid_local_fit(style,monkeypatch):
    image,lines,region,protected=full_context(style);region.after='small pet';region.settings={'repair':'patch'}
    actual=imaging.render_region;contexts=[]
    def render(image,candidate,protected,**kwargs):
        if len(candidate.words)>1:
            contexts.append(candidate.before)
            raise RenderBlocked('No safe neighboring patch; choose another repair or defer.')
        return actual(image,candidate,protected,**kwargs)
    monkeypatch.setattr(imaging,'render_region',render)
    result,diagnostic,crops=fit_search.render_adaptive_region(image,region,protected,lines,[region])
    assert contexts and diagnostic['adaptive_parameters'] and diagnostic['repair']=='patch'
    assert not diagnostic.get('fit_context') and result.size==image.size
