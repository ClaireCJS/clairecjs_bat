from PIL import Image
import pytest
from image_caption_gender_fixer.paf_album_art import AlbumArtReview


def press(widget,key):
    # Run the installed widget binding through Tcl without changing the user's
    # foreground application. Background windows drop generated key events.
    script=widget.bind(key)
    assert script and widget.bindtags()[0]==str(widget)
    command=script.split('[',1)[1].split()[0]
    assert widget.tk.call(command)=='break'


@pytest.mark.parametrize('key,target,scope',[
    ('<Return>','TCombobox','folder'),
    ('<Return>','cancel','image_run'),
    ('<KP_Enter>','TRadiobutton','session'),
])
def test_enter_applies_the_selected_ignore_and_closes_dialog(tmp_path,key,target,scope):
    source=tmp_path/'neutral.png';Image.new('RGB',(120,200),'navy').save(source)
    viewer=AlbumArtReview([{'path':str(source),'title':'Review'}],floating=True);actions=[]
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        viewer.set_review(actions.append,[],False,changes=[{'index':3,'before':'old','after':'new'}])
        viewer.ignore_substitution();dialog=viewer._dialog;dialog.update()
        children=dialog.winfo_children()
        radio=next(w for w in children if w.winfo_class()=='TRadiobutton' and str(w.cget('value'))==scope)
        radio.invoke()
        widget=(next(w for w in children if w.winfo_class()=='TButton' and 'Cancel' in str(w.cget('text')))
                if target=='cancel' else next(w for w in children if w.winfo_class()==target))
        assert widget.bind(key)
        press(widget,key);viewer.root.update_idletasks()
        assert actions==[{'action':'ignore','index':3,'scope':scope}]
        assert viewer._dialog is None and not dialog.winfo_exists()
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


@pytest.mark.parametrize('target',['TCombobox','TRadiobutton','ignore'])
def test_escape_closes_ignore_without_a_decision_and_review_remains_live(tmp_path,target):
    source=tmp_path/'neutral.png';Image.new('RGB',(120,200),'navy').save(source)
    viewer=AlbumArtReview([{'path':str(source),'title':'Review'}],floating=True);actions=[]
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        viewer.set_review(actions.append,[],False,changes=[{'index':3,'before':'old','after':'new'}])
        callback=viewer._review_callback
        viewer.ignore_substitution();dialog=viewer._dialog;dialog.update()
        children=dialog.winfo_children()
        widget=(next(w for w in children if w.winfo_class()=='TButton' and 'Ignore' in str(w.cget('text')))
                if target=='ignore' else next(w for w in children if w.winfo_class()==target))
        assert widget.bind('<Escape>')
        press(widget,'<Escape>');viewer.root.update_idletasks()
        assert actions==[] and viewer._dialog is None and not dialog.winfo_exists()
        assert viewer._review_callback is callback and viewer._review_changes[0]['index']==3
        viewer.ignore_substitution();assert viewer._dialog is not None
        viewer._dialog.destroy();viewer._dialog=None
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
