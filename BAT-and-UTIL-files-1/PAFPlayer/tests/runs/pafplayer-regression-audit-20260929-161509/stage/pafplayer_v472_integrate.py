"""One-time, checked integration into the current V471 source."""
import ast
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

p = Path('PAFPlayer.py')
original = p.read_bytes()
s = original.decode('utf-8-sig').replace('\r\n', '\n')
assert 'PROGRAM_VERSION                 = "V471"' in s
base = p.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt')
backup = p.with_name(base + '.bak'); index = 1
while backup.exists():
    backup = p.with_name(base + f' ({index}).bak'); index += 1
shutil.copyfile(p, backup)
assert hashlib.sha256(original).digest() == hashlib.sha256(backup.read_bytes()).digest()


def one(old, new):
    global s
    assert s.count(old) == 1, (old, s.count(old))
    s = s.replace(old, new, 1)


one('class _PAFBundledFeatures(', '_PAF_BUNDLED_SOURCES["PAFPlayer_screensaver"] = ' + repr(Path('PAFPlayer_screensaver.py').read_text(encoding='utf-8')) + '\n\nclass _PAFBundledFeatures(')
one('    html = augment(html)\n    return (', '    html = augment(html)\n    from PAFPlayer_screensaver import augment as screensaver_ui\n    html = screensaver_ui(html)\n    return (')
for method in ('GET', 'POST'):
    one('            def do_' + method + '(self):\n                from PAFPlayer_web_workflows import handle',
        '            def do_' + method + '(self):\n                from PAFPlayer_screensaver import handle as screensaver_handle\n                if screensaver_handle(self, owner, self.path.partition("?")[0]): return\n                from PAFPlayer_web_workflows import handle')
one('    def web_visualizer_active(self, now: float | None = None) -> bool:', '''    def note_screensaver_activity(self) -> None:
        self._last_screensaver_activity = time.monotonic()

    def status_client_active(self, now: float | None = None) -> bool:
        current = time.monotonic() if now is None else float(now)
        return self.client_active(current) or current - getattr(self, "_last_screensaver_activity", float("-inf")) <= 3.0

    def web_visualizer_active(self, now: float | None = None) -> bool:''')
one('web_client_active = bool(web_server is not None and web_server.client_active(now))',
    'web_client_active = bool(web_server is not None and web_server.status_client_active(now))')
one('web_server is not None and web_server.client_active(paused_now) and paused_now - last_web_publish',
    'web_server is not None and web_server.status_client_active(paused_now) and paused_now - last_web_publish')
one('PLAYER_BUILD_ID                 = "2026-09-29-v471-live-lock-bass-transition"', 'PLAYER_BUILD_ID                 = "2026-09-29-v472-optional-visual-screensaver"')
one('PROGRAM_VERSION                 = "V471"', 'PROGRAM_VERSION                 = "V472"')
one('PROGRAM_RELEASE_LABEL           = "V471"', 'PROGRAM_RELEASE_LABEL           = "V472"')
s = s.replace(s.splitlines()[1], '# CHAT ARTIFACT BUILD: 2026-09-29-V472-OPTIONAL-VISUAL-SCREENSAVER', 1)
compile(s, str(p), 'exec')
assert p.read_bytes() == original, 'Concurrent edit; backup preserved, overwrite refused'
p.write_bytes(s.replace('\n', '\r\n' if b'\r\n' in original else '\n').encode('utf-8'))
manifest = {'baseline': str(backup.resolve()), 'baseline_sha256': hashlib.sha256(original).hexdigest(),
            'legacy_sha256': hashlib.sha256(Path('play_audio_file.py').read_bytes()).hexdigest()}
with Path('pafplayer_v472_baseline.json').open('x', encoding='utf-8') as stream:
    json.dump(manifest, stream, indent=2)
print(json.dumps(manifest, indent=2))
