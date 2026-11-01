"""Prefilled caption edits mapped back to the detected text geometry."""
from copy import deepcopy
from dataclasses import replace
from difflib import SequenceMatcher
from .errors import IntegrityError

def caption_regions(lines,text,previous_regions=()):
    from .imaging import Region
    if not isinstance(text,str) or len(text)>100000:raise IntegrityError('Caption is too long.')
    if not text.strip():raise IntegrityError('Keep some caption text; use Skip to leave the image unchanged.')
    before=[line['text'] for line in lines];after=text.splitlines()
    if not before:raise IntegrityError('No detected text geometry is available for this image.')
    # Retain matching lines. Reflow only edited runs when lines were added or
    # removed, preserving the original caption footprint and unaffected lines.
    replacements={}
    for kind,a,b,c,d in SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if kind=='equal':continue
        if a==b:
            anchor=max(0,a-1);replacements[anchor]=replacements.get(anchor,before[anchor])+' '+' '.join(after[c:d]);continue
        new=after[c:d]
        if b-a==len(new):
            replacements.update((a+i,t) for i,t in enumerate(new));continue
        words=' '.join(new).split();total=sum(max(1,len(t)) for t in before[a:b]);offset=0;weight=0
        for i in range(a,b):
            weight+=max(1,len(before[i]));end=len(words) if i==b-1 else round(len(words)*weight/total)
            replacements[i]=' '.join(words[offset:end]);offset=end
    regions=[];protected=[w.box for line in lines for w in line['words']]
    # A rebuild belongs to this image's current review. Reuse its source spans
    # rather than widening every adjusted word into a fresh, unstyled line.
    for previous in previous_regions:
        if previous.line_index is not None:
            replacements.setdefault(previous.line_index,lines[previous.line_index]['text'])
    for i,after in sorted(replacements.items()):
        line=lines[i];words=line['words']
        previous=[r for r in previous_regions if r.line_index==i and r.ocr_span is not None]
        if previous:
            regions.extend(_edited_line(line,i,after,previous));continue
        if not words or line['text']==after:continue
        box=(min(w.box[0] for w in words),min(w.box[1] for w in words),max(w.box[2] for w in words),max(w.box[3] for w in words))
        regions.append(Region(line['text'],after,box,min(w.confidence for w in words),words,
            [{'rule':'manual-caption','before':line['text'],'after':after,'original_span':[0,len(line['text'])]}],
            line_index=i,ocr_span=(0,len(line['text']))))
    return regions,protected

def _settings_for(region,previous):
    """Copy only settings belonging to overlapping spans on the same OCR line."""
    matches=[old for old in previous if old.line_index==region.line_index and
        old.ocr_span is not None and region.ocr_span is not None and
        old.ocr_span[0]<region.ocr_span[1] and region.ocr_span[0]<old.ocr_span[1]]
    settings=[old.settings for old in matches if old.settings]
    if settings and any(value!=settings[0] for value in settings[1:]):
        raise IntegrityError('This edit combines text with different visual adjustments. '
            'Edit those substitutions separately to keep their individual settings.')
    return deepcopy(settings[0]) if settings else {}


def preserve_adjustments(regions,previous_regions):
    """Reapply local visual choices after rebuilding substitutions from rules."""
    answer=[]
    for region in regions:
        settings=_settings_for(region,previous_regions)
        exact=next((old for old in previous_regions if old.line_index==region.line_index and
            old.ocr_span==region.ocr_span and old.before==region.before),None)
        if exact is not None:
            # OCR fixes can change the source geometry as well as its style.
            region=replace(region,box=exact.box,words=deepcopy(exact.words),
                skipped=exact.skipped and exact.after==region.after)
        answer.append(replace(region,settings=settings))
    return answer


def _boundary(opcodes,position,end=False):
    # Insertion at an edge belongs to the expanded word containing that edit.
    for kind,a,b,c,d in opcodes:
        if kind=='insert' and a==position:return d if end else c
    for kind,a,b,c,d in opcodes:
        if a<=position<=b:
            if position==a:return c
            if position==b:return d
            if kind=='equal':return c+position-a
            return d if end else c
    return opcodes[-1][4] if opcodes else position


