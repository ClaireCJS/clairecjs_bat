"""Manual OCR corrections retain image geometry and local visual adjustments."""
from copy import deepcopy
from dataclasses import replace
from difflib import SequenceMatcher
from .errors import IntegrityError


def corrected_lines(lines,text):
    from .imaging import Word
    if not isinstance(text,str) or len(text)>100000 or not text.strip():
        raise IntegrityError('Keep some OCR text; the caption must be at most 100,000 characters.')
    target=text.splitlines()
    if len(target)!=len(lines):
        raise IntegrityError('Keep the existing OCR line breaks so corrections stay attached to the right image areas.')
    result=[]
    for original,caption in zip(lines,target):
        old=original['words'];tokens=caption.split()
        if tokens and not old:raise IntegrityError('This OCR line has no image geometry; correct an existing line instead.')
        ops=SequenceMatcher(None,[w.text for w in old],tokens,autojunk=False).get_opcodes()
        def edge(position):
            if position==0:return 0
            for kind,a,b,c,d in ops:
                if kind=='insert' and a==position:return d
            for kind,a,b,c,d in ops:
                if a<=position<=b:
                    if kind=='equal' or b-a==d-c:return c+position-a
                    if position==a:return c
                    if position==b:return d
            return len(tokens)
        groups=[]
        for kind,a,b,c,d in ops:
            if a==b:continue
            if kind=='equal' or b-a==d-c:groups.extend((i,i+1) for i in range(a,b))
            else:groups.append((a,b))
        words=[];offset=0
        for a,b in groups:
            selected=tokens[edge(a):edge(b)]
            if not selected:continue
            originals=old[a:b]
            box=(min(w.box[0] for w in originals),min(w.box[1] for w in originals),
                max(w.box[2] for w in originals),max(w.box[3] for w in originals))
            total=sum(len(t) for t in selected)+len(selected)-1;position=0
            for token in selected:
                left=box[0]+round((box[2]-box[0])*position/max(1,total))
                right=box[0]+round((box[2]-box[0])*(position+len(token))/max(1,total))
                if right<=left:raise IntegrityError('Too many corrected words for this OCR box; keep them within the original text area.')
                words.append(Word(token,(left,box[1],right,box[3]),min(w.confidence for w in originals),offset,offset+len(token)))
                offset+=len(token)+1;position+=len(token)+1
        value=' '.join(w.text for w in words)
        if value!=' '.join(tokens):raise IntegrityError('OCR correction could not retain its word geometry; correct one phrase at a time.')
        result.append({'text':value,'words':words})
    return result


def remap_adjustments(previous,lines):
    """OCR character offsets change; match the original image areas instead."""
    from .imaging import overlaps
    answer=[]
    for old in previous:
        if old.line_index is None or old.line_index>=len(lines):continue
        line=lines[old.line_index]
        selected=[w for w in line['words'] if any(overlaps(w.box,source.box) for source in old.words)]
        if not selected:continue
        span=(min(w.start for w in selected),max(w.end for w in selected))
        answer.append(replace(old,before=line['text'][span[0]:span[1]],words=deepcopy(selected),
            ocr_span=span,settings=deepcopy(old.settings)))
    return answer


def feminize_pronouns(text):
    """Whole words, matching case; distinguish possessive his from standalone his."""
    import re
    def change(match):
        old=match.group();key=old.casefold()
        new={'he':'she','him':'her','his':'hers'}[key]
        if key=='his':
            following=re.match(r'\s+([A-Za-z]+)',text[match.end():])
            if following and following[1].casefold() not in {
                'and','or','but','is','was','were','will','would','can','could','has','had','to','for','from','with','as','than','too'}:
                new='her'
        if old.isupper():return new.upper()
        if old.istitle():return new.title()
        return new
    return re.sub(r'\b(?:he|him|his)\b',change,text,flags=re.I)
