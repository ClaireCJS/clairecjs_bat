import re
import time
from test_images import ROOT
from PIL import Image,ImageDraw,ImageFont
from image_caption_gender_fixer import imaging,dependencies,ocr_quality
from image_caption_gender_fixer.ocr_cache import ALGORITHM

def test_small_caption_panel_ocr_with_photo_noise_keeps_real_words_and_geometry(tmp_path):
    import numpy as np
    rng=np.random.default_rng(42)
    image=Image.fromarray(rng.integers(60,200,(1000,640,3),dtype=np.uint8),'RGB')
    draw=ImageDraw.Draw(image);draw.rectangle((40,380,600,570),fill='black')
    font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',22)
    expected=['The good boy meets his wife.','A real man keeps his promise.','They walk together in the park.']
    for i,line in enumerate(expected):draw.text((55,400+i*48),line,font=font,fill='white')
    image.save(tmp_path/'generated-panel.png');exe=dependencies.require_ocr(ROOT,False,True,lambda _:False)['path']
    baseline=imaging.ocr(image,exe,ROOT/'environment/tessdata');start=time.monotonic()
    result=ocr_quality.recognize(image,exe,ROOT/'environment/tessdata')
    text=' '.join(l['text'] for l in result)
    normalize=lambda s:re.sub(r'[^a-z ]','',s.casefold()).split()
    want=normalize(' '.join(expected));got=normalize(text);old=normalize(' '.join(l['text'] for l in baseline))
    assert sum(w in got for w in want)>=sum(w in old for w in want)
    assert sum(w in got for w in want)>=len(want)*.9
    assert ocr_quality.panels(image)
    assert all(0<=w.box[0]<w.box[2]<=image.width and 0<=w.box[1]<w.box[3]<=image.height for l in result for w in l['words'])
    assert time.monotonic()-start<30 and ALGORITHM>=2

def test_eco_mode_uses_one_scan_for_normal_size_and_keeps_words(monkeypatch):
    calls=[]
    def scan(*args,**kwargs):calls.append(True);return [{'text':'hello','words':[imaging.Word('hello',(0,0,40,20),99,0,5)]}]
    monkeypatch.setattr(imaging,'ocr',scan)
    assert ocr_quality.recognize(Image.new('RGB',(400,300)),'exe','data',True)[0]['text']=='hello'
    assert calls==[True]
