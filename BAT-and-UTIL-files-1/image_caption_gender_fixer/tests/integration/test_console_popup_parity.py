import gc,time
from pathlib import Path
from types import SimpleNamespace
import pytest
from PIL import Image
from test_images import ROOT,app_for,make_image
from image_caption_gender_fixer import adjustment_menu as menus,console_input,imaging
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer.floating_artwork import FloatingArtwork


@pytest.mark.parametrize('width',[40,80,120,180,300])
def test_compact_menu_respects_width_and_keeps_every_choice_and_reason(width):
    from image_caption_gender_fixer.newspaper_columns import display_width
    choices=[menus.Choice(chr(97+i),'Choice '+str(i)) for i in range(15)]
    choices[1].reason=choices[2].reason='Rendering is blocked; adjust the proposal before approving.'
    rows=menus.menu_rows(choices,'a',width,False);text='\n'.join(rows)
    assert all(display_width(row)<width for row in rows)
    assert all('['+c.key.upper()+']' in text for c in choices)
    assert ' '.join(text.split()).count(choices[1].reason)==1
    if width>=80:assert len(rows)<len(choices)


@pytest.mark.parametrize('modifiers,expected',[(8,console_input.SHOW_ART),(4,console_input.SHOW_ART),(10,console_input.FRONT_ART),(5,console_input.FRONT_ART)])
def test_shortcuts_use_modifier_state_from_the_key_event(modifiers,expected):
    assert console_input.decode_key(True,0x41,'\x01',modifiers)==expected
    assert console_input.decode_key(False,0x41,'\x01',modifiers) is None
    assert console_input.decode_key(True,0x41,'a',0)=='a'


