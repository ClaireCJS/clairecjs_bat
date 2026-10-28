"""Console rendering contracts; generated images, real shared tqdm renderer."""
from contextlib import contextmanager
import io
import json
from pathlib import Path
import re
import sys
import pytest
from PIL import Image
from image_caption_gender_fixer import cli
from test_images import app_for
from clairecjs_utils import claire_progressbar as shared
import tqdm.std
from tqdm.utils import disp_len

ANSI=re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def console(monkeypatch,columns=100):
    monkeypatch.setattr(sys.stdin,'isatty',lambda:True)
    monkeypatch.setattr(sys.stdout,'isatty',lambda:True)
    monkeypatch.setattr(sys.stderr,'isatty',lambda:True)
    width=[columns]
    monkeypatch.setattr(tqdm.std,'_screen_shape_wrapper',lambda:lambda fp:(width[0],24))
    return width


def fixture_app(tmp_path,monkeypatch,verbose=False):
    source=tmp_path/'generated caption.png';Image.new('RGB',(100,40),'white').save(source)
    app=app_for(tmp_path,['-o']+(['--verbose'] if verbose else []),answers=iter([]))
    monkeypatch.setattr(cli,'repair_packages',lambda app:False)
    monkeypatch.setattr(cli.dependencies,'require_ocr',lambda *a,**k:{'path':'generated-fixture'})
    return app,source


def test_default_terminal_is_compact_but_caption_remains_in_results(tmp_path,monkeypatch,capsys):
    console(monkeypatch)
    app,source=fixture_app(tmp_path,monkeypatch)
    fragments=[{'text':'OCR-FRAGMENT-'+str(n),'words':[]} for n in range(150)]
    monkeypatch.setattr(app,'ocr_lines',lambda *a,**k:(fragments,False))
    result,code=app.process([str(source)])
    assert code==0 and len(result['results'][0]['caption'].splitlines())==150
    assert app.print_ocr_summary(result)
    output=capsys.readouterr()
    assert 'OCR-FRAGMENT-' not in output.err+output.out
    assert '1 ready (1 newly saved, 0 reused)' in output.out and '--verbose' in output.out
    assert '"results"' not in output.out and output.err.count('\n')<=3
    assert app._ocr_progress is None


def test_verbose_caption_is_wrapped_and_cannot_interpret_terminal_controls(tmp_path,monkeypatch,capsys):
    console(monkeypatch,80)
    app,source=fixture_app(tmp_path,monkeypatch,verbose=True)
    caption='Complete caption '+('wide words '*25)+'\x1b[2J\rAFTER-CONTROL'
    monkeypatch.setattr(app,'ocr_lines',lambda *a,**k:([{'text':caption,'words':[]}],True))
    result,code=app.process([str(source)])
    assert code==0 and result['results'][0]['caption']==caption
    output=capsys.readouterr().err
    assert 'Entire detected caption:' in output and 'REUSED' in output
    assert '\\x1b[2J\\x0dAFTER-CONTROL' in output and '\x1b[2J' not in output
    assert all(disp_len(frame)<=79 for frame in re.split('[\r\n]',output) if frame)


@pytest.mark.parametrize('columns',[40,80,120,240])
def test_shared_progress_frames_stay_bounded_and_keep_counts_visible(tmp_path,monkeypatch,capsys,columns):
    width=console(monkeypatch,columns)
    app,_source=fixture_app(tmp_path,monkeypatch)
    with shared.progress_bar(total=543,description='OCR',unit='image',
            bar_format='OCR {n_fmt}/{total_fmt} {percentage:3.0f}% |{bar:12}| ETA {remaining}') as progress:
        capsys.readouterr()
        app.ocr_progress_view(progress,Path('caption-'+'界'*140+'.png'))
        progress.update(92);progress.refresh()
        app._ocr_progress=progress
        app.diagnostics('One cache warning that must appear above the active bar.')
        app._ocr_progress=None
        initial=capsys.readouterr().err
        width[0]=80
        app.ocr_progress_view(progress,Path('a much shorter filename.png'))
        progress.refresh()
    resized=capsys.readouterr().err;output=initial+resized
    frames=[ANSI.sub('',frame) for frame in re.split('[\r\n]',output) if frame]
    assert all(disp_len(ANSI.sub('',frame))<=min(columns,140) for frame in re.split('[\r\n]',initial) if frame)
    assert all(disp_len(ANSI.sub('',frame))<=80 for frame in re.split('[\r\n]',resized) if frame)
    assert any('92/543' in frame for frame in frames)
    assert 'One cache warning' in output
    assert any('ETA' in frame for frame in frames if len(frame)>30)


@pytest.mark.parametrize('mode',['terminal','json','redirected'])
def test_main_terminal_summary_preserves_json_and_redirected_exports(tmp_path,monkeypatch,capsys,mode):
    console(monkeypatch)
    if mode=='redirected': monkeypatch.setattr(sys.stdout,'isatty',lambda:False)
    result={'state':'ocr_only','results':[{'file':'generated.png','state':'ocr_cached','reused':True,
        'caption':'FULL-CAPTION\nSECOND-LINE','cache':str(tmp_path/'.ocr'),'lines':2}],
        'summary':{'ocr_cached':1,'reused':1,'deferred':0,'failed':0}}
    monkeypatch.setattr(cli.App,'process',lambda app,targets:(result,0))
    assert cli.main(tmp_path,['-o']+(['--json'] if mode=='json' else []))==0
    output=capsys.readouterr()
    if mode=='terminal':
        assert 'OCR finished: 1 ready' in output.out and 'FULL-CAPTION' not in output.out
    else:
        assert json.loads(output.out)==result
        assert '\x1b' not in output.out+output.err


def test_interruption_closes_shared_bar_and_keeps_completed_results(tmp_path,monkeypatch):
    console(monkeypatch)
    app,source=fixture_app(tmp_path,monkeypatch)
    Image.new('RGB',(100,40),'white').save(tmp_path/'second fixture.png')
    calls=[];bars=[];real=shared.progress_bar
    @contextmanager
    def observed(**kwargs):
        with real(**kwargs) as progress:
            bars.append(progress);yield progress
    monkeypatch.setattr(shared,'progress_bar',observed)
    def interrupted(*args,**kwargs):
        calls.append(True)
        if len(calls)>1: raise KeyboardInterrupt()
        return [{'text':'completed caption','words':[]}],False
    monkeypatch.setattr(app,'ocr_lines',interrupted)
    with pytest.raises(KeyboardInterrupt): app.process([str(source.parent)])
    assert len(app.results)==1 and app.results[0]['state']=='ocr_cached'
    assert app._ocr_progress is None and bars[0].disable
