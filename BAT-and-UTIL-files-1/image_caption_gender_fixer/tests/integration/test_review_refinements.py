from PIL import Image
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer import imaging
from image_caption_gender_fixer.fs import sha256
from test_images import app_for,make_image


def test_portrait_after_landscape_and_changed_words_remain_visible_while_pulsing(tmp_path):
    tall=tmp_path/'tall.png';wide=tmp_path/'wide.png'
    Image.new('RGB',(200,600),'navy').save(tall);Image.new('RGB',(600,200),'navy').save(wide)
    viewer=AlbumArtReview([{'path':str(wide),'title':'Crop'}],{'detected':'good boy','proposed':'good girl'},floating=True)
    errors=[]
    def check():
        try:
            viewer.root.geometry('760x700+20+20')
            viewer.update_image({'path':str(tall),'title':'Full image'},{'detected':'good boy','proposed':'good girl'})
            viewer.root.update_idletasks();viewer.draw()
            assert viewer._portrait
            assert int(viewer.caption_frames[0].grid_info()['row'])==0
            assert int(viewer.caption_frames[1].grid_info()['column'])==2
            assert viewer.canvas.winfo_height()>=viewer.body.winfo_height()*.9
            for widget in (viewer.caption,viewer.proposed_caption):assert widget.tag_ranges('changed')
            content=[w.get('1.0','end-1c') for w in (viewer.caption,viewer.proposed_caption)]
            before=viewer.caption.tag_cget('changed','background')
            font=viewer.caption.tag_cget('changed','font')
            viewer.root.after_cancel(viewer._pulse_after);viewer.pulse_caption_changes()
            assert viewer.caption.tag_cget('changed','background')!=before
            assert viewer.caption.tag_cget('changed','font')==font
            assert [w.get('1.0','end-1c') for w in (viewer.caption,viewer.proposed_caption)]==content
        except BaseException as error:errors.append(error)
        finally:viewer.choose('c')
    viewer.root.after(250,check);viewer.show()
    if errors:raise errors[0]


def test_blocked_preview_ends_on_full_original_instead_of_detail_crop(tmp_path,monkeypatch):
    app=app_for(tmp_path,answers=iter(['s']));app.caption_lines=[{'text':'old','words':[]}]
    edit=imaging.Region('old','new',(0,0,20,20),99,[],[],line_index=0,ocr_span=(0,3))
    source=tmp_path/'portrait.png';crop=tmp_path/'crop.png';shown=[]
    monkeypatch.setattr(app,'preview',lambda path,*args,**kwargs:shown.append(path))
    app.review(source,dict(artifacts=[{'kind':'mask','path':str(crop),'region':0}],stage=None,
                          blocked={'region':0,'reason':'cannot fit safely'},level=3,verification=[],diagnostics=[]),[edit])
    assert shown==[source,str(crop),source]


def test_artwork_ignore_saves_exception_without_console_questions(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter([]));seen=[]
    def review(source,proposal,regions):
        seen.append(regions[0].before)
        return {'action':'ignore','index':0,'scope':'folder'}
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert seen and code==10 and result['results'][0]['state']=='skipped'
    assert sha256(source)==original and not (tmp_path/'.history.icgf').exists()
    rules,store=app.rules(tmp_path,original)
    assert any(ignore.get('phrase')==seen[0] for ignore in store.ignores)


def test_artwork_ignore_dialog_emits_selected_exception(tmp_path):
    path=tmp_path/'preview.png';Image.new('RGB',(200,600),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Full image'}],floating=True)
    actions=[]
    try:
        viewer.set_review(actions.append,[],False,changes=[{'index':2,'before':'old','after':'new'}])
        viewer.buttons['ignore'].invoke();dialog=viewer._dialog
        save=next(w for w in dialog.winfo_children() if w.winfo_class()=='TButton' and 'Ignore' in str(w['text']))
        save.invoke()
        assert actions==[{'action':'ignore','index':2,'scope':'folder'}]
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()
