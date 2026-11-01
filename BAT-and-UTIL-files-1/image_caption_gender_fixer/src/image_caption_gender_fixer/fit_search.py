"""Measured, bounded layout search after the ordinary fitting passes fail."""
from dataclasses import replace
import math
from .errors import RenderBlocked

MAX_TRIALS=900
MIN_WIDTH=.65


def _corridors(left,right,neighbors,y,height):
    spans=[(left,right)]
    for a,b,c,d in neighbors:
        if not (b<y+height and y<d):continue
        remaining=[]
        for start,end in spans:
            if c<=start or a>=end:remaining.append((start,end));continue
            if start<a:remaining.append((start,a))
            if c<end:remaining.append((c,end))
        spans=remaining
    return spans


def select_fit(region,style,neighbors,lane):
    """Measure text once per font/spacing choice, then solve safe placements.

    Width scales come from the actual available gap instead of a fixed grid.
    Every result stays in the caption lane, avoids protected rectangles and
    retains explicitly chosen font, effects, spacing and box boundaries.
    """
    from . import imaging
    _,_,Image,_,Font,_,_,_=imaging.libraries()
    cfg=region.settings;x1,y1,x2,y2=cfg.get('box',region.box)
    base_x=x1+int(cfg.get('dx',0));base_y=y1+int(cfg.get('dy',0))
    base_size=max(6,round(style['size']*float(cfg.get('scale',1))))
    minimum=min(base_size,max(8,math.ceil(base_size*.55)))
    movement=max(6,min(32,round((y2-y1)*.75)))
    faces=[str(cfg.get('font',style['font']))]
    if 'font' not in cfg:
        for item in style.get('font_candidates',[]):
            if item['score']>=style.get('font_score',0)-.12 and str(item['font']) not in faces:
                faces.append(str(item['font']))
            if len(faces)==3:break
    sizes=sorted({base_size,minimum,*[max(minimum,round(base_size*f)) for f in (1,.95,.9,.85,.8,.75,.7,.65,.6,.55)]},reverse=True)
    tracking=(float(cfg['tracking']),) if 'tracking' in cfg else (0,-.5,-1)
    variants=sorted((5*(1-size/base_size)+.25*rank+.025*abs(space-float(cfg.get('tracking',0))),rank,size,space,face)
        for rank,face in enumerate(faces) for size in sizes for space in tracking)
    foreground=tuple(cfg.get('foreground',style['foreground']))
    if 'opacity' in cfg:foreground=foreground[:3]+(round(255*cfg['opacity']),)
    best=None;trials=0;layers=0
    for lower,rank,size,space,face in variants:
        if trials>=MAX_TRIALS:break
        if best is not None and lower>=best[0]:continue
        font=Font.truetype(face,size)
        layer=imaging.styled(region.after,font,foreground,int(cfg.get('outline',0)),
            tuple(cfg.get('outline_color',(0,0,0,255))),space,tuple(cfg.get('shadow',(1,1))),
            float(cfg.get('blur',.5)),float(cfg.get('rotation',0)),tuple(cfg.get('shadow_color',(0,0,0,180))))
        layers+=1;left,top,right,bottom=lane
        if 'box' in cfg:
            left=max(left,x1);right=min(right,x2);top=max(top,y1);bottom=min(bottom,y2)
        # Keep one caption line on its own baseline. Empty pixels above the
        # sentence are not permission to move a word onto a new line/photo.
        margin=max(2,min(6,round((y2-y1)*.15)))
        top=max(top,base_y-margin);bottom=min(bottom,y2+int(cfg.get('dy',0))+margin)
        min_y=max(top,base_y-movement);max_y=min(bottom-layer.height,base_y+movement)
        if min_y>max_y:continue
        ys=[base_y,round((y1+y2-layer.height)/2),y2-layer.height,min_y,max_y]
        for a,b,c,d in neighbors:ys.extend((b-layer.height,d))
        primary={max(min_y,min(max_y,y)) for y in ys[:5]}
        extra=sorted({max(min_y,min(max_y,y)) for y in ys[5:]}-primary,key=lambda y:(abs(y-base_y),y))
        ys=sorted(primary|set(extra[:7]),key=lambda y:(abs(y-base_y),y))
        for y in ys:
            for start,end in _corridors(left,right,neighbors,y,layer.height):
                # Stay in the local gap containing/touching the source text.
                if end<x1 or start>x2:continue
                low=max(start,base_x-movement);high=min(end,base_x+movement)
                if low>high:continue
                widths={min(layer.width,end-low)}
                if low<=base_x<=high:widths.add(min(layer.width,end-base_x))
                for width in sorted(widths,reverse=True):
                    if trials>=MAX_TRIALS:break
                    trials+=1;width=int(width);horizontal=width/layer.width
                    if width<1 or horizontal<MIN_WIDTH:continue
                    last=min(base_x+movement,end-width)
                    if last<low:continue
                    x=max(low,min(last,base_x));bounds=(x,y,x+width,y+layer.height)
                    if any(imaging.overlaps(bounds,p) for p in neighbors):continue
                    distance=math.hypot(x-base_x,y-base_y)/max(1,y2-y1)
                    score=lower+2*(1-horizontal)+.05*distance
                    if best is not None and score>=best[0]:continue
                    fitted=layer if width==layer.width else layer.resize((width,layer.height),Image.Resampling.LANCZOS)
                    chosen=(fitted,(x,y),bounds,size/base_size,space,horizontal,'adaptive')
                    parameters=dict(font=face,font_size=size,tracking=space,horizontal_scale=horizontal,
                        x=x,y=y,dx=x-base_x,dy=y-base_y,score=round(score,6))
                    best=(score,chosen,parameters)
    if best is None:return None,trials,dict(layers=layers,budget=MAX_TRIALS)
    return best[1],trials,dict(best[2],layers=layers,variants=trials,budget=MAX_TRIALS)


