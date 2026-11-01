"""Review defaults, editable OCR, pronoun conversion and passive window updates."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import ctypes
from ctypes import wintypes
import pytest
from PIL import Image
import numpy as np
from image_caption_gender_fixer import imaging,repair_modes
from image_caption_gender_fixer.ocr_editor import corrected_lines,remap_adjustments,feminize_pronouns
from image_caption_gender_fixer.caption_editor import preserve_adjustments
from image_caption_gender_fixer.errors import IntegrityError
from image_caption_gender_fixer.paf_album_art import AlbumArtReview,_passive_artwork_update
from image_caption_gender_fixer.rules import builtins
from image_caption_gender_fixer.ocr_cache import OCRCache,signature
from image_caption_gender_fixer.fs import sha256
from test_images import ROOT,make_image,app_for
from test_paf_album_art import line


@pytest.mark.parametrize('before,after',[
    ('He gave him his hat. The hat is his.','She gave her her hat. The hat is hers.'),
    ('HE and HIM with HIS wife; HIS.','SHE and HER with HER wife; HERS.'),
    ('the theater and this history','the theater and this history'),
    ("He's here; he likes himself.","She's here; she likes himself."),
])
def test_pronoun_conversion_uses_whole_words_case_and_possessives(before,after):
    assert feminize_pronouns(before)==after


@pytest.mark.parametrize('text',['his wife greets boy','his lovely wife greets boy','wife greets boy','hiswife greets boy'])
def test_green_ocr_correction_keeps_valid_word_geometry(text):
    original=[line('hls wife greets boy',20)];saved=deepcopy(original)
    corrected=corrected_lines(original,text)
    assert corrected[0]['text']==text and original==saved
    for word in corrected[0]['words']:
        assert corrected[0]['text'][word.start:word.end]==word.text
        assert word.box[0]<word.box[2] and word.box[1:4:2]==(20,40)


def test_green_correction_rejects_line_changes_without_losing_old_ocr():
    original=[line('hls wife',20)]
    with pytest.raises(IntegrityError,match='line breaks'):corrected_lines(original,'his\nwife')
    assert original[0]['text']=='hls wife'


def test_green_edits_find_more_substitutions_and_keep_other_word_adjustments():
    original=[line('hls wife greets boy',20)]
    previous,_=imaging.regions(original,builtins());previous[0].settings={'scale':.8,'dx':5}
    corrected=corrected_lines(original,'his wife greets boy')
    updated,_=imaging.regions(corrected,builtins())
    rebuilt=preserve_adjustments(updated,remap_adjustments(previous,corrected))
    assert imaging.full_captions(corrected,rebuilt)['proposed']=='her wife greets girl'
    assert rebuilt[0].settings=={} and rebuilt[1].settings=={'scale':.8,'dx':5}


def viewer_for(tmp_path):
    source=tmp_path/'neutral.png';Image.new('RGB',(180,320),'navy').save(source)
    viewer=AlbumArtReview([{'path':str(source),'title':'Review'}],{'detected':'He sees his wife.','proposed':'He sees his wife.'},floating=True)
    viewer._has_drawn=True;actions=[]
    viewer.set_review(actions.append,[],False,changes=[{'index':0,'before':'his','after':'her'}],source=str(source))
    return viewer,actions,source


def close(viewer):
    viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_green_editor_regenerate_emits_ocr_edit_and_disables_approval(tmp_path):
    viewer,actions,source=viewer_for(tmp_path)
    try:
        assert str(viewer.caption['state'])=='normal'
        viewer.caption.delete('1.0','end');viewer.caption.insert('1.0','He greets his wife.')
        viewer.caption_modified(SimpleNamespace(widget=viewer.caption))
        assert viewer._ocr_dirty and viewer.buttons['a'].instate(['disabled'])
        viewer.buttons['edit_caption'].invoke()
        assert actions==[{'action':'edit_ocr','source':str(source),'text':'He greets his wife.'}]
    finally:close(viewer)


def test_pronoun_button_uses_the_current_draft_without_approving(tmp_path):
    viewer,actions,source=viewer_for(tmp_path)
    try:
        viewer.proposed_caption.insert('end',' He likes him.');viewer.caption_modified()
        viewer.buttons['pronouns'].invoke()
        assert actions==[{'action':'edit_caption','text':'She sees her wife. She likes her.'}]
    finally:close(viewer)


def test_ignore_enter_defaults_to_this_image_for_this_run(tmp_path):
    viewer,actions,source=viewer_for(tmp_path)
    try:
        viewer.buttons['ignore'].invoke();dialog=viewer._dialog
        button=next(w for w in dialog.winfo_children() if w.winfo_class()=='TButton' and 'Ignore' in str(w['text']))
        button.invoke();assert actions==[{'action':'ignore','index':0,'scope':'image_run'}]
    finally:close(viewer)


def test_default_render_is_flat_with_a_subtle_shadow_and_original_mode_keeps_pixels(tmp_path,monkeypatch):
    source=tmp_path/'neutral.png';make_image(source,'kind boy',photo=True)
    image,_=imaging.decode(source)
    word=imaging.Word('kind boy',(90,116,420,199),99,0,8)
    region=imaging.Region('kind boy','kind girl',word.box,99,[word],[])
    def refuse(*args,**kwargs):raise AssertionError('Default must not use inpainting')
    monkeypatch.setattr(imaging.libraries()[1],'inpaint',refuse)
    rendered,diagnostic,_=imaging.render_region(image,region,[word.box])
    assert diagnostic['repair']=='fill' and diagnostic['shadow']==(1,1) and diagnostic['shadow_blur']==.5
    region.settings={'repair':'original'}
    original,diagnostic,crops=imaging.render_region(image,region,[word.box],repair_only=True)
    assert np.array_equal(np.array(original),np.array(image)) and diagnostic['repair']=='original'


def test_passive_decorator_restores_stacking_after_layout_and_shell_refresh():
    events=[]
    class Guard:
        depth=0
        def __enter__(self):self.depth+=1
        def __exit__(self,*args):self.depth-=1
    class Viewer:
        _activation=Guard();root=SimpleNamespace(update_idletasks=lambda:events.append('layout'))
        window_shell=SimpleNamespace(refresh=lambda:events.append('shell'))
        def passive_position(self):events.append('capture');return (123,456)
        def restore_passive_position(self,position):events.append(('restore',position))
        def keep_passive(self):events.append('passive')
        @_passive_artwork_update
        def update(self):events.append('draw')
    Viewer().update()
    assert events==['capture','passive','draw','layout','passive','shell',('restore',(123,456))]


def test_automatic_hidden_restore_stays_at_bottom_and_preserves_foreground(tmp_path):
    viewer,actions,source=viewer_for(tmp_path)
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw();viewer.hide()
        api,hwnd,_,_=viewer._native_window()
        api.GetForegroundWindow.restype=wintypes.HWND;foreground=api.GetForegroundWindow()
        viewer.update_image({'path':str(source),'title':'Updated'},viewer.captions)
        viewer.root.update_idletasks()
        assert api.GetForegroundWindow()==foreground
        api.GetWindow.argtypes=[wintypes.HWND,wintypes.UINT];api.GetWindow.restype=wintypes.HWND
        assert api.GetWindow(hwnd,3) # A passive restore cannot become the top window.
        assert viewer.root.state()=='normal'
    finally:close(viewer)


def test_edit_ocr_pipeline_rebuilds_rules_and_saves_corrected_cache(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source,'his wife and boy');digest=sha256(source)
    app=app_for(tmp_path,answers=iter([]));seen=[]
    real=app.ocr_lines;captured=[]
    def ocr(*args,**kwargs):
        lines,reused=real(*args,**kwargs)
        for item in lines:
            for word in item['words']:
                if word.text.casefold()=='his':word.text='hls'
            item['text']=' '.join(w.text for w in item['words'])
        captured.extend(deepcopy(lines));return lines,reused
    monkeypatch.setattr(app,'ocr_lines',ocr)
    def review(path,proposal,regions):
        seen.append(deepcopy(regions))
        assert not proposal.get('blocked') and sha256(source)==digest
        if len(seen)==1:
            regions[0].settings={'scale':.9}
            return {'action':'edit_ocr','source':str(path),'text':'\n'.join(l['text'].replace('hls','his') for l in app.caption_lines)}
        assert 'her wife' in imaging.full_captions(app.caption_lines,regions)['proposed']
        assert next(r for r in regions if r.before=='boy').settings=={'scale':.9}
        return 's'
    monkeypatch.setattr(app,'review',review)
    _,code=app.process([str(source)])
    assert code==10 and len(seen)==2 and sha256(source)==digest
    executable=__import__('image_caption_gender_fixer.dependencies',fromlist=['status']).status(ROOT,True)['native']['tesseract']
    cached=OCRCache(tmp_path).get(digest,signature(ROOT,executable['path'],False),imaging.decode(source)[0].size)
    assert 'his wife' in '\n'.join(l['text'] for l in cached)


def test_green_and_yellow_drafts_are_both_carried_into_regeneration(tmp_path):
    viewer,actions,source=viewer_for(tmp_path)
    try:
        viewer.caption.delete('1.0','end');viewer.caption.insert('1.0','He greets his wife.')
        viewer.caption_modified(SimpleNamespace(widget=viewer.caption))
        viewer.proposed_caption.delete('1.0','end');viewer.proposed_caption.insert('1.0','She greets her wife.')
        viewer.caption_modified()
        viewer.buttons['edit_caption'].invoke()
        assert actions==[{'action':'edit_ocr','source':str(source),'text':'He greets his wife.','proposed_text':'She greets her wife.'}]
    finally:close(viewer)


def test_worker_requests_activation_only_for_first_show_or_explicit_restore(tmp_path,monkeypatch):
    import gc
    from image_caption_gender_fixer.floating_artwork import FloatingArtwork
    gc.collect();source=tmp_path/'neutral.png';Image.new('RGB',(180,200),'navy').save(source)
    requests=[];real=AlbumArtReview.reopen
    def record(viewer,activate=False):
        requests.append(bool(activate));return real(viewer,False)
    monkeypatch.setattr(AlbumArtReview,'reopen',record)
    art=FloatingArtwork(ROOT)
    try:
        art.update(source,'First');assert requests==[True]
        art.update(source,'Regenerated');assert requests==[True]
        art.close();art.update(source,'Recovered worker');assert requests==[True]
        art.reopen(False);assert requests==[True,False]
        art.reopen(True);assert requests==[True,False,True]
    finally:art.close()
