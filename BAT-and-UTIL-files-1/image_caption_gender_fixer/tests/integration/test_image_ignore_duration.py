from pathlib import Path
import json
import pytest
from PIL import Image
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer.fs import sha256
from test_images import app_for,make_image


@pytest.mark.parametrize('scope,label',[
    ('image_run','Ignore this image for this run'),
    ('image','Ignore this image for all future runs'),
])
def test_dialog_has_both_image_choices_and_emits_the_selected_scope(tmp_path,scope,label):
    path=tmp_path/'preview.png';Image.new('RGB',(240,360),'navy').save(path)
    viewer=AlbumArtReview([{'path':str(path),'title':'Review'}],floating=True);actions=[]
    try:
        viewer.set_review(actions.append,[],False,changes=[{'index':2,'before':'old','after':'new'}])
        viewer.ignore_substitution();dialog=viewer._dialog
        radios=[w for w in dialog.winfo_children() if w.winfo_class()=='TRadiobutton']
        assert len(radios)==6
        assert {'Ignore this image for this run','Ignore this image for all future runs'}<=set(str(w['text']) for w in radios)
        radio=next(w for w in radios if str(w['text'])==label);radio.invoke()
        button=next(w for w in dialog.winfo_children() if w.winfo_class()=='TButton' and 'Ignore' in str(w['text']))
        assert int(button.grid_info()['row'])>max(int(w.grid_info()['row']) for w in radios)
        button.invoke();assert actions==[{'action':'ignore','index':2,'scope':scope}]
    finally:viewer.root.after(0,lambda:viewer.choose('c'));viewer.show()


@pytest.mark.parametrize('interface',['artwork','console'])
@pytest.mark.parametrize('persistent',[False,True])
def test_whole_image_ignore_skips_all_changes_and_only_saved_choice_survives_new_run(tmp_path,monkeypatch,interface,persistent):
    folder=tmp_path/'images';folder.mkdir()
    source=folder/'caption.png';make_image(source,'good boy and man');original=sha256(source)
    app=app_for(tmp_path,answers=iter(['1','i' if persistent else 'r']));seen=[]
    def review(source,proposal,regions):
        seen.append(len(regions))
        return {'action':'ignore','index':0,'scope':'image' if persistent else 'image_run'} if interface=='artwork' else 'i'
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert seen and seen[0]>=2 and len(seen)==1
    assert result['results'][0]['state']=='skipped'
    assert sha256(source)==original and not (folder/'.history.icgf').exists()
    sidecar=folder/'.image-gender-fixer.stt'
    assert sidecar.exists() is persistent
    if persistent:
        records=[json.loads(line) for line in sidecar.read_text(encoding='utf-8').splitlines()]
        assert records[-1]['ignore']=={'image_hash':original}
        # The image's exclusion follows the folder and does not depend on names.
        renamed=source.with_name('renamed.png');source.rename(renamed)
        new_folder=folder.with_name('renamed-images');folder.rename(new_folder)
        source=new_folder/renamed.name
    again=app_for(tmp_path,answers=iter([]));reviews=[]
    monkeypatch.setattr(again,'review',lambda *args:reviews.append(True) or 's')
    again.process([str(source)])
    assert bool(reviews) is (not persistent)
    assert sha256(source)==original
