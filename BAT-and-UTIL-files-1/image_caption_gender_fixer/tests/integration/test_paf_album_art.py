"""Generated images, actual Pillow/Tcl/Tk, synchronous review and full captions."""
from pathlib import Path
import pytest
from image_caption_gender_fixer import cli,imaging,paf_album_art
from image_caption_gender_fixer.rules import builtins
from image_caption_gender_fixer.fs import sha256
from test_images import app_for,make_image


def line(text,y):
    words=[];offset=0
    for token in text.split(' '):
        words.append(imaging.Word(token,(offset*10,y,(offset+len(token))*10,y+20),99,offset,offset+len(token)))
        offset+=len(token)+1
    return {'text':text,'words':words}


def test_entire_caption_retains_unchanged_lines_and_corrected_ocr():
    lines=[line('This good boi and that man are in the complete caption.',0),
           line('Everything in this second line stays visible.',30)]
    regions,_=imaging.regions(lines,builtins())
    captions=imaging.full_captions(lines,regions)
    assert captions['detected']=='\n'.join(item['text'] for item in lines)
    assert captions['proposed']=='This good girl and that woman are in the complete caption.\nEverything in this second line stays visible.'
    regions[0].before='good boy';regions[0].after='great girl'
    regions[1].skipped=True
    captions=imaging.full_captions(lines,regions)
    assert captions['detected'].startswith('This good boy and that man')
    assert captions['proposed'].startswith('This great girl and that man')


def test_copied_paf_containment_preserves_alpha_and_all_four_edges(tmp_path):
    import io
    from PIL import Image,ImageDraw
    image=Image.new('RGBA',(200,100),(10,20,30,255))
    draw=ImageDraw.Draw(image)
    colors=['red','green','blue','yellow']
    for box,color in zip([(0,0,19,19),(180,0,199,19),(0,80,19,99),(180,80,199,99)],colors): draw.rectangle(box,fill=color)
    data=io.BytesIO();image.save(data,format='PNG')
    fitted,original=paf_album_art._pillow_fit_canvas_image(data.getvalue(),100,100)
    assert original.tobytes()==image.tobytes()
    assert fitted.size==(100,100) and fitted.getpixel((50,0))[3]==0
    for point,color in zip([(2,27),(97,27),(2,72),(97,72)],[(255,0,0),(0,128,0),(0,0,255),(255,255,0)]):
        assert fitted.getpixel(point)[:3]==color


@pytest.mark.parametrize('blocked',[False,True])
def test_real_gallery_resizes_keeps_caption_and_closes_synchronously(tmp_path,blocked):
    from PIL import Image
    source=tmp_path/'generated.png';Image.new('RGBA',(220,100),(255,0,0,160)).save(source)
    original=sha256(source)
    captions={'detected':'Entire original caption\n'+'unchanged line '*40,'proposed':'Entire proposed caption\n'+'unchanged line '*40}
    dialog=paf_album_art.AlbumArtReview([{'path':source,'title':'Original'},{'path':source,'title':'Proposed'}],captions,blocked=blocked)
    errors=[];observed=[]
    def checked(callback):
        try: callback()
        except BaseException as error:
            errors.append(error);dialog.choose('c')
    def after_render(callback):
        import time
        deadline=time.monotonic()+5
        def poll():
            ready=(dialog._has_drawn and dialog._photo is not None
                   and dialog._photo.width()==dialog.canvas.winfo_width())
            if ready or time.monotonic()>=deadline: checked(callback)
            else: dialog.root.after(25,poll)
        dialog.root.after(25,poll)
    def first():
        assert dialog._photo is not None
        assert captions['detected'] in dialog.caption.get('1.0','end')
        assert captions['proposed'] in dialog.proposed_caption.get('1.0','end')
        assert bool(dialog.buttons['a'].instate(['disabled']))==blocked
        if blocked:
            dialog.choose('a');assert dialog.result is None
        dialog.navigate(-1)
        dialog.root.geometry('650x650')
        after_render(second)
    def second():
        assert dialog.selector.current()==0 and dialog._photo is not None
        observed.append((dialog.canvas.winfo_width(),dialog._photo.width()))
        # Use the actual WM_DELETE_WINDOW callback: it cancels, never approves.
        dialog.root.tk.call(dialog.root.protocol('WM_DELETE_WINDOW'))
    after_render(first)
    result=dialog.show()
    if errors: raise errors[0]
    assert dialog.root is None and dialog.selection is None and not dialog.buttons
    assert result=='c' and observed and observed[0][0]==observed[0][1]
    assert sha256(source)==original