def _edited_line(line,index,target,previous):
    """Anchor caption edits to the existing regions, including separate styles."""
    from .imaging import Region,full_captions
    previous=sorted(previous,key=lambda r:r.ocr_span)
    source=line['text'];pieces=[];current='';offset=0
    for region in previous:
        a,b=region.ocr_span
        if not 0<=offset<=a<b<=len(source):
            raise IntegrityError('Caption geometry overlaps; keep the current proposal and correct OCR first.')
        gap=source[offset:a];start=len(current);current+=gap
        if gap:pieces.append((offset,a,start,len(current),False))
        start=len(current);current+=region.before if region.skipped else region.after
        pieces.append((a,b,start,len(current),True));offset=b
    start=len(current);current+=source[offset:]
    if offset<len(source):pieces.append((offset,len(source),start,len(current),False))
    if current==target:return deepcopy(previous)
    if len(previous)==1 and previous[0].ocr_span==(0,len(source)):
        region=deepcopy(previous[0]);region.after=target;region.skipped=False
        region.trace=[{'rule':'manual-caption','before':region.before,'after':target,'original_span':[0,len(source)]}]
        return [region] if region.before!=target else []
    opcodes=SequenceMatcher(None,current,target,autojunk=False).get_opcodes()
    spans=[region.ocr_span for region in previous]
    for kind,a,b,c,d in opcodes:
        if kind=='equal':continue
        selected=[p for p in pieces if p[2]<b and a<p[3]]
        if a==b:
            selected=[p for p in pieces if p[2]<a<p[3]] or [p for p in pieces if p[2]<=a<=p[3]][:1]
        projected=[]
        for x,y,u,v,changed in selected:
            if changed:projected.append((x,y))
            else:projected.append((x+max(0,a-u),x+min(v-u,b-u)))
        if not projected:continue
        left=min(p[0] for p in projected);right=max(p[1] for p in projected)
        words=[w for w in line['words'] if w.start<right and left<w.end]
        if not words:
            words=[min(line['words'],key=lambda w:min(abs(w.start-left),abs(w.end-left)))]
        spans.append((min(w.start for w in words),max(w.end for w in words)))
    groups=[]
    for a,b in sorted(spans):
        if groups and a<groups[-1][1]:groups[-1]=(groups[-1][0],max(b,groups[-1][1]))
        else:groups.append((a,b))
    def current_edge(position):
        delta=0
        for old in previous:
            a,b=old.ocr_span
            if position<=a:break
            delta+=len(old.before if old.skipped else old.after)-(b-a)
        return position+delta
    answer=[]
    for a,b in groups:
        left=_boundary(opcodes,current_edge(a));right=_boundary(opcodes,current_edge(b),True)
        wording=target[left:right]
        exact=next((old for old in previous if old.ocr_span==(a,b)),None)
        if exact is not None:
            region=deepcopy(exact)
            if wording==(region.before if region.skipped else region.after):answer.append(region);continue
            region.after=wording;region.skipped=False
        else:
            words=[w for w in line['words'] if a<=w.start and w.end<=b]
            box=(min(w.box[0] for w in words),min(w.box[1] for w in words),
                max(w.box[2] for w in words),max(w.box[3] for w in words))
            region=Region(source[a:b],wording,box,min(w.confidence for w in words),deepcopy(words),[],
                line_index=index,ocr_span=(a,b))
            region.settings=_settings_for(region,previous)
        if region.before==region.after:continue
        region.trace=[{'rule':'manual-caption','before':region.before,'after':region.after,'original_span':[a,b]}]
        answer.append(region)
    # Never silently drop wording at a punctuation/line-reflow boundary. A single
    # shared style can safely use the original line-sized fallback; conflicting
    # per-word settings remain intact and the edit is refused instead of reset.
    check=[replace(r,line_index=0) for r in answer]
    if full_captions([line],check)['proposed']!=target:
        words=line['words'];box=(min(w.box[0] for w in words),min(w.box[1] for w in words),
            max(w.box[2] for w in words),max(w.box[3] for w in words))
        region=Region(source,target,box,min(w.confidence for w in words),deepcopy(words),
            [{'rule':'manual-caption','before':source,'after':target,'original_span':[0,len(source)]}],
            line_index=index,ocr_span=(0,len(source)))
        region.settings=_settings_for(region,previous)
        return [region] if source!=target else []
    return answer


def edit_caption(text):
    import tkinter as tk
    from tkinter import ttk
    root=tk.Tk();root.title('Edit proposed caption — current text is already filled in');root.geometry('850x600')
    root.columnconfigure(0,weight=1);root.rowconfigure(1,weight=1);result=[None]
    ttk.Label(root,text='Edit the caption below. Regenerate builds a new image for approval.').grid(row=0,column=0,padx=10,pady=8)
    editor=tk.Text(root,wrap='word',undo=True,font=('Segoe UI',13),bg='#171b22',fg='#ffff58',insertbackground='#ffff58')
    editor.insert('1.0',text);editor.grid(row=1,column=0,sticky='nsew',padx=10)
    scroll=ttk.Scrollbar(root,command=editor.yview);scroll.grid(row=1,column=1,sticky='ns');editor.configure(yscrollcommand=scroll.set)
    def save():result[0]=editor.get('1.0','end-1c');root.quit()
    ttk.Button(root,text='Regenerate from edits',command=save).grid(row=2,column=0,pady=10)
    root.protocol('WM_DELETE_WINDOW',root.quit);root.bind('<Escape>',lambda e:root.quit())
    try:editor.focus_set();root.mainloop();return result[0]
    finally:root.destroy()
