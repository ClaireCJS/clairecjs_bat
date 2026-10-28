import json
from pathlib import Path
from image_caption_gender_fixer import paf_drcs


def test_current_paf_art_settings_use_read_only_registry_over_dcc(tmp_path,monkeypatch):
    import winreg
    from image_caption_gender_fixer import _paf_drcs_copy
    sibling=tmp_path/'PAFPlayer';sibling.mkdir()
    config=sibling/'PAFPlayer.dcc'
    config.write_text(json.dumps({'player_settings':{'DrcsEnabled':1,'VisualizerGranularity':2,
        'DrcsArtMicrotileDetailModeV370':7,'DrcsArtBarMicrotileDetailModeV370':8,'ArtworkSeamStrategy':0}}),encoding='utf-8')
    accesses=[]
    class Key:
        def __enter__(self): return self
        def __exit__(self,*args): pass
    def opened(root,path,reserved=0,access=winreg.KEY_READ):
        accesses.append((root,path,access));return Key()
    saved={'DrcsEnabled':1,'VisualizerGranularity':3,'MicrotileDetailMode':9,'BarMicrotileDetailMode':9,'ArtworkSeamStrategy':5}
    monkeypatch.setattr(winreg,'OpenKey',opened)
    monkeypatch.setattr(winreg,'QueryValueEx',lambda key,name:(saved[name],winreg.REG_DWORD))
    def forbidden(*args,**kwargs): raise AssertionError('Preview attempted to save PAFPlayer settings')
    monkeypatch.setattr(winreg,'SetValueEx',forbidden)
    values,origins=paf_drcs.current_settings(tmp_path/'tool',vars(_paf_drcs_copy))
    assert values['VisualizerGranularity']==3
    assert values['DrcsArtMicrotileDetailModeV370']==values['DrcsArtBarMicrotileDetailModeV370']==9
    assert values['ArtworkSeamStrategy']==5
    assert all(access==winreg.KEY_READ for root,path,access in accesses)
    assert all(source.startswith('HKCU\\') for source in origins.values())


def test_drcs_preview_preserves_transparent_source_bytes(tmp_path,monkeypatch):
    from PIL import Image
    from image_caption_gender_fixer import _paf_drcs_copy
    source=tmp_path/'transparent.png'
    image=Image.new('RGBA',(80,40),(0,0,0,0));image.putpixel((20,20),(0,0,0,255));image.save(source)
    before=source.read_bytes()
    namespace=vars(_paf_drcs_copy)
    values={'DrcsEnabled':1,'VisualizerGranularity':3,'DrcsArtMicrotileDetailModeV370':9,
            'DrcsArtBarMicrotileDetailModeV370':9,'ArtworkSeamStrategy':5}
    monkeypatch.setattr(paf_drcs,'current_settings',lambda *args:(values,{}))
    payload=paf_drcs.render(tmp_path/'tool',source,12,4)
    assert payload.startswith(b'\x1bP0;1;1;10;0;2;20;0{ @')
    assert source.read_bytes()==before
