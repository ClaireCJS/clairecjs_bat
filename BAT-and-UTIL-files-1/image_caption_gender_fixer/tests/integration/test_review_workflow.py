from pathlib import Path
import json
import pytest
from test_images import app_for,make_image,ROOT
from image_caption_gender_fixer import imaging,name_migration
from image_caption_gender_fixer.fs import sha256,identity,move
from image_caption_gender_fixer.history import History
from image_caption_gender_fixer.transactions import Transactions
from image_caption_gender_fixer.floating_artwork import FloatingArtwork
from image_caption_gender_fixer.paf_album_art import AlbumArtReview
from image_caption_gender_fixer.rules import builtins
from PIL import Image

def test_add_rule_during_review_rebuilds_and_requires_fresh_approval(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source);original=sha256(source)
    app=app_for(tmp_path,answers=iter(['a','good boi','kind friend','200','save','s']))
    result,code=app.process([str(source)])
    assert code==10 and sha256(source)==original
    assert 'kind friend' in app.preview_captions['proposed']
    assert len((tmp_path/'.image-gender-fixer.stt').read_text().splitlines())==1
    assert not (tmp_path/'.history.icgf').exists()

def test_gui_caption_edit_rerenders_before_commit(tmp_path,monkeypatch):
    source=tmp_path/'caption.png';make_image(source)
    app=app_for(tmp_path,answers=iter([]));calls=[]
    def review(source,proposal,regions):
        calls.append((proposal['transaction'],regions[0].after))
        return {'action':'edit_caption','text':'good friend'} if len(calls)==1 else 'a'
    monkeypatch.setattr(app,'review',review)
    result,code=app.process([str(source)])
    assert code==0 and len(calls)==2 and calls[1][1]=='good friend' and calls[0][0]!=calls[1][0]
    assert Path(result['results'][0]['corrected']).stem.endswith('-genderfixed')

def test_floating_action_tokens_discard_old_approval():
    art=FloatingArtwork(ROOT);one=art.begin_review(False,builtins());two=art.begin_review(False,builtins())
    art.actions.put((one,'a'));assert art.review_action(two) is None
    art.actions.put((two,'s'));assert art.review_action(two)=='s'
    art.end_review(two);art.actions.put((two,'a'));assert art.review_action(two) is None

def test_portrait_full_height_layout_edit_disables_approval_and_buttons_emit(tmp_path):
    source=tmp_path/'portrait.png';Image.new('RGB',(220,660),'blue').save(source)
    viewer=AlbumArtReview([{'path':str(source),'title':'Proposal'}],{'detected':'good boy','proposed':'good girl'},floating=True)
    actions=[];errors=[]
    def check():
        try:
            if not viewer._has_drawn:viewer.root.after(40,check);return
            viewer.set_review(actions.append,[],False)
            assert viewer._portrait and viewer.canvas.winfo_height()>viewer.body.winfo_height()*.9
            viewer.proposed_caption.insert('end','!');viewer.caption_modified()
            assert viewer.buttons['a'].instate(['disabled'])
            viewer.buttons['edit_caption'].invoke()
            assert actions==[{'action':'edit_caption','text':'good girl!'}]
            viewer._dirty=False;viewer.set_review(actions.append,[],True);viewer.choose('a');assert len(actions)==1
            viewer.choose('s');assert actions[-1]=='s'
        except BaseException as error:errors.append(error)
        finally:viewer.choose('c')
    viewer.root.after(250,check);viewer.show()
    if errors:raise errors[0]

def test_legacy_suffix_rename_collision_preserves_bytes_and_undo(tmp_path):
    import uuid
    source=tmp_path/'sample.png';make_image(source);original=sha256(source)
    state=tmp_path/'tool';tx=Transactions(state)
    transaction=str(uuid.uuid4());stage=tmp_path/('.icgf-'+transaction+'.png');Image.new('RGB',(50,50),'red').save(stage)
    event=tx.commit(source,stage,original,transaction,'f'*64,'default',[])
    corrected=tmp_path/event['corrected'];legacy=corrected.with_name('sample-gendeerfixed.png');move(corrected,legacy)
    # Simulate history from the old released spelling with a fresh hash chain.
    folder=tmp_path/'old';folder.mkdir();move(legacy,folder/legacy.name);move(tmp_path/event['backup'],folder/event['backup'])
    event=dict(event,corrected=legacy.name);old=History(folder)
    txkeys=Transactions.event_values(event)
    with __import__('image_caption_gender_fixer.fs',fromlist=['folder_lock']).folder_lock(folder):old.append('committed',**txkeys)
    occupied=folder/'sample-genderfixed.png';occupied.write_bytes(b'keep me')
    digest=sha256(folder/legacy.name);result=name_migration.migrate(state,folder/legacy.name)
    new=Path(result['to']);assert new.name=='sample-genderfixed (1).png' and sha256(new)==digest and occupied.read_bytes()==b'keep me'
    active=History(folder).resolve(new.name)[0];tx.undo(folder,active)
    assert sha256(folder/source.name)==original

def test_migration_recovers_after_move_before_history_append(tmp_path,monkeypatch):
    source=tmp_path/'a-gendeerfixed.png';source.write_bytes(b'image bytes');digest=sha256(source);state=tmp_path/'state'
    real=name_migration.append
    monkeypatch.setattr(name_migration,'append',lambda *args:(_ for _ in ()).throw(OSError('simulated interruption')))
    with pytest.raises(OSError):name_migration.migrate(state,source)
    target=tmp_path/'a-genderfixed.png';assert sha256(target)==digest
    monkeypatch.setattr(name_migration,'append',real);name_migration.recover(state)
    assert sha256(target)==digest and not (tmp_path/'.history.icgf').exists()


def test_dry_run_legacy_name_repair_has_no_writes_and_double_numbers_are_excluded(tmp_path):
    from image_caption_gender_fixer.cli import product_name
    source=tmp_path/'legacy-gendeerfixed (1) (1).png';make_image(source)
    before={str(p):p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    app=app_for(tmp_path,['--dry-run','--json'])
    app.process([str(source)])
    assert before=={str(p):p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    assert product_name(source) and product_name('a-genderfixed (1) (1).jpg')
