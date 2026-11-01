"""Plan complete edits before saving crops; jointly fit crowded caption lines."""
from dataclasses import replace

from .errors import RenderBlocked


def _fit(image,region,protected,lines,others):
    from . import imaging
    try:return imaging.render_fitting_region(image,region,protected,lines,others)
    except RenderBlocked as error:
        if 'cannot fit safely' not in str(error) or int(region.settings.get('fit_retry',0)):
            raise
        previous=getattr(error,'fit_trials',0)
    # Start with the least intrusive fit. Escalate automatically, once, before
    # asking the human; approval is still required for the resulting image.
    candidate=replace(region,settings=dict(region.settings,move_squeeze=True,fit_retry=1))
    try:result,diagnostic,crops=imaging.render_fitting_region(image,candidate,protected,lines,others)
    except RenderBlocked as error:
        error.fit_trials=previous+getattr(error,'fit_trials',0)
        raise
    diagnostic['fit_trials']+=previous
    diagnostic['automatic_fit']=True
    diagnostic.setdefault('warnings',[]).append('Automatic fitting tightened this caption; inspect readability before approving.')
    return result,diagnostic,crops


def _line_task(image,regions,lines,index):
    """Only combine validated, compatible edits within the same caption lane."""
    from . import imaging
    line_index=regions[index].line_index
    if line_index is None or not 0<=line_index<len(lines):return None
    members=[i for i,r in enumerate(regions) if not r.skipped and r.line_index==line_index]
    if len(members)<2:return None
    line=lines[line_index];words=line['words']
    if not words:return None
    settings=[]
    for i in members:
        cfg={k:v for k,v in regions[i].settings.items() if k not in ('move_squeeze','fit_retry') and not k.startswith('_')}
        if any(k in cfg for k in ('box','dx','dy','rotation','protected','mask_sides')):return None
        settings.append(cfg)
    if any(cfg!=settings[0] for cfg in settings[1:]):return None
    ordered=sorted((regions[i] for i in members),key=lambda r:r.ocr_span or (-1,-1))
    previous=0;after=line['text']
    for region in ordered:
        if region.ocr_span is None:return None
        a,b=region.ocr_span
        if not 0<=previous<=a<b<=len(line['text']) or line['text'][a:b]!=region.before:return None
        previous=b
    for region in reversed(ordered):
        a,b=region.ocr_span;after=after[:a]+region.after+after[b:]
    box=(min(w.box[0] for w in words),min(w.box[1] for w in words),
         max(w.box[2] for w in words),max(w.box[3] for w in words))
    lanes=[imaging.caption_lane(image,regions[i],lines) for i in members]
    lane=(max(b[0] for b in lanes),max(b[1] for b in lanes),min(b[2] for b in lanes),min(b[3] for b in lanes))
    if not (lane[0]<=box[0]<box[2]<=lane[2] and lane[1]<=box[1]<box[3]<=lane[3]):return None
    combined=replace(regions[index],before=line['text'],after=after,box=box,words=list(words),
        confidence=min(w.confidence for w in words),ocr_span=(0,len(line['text'])),
        settings=dict(settings[0],move_squeeze=True,fit_retry=1))
    return min(members),members,combined


def render_plan(image,regions,protected,lines):
    """A failed word fit may restart its line as one coherent replacement.

    No artifact or source is written while searching. Each line is combined at
    most once, and protected ink from other lines always remains protected.
    """
    tasks=[(i,[i],r) for i,r in enumerate(regions) if not r.skipped]
    combined_lines=set()
    while True:
        current=image.copy();reserved=list(protected);rendered=[]
        for index,members,region in tasks:
            others=[r for i,r in enumerate(regions) if i not in members]
            try:current,diagnostic,crops=_fit(current,region,reserved,lines,others)
            except RenderBlocked as error:
                replacement=None
                if 'cannot fit safely' in str(error) and region.line_index not in combined_lines:
                    replacement=_line_task(image,regions,lines,index)
                if replacement is not None:
                    combined_lines.add(region.line_index)
                    first,group,combined=replacement
                    tasks=[task for task in tasks if not any(i in group for i in task[1])]
                    tasks.append(replacement);tasks.sort(key=lambda task:task[0])
                    break
                reason=str(error)
                if len(members)>1:reason+=' Fitting '+str(len(members))+' substitutions together within this caption line also failed.'
                return current,rendered,{'region':index,'reason':reason,'fit_trials':getattr(error,'fit_trials',0),
                    'fit_exhausted':'cannot fit safely' in str(error)}
            diagnostic['members']=members
            if len(members)>1:
                diagnostic['line_fit']={'before':region.before,'after':region.after}
                diagnostic['automatic_fit']=True;diagnostic['level']=max(2,diagnostic['level'])
                diagnostic.setdefault('warnings',[]).append('Crowded substitutions were fitted together within their original caption line.')
            # Replaced OCR boxes are obsolete. Reserve actual new ink rather
            # than both old and new boxes, including any redrawn context words.
            for box in diagnostic.get('source_boxes',[w.box for w in region.words]):
                if box in reserved:reserved.remove(box)
            reserved.append(diagnostic.get('text_bounds',diagnostic['affected']))
            rendered.append((index,diagnostic,crops))
        else:return current,rendered,None
