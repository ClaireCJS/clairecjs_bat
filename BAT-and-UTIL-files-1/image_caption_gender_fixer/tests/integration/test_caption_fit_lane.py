import pytest
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from image_caption_gender_fixer import imaging
from image_caption_gender_fixer.errors import RenderBlocked


def test_longer_caption_is_squeezed_inside_its_panel_instead_of_moving_into_photo(monkeypatch):
    image=Image.new('RGBA',(620,260),(40,80,120,255));draw=ImageDraw.Draw(image)
    draw.rectangle((400,0,619,259),fill='black')
    font_path=r'C:\Windows\Fonts\arial.ttf';font=ImageFont.truetype(font_path,24)
    text='Keep this image';box=(408,65,600,94)
    draw.text((408,62),text,font=font,fill='white')
    words=[imaging.Word(text,box,99,0,len(text))]
    edit=imaging.Region(text,'Please keep this original image',box,99,words,[],line_index=0,ocr_span=(0,len(text)))
    monkeypatch.setattr(imaging,'estimate',lambda *args:dict(foreground=(255,255,255,255),background=(0,0,0),background_alpha=255,texture=0,font=font_path,size=24,font_score=1,font_candidates=[]))
    monkeypatch.setattr('image_caption_gender_fixer.ocr_quality.panels',lambda image:[(400,0,620,260)])
    result,diagnostic,_=imaging.render_fitting_region(image,edit,[box],[{'text':text,'words':words}],[edit])
    assert result.crop((0,0,400,260)).tobytes()==image.crop((0,0,400,260)).tobytes()
    assert diagnostic['fit_action']=='squeeze' and diagnostic['horizontal_scale']>=.8
    assert diagnostic['affected'][0]>=400


def test_unknown_caption_background_still_limits_displacement(monkeypatch):
    image=Image.new('RGBA',(600,180),'white');box=(520,60,590,88)
    word=imaging.Word('short',box,99,0,5);edit=imaging.Region('short','a very long replacement caption',box,99,[word],[],line_index=0,ocr_span=(0,5))
    monkeypatch.setattr('image_caption_gender_fixer.ocr_quality.panels',lambda image:[])
    with pytest.raises(RenderBlocked):imaging.render_fitting_region(image,edit,[box],[{'text':'short','words':[word]}],[edit])
