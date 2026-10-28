"""Explicit Windows install overrides remain opt-in and support deferred retry."""
import os
from unittest import mock

import PAFPlayer as app
import PAFPlayer_lockscreen as lockscreen


def test_tray_motif_abort_is_returned_to_survey():
    question = {'kind': 'tray_style'}
    with mock.patch.object(app, '_install_survey_arrow_menu', return_value='abort'):
        assert app._install_survey_arrow_choice(question, 0) == 'abort'


def test_explicit_lockscreen_override_defers_when_uac_disabled(tmp_path):
    with mock.patch.dict(os.environ, {'LOCALAPPDATA': str(tmp_path)}), \
         mock.patch.object(lockscreen, 'uac_enabled', return_value=False), \
         mock.patch.object(lockscreen, 'install_embedded_lockscreen') as install:
        message = app._install_survey_install_lockscreen(lambda _: '')
        assert 'did not change UAC' in message
        assert lockscreen.deferred_install_path().is_file()
        install.assert_not_called()


def test_deferred_install_retries_after_uac_is_enabled(tmp_path):
    with mock.patch.dict(os.environ, {'LOCALAPPDATA': str(tmp_path)}):
        lockscreen.request_deferred_install()
        with mock.patch.object(lockscreen, 'installed_version', return_value=''), \
             mock.patch.object(lockscreen, 'uac_enabled', return_value=False), \
             mock.patch.object(lockscreen, 'install_embedded_lockscreen') as install:
            assert lockscreen.maybe_auto_install_lockscreen() == 0
            install.assert_not_called()
        with mock.patch.object(lockscreen, 'installed_version', return_value=''), \
             mock.patch.object(lockscreen, 'uac_enabled', return_value=True), \
             mock.patch.object(lockscreen, 'install_embedded_lockscreen', return_value=0) as install:
            assert lockscreen.maybe_auto_install_lockscreen() == 0
            install.assert_called_once()
        with mock.patch.object(lockscreen, 'installed_version', return_value=lockscreen.EMBEDDED_INSTALL_VERSION), \
             mock.patch.object(lockscreen, 'install_embedded_lockscreen') as install:
            assert lockscreen.maybe_auto_install_lockscreen() == 0
            install.assert_not_called()
