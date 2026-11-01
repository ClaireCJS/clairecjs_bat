"""Formerly blocked layouts must actually render after explicit fitting."""
from dataclasses import replace
from pathlib import Path
import pytest
from PIL import Image,ImageDraw,ImageFont
from image_caption_gender_fixer import imaging
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


def tight_words(font):
    text='man pal';image=Image.new('RGBA',(240,100),'white');draw=ImageDraw.Draw(image)
    words=[];offset=0;x=50
    for token in text.split():
        width=round(draw.textlength(token,font=font));box=(x,30,x+width,56)
        draw.text((x,25),token,font=font,fill='black')
        words.append(imaging.Word(token,box,99,offset,offset+len(token)));offset+=len(token)+1;x+=width+1
    edits=[imaging.Region(word.text,after,word.box,99,[word],[],line_index=0,ocr_span=(word.start,word.end))
           for word,after in zip(words,('woman','friend'))]
    # Force true local space limits; otherwise the last word can move into whitespace.
    protected=[w.box for w in words]+[(0,25,50,62),(x,25,240,62)]
    return image,[{'text':text,'words':words}],edits,protected


def full_line(font,before,after):
    draw=ImageDraw.Draw(Image.new('RGBA',(1,1)));width=round(draw.textlength(before,font=font))
    image=Image.new('RGBA',(width+2,90),'white');ImageDraw.Draw(image).text((1,25),before,font=font,fill='black')
    box=(1,30,width+1,56);word=imaging.Word(before,box,99,0,len(before))
    edit=imaging.Region(before,after,box,99,[word],[],line_index=0,ocr_span=(0,len(before)))
    return image,[{'text':before,'words':[word]}],edit,[box]


def test_first_click_fits_without_borrowing_other_edited_words(style):
    image,lines,edits,protected=tight_words(style);source=image.tobytes()
    with pytest.raises(RenderBlocked):imaging.render_fitting_region(image,edits[0],protected,lines,edits)
    assert imaging.request_fit(edits)==1
    result,diagnostic,_=imaging.render_fitting_region(image,edits[0],protected,lines,edits)
    assert diagnostic['fit_action']=='squeeze' and diagnostic['fit_retry']==1 and diagnostic['fit_trials']>1
    assert not imaging.overlaps(diagnostic['text_bounds'],edits[1].box)
    assert result.crop(edits[1].box).tobytes()==image.crop(edits[1].box).tobytes()
    assert image.tobytes()==source and result.tobytes()!=source
    assert imaging.full_captions(lines,edits)['proposed']=='woman friend'


def test_first_click_fits_a_longer_whole_line_that_mild_fitting_cannot(style):
    image,lines,edit,protected=full_line(style,'Keep the picture','Please keep the entire picture')
    with pytest.raises(RenderBlocked):imaging.render_fitting_region(image,edit,protected,lines,[edit])
    imaging.request_fit([edit]);result,diagnostic,_=imaging.render_fitting_region(image,edit,protected,lines,[edit])
    assert result.size==image.size and diagnostic['fit_retry']==1 and diagnostic['level']==3
    assert diagnostic['fit_scale']<.8 or diagnostic['horizontal_scale']<.8
    assert 0<=diagnostic['text_bounds'][0]<diagnostic['text_bounds'][2]<=image.width


def test_one_click_automatically_escalates_to_the_second_pass(style):
    image,lines,edit,protected=full_line(style,'Nice day','Such a really wonderful day')
    assert imaging.request_fit([edit])==1
    with pytest.raises(RenderBlocked):
        imaging._render_fitting_pass(image,edit,protected,lines,[edit])
    result,diagnostic,_=imaging.render_fitting_region(image,edit,protected,lines,[edit])
    assert diagnostic['fit_retry']==2 and diagnostic['level']==3 and result.size==image.size
    assert imaging.request_fit([edit])==2


@pytest.mark.parametrize('manual_box',[False,True])
def test_corrected_ocr_without_matching_span_can_fit_its_own_box(style,manual_box):
    image,lines,edits,protected=tight_words(style);edit=edits[0]
    lines[0]['text']='m pal';edit.ocr_span=(0,1)
    if manual_box:edit.settings['box']=edit.box
    before=(edit.before,edit.after,edit.box,edit.ocr_span)
    imaging.request_fit([edit]);_,diagnostic,_=imaging.render_fitting_region(image,edit,protected,lines,edits)
    assert diagnostic['fit_retry']==1 and (edit.before,edit.after,edit.box,edit.ocr_span)==before
    if manual_box:assert edit.settings['box']==edit.box


def test_exhausted_search_is_specific_and_never_covers_protected_text(style):
    image,lines,edit,protected=full_line(style,'Nice day','This replacement caption is far too long to remain readable inside this tiny original space')
    imaging.request_fit([edit]);imaging.request_fit([edit]);before=image.tobytes()
    with pytest.raises(RenderBlocked,match='Automatic limits reached') as error:
        imaging.render_fitting_region(image,edit,protected,lines,[edit])
    assert error.value.fit_trials>0 and image.tobytes()==before


def test_review_crop_padding_does_not_block_the_next_independent_edit(tmp_path,style,monkeypatch):
    image,lines,edits,protected=tight_words(style)
    edits[0].after='men';edits[1].after='kid'
    source=tmp_path/'caption.png';image.save(source);digest=sha256(source)
    monkeypatch.setattr(imaging,'scene_faces',lambda image:[])
    monkeypatch.setattr(imaging,'ocr',lambda *args,**kwargs:[{'text':'men kid'}])
    proposal=imaging.proposal(source,image,{'format':'PNG','info':{},'exif':Image.Exif()},edits,protected,tmp_path,'unused',digest,'f'*64,caption_lines=lines)
    assert not proposal.get('blocked') and len(proposal['diagnostics'])==2
    first,second=proposal['diagnostics']
    assert imaging.overlaps(first['affected'],edits[1].box)
    assert not imaging.overlaps(first['text_bounds'],second['text_bounds'])
    expected=imaging.render_fitting_region(image,edits[0],protected,lines,edits)[0]
    with Image.open(proposal['stage']) as rendered:
        assert rendered.crop(first['text_bounds']).tobytes()==expected.crop(first['text_bounds']).tobytes()
    assert sha256(source)==digest


def test_automatic_fit_and_artwork_retry_both_need_fresh_review(tmp_path,style,monkeypatch):
    image,lines,edits,protected=tight_words(style);source=tmp_path/'caption.png';image.save(source);digest=sha256(source)
    app=app_for(tmp_path,answers=iter([]));proposals=[]
    monkeypatch.setattr(app,'ocr_lines',lambda *args,**kwargs:(lines,False))
    monkeypatch.setattr(imaging,'regions',lambda *args:(edits,protected))
    monkeypatch.setattr(imaging,'scene_faces',lambda image:[])
    monkeypatch.setattr(imaging,'ocr',lambda *args,**kwargs:[{'text':'woman friend'}])
    def review(path,proposal,regions):
        proposals.append(proposal)
        assert sha256(source)==digest and not (tmp_path/'.history.icgf').exists()
        if len(proposals)==1:
            assert not proposal.get('blocked') and all(d.get('automatic_fit') for d in proposal['diagnostics'])
            return {'action':'fit_all'}
        assert not proposal.get('blocked') and all(d['fit_retry']==1 for d in proposal['diagnostics'])
        return 's'
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert len(proposals)==2 and code==10 and result['results'][0]['state']=='skipped'
    assert proposals[0]['transaction']!=proposals[1]['transaction'] and sha256(source)==digest
