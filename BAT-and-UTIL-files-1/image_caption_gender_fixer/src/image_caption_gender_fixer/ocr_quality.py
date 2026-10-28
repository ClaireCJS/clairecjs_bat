"""Bounded local OCR retries and caption-panel scans; no text is invented."""
from dataclasses import replace
import math

POLICY='panel-gray-upscale-v2'

def quality(lines):
    words=[w for line in lines for w in line['words']]
    if not words:return -1000
    score=0
    for word in words:
        letters=sum(c.isalnum() for c in word.text);junk=len(word.text)-letters
        score+=math.sqrt(max(1,letters))*(word.confidence-42)/25
        if letters<2 and word.text.casefold() not in ('a','i'):score-=1.8
        score-=max(0,junk-letters)*.8
    return score

def clean(lines):
    result=[]
    for line in lines:
        # Isolated photo noise is common in sparse mode. Keep ordinary words,
        # including low-confidence words, rather than rewriting spelling.
        words=[w for w in line['words'] if not (w.confidence<45 and sum(c.isalnum() for c in w.text)<=2)]
        if not words:continue
        offset=0;packed=[]
        for w in words:packed.append(replace(w,start=offset,end=offset+len(w.text)));offset+=len(w.text)+1
        result.append({'text':' '.join(w.text for w in packed),'words':packed})
    return result

def panels(image):
    from .imaging import libraries
    np,cv,*_=libraries();rgb=np.array(image.convert('RGB'))
    factor=min(1,1400/max(image.size));small=cv.resize(rgb,None,fx=factor,fy=factor) if factor<1 else rgb
    gray=cv.cvtColor(small,cv.COLOR_RGB2GRAY);h,w=gray.shape;found=[]
    for mask in [(gray<55).astype('uint8')*255,(gray>220).astype('uint8')*255]:
        contours,_=cv.findContours(mask,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            x,y,cw,ch=cv.boundingRect(contour);area=cw*ch
            if cw<w*.20 or ch<24 or area<w*h*.008 or area>w*h*.85 or cw/ch>18:continue
            if cv.contourArea(contour)/area<.78:continue
            crop=gray[y:y+ch,x:x+cw]
            if float(np.std(crop))<30:continue
            # Require many contrasting text-sized components inside the panel.
            interior=crop[2:-2,2:-2]
            binary=((interior>150) if np.median(crop)<128 else (interior<110)).astype('uint8')
            count,_,stats,_=cv.connectedComponentsWithStats(binary,8)
            glyphs=sum(1 for sx,sy,sw,sh,sa in stats[1:] if 2<=sw<cw*.18 and 4<=sh<ch*.6 and sa>=4)
            if glyphs<8:continue
            box=tuple(round(v/factor) for v in (x,y,x+cw,y+ch))
            if not any(abs(box[0]-b[0])<8 and abs(box[1]-b[1])<8 for b in found):found.append(box)
    return sorted(found,key=lambda b:(b[2]-b[0])*(b[3]-b[1]),reverse=True)[:3]

def mapped(lines,scale,box,size):
    result=[]
    for line in lines:
        words=[]
        for word in line['words']:
            x1,y1,x2,y2=word.box
            coords=(max(0,min(size[0]-1,round(x1/scale)+box[0])),max(0,min(size[1]-1,round(y1/scale)+box[1])),
                    max(1,min(size[0],round(x2/scale)+box[0])),max(1,min(size[1],round(y2/scale)+box[1])))
            if coords[0]<coords[2] and coords[1]<coords[3]:words.append(replace(word,box=coords))
        if words:result.append({'text':line['text'],'words':words})
    return result

def recognize(image,executable,tessdata,eco=False):
    from . import imaging
    from PIL import Image,ImageOps
    initial=imaging.ocr(image,executable,tessdata,eco)
    if max(image.size)>1800 and any(w.confidence<80 for l in initial for w in l['words']):
        retry=imaging.ocr(image,executable,tessdata,eco,True)
        if quality(retry)>=quality(initial):initial=retry
    if eco:return clean(initial)
    result=clean(initial)
    def retains_words(alternate,original):
        import re
        def normalized(text):return re.sub(r'[^\w]','',text.casefold())
        new={normalized(w.text) for line in alternate for w in line['words']}
        return all(normalized(w.text) in new for line in original for w in line['words'] if w.confidence>=75)
    # A grayscale enlarged pass separates small glyphs without forcing a
    # photographic page into one text block. Limit memory and number of passes.
    scale=min(2.5,2800/max(image.size))
    if scale>1.05 or quality(result)<2:
        scale=max(1,scale);prepared=ImageOps.autocontrast(ImageOps.grayscale(image))
        if scale!=1:prepared=prepared.resize((round(image.width*scale),round(image.height*scale)),Image.Resampling.LANCZOS)
        alternate=clean(mapped(imaging.ocr(prepared,executable,tessdata,False,True,psm=11),scale,(0,0,*image.size),image.size))
        if quality(alternate)>quality(result) and retains_words(alternate,result):result=alternate
    for box in panels(image):
        crop=ImageOps.grayscale(image.crop(box));scale=min(3,2200/max(crop.size))
        if scale>1:crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
        else:scale=1
        if crop.getextrema()[0]<80 and sum(crop.histogram()[:128])>crop.width*crop.height*.5:crop=ImageOps.invert(crop)
        crop=ImageOps.autocontrast(crop)
        candidate=clean(mapped(imaging.ocr(crop,executable,tessdata,False,True,psm=6),scale,box,image.size))
        def inside(line):
            return all(box[0]<=sum(w.box[::2])/2<=box[2] and box[1]<=sum(w.box[1::2])/2<=box[3] for w in line['words'])
        previous=[l for l in result if inside(l)]
        if candidate and quality(candidate)>quality(previous) and retains_words(candidate,previous):result=[l for l in result if not inside(l)]+candidate
    return sorted(result,key=lambda l:(min(w.box[1] for w in l['words']),min(w.box[0] for w in l['words'])))
