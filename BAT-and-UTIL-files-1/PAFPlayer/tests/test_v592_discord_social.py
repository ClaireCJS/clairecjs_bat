"""Focused transport and privacy checks; the licensed SDK is tested after download."""
import base64
import io
import threading
import types
from pathlib import Path
from unittest import mock

import pytest

import PAFPlayer_discord as discord


def runtime(tmp_path):
    state={'playing':True,'track':{'title':'A Song','artist':'An Artist'}}
    server=types.SimpleNamespace(snapshot=lambda:state,current_audio=lambda:tmp_path/'music.flac')
    result=types.SimpleNamespace(
        app=types.SimpleNamespace(__file__=str(tmp_path/'PAFPlayer.py')),
        server=server, settings={'discord_enabled':True,'discord_application_id':'123456789012345678',
                                 'discord_share_local_titles':True,'discord_transport':'social_sdk'},
        stop_event=threading.Event(),save_settings=mock.Mock(),log=mock.Mock())
    return result,state


def test_social_route_never_opens_desktop_ipc(tmp_path):
    active,state=runtime(tmp_path)
    helper=mock.Mock()
    helper.client_id=active.settings['discord_application_id']
    helper.running.return_value=False
    with mock.patch.object(discord,'SocialSDKProcess',return_value=helper), \
         mock.patch.object(discord,'DiscordIPC',side_effect=AssertionError('IPC must not open')):
        publisher=discord.Publisher(active)
        publisher.tick(now=1)
        helper.start.assert_called_once()
        helper.set_activity.assert_called_once_with({'details':'🎵 A Song · 👩‍🎤 An Artist',
                                                      'state':'🎤 ♪','instance':False})
        state['private']=True
        publisher.tick(now=2)
        helper.set_activity.assert_called_with(None)


def test_desktop_mode_keeps_existing_ipc(tmp_path):
    active,_=runtime(tmp_path)
    active.settings['discord_transport']='desktop_ipc'
    pipe=mock.Mock()
    pipe.client_id=active.settings['discord_application_id']
    with mock.patch.object(discord,'DiscordIPC',return_value=pipe), \
         mock.patch.object(discord,'SocialSDKProcess',side_effect=AssertionError('SDK must not start')):
        discord.Publisher(active).tick(now=1)
    pipe.set_activity.assert_called_once()


def test_social_helper_protocol_encodes_activity_and_has_no_path(tmp_path):
    active,_=runtime(tmp_path)
    bridge=discord.SocialSDKProcess(active,active.settings['discord_application_id'])
    written=io.StringIO()
    bridge.process=types.SimpleNamespace(stdin=written,poll=lambda:None)
    bridge.start=lambda:None
    bridge.set_activity({'details':'Björk','state':'Paused · Artist','instance':False})
    op,title,artist,image,image_text=written.getvalue().rstrip('\n').split('\t')
    assert op=='SET'
    assert base64.b64decode(title).decode('utf-8')=='Björk'
    assert base64.b64decode(artist).decode('utf-8')=='Paused · Artist'
    assert not image and not image_text
    assert str(tmp_path) not in written.getvalue()


def test_missing_helper_is_clear_and_does_not_change_settings(tmp_path):
    active,_=runtime(tmp_path)
    before=active.settings.copy()
    assert not discord.social_sdk_available(active)
    publisher=discord.Publisher(active)
    publisher.tick(now=1)
    assert 'SDK helper is not installed' in active.discord_status
    assert active.settings==before
    active.save_settings.assert_not_called()


def test_saved_transport_and_authorization_rules(tmp_path):
    active,_=runtime(tmp_path)
    active.settings['discord_enabled']=False
    with mock.patch.object(discord.Publisher,'start'):
        result=discord.configure(active,{'enabled':True,'transport':'social_sdk',
                                         'application_id':'123456789012345678',
                                         'share_local_titles':True})
    assert result['ok']
    assert active.settings['discord_transport']=='social_sdk'
    active.save_settings.assert_called_once()
    with mock.patch.object(discord.SocialSDKProcess,'authorize') as authorize, \
         mock.patch.object(discord.SocialSDKProcess,'start'):
        discord.configure(active,{'operation':'authorize'})
    authorize.assert_called_once()


def test_bad_transport_and_id_do_not_save(tmp_path):
    active,_=runtime(tmp_path)
    before=active.settings.copy()
    with pytest.raises(ValueError):discord.configure(active,{'enabled':True,'transport':'unofficial'})
    with pytest.raises(ValueError):discord.configure(active,{'enabled':True,'transport':'social_sdk','application_id':'bad'})
    assert active.settings==before
    active.save_settings.assert_not_called()


def test_migration_defaults_to_desktop_ipc(tmp_path):
    active,_=runtime(tmp_path)
    active.settings.pop('discord_transport')
    with mock.patch.object(discord,'DiscordIPC') as ipc:
        ipc.return_value.client_id=active.settings['discord_application_id']
        discord.Publisher(active).tick(now=1)
    ipc.assert_called_once()


def test_web_controls_include_explicit_social_and_account_actions():
    source=(Path(__file__).resolve().parents[1]/'src'/'PAFPlayer_workflows_ui.py').read_text(encoding='utf-8')
    assert 'id="discordTransport"' in source
    assert 'id="discordConnect"' in source
    assert 'id="discordForget"' in source
    assert "application_id:$('discordApplicationId').value.trim()" in source
