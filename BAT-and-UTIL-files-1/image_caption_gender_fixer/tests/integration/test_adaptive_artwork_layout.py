from types import SimpleNamespace
from PIL import Image
import pytest
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer.artwork_layout import choose_layout


@pytest.mark.parametrize('image,window,side',[
    ((1000,1000),(1920,1000),True),
    ((400,1200),(760,700),True),
    ((1800,600),(1200,900),False),
    ((600,1000),(680,420),True),
])
def test_layout_chooses_larger_image_without_cropping(image,window,side):
    plan=choose_layout(*window,image,(210,210),(8,8),26)
    assert plan.side is side
    assert abs(plan.image_width/plan.image_height-image[0]/image[1])<.02
    assert plan.image_width<=window[0] and plan.image_height<=window[1]
    if side and window[0]>=1500:assert plan.image_height==window[1]


def test_square_image_controls_use_side_space_and_survive_resize_with_draft(tmp_path):
    path=tmp_path/'square.png';Image.new('RGB',(800,800),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Square'}],{'detected':'old phrase','proposed':'new phrase'},floating=True)
    try:
        viewer.root.geometry('1600x900+20+20');viewer.passive_show();viewer.root.update_idletasks();viewer.draw();viewer.root.update_idletasks()
        assert viewer._layout_plan.side
        assert viewer.canvas.winfo_height()>viewer.root.winfo_height()*.9
        for bank,caption in zip(viewer.control_banks,viewer.caption_frames):
            assert str(bank.grid_info()['in'])==str(caption)
            assert bank.winfo_rooty()>=caption.winfo_rooty()
            assert bank.winfo_rooty()+bank.winfo_height()<=caption.winfo_rooty()+caption.winfo_height()
        viewer.set_review(lambda _:None,[],False)
        viewer.proposed_caption.insert('end',' draft');viewer.caption_modified()
        viewer.root.geometry('900x950+20+20');viewer.root.update_idletasks();viewer.draw();viewer.root.update_idletasks()
        assert not viewer._layout_plan.side
        assert viewer.proposed_caption.get('1.0','end-1c')=='new phrase draft'
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_artwork_letters_invoke_buttons_but_text_fields_keep_typing(tmp_path,monkeypatch):
    path=tmp_path/'image.png';Image.new('RGB',(800,800),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Review'}],floating=True);actions=[]
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        viewer.set_review(actions.append,[],False,changes=[{'index':0,'before':'old','after':'new'}],source=str(path))
        monkeypatch.setattr(viewer,'ignore_substitution',lambda:actions.append('ignore'))
        event=SimpleNamespace(widget=viewer.canvas,state=0,char='I',keysym='I')
        assert viewer.button_hotkey(event)=='break' and actions==['ignore']
        event.widget=viewer.proposed_caption;viewer.button_hotkey(event);assert actions==['ignore']
        event.widget=viewer.canvas;event.char='a';event.keysym='a';viewer._dirty=True;viewer.set_review(actions.append,[],False)
        viewer.button_hotkey(event);assert actions==['ignore']
        assert not {'p','q'}&set(viewer.buttons)
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_caption_pulse_has_identical_positions_font_and_line_breaks(tmp_path):
    path=tmp_path/'image.png';Image.new('RGB',(600,600),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Review'}],{'detected':'a longer old phrase that wraps','proposed':'a longer new phrase that wraps'},floating=True)
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw();viewer.root.update_idletasks()
        def positions():return [(widget.tag_cget('changed','font'),[widget.bbox('1.0+'+str(i)+'c') for i in range(len(widget.get('1.0','end-1c')))],widget.dlineinfo('1.0'),widget.get('1.0','end-1c')) for widget in (viewer.caption,viewer.proposed_caption)]
        before=positions();background=viewer.caption.tag_cget('changed','background')
        viewer.root.after_cancel(viewer._pulse_after);viewer.pulse_caption_changes();viewer.root.update_idletasks()
        assert positions()==before
        assert viewer.caption.tag_cget('changed','background')!=background
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_console_review_does_not_offer_pause_actions(tmp_path,monkeypatch):
    from image_caption_gender_fixer import adjustment_menu as menus
    from test_images import app_for
    app=app_for(tmp_path,answers=iter([]));seen=[]
    def choose(app,title,choices,*args,**kwargs):
        seen.extend(choices);return 's'
    monkeypatch.setattr(menus,'choose',choose)
    assert menus.review(app,'[y]approve, [s]kip, [c]ancel',False)=='s'
    assert not {'p','q'}&{c.key for c in seen}
    assert all('pause' not in c.label.casefold() for c in seen)


def test_side_adjustment_panel_keeps_prefilled_value_and_returns_review_banks(tmp_path):
    path=tmp_path/'square.png';Image.new('RGB',(800,800),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Review'}],floating=True)
    values=[]
    try:
        viewer.root.geometry('1600x900+20+20');viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        viewer.set_dialog({'kind':'input','title':'Tracking adjustment','default':'12'},values.append)
        viewer.root.update_idletasks();viewer.draw()
        assert str(viewer.control_panel.frame.grid_info()['in'])==str(viewer.caption_frames[1])
        viewer.control_panel.value.set('14')
        viewer.root.geometry('1500x850+20+20');viewer.root.update_idletasks();viewer.draw()
        assert viewer.control_panel.value.get()=='14'
        viewer.control_panel.buttons['submit'].invoke();assert values==['14']
        viewer.set_dialog(None,None);viewer.root.update_idletasks()
        assert all(bank.winfo_manager()=='grid' for bank in viewer.control_banks)
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_many_adjustment_choices_stay_inside_the_popup_and_have_letter_keys(tmp_path):
    path=tmp_path/'square.png';Image.new('RGB',(800,800),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Review'}],floating=True);values=[]
    try:
        viewer.root.geometry('1600x900+20+20');viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        spec={'kind':'menu','title':'Visual adjustments','default':'a',
              'choices':[{'key':chr(97+i),'label':'Adjust the selected caption setting '+str(i)} for i in range(16)]}
        viewer.set_dialog(spec,values.append);viewer.root.update_idletasks();viewer.draw();viewer.root.update_idletasks()
        frame=viewer.control_panel.frame
        assert frame.winfo_rooty()+frame.winfo_height()<=viewer.root.winfo_rooty()+viewer.root.winfo_height()
        for button in viewer.control_panel.buttons.values():assert button.winfo_rooty()+button.winfo_height()<=frame.winfo_rooty()+frame.winfo_height()
        event=SimpleNamespace(widget=viewer.canvas,state=0,char='i',keysym='i')
        assert viewer.button_hotkey(event)=='break' and values==['i']
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
