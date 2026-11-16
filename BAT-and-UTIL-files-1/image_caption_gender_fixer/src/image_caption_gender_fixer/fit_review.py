"""Rank a bounded set of complete in-memory renders for interactive review."""
from dataclasses import dataclass,field
from difflib import SequenceMatcher
from pathlib import Path
from subprocess import TimeoutExpired
import re

from .errors import DependencyUnavailable


PROFILES=('larger type','natural width')


@dataclass
class FitReview:
    """Per-image review choices; retain recipes only, not full-size images."""
    choices:list=field(default_factory=list)
    position:int=0

    def advance(self):
        if len(self.choices)>1:self.position=(self.position+1)%len(self.choices)

    def summary(self):
        if len(self.choices)<2:return None
        _,_,desc=self.choices[self.position]
        return dict(number=self.position+1,total=len(self.choices),description=desc)


def _words(text):
    return re.findall(r'[^\W_]+',text.casefold())


def _expected(regions,diagnostic,index):
    if diagnostic.get('fit_context'):return diagnostic['fit_context']['after']
    if diagnostic.get('line_fit'):return diagnostic['line_fit']['after']
    return regions[index].after


def _ocr_quality(expected,original,detected):
    words=_words(expected);seen=_words(' '.join(line['text'] for line in detected))
    if not words:return 0.,0
    matched=sum(group.size for group in SequenceMatcher(None,words,seen,autojunk=False).get_matching_blocks())
    # Penalize leftover source lettering, but accept legitimate occurrences
    # that the replacement itself still contains (for example repeated names).
    before=_words(original)
    def occurrences(tokens):
        return sum(tokens[i:i+len(before)]==before for i in range(len(tokens)-len(before)+1)) if before else 0
    excess=max(0,occurrences(seen)-occurrences(words))
    precision=2*matched/max(1,len(words)+len(seen))
    confidences=[w.confidence for line in detected for w in line.get('words',[]) if w.confidence>=0]
    confidence=round(sum(confidences)/len(confidences)/10) if confidences else 0
    return max(0.,precision-.2*excess),confidence


def _score(regions,index,diagnostic,detected):
    expected=_expected(regions,diagnostic,index)
    source=diagnostic.get('fit_context',diagnostic.get('line_fit',{})).get('before',regions[index].before)
    accuracy,confidence=_ocr_quality(expected,source,detected)
    # Small OCR confidence differences should not outweigh visual quality.
    contrast=min(1.,max(0.,diagnostic.get('ink_contrast',0)/110))
    context=diagnostic.get('fit_context') or {}
    visual=(.5*diagnostic['fit_scale']+.45*diagnostic.get('horizontal_scale',1)+.65*contrast
        -.3*bool(diagnostic.get('expansion_warning'))-.15*min(1,diagnostic.get('seam_warning',0)/85)
        -.025*max(0,len(context.get('after','').split())-len(regions[index].after.split())))
    return round(accuracy,2),visual+.01*confidence


def _distinct(a,b):
    return (a.get('font_used')!=b.get('font_used') or a.get('source_boxes')!=b.get('source_boxes') or
        any(abs(x-y)>=2 for x,y in zip(a['text_bounds'],b['text_bounds'])))


def _description(index,d):
    label='Region '+str(index+1)+' · '+Path(d['font_used']).stem
    p=d.get('adaptive_parameters')
    size=str(p['font_size'])+' px' if p else str(round(d['fit_scale']*100))+'% size'
    width=str(round(d['horizontal_scale']*100))+'% width'
    offset=(' · offset '+str(p['dx'])+','+str(p['dy'])+' px') if p and (p['dx'] or p['dy']) else ''
    return label+' · '+size+' · '+width+offset


def select(review,render,recognize,regions):
    """Run at most two additional plans for the most constrained region."""
    if review.choices:
        target,profile,_=review.choices[review.position]
        try:result=render((target,profile) if profile else None)
        except DependencyUnavailable:result=None
        if result and not result[2]:return result
        # Never present an incomplete replay as an approvable alternative.
        review.choices.clear();review.position=0
        return render(None)
    base=render(None)
    if base[2]:return base
    eligible=[(index,d) for index,d,_ in base[1] if regions[index].after.strip() and
        (d.get('automatic_fit') or d.get('fit_action')!='normal' or d.get('fit_scale',1)<=.9 or d.get('expansion_warning'))]
    if not eligible:return base
    target,base_d=min(eligible,key=lambda item:item[1]['fit_scale']*item[1]['horizontal_scale'])
    # The selector changes only the chosen region. Do not swap in a plan
    # that also moved some other edit or changed which words it erased.
    def other_layout(plan):
        return [(i,d['members'],d['text_bounds'],d['font_used'],d['source_boxes'])
            for i,d,_ in plan[1] if i!=target]
    rest=other_layout(base);candidates=[base_d];options=[]
    def evaluate(plan,diagnostic,profile):
        # OCR is a ranking signal. A timed-out candidate need not discard a
        # valid geometric fit; the selected proposal still gets verification.
        try:detected=recognize(plan[0],diagnostic['affected'])
        except (DependencyUnavailable,TimeoutExpired):detected=[]
        options.append((_score(regions,target,diagnostic,detected),(target,profile,_description(target,diagnostic))))
    evaluate(base,base_d,None);best=base
    for profile in PROFILES:
        plan=render((target,profile))
        if plan[2] or other_layout(plan)!=rest:continue
        d=next((d for i,d,_ in plan[1] if i==target),None)
        if d is None or not all(_distinct(d,previous) for previous in candidates):continue
        candidates.append(d);evaluate(plan,d,profile)
        if options[-1][0]>max(score for score,_ in options[:-1]):best=plan
    options.sort(key=lambda item:item[0],reverse=True)
    review.choices=[choice for _,choice in options]
    return best
