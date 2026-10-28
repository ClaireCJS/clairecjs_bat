"""Automatic Discord transport and conditional setup guidance."""
import threading
import types
from pathlib import Path
from unittest import mock

import PAFPlayer_discord as discord


APP_ID = '123456789012345678'


def runtime(tmp_path):
    state = {'playing': True, 'track': {'title': 'Song', 'artist': 'Artist'}}
    server = types.SimpleNamespace(snapshot=lambda: state,
                                   current_audio=lambda: tmp_path / 'track.flac')
    active = types.SimpleNamespace(
        app=types.SimpleNamespace(__file__=str(tmp_path / 'PAFPlayer.py')),
        server=server,
        settings={'discord_enabled': True, 'discord_application_id': APP_ID,
                  'discord_share_local_titles': True, 'discord_transport': 'automatic'},
        stop_event=threading.Event(), save_settings=mock.Mock(), log=mock.Mock())
    return active, state


def desktop(*, available=True, events=None):
    pipe = mock.Mock()
    pipe.client_id = APP_ID
    pipe.pipe = object()
    if not available:
        pipe.connect.side_effect = ConnectionError('Discord desktop IPC was not found')
    if events is not None:
        pipe.set_activity.side_effect = lambda activity: events.append(('desktop', activity))
    return pipe


def sdk(*, events=None):
    helper = mock.Mock()
    helper.client_id = APP_ID
    helper.running.return_value = False
    helper.connected = False
    helper.authorization_required = True
    helper.authorizing = False
    if events is not None:
        helper.close.side_effect = lambda: events.append(('sdk_close', None))
    return helper


def test_automatic_uses_desktop_without_starting_sdk(tmp_path):
    active, _ = runtime(tmp_path)
    pipe = desktop()
    with mock.patch.object(discord, 'DiscordIPC', return_value=pipe), \
         mock.patch.object(discord, 'SocialSDKProcess', side_effect=AssertionError('SDK should stay idle')):
        publisher = discord.Publisher(active)
        publisher.tick(now=1)
    pipe.set_activity.assert_called_once()
    assert publisher.active_transport == 'desktop_ipc'
    active.discord = publisher
    assert discord.connection_health(active)['instructions'] == ''


def test_automatic_falls_back_to_sdk_without_duplicate_desktop_update(tmp_path):
    active, _ = runtime(tmp_path)
    pipe, helper = desktop(available=False), sdk()
    with mock.patch.object(discord, 'DiscordIPC', return_value=pipe), \
         mock.patch.object(discord, 'SocialSDKProcess', return_value=helper):
        publisher = discord.Publisher(active)
        publisher.tick(now=1)
    pipe.set_activity.assert_not_called()
    helper.start.assert_called_once()
    helper.set_activity.assert_called_once()
    assert publisher.active_transport == 'social_sdk'


def test_automatic_switches_to_desktop_after_sdk_fallback(tmp_path):
    active, _ = runtime(tmp_path)
    events = []
    unavailable, available = desktop(available=False), desktop(events=events)
    helper = sdk(events=events)
    with mock.patch.object(discord, 'DiscordIPC', side_effect=[unavailable, available]), \
         mock.patch.object(discord, 'SocialSDKProcess', return_value=helper):
        publisher = discord.Publisher(active)
        publisher.tick(now=1)
        publisher.tick(now=16)
    assert events[0][0] == 'sdk_close'
    assert events[1][0] == 'desktop'
    assert publisher.active_transport == 'desktop_ipc'
    assert publisher.social is None


def test_automatic_falls_back_when_desktop_pipe_breaks(tmp_path):
    active, _ = runtime(tmp_path)
    pipe, helper = desktop(), sdk()
    pipe.set_activity.side_effect = [None, BrokenPipeError('pipe closed')]
    with mock.patch.object(discord, 'DiscordIPC', return_value=pipe), \
         mock.patch.object(discord, 'SocialSDKProcess', return_value=helper):
        publisher = discord.Publisher(active)
        publisher.tick(now=1)
        publisher.tick(now=16)
    assert publisher.active_transport == 'social_sdk'
    helper.set_activity.assert_called_once()
    pipe.close.assert_called()


def test_guidance_only_when_enabled_and_unhealthy(tmp_path):
    active, _ = runtime(tmp_path)
    assert 'Start Discord Desktop' in discord.connection_health(active)['instructions']
    active.settings['discord_enabled'] = False
    assert discord.connection_health(active)['instructions'] == ''
    active.settings['discord_enabled'] = True
    publisher = discord.Publisher(active)
    publisher.ipc = desktop()
    publisher.active_transport = 'desktop_ipc'
    active.discord = publisher
    assert discord.connection_health(active) == {
        'enabled': True, 'working': True,
        'connection': 'desktop_ipc', 'instructions': ''}
    active.settings['discord_share_local_titles'] = False
    assert 'Allow titles/artists' in discord.connection_health(active)['instructions']


def test_automatic_allows_sdk_account_authorization(tmp_path):
    active, _ = runtime(tmp_path)
    publisher = discord.Publisher(active)
    active.discord = publisher
    helper = sdk()
    with mock.patch.object(discord, 'SocialSDKProcess', return_value=helper):
        publisher.authorize()
    helper.authorize.assert_called_once()
    helper.set_activity.assert_not_called()


def test_sdk_presence_failure_shows_guidance_even_when_connected(tmp_path):
    active, _ = runtime(tmp_path)
    publisher = discord.Publisher(active)
    publisher.active_transport = 'social_sdk'
    publisher.social = sdk()
    publisher.social.connected = True
    publisher.social.publish_failed = False
    active.discord = publisher
    assert discord.connection_health(active)['instructions'] == ''
    publisher.social.publish_failed = True
    health = discord.connection_health(active)
    assert not health['working']
    assert 'Social SDK profile update failed' in health['instructions']


def test_helper_status_protocol_tracks_ready_and_failed_publication(tmp_path):
    active, _ = runtime(tmp_path)
    bridge = discord.SocialSDKProcess(active, APP_ID)
    observed = []

    def stream():
        yield 'STATE\tREADY\n'
        observed.append((bridge.connected, bridge.publish_failed))
        yield 'STATUS\tDiscord profile update failed\n'
        observed.append((bridge.connected, bridge.publish_failed))
        yield 'STATUS\tDiscord profile activity updated\n'
        observed.append((bridge.connected, bridge.publish_failed))

    bridge.process = types.SimpleNamespace(stdout=stream())
    bridge._read_status()
    assert observed == [(True, False), (True, True), (True, False)]
    assert not bridge.connected


def test_automatic_choice_is_saved(tmp_path):
    active, _ = runtime(tmp_path)
    active.settings['discord_enabled'] = False
    with mock.patch.object(discord.Publisher, 'start'):
        discord.configure(active, {'enabled': True, 'transport': 'automatic',
                                   'application_id': APP_ID, 'share_local_titles': True})
    assert active.settings['discord_transport'] == 'automatic'
    active.save_settings.assert_called_once()


def test_web_controls_have_automatic_mode_and_hidden_guidance():
    source = (Path(__file__).resolve().parents[1] / 'PAFPlayer_workflows_ui.py').read_text(encoding='utf-8')
    assert '<option value="automatic">' in source
    assert 'id="discordMethodNote"' in source
    assert 'role="status" hidden' in source
    assert "state?.discord_health?.instructions" in source
    assert "!state?.discord_health?.working" in source
