"""Opt-in fitting must retain protected text and require fresh review."""
import pytest
from PIL import Image,ImageDraw,ImageFont
from image_caption_gender_fixer import imaging
from image_caption_gender_fixer.errors import RenderBlocked


@pytest.fixture
def known_style(monkeypatch):
    font_path=r'C:\Windows\Fonts\arial.ttf'
    style=dict(foreground=(0,0,0,255),background=(255,255,255),background_alpha=255,
               texture=0,font=font_path,size=24,font_score=1,font_candidates=[])
    monkeypatch.setattr(imaging,'estimate',lambda image,region:dict(style))
    return ImageFont.truetype(font_path,24)


def region(box,before='man',after='woman'):
    word=imaging.Word(before,box,99,0,len(before))
    return imaging.Region(before,after,box,99,[word],[],line_index=0,ocr_span=(0,len(before)))


@pytest.mark.parametrize('direction',['right','left'])
def test_opt_in_moves_to_safe_space_without_covering_neighbor(known_style,direction):
    box=(100,30,145,55) if direction=='right' else (210,30,250,55)
    image=Image.new('RGBA',(260,100),'white');ImageDraw.Draw(image).text(box[:2],'man',font=known_style,fill='black')
    edit=region(box)
    obstacle=(0,25,102,70) if direction=='right' else (255,25,260,70)
    protected=[box,obstacle]
    with pytest.raises(RenderBlocked,match='cannot fit safely'):imaging.render_region(image,edit,protected)
    edit.settings['move_squeeze']=True
    result,diagnostic,_=imaging.render_fitting_region(image,edit,protected,[],[edit])
    assert diagnostic['fit_action']==direction and diagnostic['level']>=2
    assert result.crop(obstacle).tobytes()==image.crop(obstacle).tobytes()
    assert result.size==image.size and edit.before=='man'


def caption_image(font):
    text='bright man today';words=[];offset=0;x=10
    image=Image.new('RGBA',(260,100),'white');draw=ImageDraw.Draw(image)
    for token in text.split():
        width=round(draw.textlength(token,font=font))
        box=(x,30,x+width,58);words.append(imaging.Word(token,box,99,offset,offset+len(token)))
        draw.text((x,25),token,font=font,fill='black')
        x+=width+5;offset+=len(token)+1
    word=words[1]
    edit=imaging.Region('man','woman',word.box,99,[word],[],settings={'move_squeeze':True},line_index=0,ocr_span=(word.start,word.end))
    return image,{'text':text,'words':words},edit


def test_squeeze_uses_adjacent_words_and_preserves_caption_spans(known_style):
    image,line,edit=caption_image(known_style);original=image.tobytes()
    result,diagnostic,_=imaging.render_fitting_region(image,edit,[w.box for w in line['words']],[line],[edit])
    assert diagnostic['fit_action']=='squeeze' and .8<=diagnostic['horizontal_scale']<1
    assert diagnostic['fit_context']==dict(before='bright man today',after='bright woman today',words_per_side=1)
    assert edit.before=='man' and edit.after=='woman' and len(edit.words)==1
    assert imaging.full_captions([line],[edit])['proposed']=='bright woman today'
    assert image.tobytes()==original and result.tobytes()!=original and diagnostic['level']>=2


def test_context_cannot_erase_another_edit(known_style):
    image,line,edit=caption_image(known_style);other=region(line['words'][0].box,'bright','clear')
    with pytest.raises(RenderBlocked,match='cannot fit safely'):
        imaging.render_fitting_region(image,edit,[w.box for w in line['words']],[line],[edit,other])


def test_blocked_console_default_is_move_and_success_default_stays_skip(tmp_path):
    from test_images import app_for
    prompts=[]
    app=app_for(tmp_path);app.interactive=True
    app.ask_callback=lambda message:prompts.append(message) or ''
    assert app.review_question('[m]ove, [s]kip: ',True)=='m'
    assert app.review_question('[m]ove, [s]kip: ',False)=='s'
    assert 'ENTER=Move/squeeze text to fit' in prompts[0] and 'ENTER=Skip image' in prompts[1]


def test_automatic_context_fit_requires_review_before_commit(tmp_path,known_style,monkeypatch):
    from test_images import app_for
    from image_caption_gender_fixer.fs import sha256
    from image_caption_gender_fixer.history import History
    from pathlib import Path
    image,line,_=caption_image(known_style);source=tmp_path/'caption.png';image.save(source)
    digest=sha256(source);app=app_for(tmp_path,answers=iter([]));proposals=[]
    monkeypatch.setattr(app,'ocr_lines',lambda *args,**kwargs:([line],False))
    def approve(source,proposal,regions):
        proposals.append(proposal)
        assert not proposal.get('blocked') and proposal['level']>=2
        assert proposal['diagnostics'][0]['fit_action']=='squeeze'
        assert sha256(source)==digest and not (tmp_path/'.history.icgf').exists()
        return 'a'
    monkeypatch.setattr(app,'review',approve)
    result,code=app.process([str(source)])
    assert code==0 and len(proposals)==1
    event=next(iter(History(tmp_path).transactions().values()))
    assert sha256(tmp_path/event['backup'])==digest
    assert Path(result['results'][0]['corrected']).is_file()
