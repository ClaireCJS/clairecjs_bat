"""Discord lyric lead time, saved setting, and browser-free clock updates."""
import ast
import math
from pathlib import Path
import threading
import time
from unittest import mock

import pytest

import PAFPlayer as app
import PAFPlayer_discord as discord
from test_v592_discord_social import runtime


ROOT = Path(__file__).resolve().parents[1]


def timed_state():
    return {
        'playing': True, 'paused': False, 'lyric': 'First line',
        'lyric_timeline': [[0.0, 'First line'], [10.0, 'Second line'], [12.0, '']],
        'lyric_position_seconds': 8.5, 'lyric_clock_epoch': 100.0,
        'karaoke_offset_seconds': 0.0, 'speed': 1.0,
    }


def test_lead_selects_future_lyric_without_changing_zero_lag():
    state = timed_state()
    assert discord.discord_lyric_at(state, 0, now_epoch=100) == 'First line'
    assert discord.discord_lyric_at(state, 1.5, now_epoch=100) == 'Second line'
    assert discord.discord_lyric_at(state, 1.5, now_epoch=102) == 'Second line'
    state['lyric_position_seconds'] = 10.5
    assert discord.discord_lyric_at(state, 1.5, now_epoch=100) == ''


def test_pause_fallback_offset_and_playback_speed():
    state = timed_state()
    state['paused'] = True
    assert discord.discord_lyric_at(state, 5, now_epoch=100) == 'First line'
    state['paused'] = False
    state['speed'] = 2.0
    assert discord.discord_lyric_at(state, .75, now_epoch=100) == 'Second line'
    state['speed'] = 1.0
    state['karaoke_offset_seconds'] = .5
    assert discord.discord_lyric_at(state, 1.0, now_epoch=100) == 'Second line'
    state['lyric_timeline'] = []
    assert discord.discord_lyric_at(state, 1.5, now_epoch=100) == 'First line'


def test_public_activity_uses_lead_and_still_clears_private_tracks(tmp_path):
    active, state = runtime(tmp_path)
    state.update(timed_state())
    state['lyric_clock_epoch'] = time.time()
    active.settings['discord_lag_seconds'] = 1.5
    activity, _ = discord.public_activity(active)
    assert activity['state'] == '🎤 Second line'
    state['private'] = True
    assert discord.public_activity(active)[0] is None


@pytest.mark.parametrize('bad', ['nan', math.inf, -1, 5.01, 'not a number', True])
def test_invalid_lag_cannot_partially_change_settings(tmp_path, bad):
    active, _ = runtime(tmp_path)
    before = active.settings.copy()
    with pytest.raises(ValueError, match='Discord lag'):
        discord.configure(active, {'enabled': True, 'application_id': active.settings['discord_application_id'],
                                   'transport': 'social_sdk', 'lag_seconds': bad})
    assert active.settings == before
    active.save_settings.assert_not_called()


def test_valid_lag_is_saved_without_starting_an_unrequested_connection(tmp_path):
    active, _ = runtime(tmp_path)
    active.settings['discord_enabled'] = False
    result = discord.configure(active, {'enabled': False, 'lag_seconds': '1.5'})
    assert result['lag_seconds'] == 1.5
    assert active.settings['discord_lag_seconds'] == 1.5
    assert active.discord_status.startswith('Disabled')
    active.save_settings.assert_called_once()


def test_lightweight_clock_refresh_does_not_build_browser_status(tmp_path):
    server = object.__new__(app.PAFWebServer)
    server._lock = threading.RLock()
    server._state = {'track': {'title': 'Current'}, 'metadata': {}, 'lyric': ''}
    server._current_audio = tmp_path / 'current.flac'
    with mock.patch.object(server, '_refresh_status_json_locked', side_effect=AssertionError('Browser JSON built')):
        server.publish_discord_clock(
            lyric='First line', lyric_timeline=[[0, 'First line']], position=3.0,
            clock_epoch=100.0, offset=.2, speed=1.0, paused=False,
        )
    snapshot = server.discord_snapshot()
    assert snapshot['lyric'] == 'First line'
    assert snapshot['_audio_path'] == tmp_path / 'current.flac'
    assert snapshot['lyric_position_seconds'] == 3.0


def test_faster_publish_checks_do_not_reprobe_cover_art_each_time(tmp_path):
    active, state = runtime(tmp_path)
    active.app.probe_audio_raw_tags = mock.Mock(return_value={})
    for lyric in ('One', 'Two', 'Three'):
        state['lyric'] = lyric
        assert discord.public_activity(active)[0]['state'] == '🎤 ' + lyric
    active.app.probe_audio_raw_tags.assert_called_once()
    state['metadata'] = {'Album': 'Changed'}
    discord.public_activity(active)
    assert active.app.probe_audio_raw_tags.call_count == 2


def test_web_control_and_single_file_bundle_match_sidecars():
    ui = (ROOT / 'src' / 'PAFPlayer_workflows_ui.py').read_text(encoding='utf-8')
    assert 'id="discordLagSlider"' in ui
    assert 'id="discordLagSeconds" type="text"' in ui
    assert 'lag_seconds:readDiscordLag()' in ui
    source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
    prefix = '_PAF_BUNDLED_SOURCES = '
    bundle = ast.literal_eval(next(line[len(prefix):] for line in source.splitlines() if line.startswith(prefix)))
    for name in ('PAFPlayer_discord', 'PAFPlayer_workflows_ui'):
        assert bundle[name] == (ROOT / 'src' / (name + '.py')).read_text(encoding='utf-8')
