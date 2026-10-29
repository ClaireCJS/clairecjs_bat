import os
import sys
import pytest
import tqdm.std
from test_images import app_for
from image_caption_gender_fixer import cli,newspaper_columns
from image_caption_gender_fixer.fs import sha256
from PIL import Image

def test_verbose_ocr_uses_newspaper_columns_and_retains_original_caption(tmp_path,monkeypatch,capsys):
    for stream in (sys.stdin,sys.stdout,sys.stderr):monkeypatch.setattr(stream,'isatty',lambda:True)
    monkeypatch.setattr(tqdm.std,'_screen_shape_wrapper',lambda:lambda fp:(120,24))
    monkeypatch.setattr(newspaper_columns.shutil,'get_terminal_size',lambda *a,**k:os.terminal_size((120,24)))
    source=tmp_path/'generated.png';Image.new('RGB',(100,40),'white').save(source);before=sha256(source)
    app=app_for(tmp_path,['-o','--verbose'],answers=iter([]))
    monkeypatch.setattr(cli,'repair_packages',lambda app:False)
    monkeypatch.setattr(cli.dependencies,'require_ocr',lambda *a,**k:{'path':'fake'})
    caption='\n'.join('Line '+str(i) for i in range(50))
    monkeypatch.setattr(app,'ocr_lines',lambda *a,**k:([{'text':caption,'words':[]}],True))
    result,code=app.process([str(source)])
    output=capsys.readouterr().err
    assert code==0 and result['results'][0]['caption']==caption
    assert '  │  ' in output and 'Line 49' in output and 'REUSED' in output
    assert sha256(source)==before and not(tmp_path/'.history.icgf').exists()

def test_long_lines_never_overflow_a_four_pair_comparison():
    old='\n'.join(('X'*26)+str(i) for i in range(80))
    new='\n'.join(('Y'*26)+str(i) for i in range(80))
    result=newspaper_columns.compare_columns(old,new,width=240,height=12,enabled=False)
    assert all(newspaper_columns.display_width(row)<=240 for row in result.splitlines())
