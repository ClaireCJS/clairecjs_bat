from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')


def test_channels_have_favorite_default_contract():
    assert '"output_channels": ("OutputChannelsFavorites", "OutputChannels")' in SOURCE
    assert 'if key == "output_channels":' in SOURCE
    assert 'return int(value) in {2, 5, 7, 12}' in SOURCE


def test_locked_session_uses_read_only_query_before_desktop_fallback():
    start = SOURCE.index('def windows_session_is_locked()')
    end = SOURCE.index('\ndef bass_adjustment_db', start)
    body = SOURCE[start:end]
    assert '_windows_wts_session_is_locked()' in body
    assert '_windows_input_desktop_is_locked()' in body
    assert body.index('_windows_wts_session_is_locked()') < body.index('_windows_input_desktop_is_locked()')
    assert 'SwitchDesktop' not in body
