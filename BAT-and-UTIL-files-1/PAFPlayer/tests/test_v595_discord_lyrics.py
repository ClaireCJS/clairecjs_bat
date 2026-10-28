"""Displayed-lyric publication cadence on both Discord connections."""
from unittest import mock

import pytest

import PAFPlayer_discord as discord
from test_v592_discord_social import runtime


@pytest.mark.parametrize('transport', ['desktop_ipc', 'social_sdk'])
def test_lyric_changes_publish_once_and_animation_does_not(tmp_path, transport):
    active, state = runtime(tmp_path)
    active.settings['discord_transport'] = transport
    state['lyric'] = 'First line'
    bridge = mock.Mock()
    bridge.client_id = active.settings['discord_application_id']
    bridge.running.return_value = True
    bridge_class = discord.DiscordIPC if transport == 'desktop_ipc' else discord.SocialSDKProcess
    with mock.patch.object(discord, bridge_class.__name__, return_value=bridge):
        publisher = discord.Publisher(active)
        publisher.tick(now=1)
        state['lyric_progress'] = .9
        publisher.tick(now=2)
        state['lyric_progress'] = 0
        publisher.tick(now=3)
        assert bridge.set_activity.call_count == 1
        state['lyric'] = 'Second line'
        publisher.tick(now=4)
        assert bridge.set_activity.call_count == 2
        assert bridge.set_activity.call_args.args[0]['state'] == '🎤 Second line'
        state['lyric'] = ''
        publisher.tick(now=5)
        assert bridge.set_activity.call_count == 3
        assert bridge.set_activity.call_args.args[0]['state'] == '🎤 ♪'
        state['private'] = True
        publisher.tick(now=6)
        bridge.set_activity.assert_called_with(None)


def test_application_name_is_not_embedded_in_payload(tmp_path):
    active, state = runtime(tmp_path)
    state['metadata'] = {'Album': 'A Record', 'Year': '2003'}
    state['lyric'] = 'Sing along'
    activity, _ = discord.public_activity(active)
    assert activity['details'] == '🎵 A Song · 👩‍🎤 An Artist · 💿 A Record (2003)'
    assert activity['state'] == '🎤 Sing along'
    assert 'name' not in activity


@pytest.mark.parametrize('transport', ['desktop_ipc', 'social_sdk'])
def test_track_change_replaces_metadata_and_lyric(tmp_path, transport):
    active, state = runtime(tmp_path)
    active.settings['discord_transport'] = transport
    state['lyric'] = 'Old lyric'
    bridge = mock.Mock()
    bridge.client_id = active.settings['discord_application_id']
    bridge.running.return_value = True
    bridge_class = discord.DiscordIPC if transport == 'desktop_ipc' else discord.SocialSDKProcess
    with mock.patch.object(discord, bridge_class.__name__, return_value=bridge):
        publisher = discord.Publisher(active)
        publisher.tick(now=1)
        state['track'] = {'title': 'Next song', 'artist': 'Next artist'}
        state['metadata'] = {'Album': 'Next album', 'Year': '2024'}
        state['lyric'] = 'New lyric'
        publisher.tick(now=2)
    assert bridge.set_activity.call_count == 2
    activity = bridge.set_activity.call_args.args[0]
    assert activity['details'] == '🎵 Next song · 👩‍🎤 Next artist · 💿 Next album (2024)'
    assert activity['state'] == '🎤 New lyric'
