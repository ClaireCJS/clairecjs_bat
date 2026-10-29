import io,re,time
from types import SimpleNamespace
import pytest
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
from test_images import ROOT
from image_caption_gender_fixer import imaging,dependencies,ocr_quality
from image_caption_gender_fixer.ocr_cache import signature,ALGORITHM


def test_tsv_words_starting_with_quotes_do_not_consume_other_records(monkeypatch):
    tsv='level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
    tsv+='5\t1\t1\t1\t1\t1\t1\t2\t20\t10\t97\t"hello\n'
    tsv+='5\t1\t1\t1\t1\t2\t23\t2\t20\t10\t98\tworld\n'
    monkeypatch.setattr(imaging.subprocess,'run',lambda *args,**kwargs:SimpleNamespace(returncode=0,stdout=tsv.encode(),stderr=b''))
    result=imaging.ocr(Image.new('RGB',(100,60),'white'),'exe','data')
    assert result[0]['text']=='"hello world'
    assert len(result[0]['words'])==2 and result[0]['words'][1].start==7


@pytest.mark.parametrize('size,blur,stroke,minimum',[(13,.35,1,14),(18,.3,1,15)])
def test_photo_overlay_retries_recover_small_outlined_caption(size,blur,stroke,minimum):
    y,x=np.mgrid[:480,:640];rng=np.random.default_rng(8401)
    pixels=np.stack([95+35*np.sin(x/30)+y*.1,100+35*np.cos(y/25)+x*.04,110+25*np.cos((x+y)/40)],axis=2)
    pixels+=rng.normal(0,5,pixels.shape)
    image=Image.fromarray(pixels.clip(0,255).astype('uint8'),'RGB');draw=ImageDraw.Draw(image)
    expected=['They walked beside the river.','The little garden was quiet.','Please keep the original image.']
    font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',size)
    for i,line in enumerate(expected):draw.text((35,220+i*(size+12)),line,font=font,fill=(240 if size==13 else 245,)*3,stroke_width=stroke,stroke_fill=(5,5,5))
    image=image.filter(ImageFilter.GaussianBlur(blur));buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=82)
    image=Image.open(io.BytesIO(buffer.getvalue())).convert('RGBA');snapshot=image.tobytes()
    exe=dependencies.require_ocr(ROOT,False,True,lambda _:False)['path'];start=time.monotonic()
    lines=ocr_quality.recognize(image,exe,ROOT/'environment/tessdata')
    words=re.findall('[a-z]+',' '.join(l['text'] for l in lines).lower())
    wanted=re.findall('[a-z]+',' '.join(expected).lower())
    assert sum(w in words for w in wanted)>=minimum
    assert all(0<=w.box[0]<w.box[2]<=image.width and 0<=w.box[1]<w.box[3]<=image.height for l in lines for w in l['words'])
    assert image.tobytes()==snapshot and time.monotonic()-start<30


def test_targeted_retries_have_a_budget_and_preserve_strong_source_words(monkeypatch):
    original=[{'text':'Keep this image','words':[imaging.Word('Keep',(10,20,50,40),99,0,4),imaging.Word('this',(55,20,85,40),30,5,9),imaging.Word('image',(90,20,140,40),30,10,15)]}]
    calls=[]
    def scan(*args,**kwargs):
        calls.append(kwargs)
        return [{'text':'A different sentence','words':[imaging.Word('A',(20,20,40,40),99,0,1),imaging.Word('different',(45,20,120,40),99,2,11),imaging.Word('sentence',(125,20,200,40),99,12,20)]}]
    monkeypatch.setattr(imaging,'ocr',scan)
    result=ocr_quality.targeted_retries(Image.new('RGB',(250,100),'gray'),original,'exe','data',budget=2)
    assert len(calls)==2 and result==original


def test_new_quality_policy_invalidates_old_cache_keys():
    assert ALGORITHM>=3 and ocr_quality.POLICY=='panel-block-threshold-v3.1'
