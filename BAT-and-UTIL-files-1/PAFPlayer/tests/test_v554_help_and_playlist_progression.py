from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')


def test_playlist_browser_yields_when_decoder_finishes():
    start = SOURCE.index('def interactive_playlist_browser(')
    end = SOURCE.index('\ndef load_playlist(', start)
    body = SOURCE[start:end]
    assert 'while not msvcrt.kbhit()' in body
    assert 'close_callback is not None and close_callback()' in body
    assert 'time.sleep(0.025)' in body


def test_single_navigation_keys_sort_before_function_keys():
    assert '"LEFT", "RIGHT", "UP", "DOWN"' in SOURCE
    assert 'if match: return (2, int(match.group(1)), upper)' in SOURCE
    assert 'return (1, single_named.get' in SOURCE
