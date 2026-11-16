"""Rank real previews, cycle to a fresh transaction, and approve that exact fit."""
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from image_caption_gender_fixer import fit_review,imaging,smart_fitting
from image_caption_gender_fixer.fs import sha256
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from test_adaptive_fitting import isolated_word,style
from test_images import app_for


def test_ranking_prefers_the_readable_render_and_next_uses_fresh_approval(tmp_path,monkeypatch,style):
    image,lines,region,protected=isolated_word(style)
    source=tmp_path/'neutral.png';image.save(source);original=sha256(source)
    baseline,rendered,blocked=smart_fitting.render_plan(image,[region],protected,lines)
    assert not blocked
    baseline_ink=baseline.crop(rendered[0][1]['affected']).tobytes()
    app=app_for(tmp_path,answers=iter([]));seen=[];calls=[]
    monkeypatch.setattr(app,'ocr_lines',lambda *args,**kwargs:(lines,False))
    monkeypatch.setattr(imaging,'regions',lambda *args:([region],protected))
    monkeypatch.setattr(imaging,'scene_faces',lambda image:[])
    def recognize(crop,*args,**kwargs):
        calls.append((crop.size,kwargs.get('timeout')))
        return [{'text':'cat' if crop.tobytes()==baseline_ink else region.after}]
    monkeypatch.setattr(imaging,'ocr',recognize)
    def review(path,proposal,regions):
        assert not proposal.get('blocked') and proposal['level']>=2
        assert sha256(source)==original and not (tmp_path/'.history.icgf').exists()
        assert sum(a['kind']=='proposal' for a in proposal['artifacts'])==1
        summary=proposal['fit_review'];assert 2<=summary['total']<=3
        staged=Path(proposal['stage'])
        with Image.open(staged) as handle:pixels=handle.convert('RGBA').tobytes()
        seen.append((proposal['transaction'],summary['number'],staged,pixels))
        if len(seen)==1:
            assert proposal['verification'][0]['replacement_confirmed']
            initial_ocr_calls=len(calls)
            assert 2<=initial_ocr_calls<=3 and all(timeout==3 for _,timeout in calls)
            return {'action':'next_fit'}
        if len(seen)<=summary['total']:return 'next_fit'
        return 'a'
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert code==0 and 3<=len(seen)<=4
    assert [v[1] for v in seen]==[*range(1,len(seen)),1]
    assert len({v[0] for v in seen})==len(seen)
    assert len({v[3] for v in seen})==len(seen)-1 and seen[0][3]==seen[-1][3]
    assert len(calls)==2*(len(seen)-1)
    assert all(not item[2].exists() for item in seen)
    with Image.open(result['results'][0]['corrected']) as corrected:
        assert corrected.convert('RGBA').tobytes()==seen[-1][3]
    assert region.settings=={}


def test_layout_comparison_rejects_alternatives_that_change_other_regions():
    regions=[SimpleNamespace(after='clear text',before='text'),SimpleNamespace(after='more',before='less')]
    def diagnostic(index,x):
        return dict(members=[index],text_bounds=(x,0,x+10,10),font_used='Arial.ttf',source_boxes=[(0,0,1,1)],
                    affected=(0,0,30,10),fit_scale=.8 if index==0 else 1.,horizontal_scale=.9 if index==0 else 1.,fit_action='squeeze' if index==0 else 'normal')
    calls=[]
    def render(alternative):
        calls.append(alternative)
        return alternative,[(0,diagnostic(0,2 if alternative else 0),{}),(1,diagnostic(1,19 if alternative else 20),{})],None
    review=fit_review.FitReview()
    result=fit_review.select(review,render,lambda output,box:[{'text':'clear text'}],regions)
    assert result[0] is None and review.summary() is None and len(calls)==3


def test_ocr_ranking_penalizes_wrong_order_and_leftover_source():
    correct=fit_review._ocr_quality('the clear line','old line',[{'text':'The clear line!'}])
    wrong_order=fit_review._ocr_quality('the clear line','old line',[{'text':'clear line the'}])
    ghost=fit_review._ocr_quality('the clear line','old line',[{'text':'the clear line old line'}])
    assert correct[0]==1 and correct[0]>wrong_order[0] and correct[0]>ghost[0]
    assert fit_review._ocr_quality('old line is fine','old line',[{'text':'old line is fine'}])[0]==1


def test_popup_next_fit_hotkey_shows_position_and_preserves_pending_caption(tmp_path):
    source=tmp_path/'neutral.png';Image.new('RGB',(300,230),'white').save(source)
    viewing=AlbumArtReview([{'path':str(source),'title':'Review'}],{'detected':'cat','proposed':'kitten'},floating=True)
    actions=[]
    try:
        viewing.passive_show();viewing.root.update_idletasks();viewing.draw()
        selected={'index':0,'before':'cat','after':'kitten','fit_review':{'number':1,'total':3,'description':'Region 1 · Arial · 20 px · 90% width'}}
        viewing.set_review(actions.append,[],False,changes=[selected],source=str(source))
        button=viewing.buttons['next_fit'];assert '1/3' in button.cget('text') and '20 px' in viewing.notice.cget('text')
        event=SimpleNamespace(widget=viewing.canvas,state=0,char='t',keysym='t')
        viewing.button_hotkey(event);assert actions==[{'action':'next_fit'}]
        viewing.set_review(actions.append,[],False,changes=[selected],source=str(source))
        viewing.proposed_caption.insert('end','!');viewing.caption_modified()
        assert button.instate(['disabled'])
        viewing.button_hotkey(event);assert len(actions)==1
        assert viewing.proposed_caption.get('1.0','end-1c')=='kitten!'
    finally:
        viewing.root.after(0,lambda:viewing.choose('c'));viewing.show()


def test_console_t_cycles_without_approving(tmp_path):
    app=app_for(tmp_path,answers=iter(['t']))
    assert app.review_question('[t]ry next fit, [y]approve, [s]kip: ',False)=='next_fit'
