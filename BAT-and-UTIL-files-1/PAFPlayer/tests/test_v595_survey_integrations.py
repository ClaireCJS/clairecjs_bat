"""Survey connection checks and credential handling."""
from unittest import mock

import PAFPlayer as app
import PAFPlayer_discord as discord


def answers(*values):
    source = iter(values)
    return lambda _: next(source)


def test_discord_desktop_test_does_not_publish_activity():
    output, plan = [], {}
    pipe = mock.Mock()
    with mock.patch.object(discord, 'DiscordIPC', return_value=pipe):
        app._install_survey_integration({'key': 'discord'},
                                        answers('d', '123456789012345678', 't'),
                                        output.append, plan, interactive=False)
    pipe.connect.assert_called_once()
    pipe.close.assert_called_once()
    pipe.set_activity.assert_not_called()
    assert plan == {'discord_transport': 'desktop_ipc',
                    'discord_application_id': '123456789012345678'}
    assert 'pipe opened' in '\n'.join(output)


def test_lastfm_secrets_do_not_enter_survey_plan():
    output, plan = [], {}
    app._install_survey_integration({'key': 'lastfm'},
                                    answers('listener', 'api-key', 'api-secret', 'password', ''),
                                    output.append, plan, interactive=False)
    assert plan == {'lastfm_username': 'listener'}
    assert 'api-secret' not in '\n'.join(output)
    assert 'password' not in repr(plan)
