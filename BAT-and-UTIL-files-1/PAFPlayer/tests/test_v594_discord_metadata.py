"""Rich Presence text and artwork contracts for both Discord transports."""
import base64
import io
import threading
import types
from pathlib import Path
from unittest import mock

import PAFPlayer_discord as discord


def runtime(tmp_path, metadata=None, raw=None):
    state={'playing':True,'paused':False,
           'track':{'title':'A Song','artist':'An Artist'},'metadata':metadata or {}}
    app=types.SimpleNamespace(probe_audio_raw_tags=lambda path:raw or {})
    server=types.SimpleNamespace(snapshot=lambda:state,current_audio=lambda:tmp_path/'song.flac')
    active=types.SimpleNamespace(app=app,server=server,
                                 settings={'discord_share_local_titles':True},
                                 stop_event=threading.Event(),log=mock.Mock())
    return active,state


def test_artist_song_album_and_year_are_labeled(tmp_path):
    active,state=runtime(tmp_path,{'Album':'A Record','Year':'2002-08-31'})
    activity,status=discord.public_activity(active)
    assert status=='Ready'
    assert activity['details']=='🎵 A Song · 👩‍🎤 An Artist · 💿 A Record (2002)'
    assert activity['state']=='🎤 ♪'
    state['paused']=True
    state['playing']=False
    state['lyric']='A lyric on the screen'
    assert discord.public_activity(active)[0]['state']=='🎤 A lyric on the screen'


def test_long_titles_keep_both_artist_and_song_within_discord_limit(tmp_path):
    active,state=runtime(tmp_path,{'Album':'A'*250,'Year':'1989'})
    state['track']={'title':'Song'*100,'artist':'Artist'*100}
    activity,_=discord.public_activity(active)
    assert all(mark in activity['details'] for mark in ('🎵','👩‍🎤','💿'))
    assert len(activity['details'])<=128 and len(activity['state'])<=128


def test_missing_metadata_lyric_and_stop(tmp_path):
    active,state=runtime(tmp_path)
    state['track']={'title':'Only title'}
    assert discord.public_activity(active)[0]=={
        'details':'🎵 Only title','state':'🎤 ♪','instance':False}
    state['lyric']='  '
    assert discord.public_activity(active)[0]['state']=='🎤 ♪'
    state['lyric']='Long ' * 100
    assert len(discord.public_activity(active)[0]['state'])<=128
    state['transport_stopped']=True
    assert discord.public_activity(active)[0] is None


def test_exact_musicbrainz_release_id_adds_cover_asset(tmp_path):
    mbid='76df3287-6cda-33eb-8e9a-044b5e15ffdd'
    active,_=runtime(tmp_path,{'Album':'A Record','Year':'2002'},
                     {'MUSICBRAINZ_ALBUMID':mbid})
    activity,_=discord.public_activity(active)
    assert activity['assets']=={
        'large_image':f'https://coverartarchive.org/release/{mbid}/front-500',
        'large_text':'A Record (2002)'}


def test_explicit_public_cover_url_and_private_url_filter(tmp_path):
    active,_=runtime(tmp_path,{'Cover Art URL':'https://images.example.org/cover.jpg'})
    assert discord.public_activity(active)[0]['assets']['large_image']=='https://images.example.org/cover.jpg'
    for url in ('http://images.example.org/cover.jpg','https://127.0.0.1/cover.jpg',
                'https://player.local/cover.jpg','https://user:token@images.example.org/cover.jpg',
                'https://images.example.org/cover.jpg?token=secret'):
        active.server.snapshot()['metadata']={'Cover Art URL':url}
        assert 'assets' not in discord.public_activity(active)[0]


def test_private_or_disabled_sharing_never_probes_or_sends_cover(tmp_path):
    active,state=runtime(tmp_path,{'Genre':'Private'}, {'MUSICBRAINZ_ALBUMID':'76df3287-6cda-33eb-8e9a-044b5e15ffdd'})
    active.app.probe_audio_raw_tags=mock.Mock()
    assert discord.public_activity(active)[0] is None
    active.app.probe_audio_raw_tags.assert_not_called()
    state['metadata']={}
    active.settings['discord_share_local_titles']=False
    assert discord.public_activity(active)[0] is None
    active.app.probe_audio_raw_tags.assert_not_called()


def test_social_helper_receives_art_and_tooltip(tmp_path):
    active,_=runtime(tmp_path)
    bridge=discord.SocialSDKProcess(active,'123456789012345678')
    output=io.StringIO()
    bridge.process=types.SimpleNamespace(stdin=output,poll=lambda:None)
    bridge.start=lambda:None
    bridge.set_activity({'details':'🎤 Song','state':'💿 Album (2020)',
                         'assets':{'large_image':'https://images.example.org/cover.jpg',
                                   'large_text':'Album (2020)'}})
    command,*fields=output.getvalue().strip().split('\t')
    assert command=='SET'
    assert [base64.b64decode(field).decode('utf-8') for field in fields]==[
        '🎤 Song','💿 Album (2020)','https://images.example.org/cover.jpg','Album (2020)']


def test_desktop_ipc_receives_art_without_local_file_path(tmp_path):
    active,_=runtime(tmp_path,{'Cover Art URL':'https://images.example.org/cover.jpg'})
    activity,_=discord.public_activity(active)
    pipe=discord.DiscordIPC('123456789012345678')
    pipe.pipe=io.BytesIO()
    pipe.set_activity(activity)
    assert b'images.example.org/cover.jpg' in pipe.pipe.getvalue()
    assert str(tmp_path).encode() not in pipe.pipe.getvalue()
