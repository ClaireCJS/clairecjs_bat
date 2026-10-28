import importlib.util
from pathlib import Path
import sys
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pafplayer_v548", ROOT / "PAFPlayer.py")
PAF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PAF
SPEC.loader.exec_module(PAF)


def test_cli_locked_bass_options_are_session_only_and_validated():
    remaining = PAF.apply_bass_cli_options([
        "--bass-reduction-while-locked", "--locked-bass-reduction-percent=65", "song.flac"
    ])
    assert remaining == ["song.flac"]
    with mock.patch.object(PAF, "paf_registry_query_value", side_effect=OSError):
        settings = PAF.load_bass_settings()
    assert settings["ReduceBassWhenLocked"] == 1
    assert settings["LockedBassReductionPercent"] == 65
    try:
        PAF.apply_bass_cli_options(["--locked-bass-reduction-percent=101"])
    except ValueError:
        pass
    else:
        raise AssertionError("out-of-range reduction must be rejected")


def test_explicit_on_off_persists_and_default_percent_saves_user_default():
    with mock.patch.object(PAF, "save_player_setting_value") as save_setting, mock.patch.object(
        PAF, "save_user_default"
    ) as save_default:
        remaining = PAF.apply_bass_cli_options([
            "--bass-reduction-while-locked=off",
            "--default-bass-reduction-percent-while-locked=50",
            "song.flac",
        ])
    assert remaining == ["song.flac"]
    save_setting.assert_called_once_with("ReduceBassWhenLocked", 0)
    save_default.assert_called_once_with("LockedBassReductionPercent", 50)
    assert PAF.PLAYER_SETTING_DEFAULTS["LockedBassReductionPercent"] == 50


def test_buffered_waveout_command_applies_locked_bass_before_expansion():
    with mock.patch.object(PAF, "probe_audio_stream_layout", return_value=(2, "stereo")):
        command = PAF.matrixmixer_inspired_ffmpeg_command(
            Path("ffmpeg.exe"), Path("song.flac"), 0, 100, 1.0, 5, 0,
            reduce_bass_when_locked=True, locked_bass_reduction_percent=60,
            bass_boost_enabled=False, bass_boost_percent=0, session_locked=True,
        )
    filters = command[command.index("-af") + 1].split(",")
    bass_index = next(index for index, value in enumerate(filters) if value.startswith("bass=g=-12"))
    pan_index = next(index for index, value in enumerate(filters) if value.startswith("pan=5.1"))
    assert bass_index < pan_index
