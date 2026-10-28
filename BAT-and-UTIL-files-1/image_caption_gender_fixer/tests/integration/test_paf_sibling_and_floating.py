import inspect
import os
from pathlib import Path
import textwrap
import pytest
from image_caption_gender_fixer import paf_album_art,paf_backend,paf_drcs
from image_caption_gender_fixer.floating_artwork import FloatingArtwork

ROOT=Path(os.environ.get('ICGF_TEST_INSTALLATION',Path(__file__).resolve().parents[2]))


def test_real_installed_sibling_routines_are_loaded_as_source_without_player_startup():
    backend=paf_backend.get_backend(ROOT)
    source=ROOT.parent/'PAFPlayer/PAFPlayer.py'
    if not source.is_file(): pytest.skip('No installed sibling PAFPlayer on this machine')
    assert backend.origin=='installed-pafplayer',backend.fallback_reason
    assert Path(backend.fit.__code__.co_filename)==source
    assert Path(backend.photo.__code__.co_filename)==source
    assert Path(backend.terminal.__code__.co_filename)==source
    graphics,metadata=paf_drcs.graphics(ROOT)
    assert metadata['origin']=='installed-pafplayer'
    assert Path(graphics['_visualizer_art_microtiles'].__code__.co_filename)==source
    assert Path(graphics['define_all_player_drcs'].__code__.co_filename)==source
    assert backend.source_sha256 and backend.version


def test_sibling_definitions_override_copies_without_executing_player_top_level(tmp_path):
    sibling=tmp_path/'PAFPlayer';sibling.mkdir()
    definitions=[]
    for name in paf_backend.GUI_NAMES+paf_backend.TERMINAL_NAMES:
        if name=='_pillow_fit_canvas_image':
            definitions.append('def _pillow_fit_canvas_image(data,width,height):\n return "installed sentinel", "original"\n')
        else:
            module=paf_album_art if name in paf_backend.GUI_NAMES else paf_backend
            definitions.append(textwrap.dedent(inspect.getsource(getattr(module,name))))
    (sibling/'PAFPlayer.py').write_text('PROGRAM_VERSION="TEST"\nraise RuntimeError("Player startup must not execute")\n'+'\n\n'.join(definitions),encoding='utf-8')
    backend=paf_backend.get_backend(tmp_path/'tool')
    assert backend.origin=='installed-pafplayer' and backend.version=='TEST'
    assert backend.fit(b'',1,1)==('installed sentinel','original')


def test_missing_sibling_uses_attributed_internal_fallback(tmp_path):
    backend=paf_backend.get_backend(tmp_path/'tool')
    assert backend.origin=='internal-pafplayer-copy' and backend.fallback_reason
    assert backend.fit is paf_album_art._pillow_fit_canvas_image


def test_actual_paf_terminal_routine_renders_twin_drcs_without_chafa(tmp_path,monkeypatch):
    from PIL import Image
    source=tmp_path/'terminal.png';Image.new('RGB',(200,100),'purple').save(source)
    import subprocess
    def blocked(*args,**kwargs): raise AssertionError('Twin DRCS preview started an external encoder')
    monkeypatch.setattr(subprocess,'run',blocked)
    payload=paf_backend.terminal_image(ROOT,source,30,8)
    assert payload.startswith(b'\x1bP0;1;1;10;0;2;20;0{ @')
    assert b'\x1b( @' in payload and b'\x1b(B' in payload and b'48;2;' in payload
    assert not list(tmp_path.glob('.icgf-*'))


def test_floating_window_follows_latest_image_and_thread_is_joined(tmp_path,monkeypatch):
    from PIL import Image
    original_schedule=paf_album_art.AlbumArtReview.schedule_draw
    def delayed_draw(viewer,event=None):
        original_schedule(viewer,event)
        viewer.root.after_cancel(viewer._draw_after)
        viewer._draw_after=viewer.root.after(450,viewer.draw)
    monkeypatch.setattr(paf_album_art.AlbumArtReview,'schedule_draw',delayed_draw)
    first=tmp_path/'first.png';last=tmp_path/'last.png'
    Image.new('RGB',(200,100),'red').save(first)
    Image.new('RGB',(100,200),'blue').save(last)
    artwork=FloatingArtwork(ROOT)
    try:
        artwork.update(first,'First',{'detected':'first caption','proposed':'first proposal'})
        thread=artwork.thread
        assert thread.is_alive() and not thread.daemon
        artwork.update(last,'Last',{'detected':'last caption','proposed':'last proposal'})
        assert artwork.thread is thread and artwork.last_path==str(last)
        assert not artwork.error
    finally: artwork.close()
    assert artwork.stopped.is_set() and not artwork.thread.is_alive()
