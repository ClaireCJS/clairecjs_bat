"""Single-key choices, contextual defaults, and independent repair availability."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_images import app_for,make_image
from image_caption_gender_fixer import adjustment_menu as menus,imaging
from image_caption_gender_fixer.errors import RenderBlocked
from image_caption_gender_fixer.fs import sha256


def test_one_raw_key_returns_without_enter_and_help_stays_in_menu(tmp_path,monkeypatch,capsys):
    app=app_for(tmp_path,answers=iter([]));app.ask_callback=None
    keys=iter(['h','x','s'])
    monkeypatch.setattr(menus,'console_key',lambda:next(keys))
    result=menus.choose(app,'Test menu',[menus.Choice('s','Smaller'),menus.Choice('b','Back')],'s','Explanation for this menu.')
    assert result=='s'
    output=capsys.readouterr().err
    assert 'Explanation for this menu' in output and 'ENTER=Smaller' in output and 'one key, no ENTER' in output


def test_enter_uses_enabled_default_and_disabled_choice_explains_reason(tmp_path,capsys):
    app=app_for(tmp_path,answers=iter(['p','']))
    assert menus.choose(app,'Repair',[menus.Choice('p','Patch','No safe donor patch'),menus.Choice('t','Telea'),menus.Choice('b','Back')],'t','Repair help')=='t'
    assert 'No safe donor patch' in capsys.readouterr().err


@pytest.mark.parametrize('key',['\x1b','b'])
def test_back_has_no_adjustment_side_effects(tmp_path,monkeypatch,key):
    app=app_for(tmp_path,answers=iter([key]))
    region=imaging.Region('boy','girl',(5,5,50,25),99,[],[])
    monkeypatch.setattr(imaging,'estimate',lambda *a:{'size':20})
    outcome=menus.visual(app,tmp_path/'a.png',SimpleNamespace(size=(300,200)),region,[],{'blocked':{'region':0,'reason':'Replacement cannot fit safely'},'artifacts':[]},lambda _:None,0)
    assert outcome=='back' and not region.settings and region.after=='girl'


def test_blocked_fit_default_shrinks_and_minimum_size_offers_prefilled_wording(tmp_path,monkeypatch):
    app=app_for(tmp_path,answers=iter(['']))
    region=imaging.Region('boy','girl',(5,5,50,25),99,[],[])
    proposal={'blocked':{'region':0,'reason':'Replacement cannot fit safely'},'artifacts':[]}
    monkeypatch.setattr(imaging,'estimate',lambda *a:{'size':20})
    assert menus.visual(app,tmp_path/'a.png',SimpleNamespace(size=(300,200)),region,[],proposal,lambda _:None,0)=='changed'
    assert region.settings['scale']==.95
    monkeypatch.setattr(imaging,'estimate',lambda *a:{'size':6})
    app.ask_callback=lambda _:'';seen=[]
    monkeypatch.setattr(menus,'edit_wording',lambda text:seen.append(text) or 'friend')
    assert menus.visual(app,tmp_path/'a.png',SimpleNamespace(size=(300,200)),region,[],proposal,lambda _:None,0)=='changed'
    assert seen==['girl'] and region.after=='friend'


def test_review_key_is_immediate_and_blocked_default_opens_adjustment(tmp_path,monkeypatch):
    app=app_for(tmp_path,answers=iter([]));app.ask_callback=None
    monkeypatch.setattr(menus,'console_key',lambda:'v')
    assert app.review_question('[y]approve [v]adjust [s]skip [c]cancel',False)=='v'
    monkeypatch.setattr(menus,'console_key',lambda:'\r')
    assert app.review_question('[v]adjust [s]skip [c]cancel',True)=='v'


def test_gui_approval_action_is_not_misread_as_console_add_rule(tmp_path):
    app=app_for(tmp_path,answers=iter([]));app.ask_callback=None
    class Artwork:
        stopped=SimpleNamespace(is_set=lambda:False)
        def begin_review(self,*args):return 'current-token'
        def review_action(self,token):return 'a'
        def end_review(self,token):self.ended=token
    app.floating_artwork=Artwork()
    assert app.review_question('[y]approve [a]add rule [v]adjust [s]skip [c]cancel',False)=='a'
    assert app.floating_artwork.ended=='current-token'


def test_returning_from_adjustment_reuses_current_proposal(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter(['v','\x1b','s']))
    actual=imaging.proposal;calls=[]
    def proposal(*a,**k):result=actual(*a,**k);calls.append(result['transaction']);return result
    monkeypatch.setattr(imaging,'proposal',proposal)
    result,code=app.process([str(source)])
    assert code==10 and len(calls)==1 and sha256(source)==original


def test_cancel_from_adjustment_exits_menu_and_retains_original(tmp_path):
    source=tmp_path/'caption.png';make_image(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter(['v','q']))
    result,code=app.process([str(source)])
    assert code==20 and sha256(source)==original and result['results'][0]['state']=='canceled'


def test_background_available_even_when_replacement_text_cannot_fit(tmp_path,monkeypatch,capsys):
    from PIL import Image
    source=tmp_path/'caption.png';make_image(source)
    image,_=imaging.decode(source)
    region=imaging.Region('good boi','girl'*100,(90,116,398,199),99,[imaging.Word('good boi',(90,116,398,199),99,0,8)],[])
    repair,diagnostic,crops=imaging.render_region(image,region,[region.box],repair_only=True)
    assert diagnostic['background_only'] and 'repair_score' in diagnostic and 'repair' in crops
    with pytest.raises(RenderBlocked,match='fit'):imaging.render_region(image,region,[region.box])
    app=app_for(tmp_path,answers=iter(['t']));artifacts=[]
    proposal={'transaction':'test-preview','artifacts':artifacts}
    assert menus.background(app,source,image,region,[region.box],proposal,lambda _:None,0)=='changed'
    assert region.settings['repair']=='telea'
    output=capsys.readouterr().err
    assert 'background available; text/layout still blocked' in output
    assert not 'Telea inpainting — unavailable' in output
    app.cleanup(artifacts)


def test_real_missing_patch_donor_has_explanation_but_other_repairs_remain_available(tmp_path,monkeypatch,capsys):
    source=tmp_path/'caption.png';make_image(source)
    image,_=imaging.decode(source)
    word=imaging.Word('good boi',(90,116,398,199),99,0,8)
    region=imaging.Region('good boi','good girl',word.box,99,[word],[])
    # Cover every in-bounds donor candidate without covering this word's mask.
    protected=[word.box,(0,211,image.width,image.height),(410,0,image.width,211)]
    with pytest.raises(RenderBlocked,match='No safe neighboring patch'):
        imaging.render_region(image,replace(region,settings={'repair':'patch'}),protected,repair_only=True)
    for method in ('fill','telea'):
        _,diagnostic,_=imaging.render_region(image,replace(region,settings={'repair':method}),protected,repair_only=True)
        assert diagnostic['background_only']
    app=app_for(tmp_path,answers=iter(['p','t']));artifacts=[]
    proposal={'transaction':'no-donor-preview','artifacts':artifacts}
    assert menus.background(app,source,image,region,protected,proposal,lambda _:None,0)=='changed'
    assert region.settings['repair']=='telea'
    assert 'No safe neighboring patch' in capsys.readouterr().err
    app.cleanup(artifacts)



def test_prefilled_color_uses_detected_current_color(tmp_path,monkeypatch):
    region=imaging.Region('boy','girl',(5,5,50,25),99,[],[])
    app=app_for(tmp_path,answers=iter(['c','']))
    monkeypatch.setattr(imaging,'estimate',lambda *a:{'size':20,'foreground':(10,20,30,255)})
    assert menus.visual(app,tmp_path/'a.png',SimpleNamespace(size=(300,200)),region,[],{'artifacts':[]},lambda _:None,0)=='changed'
    assert region.settings['foreground']==(10,20,30,255)


def test_extra_controls_keep_existing_mask_adjustments_available_by_key(tmp_path):
    region=imaging.Region('boy','girl',(5,5,50,25),99,[],[])
    app=app_for(tmp_path,answers=iter(['x','r','4']))
    assert menus.advanced(app,SimpleNamespace(size=(300,200)),region)=='changed'
    assert region.settings['mask_sides']=={'right':4}



def test_background_enter_chooses_lowest_available_score_even_if_text_is_blocked(tmp_path,monkeypatch,capsys):
    scores={'fill':50,'gradient':20,'telea':10,'navier':8}
    def render(image,region,protected,*,repair_only=False):
        method=region.settings['repair']
        if method=='patch':raise RenderBlocked('No safe neighboring patch')
        if not repair_only:raise RenderBlocked('Replacement cannot fit safely')
        return image,{'repair_score':scores[method]},{}
    monkeypatch.setattr(imaging,'render_region',render)
    app=app_for(tmp_path,answers=iter(['p','']))
    region=imaging.Region('boy','girl',(5,5,50,25),99,[],[])
    assert menus.background(app,tmp_path/'a.png',None,region,[],{'artifacts':[],'transaction':'rank'},lambda _:None,0)=='changed'
    assert region.settings['repair']=='navier'
    assert 'ENTER=Navier inpainting' in capsys.readouterr().err


def test_all_background_failures_default_to_back_without_mutation(tmp_path,monkeypatch):
    def unavailable(*args,**kwargs):raise RenderBlocked('No reliable erasure mask')
    monkeypatch.setattr(imaging,'render_region',unavailable)
    app=app_for(tmp_path,answers=iter(['']))
    region=imaging.Region('boy','girl',(5,5,50,25),99,[],[])
    assert menus.background(app,tmp_path/'a.png',None,region,[],{'artifacts':[],'transaction':'none'},lambda _:None,0)=='back'
    assert not region.settings


def test_value_escape_returns_to_menu_without_setting_color(tmp_path,monkeypatch):
    monkeypatch.setattr(imaging,'estimate',lambda *a:{'size':20})
    app=app_for(tmp_path,answers=iter(['c','\x1b','b']))
    region=imaging.Region('boy','girl',(5,5,50,25),99,[],[])
    assert menus.visual(app,tmp_path/'a.png',SimpleNamespace(size=(300,200)),region,[],{'artifacts':[]},lambda _:None,0)=='back'
    assert not region.settings