def test_every_review_action_is_available_in_artwork_and_cancel_is_a_job_decision(tmp_path):
    path=tmp_path/'image.png';Image.new('RGB',(200,600),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Review'}],floating=True);actions=[]
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        assert set(('a','r','s','d','add_rule','edit_caption','m','o','v','b','ignore','c','help')).issubset(viewer.buttons)
        for key,action in [('r','s'),('s','s'),('o','o'),('v','v'),('b','b'),('c','c')]:
            viewer.set_review(actions.append,[],False,changes=[{'index':0,'before':'old','after':'new'}],source=str(path))
            viewer._has_drawn=True;viewer.set_review(actions.append,[],False)
            viewer.buttons[key].invoke();assert actions[-1]==action
            assert viewer.root.winfo_exists()
        viewer.set_review(actions.append,[],True)
        assert viewer.buttons['a'].instate(['disabled'])
        assert 'p' not in viewer.buttons and 'q' not in viewer.buttons
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_triple_click_uses_the_default_viewer_for_the_displayed_image(tmp_path,monkeypatch):
    from image_caption_gender_fixer import paf_album_art
    path=tmp_path/'spaces & brackets [1].png';Image.new('RGB',(200,600),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Displayed proposal'}],floating=True);opened=[];snapshot=path.read_bytes()
    monkeypatch.setattr(paf_album_art.os,'startfile',lambda path,operation:opened.append((path,operation)))
    try:
        assert viewer.canvas.bind('<Triple-Button-1>')
        assert viewer.open_default_viewer()=='break'
        assert opened==[(str(path.absolute()),'open')] and path.read_bytes()==snapshot
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_visual_submenus_and_prefilled_fields_can_be_completed_in_artwork(tmp_path,monkeypatch):
    from image_caption_gender_fixer.popup_controls import ControlPanel
    gc.collect();path=tmp_path/'image.png';Image.new('RGB',(400,200),'white').save(path)
    original=ControlPanel.show;steps=[]
    def show(panel,spec,callback):
        original(panel,spec,callback)
        if spec is None:return
        steps.append(spec)
        if spec['kind']=='menu':panel.viewer.root.after(20,lambda:panel.buttons['t'].invoke())
        else:
            assert spec['default']=='0'
            panel.viewer.root.after(20,lambda:(panel.value.set('-1'),panel.buttons['submit'].invoke()))
    monkeypatch.setattr(ControlPanel,'show',show);monkeypatch.setattr(menus,'console_key',lambda:None)
    monkeypatch.setattr(imaging,'estimate',lambda *args:{'size':20})
    art=FloatingArtwork(ROOT);app=app_for(tmp_path,answers=iter([]));app.ask_callback=None;app.floating_artwork=art
    region=imaging.Region('old','new',(20,20,70,45),99,[],[])
    try:
        art.update(path,'Proposal')
        result=menus.visual(app,path,SimpleNamespace(size=(400,200)),region,[],{'artifacts':[]},lambda _:None,0)
        assert result=='changed' and region.settings['tracking']==-1
        assert [step['kind'] for step in steps]==['menu','input']
    finally:art.close()


def test_console_hotkeys_do_not_answer_or_reset_current_menu(tmp_path,monkeypatch):
    app=app_for(tmp_path,answers=iter([]));app.ask_callback=None;calls=[]
    keys=iter([console_input.SHOW_ART,console_input.FRONT_ART,'s'])
    monkeypatch.setattr(menus,'console_key',lambda:next(keys))
    monkeypatch.setattr(app,'reopen_artwork',lambda activate=False:calls.append(activate))
    assert menus.choose(app,'Review',[menus.Choice('s','Skip')],'s','Help')=='s'
    assert calls==[False,True]


def test_popup_creation_is_independent_of_terminal_failure_or_redirection(tmp_path,monkeypatch,capsys):
    from image_caption_gender_fixer import floating_artwork,paf_backend
    from image_caption_gender_fixer.errors import DependencyUnavailable
    path=tmp_path/'image.png';Image.new('RGB',(200,600),'navy').save(path)
    calls=[]
    class Art:
        def __init__(self,root):pass
        def update(self,*args):calls.append(args)
    monkeypatch.setattr(floating_artwork,'FloatingArtwork',Art)
    def fail(*args):raise DependencyUnavailable('simulated terminal renderer failure')
    monkeypatch.setattr(paf_backend,'terminal_image',fail)
    app=app_for(tmp_path);app.args.no_preview=False
    monkeypatch.setattr('sys.stdout.isatty',lambda:True);app.preview(path,'Original')
    assert calls and 'simulated terminal renderer failure' in capsys.readouterr().err
    monkeypatch.setattr('sys.stdout.isatty',lambda:False);app.preview(path,'Original again')
    assert len(calls)==2


def test_failed_window_can_restart_without_losing_review_or_dialog(tmp_path,monkeypatch):
    import tkinter as tk
    from image_caption_gender_fixer.errors import DependencyUnavailable
    gc.collect();path=tmp_path/'image.png';Image.new('RGB',(200,600),'navy').save(path)
    original=tk.Tk;calls=[]
    def fail_once(*args,**kwargs):
        calls.append(None)
        if len(calls)==1:raise RuntimeError('simulated Tk startup failure')
        return original(*args,**kwargs)
    monkeypatch.setattr(tk,'Tk',fail_once)
    art=FloatingArtwork(ROOT)
    try:
        with pytest.raises(DependencyUnavailable,match='simulated Tk startup failure'):art.update(path,'First')
        token=art.begin_review(False,[],changes=[{'index':0,'before':'old','after':'new'}],source=str(path))
        dialog=art.begin_dialog({'kind':'input','title':'Value','default':'prefilled'})
        art.reopen()
        assert art.thread.is_alive() and art.error is None and art.review_token==token and art.dialog_token==dialog
        assert art._dialog_spec['default']=='prefilled'
        art.end_dialog(dialog);art.end_review(token)
    finally:art.close()


@pytest.mark.parametrize('state',['withdrawn','iconic'])
def test_shortcut_reopens_hidden_or_minimized_artwork_passively(tmp_path,state):
    path=tmp_path/'image.png';Image.new('RGB',(200,600),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Proposal'}],floating=True)
    try:
        viewer.passive_show();viewer.root.update()
        viewer.root.withdraw() if state=='withdrawn' else viewer.root.iconify()
        viewer.root.update_idletasks();viewer.reopen(False);viewer.root.update_idletasks()
        assert viewer.root.state()=='normal'
        api,hwnd,getter,_=viewer._native_window();assert getter(hwnd,-20)&0x08000000
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_reopen_preserves_caption_draft_and_adjustments_cannot_discard_it(tmp_path):
    path=tmp_path/'image.png';Image.new('RGB',(200,600),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Review'}],{'detected':'old caption','proposed':'new caption'},floating=True)
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        viewer.set_review(lambda action:None,[],False,changes=[{'index':0,'before':'old','after':'new'}],source=str(path))
        viewer.proposed_caption.insert('end',' revised');viewer.caption_modified()
        draft=viewer.proposed_caption.get('1.0','end-1c')
        viewer.hide();viewer.reopen(False)
        assert viewer.proposed_caption.get('1.0','end-1c')==draft
        for key in ('a','m','o','v','b','rename_image'):assert viewer.buttons[key].instate(['disabled'])
        assert not viewer.buttons['edit_caption'].instate(['disabled'])
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
