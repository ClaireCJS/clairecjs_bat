"""Automatic fitting should use line geometry, preserve other text and ask for review."""
from dataclasses import replace
import pytest
from PIL import Image,ImageDraw,ImageFont
from image_caption_gender_fixer import imaging,smart_fitting
from image_caption_gender_fixer.fs import sha256
from test_images import app_for
from test_fit_retries import full_line

FONT=r'C:\Windows\Fonts\arial.ttf'


@pytest.fixture
def style(monkeypatch):
    monkeypatch.setattr(imaging,'estimate',lambda *args:dict(foreground=(0,0,0,255),background=(255,255,255),
        background_alpha=255,texture=0,font=FONT,size=24,font_score=1,font_candidates=[]))
    monkeypatch.setattr('image_caption_gender_fixer.ocr_quality.panels',lambda image:[])
    return ImageFont.truetype(FONT,24)


def crowded_line(font):
    text='cat longword sun';words=[];x=20;offset=0
    image=Image.new('RGBA',(320,135),'white');draw=ImageDraw.Draw(image)
    for token in text.split():
        width=round(draw.textlength(token,font=font));box=(x,30,x+width,56)
        words.append(imaging.Word(token,box,99,offset,offset+len(token)))
        draw.text((x,25),token,font=font,fill='black');offset+=len(token)+1;x+=width+5
    edits=[imaging.Region(w.text,after,w.box,99,[w],[],line_index=0,ocr_span=(w.start,w.end))
        for w,after in zip(words,('a marvelous creature','x','moon'))]
    other=(20,88,290,114);draw.text((20,83),'Leave this unchanged',font=font,fill='black')
    return image,[dict(text=text,words=words)],edits,[w.box for w in words]+[other],other


def test_first_proposal_uses_stronger_fitting_without_waiting_for_a_button(style,tmp_path,monkeypatch):
    image,lines,edit,protected=full_line(style,'Nice day','Such a really wonderful day')
    source=tmp_path/'neutral.png';image.save(source);digest=sha256(source)
    app=app_for(tmp_path,answers=iter([]));seen=[]
    monkeypatch.setattr(app,'ocr_lines',lambda *args,**kwargs:(lines,False))
    monkeypatch.setattr(imaging,'regions',lambda *args:([edit],protected))
    monkeypatch.setattr(imaging,'scene_faces',lambda image:[])
    monkeypatch.setattr(imaging,'ocr',lambda *args,**kwargs:[{'text':edit.after}])
    def review(path,proposal,regions):
        assert not proposal.get('blocked')
        assert proposal['diagnostics'][0]['automatic_fit']
        assert proposal['diagnostics'][0]['fit_retry']==2 and proposal['level']==3
        assert sha256(source)==digest and not (tmp_path/'.history.icgf').exists()
        seen.append(proposal);return 's'
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert len(seen)==1 and code==10 and result['results'][0]['state']=='skipped'
    assert sha256(source)==digest


def test_multiple_crowded_changes_fit_together_without_erasing_other_lines(style):
    image,lines,edits,protected,other=crowded_line(style);before=image.tobytes()
    result,rendered,blocked=smart_fitting.render_plan(image,edits,protected,lines)
    assert blocked is None and len(rendered)==1
    _,diagnostic,_=rendered[0]
    assert diagnostic['members']==[0,1,2] and diagnostic['automatic_fit']
    assert diagnostic['line_fit']=={'before':'cat longword sun','after':'a marvelous creature x moon'}
    assert result.crop(other).tobytes()==image.crop(other).tobytes()
    assert image.tobytes()==before and result.tobytes()!=before
    assert imaging.full_captions(lines,edits)['proposed']=='a marvelous creature x moon'
    assert [(r.before,r.after) for r in edits]==[('cat','a marvelous creature'),('longword','x'),('sun','moon')]


def test_joint_line_proposal_verifies_every_substitution(style,tmp_path,monkeypatch):
    image,lines,edits,protected,other=crowded_line(style)
    source=tmp_path/'neutral.png';image.save(source);digest=sha256(source)
    monkeypatch.setattr(imaging,'scene_faces',lambda image:[])
    monkeypatch.setattr(imaging,'ocr',lambda *args,**kwargs:[{'text':'a marvelous creature x moon'}])
    proposal=imaging.proposal(source,image,{'format':'PNG','info':{},'exif':Image.Exif()},edits,protected,tmp_path,'unused',digest,'rules',caption_lines=lines)
    assert not proposal.get('blocked') and proposal['stage']
    assert [v['region'] for v in proposal['verification']]==[0,1,2]
    assert all(v['replacement_confirmed'] for v in proposal['verification'])
    assert len(proposal['diagnostics'])==1 and sha256(source)==digest
    with Image.open(proposal['stage']) as output:
        assert output.crop(other).tobytes()==image.crop(other).tobytes()


@pytest.mark.parametrize('kind',['different_repairs','manual_box','invalid_span'])
def test_joint_fitting_does_not_override_incompatible_or_unverified_geometry(style,kind):
    image,lines,edits,protected,other=crowded_line(style);before=image.tobytes()
    if kind=='different_repairs':edits[1].settings['repair']='gradient'
    elif kind=='manual_box':edits[0].settings['box']=edits[0].box
    else:edits[0].ocr_span=(0,1)
    _,_,blocked=smart_fitting.render_plan(image,edits,protected,lines)
    assert blocked and blocked['fit_exhausted'] and blocked['fit_trials']>0
    assert image.tobytes()==before


def test_exhausted_fitting_reports_limits_and_never_saves_a_stage(style,tmp_path,monkeypatch):
    image,lines,edit,protected=full_line(style,'Nice day','W'*120)
    source=tmp_path/'neutral.png';image.save(source);digest=sha256(source)
    monkeypatch.setattr(imaging,'scene_faces',lambda image:[])
    proposal=imaging.proposal(source,image,{'format':'PNG','info':{},'exif':Image.Exif()},[edit],protected,tmp_path,'unused',digest,'rules',caption_lines=lines)
    assert proposal['blocked']['fit_exhausted'] and proposal['blocked']['fit_trials']>0
    assert 'Automatic limits reached' in proposal['blocked']['reason']
    assert proposal['stage'] is None and not proposal['artifacts'] and sha256(source)==digest


def test_erased_source_box_does_not_keep_reserving_empty_space(style):
    image=Image.new('RGBA',(228,110),'white');draw=ImageDraw.Draw(image)
    words=[imaging.Word('longword',(60,30,185,56),99,0,8),imaging.Word('man',(186,30,228,56),99,9,12)]
    for w in words:draw.text((w.box[0],25),w.text,font=style,fill='black')
    edits=[imaging.Region(w.text,after,w.box,99,[w],[],line_index=0,ocr_span=(w.start,w.end))
        for w,after in zip(words,('x','woman'))]
    result,rendered,blocked=smart_fitting.render_plan(image,edits,[w.box for w in words],[dict(text='longword man',words=words)])
    assert not blocked and len(rendered)==2
    first,second=[item[1] for item in rendered]
    assert imaging.overlaps(second['text_bounds'],words[0].box)
    assert not imaging.overlaps(first['text_bounds'],second['text_bounds'])