def _contexts(region,lines,others):
    """Allow more unchanged context only when its source spans are verified."""
    cfg=region.settings
    if any(key in cfg for key in ('box','dx','dy','rotation','protected','mask_sides')):return []
    index=region.line_index;span=region.ocr_span
    if index is None or not 0<=index<len(lines) or not span:return []
    line=lines[index];start,end=span
    if line['text'][start:end]!=region.before:return []
    words=line['words'];selected=[i for i,w in enumerate(words) if w.start<end and start<w.end]
    if not selected:return []
    occupied=[w.box for other in others if not (other.line_index==region.line_index and
        other.ocr_span==region.ocr_span and other.box==region.box) for w in other.words]
    contexts=[];seen={tuple(w.box for w in region.words)}
    for count in (1,2,len(words)):
        context=words[max(0,min(selected)-count):min(len(words),max(selected)+count+1)]
        key=tuple(w.box for w in context)
        if key in seen or any(w.box in occupied for w in context):continue
        seen.add(key);a,b=context[0].start,context[-1].end
        box=(min(w.box[0] for w in context),min(w.box[1] for w in context),max(w.box[2] for w in context),max(w.box[3] for w in context))
        contexts.append((replace(region,before=line['text'][a:b],after=line['text'][a:start]+region.after+line['text'][end:b],
            words=list(context),box=box,confidence=min(w.confidence for w in context)),count))
    return contexts


def render_adaptive_region(image,region,protected,lines,others):
    from . import imaging
    lane=imaging.caption_lane(image,region,lines);best=None;trials=0
    candidates=[(region,0),*_contexts(region,lines,others)]
    for candidate,count in candidates:
        candidate=replace(candidate,settings=dict(region.settings,_fit_lane=lane,_fit_mode='adaptive',_adaptive_fit=True,fit_retry=2))
        try:result,diagnostic,crops=imaging.render_region(image,candidate,protected)
        except RenderBlocked as error:
            # Optional larger contexts may lack a patch donor or another
            # repair prerequisite. They must not discard a valid local fit.
            if 'cannot fit safely' not in str(error) and not count:raise
            trials+=getattr(error,'fit_trials',0);continue
        trials+=diagnostic['fit_trials'];score=diagnostic['adaptive_parameters']['score']+.02*(len(candidate.words)-len(region.words))
        if count:
            diagnostic['fit_context']=dict(before=candidate.before,after=candidate.after,words_per_side=count)
            diagnostic.setdefault('warnings',[]).append('Auto-fit redrew '+str(len(candidate.words)-len(region.words))+
                ' unchanged context words within this caption line; check their lettering and spacing.')
        if best is None or score<best[0]:best=(score,result,diagnostic,crops)
        if score<=.35:break
    if best is None:
        error=RenderBlocked('Replacement cannot fit safely within image/protected text. '
            'Automatic limits reached after measured font, spacing, width and alignment searches; correct OCR geometry or edit the prefilled wording.')
        error.fit_trials=trials;raise error
    _,result,diagnostic,crops=best;diagnostic['fit_trials']=trials
    diagnostic['automatic_fit']=True;diagnostic['level']=max(2,diagnostic['level'])
    return result,diagnostic,crops