def test_paf_photo_reuses_same_tk_image_only_for_matching_dimensions():
    import tkinter as tk
    from PIL import Image
    root=tk.Tk();root.withdraw()
    try:
        first=paf_album_art.reuse_or_create_photoimage(None,Image.new('RGBA',(20,20),'red'),root)
        same=paf_album_art.reuse_or_create_photoimage(first,Image.new('RGBA',(20,20),'blue'),root)
        changed=paf_album_art.reuse_or_create_photoimage(same,Image.new('RGBA',(30,20),'green'),root)
        assert same is first and changed is not same and changed.width()==30
        first=same=changed=None
    finally: root.destroy()


def test_review_updates_both_previews_and_keeps_last_proposal_with_full_caption(tmp_path,monkeypatch):
    source=tmp_path/'generated-caption.png';make_image(source)
    before=sha256(source);app=app_for(tmp_path,answers=iter(['s']));app.args.no_preview=False
    monkeypatch.setattr(cli.sys.stdout,'isatty',lambda:True)
    from image_caption_gender_fixer import paf_backend,floating_artwork
    calls=[];terminal=[];closed=[]
    class Floating:
        def __init__(self,root): pass
        def update(self,path,title,captions): calls.append((str(path),title,captions))
        def close(self): closed.append(True)
    monkeypatch.setattr(floating_artwork,'FloatingArtwork',Floating)
    monkeypatch.setattr(paf_backend,'terminal_image',lambda root,path,columns,rows:b'drcs-fixture')
    monkeypatch.setattr(app,'write_terminal_image',lambda payload:terminal.append(payload))
    result,code=app.process([str(source)])
    assert code==10 and result['results'][0]['state']=='skipped'
    assert len(calls)>2 and len(calls)==len(terminal)
    assert calls[0][1]=='Original image' and calls[-1][1]=='Complete proposed corrected image'
    captions=calls[-1][2]
    assert captions['detected']=='good boi' and captions['proposed']=='good girl'
    assert sha256(source)==before
    app.close_previews();assert closed==[True]
    assert not list(tmp_path.glob('.icgf-*.png')) and not(tmp_path/'.history.icgf').exists()


def test_no_match_image_still_reports_entire_caption(tmp_path,capsys):
    source=tmp_path/'no-match.png';make_image(source,text='Hello world')
    app=app_for(tmp_path,answers=iter([]))
    result,code=app.process([str(source)])
    assert code==10 and 'Hello world' in capsys.readouterr().err
    assert result['results'][0]['reason']=='no_substitution'


def test_unreadable_preview_never_enables_approval(tmp_path):
    source=tmp_path/'not-an-image.png';source.write_bytes(b'generated invalid image fixture')
    dialog=paf_album_art.AlbumArtReview([{'path':source,'title':'Unreadable preview'}])
    errors=[]
    def check():
        try:
            assert dialog.blocked and not dialog._has_drawn
            assert dialog.buttons['a'].instate(['disabled'])
            dialog.choose('a');assert dialog.result is None
        except BaseException as error: errors.append(error)
        finally: dialog.choose('s')
    dialog.root.after(200,check)
    assert dialog.show()=='s'
    if errors: raise errors[0]


@pytest.mark.parametrize('error_type',[RuntimeError,KeyboardInterrupt])
def test_gui_callback_failure_closes_window_and_propagates_safely(tmp_path,error_type):
    from PIL import Image
    source=tmp_path/'callback.png';Image.new('RGB',(50,50),'white').save(source)
    dialog=paf_album_art.AlbumArtReview([{'path':source,'title':'Generated fixture'}])
    def fail(): raise error_type('Generated callback failure')
    dialog.root.after(100,fail)
    with pytest.raises(error_type): dialog.show()
