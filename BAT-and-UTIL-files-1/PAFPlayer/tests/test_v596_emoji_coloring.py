"""V596 emoji rendering choices and remote tray preference isolation."""
from pathlib import Path
from unittest import mock
import ast

import PAFPlayer as app
from PAFPlayer_remote_tray import RemoteTrayAppSettings


ROOT = Path(__file__).resolve().parents[1]


def test_exact_choices_follow_the_selected_treatment():
    assert app.emoji_coloring_choices(0, 0, 0) == (
        'Official color emoji — no additional coloring',
        'Monochrome emoji — Plasma',
    )
    assert app.emoji_coloring_choices(0, 0, 2)[1] == 'Monochrome emoji — Vertical wave'
    assert app.emoji_coloring_choices(1, 3, 0)[1] == 'Monochrome emoji — Ocean'
    assert app.emoji_coloring_choices(2, 3, 0)[1] == 'Monochrome emoji — Solid color'


def test_artwork_and_floating_labels_use_their_own_saved_treatments():
    with (mock.patch.object(app, 'load_external_album_art_karaoke_color_mode', return_value=1),
          mock.patch.object(app, 'load_external_album_art_karaoke_color_palettes', return_value=(0, 3, 0)),
          mock.patch.object(app, 'load_external_album_art_karaoke_pattern_treatments', return_value=(0, 0, 0)),
          mock.patch.object(app, 'load_external_floating_karaoke_color_mode', return_value=0),
          mock.patch.object(app, 'load_external_floating_karaoke_color_palettes', return_value=(0, 0, 0)),
          mock.patch.object(app, 'load_external_floating_karaoke_pattern_treatments', return_value=(2, 0, 0))):
        assert app.current_emoji_coloring_choices('artwork')[1] == 'Monochrome emoji — Ocean'
        assert app.current_emoji_coloring_choices('floating')[1] == 'Monochrome emoji — Vertical wave'


def test_tray_request_uses_renderer_queue_and_existing_preference():
    renderer = object.__new__(app.ExternalAlbumArtWindow)
    renderer._ensure_started = mock.Mock()
    renderer._commands = mock.Mock()
    assert renderer.set_popup_color_emoji(True) is True
    renderer._commands.put.assert_called_once_with(('set-popup-color-emoji', True))


def test_remote_tray_edit_stays_in_its_server_profile(tmp_path):
    settings = RemoteTrayAppSettings('music.example:666', config_root=tmp_path)
    key = app.EXTERNAL_ALBUM_ART_POPUP_COLOR_EMOJI_VALUE
    settings.set_server_preferences({key: {'type': 4, 'value': 1}})
    with (mock.patch.object(app, 'ensure_pafplayer_registry_migrated'),
          mock.patch.object(app, 'paf_registry_query_value'),
          mock.patch.object(app, 'paf_registry_set_value'),
          mock.patch.object(app, 'paf_registry_delete_value')):
        settings.install_player_preference_backend(app)
        assert app.load_external_album_art_popup_color_emoji() is True
        app.save_external_album_art_popup_color_emoji(False)
        assert app.load_external_album_art_popup_color_emoji() is False
    saved = settings.load_player_settings()
    assert saved['RendererPreferences'][key] == {'type': 4, 'value': 0}
    assert saved['PresentationOptions']['inherit'] is False


def test_single_file_bundle_matches_tray_options_source():
    source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
    prefix = "_PAF_BUNDLED_SOURCES['PAFPlayer_tray_options'] = "
    line = next(line for line in source.splitlines() if line.startswith(prefix))
    assert ast.literal_eval(line[len(prefix):]) == (ROOT / 'PAFPlayer_tray_options.py').read_text(encoding='utf-8')
