from pathlib import Path
import importlib.util


ROOT = Path(__file__).resolve().parents[1]


def load_tray():
    spec = importlib.util.spec_from_file_location('paf_tray_v551', ROOT / 'src' / 'PAFPlayer_tray.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_twenty_types_ten_colors_make_two_hundred_combinations():
    tray = load_tray()
    assert len(tray.TRAY_ICON_TYPES) == 20
    assert len(tray.TRAY_ICON_COLORS) == 10
    assert len(tray.TRAY_ICON_STYLES) == 200
    assert len({item[4] for item in tray.TRAY_ICON_STYLES}) == 20


def test_every_combination_renders_native_pixels():
    tray = load_tray()
    for index in range(200):
        pixels, mask = tray.tray_icon_pixels(index)
        assert len(pixels) == 32 * 32 * 4
        assert len(mask) == 32 * 4


def test_full_info_hover_contract_is_persistent_and_delayed():
    tray_source = (ROOT / 'src' / 'PAFPlayer_tray.py').read_text(encoding='utf-8')
    hover_source = (ROOT / 'src' / 'PAFPlayer_tray_hover.py').read_text(encoding='utf-8')
    player_source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
    assert 'Full info on tooltip' in tray_source
    assert "'TrayFullInfoTooltip'" in tray_source
    assert 'HOVER_DELAY_SECONDS = .666' in hover_source
    assert 'min(199' in player_source
