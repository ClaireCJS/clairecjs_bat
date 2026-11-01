"""Real repair samples and menu choices, including blocked fits and draft text."""
import hashlib
import io
from pathlib import Path
from PIL import Image
import pytest
from image_caption_gender_fixer import imaging,repair_modes
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer.fs import sha256
from test_images import app_for,make_image


def sample_image(tmp_path):
    source=tmp_path/'neutral.png';make_image(source,photo=True);image,_=imaging.decode(source)
    word=imaging.Word('good boi',(90,116,398,199),99,0,8)
    region=imaging.Region('good boi','good girl'*100,word.box,99,[word],[])
    choices=repair_modes.samples(image,region,[word.box])
    return source,image,region,choices


def test_real_graphic_samples_work_independently_of_replacement_fit(tmp_path):
    source,image,region,choices=sample_image(tmp_path);digest=sha256(source)
    assert {item['mode'] for item in choices}==repair_modes.KEYS
    available=[item for item in choices if item['available']]
    assert len(available)>=5
    for item in available:
        with Image.open(io.BytesIO(item['thumbnail'])) as sample:assert sample.size==(104,42)
    assert len({hashlib.sha256(item['thumbnail']).digest() for item in available})>=3
    assert sha256(source)==digest
    assert sorted(p.name for p in tmp_path.iterdir())==['neutral.png']


def test_graphical_menu_changes_blocked_repairs_and_keeps_a_typed_caption(tmp_path):
    source,image,region,choices=sample_image(tmp_path)
    viewer=AlbumArtReview([{'path':str(source),'title':'Blocked'}],{'detected':'good boi','proposed':'good girl'},floating=True)
    actions=[]
    try:
        viewer.passive_show();viewer.root.update_idletasks();viewer.draw()
        change={'index':0,'before':'good boi','after':'good girl','fit_exhausted':True,
            'repairs':{'index':0,'mode':'auto','choices':choices}}
        viewer.set_review(actions.append,[],True,changes=[change],source=str(source))
        picker=viewer.repair_picker
        assert viewer.buttons['a'].instate(['disabled']) and viewer.buttons['m'].instate(['disabled'])
        assert 'exhausted' in str(viewer.buttons['m'].cget('text'))
        assert not picker.button.instate(['disabled'])
        assert all(picker.menu.entrycget(index,'image') for index in picker.entries.values())
        assert all(picker.menu.entrycget(index,'compound')=='left' for index in picker.entries.values())
        viewer.proposed_caption.insert('end',' today');viewer.caption_modified()
        assert viewer._dirty
        picker.menu.invoke(picker.entries['gradient'])
        assert actions==[{'action':'repair_mode','mode':'gradient','source':str(source),'text':'good girl today'}]
        assert picker.button.instate(['disabled'])
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_unavailable_patch_has_a_graphic_and_reason_and_cannot_be_selected(tmp_path):
    source=tmp_path/'neutral.png';make_image(source);image,_=imaging.decode(source)
    word=imaging.Word('good boi',(90,116,398,199),99,0,8)
    region=imaging.Region('good boi','good girl',word.box,99,[word],[])
    protected=[word.box,(0,211,image.width,image.height),(410,0,image.width,211)]
    choices=repair_modes.samples(image,region,protected)
    patch=next(item for item in choices if item['mode']=='patch')
    assert not patch['available'] and 'No safe neighboring patch' in patch['reason']
    viewer=AlbumArtReview([{'path':str(source),'title':'Review'}],floating=True);actions=[]
    try:
        viewer.set_review(actions.append,[],True,changes=[{'index':0,'before':region.before,'after':region.after,
            'repairs':{'index':0,'mode':'auto','choices':choices}}],source=str(source))
        picker=viewer.repair_picker;index=picker.entries['patch']
        assert picker.menu.entrycget(index,'image') and picker.menu.entrycget(index,'state')=='disabled'
        picker.menu.invoke(index);assert not actions
        picker.menu.invoke(picker.entries['telea']);assert actions[0]['mode']=='telea'
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


