"""Bounded local OCR retries and caption-panel scans; no text is invented."""
from dataclasses import replace
import math

POLICY='panel-block-threshold-v3.1'

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
    result=targeted_retries(image,result,executable,tessdata)
    return sorted(result,key=lambda l:(min(w.box[1] for w in l['words']),min(w.box[0] for w in l['words'])))


def weak(lines):
    import re
    words=[w for line in lines for w in line['words']]
    if not words:return True
    return (sum(w.confidence for w in words)/len(words)<86 or
            any(w.confidence<65 or re.search(r'[\\|={}<>\[\]~]',w.text) for w in words))


def crop_boxes(lines,size):
    """Group nearby detected lines into caption blocks, including photo overlays."""
    rows=[]
    for line in lines:
        words=[w for w in line['words'] if sum(c.isalnum() for c in w.text)>=2 and w.confidence>=15]
        if not words:continue
        box=(min(w.box[0] for w in words),min(w.box[1] for w in words),max(w.box[2] for w in words),max(w.box[3] for w in words))
        rows.append((box,words))
    groups=[]
    for box,words in sorted(rows,key=lambda r:r[0][1]):
        height=max(1,box[3]-box[1]);chosen=None
        for group in groups:
            a,b,c,d=group['box'];overlap=min(c,box[2])-max(a,box[0])
            if overlap>0 and box[1]-d<=max(height,group['height'])*1.8:
                chosen=group;break
        if chosen is None:groups.append({'box':box,'height':height,'words':list(words),'rows':1})
        else:
            a,b,c,d=chosen['box'];chosen['box']=(min(a,box[0]),min(b,box[1]),max(c,box[2]),max(d,box[3]))
            chosen['words'].extend(words);chosen['rows']+=1
            chosen['height']=min(height,chosen['height'])
    result=[]
    for group in groups:
        if len(group['words'])<3:continue
        x1,y1,x2,y2=group['box'];pad=max(4,round(group['height']*.45))
        box=(max(0,x1-pad),max(0,y1-pad),min(size[0],x2+pad),min(size[1],y2+pad))
        if (box[2]-box[0])*(box[3]-box[1])>size[0]*size[1]*.85:continue
        result.append((box,6 if group['rows']>1 else 7))
    return sorted(result,key=lambda entry:-(entry[0][2]-entry[0][0])*(entry[0][3]-entry[0][1]))[:3]


def crop_variants(image,box):
    """Bounded, padded grayscale/Otsu/adaptive variants with reversible geometry."""
    from PIL import Image,ImageOps
    from .imaging import libraries
    np,cv,*_=libraries()
    crop=image.crop(box).convert('RGBA')
    rgba=np.array(crop);visible=rgba[:,:,:3][rgba[:,:,3]>32]
    luminance=float(np.median(visible)) if visible.size else 0
    background=Image.new('RGBA',crop.size,'black' if luminance>160 else 'white')
    background.alpha_composite(crop)
    gray=ImageOps.autocontrast(ImageOps.grayscale(background))
    if sum(gray.histogram()[:128])>gray.width*gray.height*.55:gray=ImageOps.invert(gray)
    # A stable enlarged character height helps line OCR; also cap total memory.
    scale=min(3,2400/max(gray.size))
    if scale!=1:gray=gray.resize((round(gray.width*scale),round(gray.height*scale)),Image.Resampling.LANCZOS)
    array=np.array(gray)
    contrast=cv.createCLAHE(clipLimit=2,tileGridSize=(8,8)).apply(array)
    _,binary=cv.threshold(contrast,0,255,cv.THRESH_BINARY+cv.THRESH_OTSU)
    adaptive=cv.adaptiveThreshold(contrast,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,cv.THRESH_BINARY,31,11)
    # White caption lettering with a dark outline often lies over a photo.
    # Separate the bright/dark ink from the midtone background before OCR.
    light_ink=Image.fromarray(255-(array>170).astype('uint8')*255)
    dark_ink=Image.fromarray((array>=85).astype('uint8')*255)
    for variant in (gray,light_ink,dark_ink,Image.fromarray(binary),Image.fromarray(adaptive)):
        border=12
        yield ImageOps.expand(variant,border=border,fill=255),scale,border


def targeted_retries(image,result,executable,tessdata,budget=8):
    """Use the best local evidence, preserving strong words in each crop."""
    from dataclasses import replace
    from . import imaging
    import re
    def normalized(text):return re.sub(r'[^\w]','',text.casefold())
    def inside(line,box):
        return all(box[0]<=(w.box[0]+w.box[2])/2<=box[2] and box[1]<=(w.box[1]+w.box[3])/2<=box[3] for w in line['words'])
    def retain(candidate,previous):
        new={normalized(w.text) for line in candidate for w in line['words']}
        count=sum(len(line['words']) for line in previous)
        threshold=75 if count<3 else 92
        return all(normalized(w.text) in new for line in previous for w in line['words'] if w.confidence>=threshold)
    boxes=crop_boxes(result,image.size)
    # A weak single line still benefits even when no multiword block was found.
    if not boxes:
        for line in result:
            if not weak([line]) or not line['words']:continue
            words=line['words'];pad=max(4,round(max(w.box[3]-w.box[1] for w in words)*.4))
            box=(max(0,min(w.box[0] for w in words)-pad),max(0,min(w.box[1] for w in words)-pad),min(image.width,max(w.box[2] for w in words)+pad),min(image.height,max(w.box[3] for w in words)+pad))
            boxes.append((box,7))
            if len(boxes)==3:break
    for box,psm in boxes:
        previous=[line for line in result if inside(line,box)]
        if not weak(previous):continue
        best=previous
        for prepared,scale,border in crop_variants(image,box):
            if budget<=0:break
            budget-=1
            scanned=imaging.ocr(prepared,executable,tessdata,False,True,psm=psm)
            unpadded=[dict(text=line['text'],words=[replace(w,box=tuple(v-border for v in w.box)) for w in line['words']]) for line in scanned]
            candidate=clean(mapped(unpadded,scale,box,image.size))
            if candidate and quality(candidate)>quality(best) and retain(candidate,previous):best=candidate
            if not weak(best):break
        if best is not previous:result=[line for line in result if not inside(line,box)]+best
    return result
