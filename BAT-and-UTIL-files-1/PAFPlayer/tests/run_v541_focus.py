"""Focused regression checks for V541 tray icon selection and hover safety."""
from __future__ import annotations

import ast
import ctypes
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import PAFPlayer_tray as tray


def check(condition, message):
    if not condition:
        raise AssertionError(message)


class App:
    def __init__(self):
        self.settings = {'TrayIconEnabled': 1, 'TrayIconStyle': 0}

    def load_player_settings(self):
        return dict(self.settings)

    def save_player_settings(self, values):
        self.settings.update(values)


class LiveTray:
    def __init__(self, app):
        self.app = app
        self.refreshed = False

    def refresh(self):
        self.refreshed = True

    def status(self):
        return {'saved_enabled': bool(self.app.settings['TrayIconEnabled']),
                'icon_style': self.app.settings['TrayIconStyle']}


check(len(tray.TRAY_ICON_STYLES) == 20, 'expected exactly 20 tray icon choices')
check(len({entry[0] for entry in tray.TRAY_ICON_STYLES}) == 20, 'icon keys must be unique')
check(len({tray.tray_icon_pixels(i)[0] for i in range(20)}) == 20, 'all native icon bitmaps must differ')
for index in range(20):
    pixels, mask = tray.tray_icon_pixels(index)
    check(len(pixels) == 32 * 32 * 4 and len(mask) == 32 * 4, 'invalid CreateIcon buffers')
if os.name == 'nt':
    icons = [tray.create_tray_icon(index) for index in range(20)]
    check(all(icons), 'Windows failed to create one or more native HICONs')
    for native_icon in icons:
        ctypes.windll.user32.DestroyIcon(native_icon)

app = App()
live = LiveTray(app)
runtime = SimpleNamespace(app=app, tray=live)
result = tray.configure(runtime, {'icon_style': 19})
check(result['icon_style'] == 19 and live.refreshed, 'web selection was not persisted/refreshed')
result = tray.configure(SimpleNamespace(app=app), {'icon_style': 3})
check(result['icon_style'] == 3 and len(result['icon_styles']) == 20, 'headless web response is incomplete')
try:
    tray.configure(runtime, {'icon_style': 20})
except ValueError:
    pass
else:
    raise AssertionError('out-of-range icon accepted')

hover = (ROOT / 'PAFPlayer_tray_hover.py').read_text(encoding='utf-8')
check('HOVER_DELAY_SECONDS = .70' in hover, 'hover delay missing')
check('0x00000020' in hover, 'WS_EX_TRANSPARENT missing')
check('CARD_WIDTH, CARD_HEIGHT, ICON_GAP = 450, 220, 12' in hover and 'Shell_NotifyIconGetRect' in hover,
      'safe placement missing')
check("'Choose tray icon'" in (ROOT / 'PAFPlayer_tray.py').read_text(encoding='utf-8'), 'native chooser missing')

main_text = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8-sig')
tree = ast.parse(main_text)
assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                  and any(isinstance(target, ast.Name) and target.id == '_PAF_BUNDLED_SOURCES'
                          for target in node.targets))
bundled = ast.literal_eval(assignment.value)
for name in ('PAFPlayer_tray', 'PAFPlayer_tray_hover'):
    check(bundled[name] == (ROOT / (name + '.py')).read_text(encoding='utf-8'), name + ' bundle drift')
check('"TrayIconStyle": 0' in main_text and 'PROGRAM_VERSION                 = "V541"' in main_text,
      'V541 version/default missing')
print('V541 focused tray checks passed')