def test_selecting_mode_regenerates_with_draft_and_auto_restores_default(tmp_path,monkeypatch):
    source=tmp_path/'neutral.png';make_image(source);digest=sha256(source)
    app=app_for(tmp_path,answers=iter([]));seen=[]
    def review(path,proposal,regions):
        assert not proposal.get('blocked') and sha256(source)==digest
        seen.append(proposal)
        if len(seen)==1:return {'action':'repair_mode','mode':'gradient','source':str(path),'text':'good girl today'}
        if len(seen)==2:
            assert all(d['repair']=='gradient' for d in proposal['diagnostics'])
            assert 'good girl today' in imaging.full_captions(app.caption_lines,regions)['proposed']
            return {'action':'repair_mode','mode':'auto','source':str(path)}
        assert all(d['repair']=='fill' for d in proposal['diagnostics']);return 's'
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert code==10 and len(seen)==3 and sha256(source)==digest
    assert not (tmp_path/'.history.icgf').exists() and not list(tmp_path.glob('.icgf-*.png'))



def test_real_floating_dropdown_regenerates_and_returns_to_review(tmp_path,monkeypatch):
    import time
    from image_caption_gender_fixer import adjustment_menu
    source=tmp_path/'neutral.png';make_image(source);digest=sha256(source)
    app=app_for(tmp_path);app.interactive=True;app.args.no_preview=False;events=[]
    original=repair_modes.RepairPicker.update;deadline=time.monotonic()+25
    def update(picker,changes,active):
        original(picker,changes,active)
        if not active or not picker.metadata:return
        mode=picker.metadata['mode']
        if mode=='auto' and not events:
            events.append('gradient')
            picker.viewer.root.after(20,lambda:picker.menu.invoke(picker.entries['gradient']))
        elif mode=='gradient' and events==['gradient']:
            events.append('skip')
            picker.viewer.root.after(20,lambda:picker.viewer.buttons['s'].invoke())
    monkeypatch.setattr(repair_modes.RepairPicker,'update',update)
    monkeypatch.setattr(adjustment_menu,'console_key',lambda:'c' if time.monotonic()>deadline else None)
    try:
        result,code=app.process([str(source)])
        assert code==10 and result['results']==[{'file':str(source),'state':'skipped'}]
        assert events==['gradient','skip'] and sha256(source)==digest
        assert app.floating_artwork.error is None
    finally:app.close_previews()


def test_closed_windows_leave_no_tk_cycles_for_another_thread_to_collect(tmp_path):
    import subprocess,sys
    from test_images import ROOT
    from image_caption_gender_fixer import paf_album_art
    source=tmp_path/'neutral.png';Image.new('RGB',(250,400),'navy').save(source)
    code=r"""
import gc,os,sys,threading
from pathlib import Path
sys.path[:0]=sys.argv[1:3]
handles=[os.add_dll_directory(str(Path(sys.argv[2])/part)) for part in ('numpy.libs','PIL','cv2','.dlls') if (Path(sys.argv[2])/part).is_dir()]
import tkinter as tk
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer import repair_modes
for iteration in range(4):
    viewer=AlbumArtReview([{'path':sys.argv[3],'title':'Cleanup regression'}],floating=True)
    viewer.root.update_idletasks();viewer.draw()
    choices=[dict(mode=key,label=label,description=desc,available=True,thumbnail=repair_modes._illustration(key)) for key,label,desc in repair_modes.MODES]
    for redraw in range(3):
        viewer.set_review(lambda value:None,[],True,changes=[dict(index=0,before='old',after='new',repairs=dict(index=0,mode='auto',choices=list(choices)))],source=sys.argv[3])
    viewer.root.after(0,lambda:viewer.choose('c'));viewer.show();viewer=None
    assert not any(isinstance(obj,(tk.Misc,tk.Variable,tk.Image)) for obj in gc.get_objects())
    worker=threading.Thread(target=gc.collect);worker.start();worker.join()
print('owner-thread cleanup passed')
"""
    result=subprocess.run([sys.executable,'-B','-I','-S','-c',code,
        str(Path(paf_album_art.__file__).parents[1]),str(ROOT/'environment/packages'),str(source)],
        capture_output=True,text=True,timeout=35)
    assert result.returncode==0,(result.stdout,result.stderr)
    assert 'owner-thread cleanup passed' in result.stdout
