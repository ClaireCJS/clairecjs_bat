"""Two real CLI processes: isolated silent playback --no-tray and --tray-only.

Preserves fixtures/reports. Does not stop or command the user's live player.
The observer records renderer events, not desktop screenshots.
"""
import argparse
import collections
import datetime
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import wave
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run_PAFPlayer_tests import install_guards, unique


def child(role, stage, address, report):
    work = stage / role
    work.mkdir(exist_ok=True)
    for key in ('APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP'):
        os.environ[key] = str(work)
    os.environ['PLAY_AUDIO_FILE_HISTORY_DB'] = str(work / 'history.sqlite3')
    for key in tuple(os.environ):
        if key.startswith('LASTFM_') or key == 'PAFPLAYER_DISCORD_WEBHOOK':
            os.environ.pop(key)
    tempfile.tempdir = str(work)
    sys.path.insert(0, str(stage))
    os.chdir(stage)
    sys.argv = [str(stage / 'PAFPlayer.py'), '--unit-tests']
    blocked = install_guards(ROOT / 'tests')
    import PAFPlayer as app
    import PAFPlayer_remote_tray as remote
    app.global_config_profiles_path = lambda: work / 'profiles.json'
    app.append_pafplayer_trace = lambda *a, **kw: None
    app.append_pafplayer_error = lambda *a, **kw: None
    app.append_pafplayer_exception = lambda *a, **kw: None
    errors = []
    sys.unraisablehook = lambda item: errors.append('Unraisable: ' + str(item.exc_value))
    app.record_pafplayer_runtime_warning = lambda *a, **kw: errors.append(str(a)[:1000])
    app.record_pafplayer_callback_exception = lambda *a, **kw: errors.append(str(a)[:1000])
    settings = remote.RemoteTrayAppSettings(address, work / 'settings')
    settings.install_player_preference_backend(app)
    pref = {
        'ExternalAlbumArtLyricsModeV180': int(os.environ.get('PAF_TEST_RESTORED_LYRICS', '0')),
        'Looping': 0, 'RepeatMode': 3,
        'ExternalFloatingLyricsGeometry': '1000x220+100+100',
        'ExternalFloatingLyricsKaraokeColorMode': 1,
        'ExternalAlbumArtPopupEmojimaxV295': 1,
        'ExternalAlbumArtKaraokeEnabledV336': 1,
        'ExternalAlbumArtPopupColorEmojiV295': 0,
        'ExternalAlbumArtKaraokeColorMode': 2,
        'KaraokeEmojimax': 1,
        'FloatingLyricsTrackIntroSeconds': '0.25',
    }
    settings.save_player_settings({
        'MachineOptions': {'remote_floating_lyrics': True, 'remote_hotkeys': False,
                          'remote_album_art': True, 'album_wallpaper': False},
        'RendererPreferences': {k: {'type': 1 if isinstance(v, str) else 4, 'value': v}
                                for k, v in pref.items()},
    })
    # Publish only these fixture preferences; never inherit the user's real registry.
    app._global_config_registry_value_snapshot = lambda: {'\\'.join(app._paf_registry_location(k)):
        {'kind': 'REG_SZ' if isinstance(v, str) else 'REG_DWORD', 'value': v} for k, v in pref.items()}
    import PAFPlayer_steam as steam
    steam.get_monitor = lambda module: SimpleNamespace(visualizer_fps=lambda value:value, block_gallery=lambda:False)
    # The tray CLI constructs this adapter itself; point it at the isolated file.
    original_init = remote.RemoteTrayAppSettings.__init__
    remote.RemoteTrayAppSettings.__init__ = lambda self, label, config_root=None: original_init(self, label, work / 'settings')
    events = collections.Counter()
    # Compare each real Tk variable's interpreter with its creation thread's root.
    import tkinter as tk
    roots_by_thread = {}
    init_root, init_variable = tk.Tk.__init__, tk.Variable.__init__
    def track_root(self, *args, **kwargs):
        init_root(self, *args, **kwargs)
        roots_by_thread[threading.get_ident()] = id(self.tk)
    init_top = tk.Toplevel.__init__
    def track_top(self, *args, **kwargs):
        init_top(self, *args, **kwargs)
        def inspect_options():
            if not self.winfo_exists() or self.title() != 'PAFPlayer — Tray Options': return
            pending = [self]; labels = []
            while pending:
                widget = pending.pop(); pending.extend(widget.winfo_children())
                try: labels.append(str(widget.cget('text')))
                except tk.TclError: pass
            events['options_dialogs'] += 1
            events['options_follow_checkbox'] += int('Follow the server’s artwork and lyric appearance' in labels)
            events['options_art_lyrics_choice'] += int('Lyrics over album artwork:' in labels)
            self.destroy()
        self.after(900, inspect_options)
    tk.Toplevel.__init__ = track_top
    def track_variable(self, *args, **kwargs):
        init_variable(self, *args, **kwargs)
        events['tk_variables'] += 1
        if id(self._tk) != roots_by_thread.get(threading.get_ident()):
            events['wrong_thread_interpreter'] += 1
    tk.Tk.__init__, tk.Variable.__init__ = track_root, track_variable
    event_stream = report.with_suffix('.events.jsonl').open('x', encoding='utf-8')
    samples = []
    if role == 'client':
        import faulthandler
        faulthandler.dump_traceback_later(38, file=sys.stderr)
        base = app.ExternalAlbumArtWindow
        class ObservedRenderer(base):
            def _gui_main(self):
                last = [0.0]
                def observe(frame, event, value):
                    name = frame.f_code.co_name
                    if event != 'return' or name not in ('render_floating_lyric', 'hide_floating_lyrics_window',
                                                         'expire_track_intro', 'process_commands'):
                        return
                    if name != 'process_commands': events[name] += 1
                    state = frame.f_locals.get('state')
                    if not isinstance(state, dict): return
                    now = time.monotonic()
                    if now - last[0] < .10: return
                    last[0] = now
                    window = state.get('floating_window')
                    text = str(state.get('lyric_floating') or '')
                    try: visibility = window.state() if window is not None else 'absent'
                    except Exception: visibility = 'destroyed'
                    root = frame.f_locals.get('root')
                    sample = {'at': now, 'event': name, 'text': text[:150], 'window': visibility,
                              'art_window': root.state() if root else 'unknown',
                              'art_lyric': str(state.get('lyric_artwork') or state.get('lyric') or '')[:150],
                              'karaoke': bool(state.get('artwork_karaoke_enabled')),
                              'art_color_mode': state.get('karaoke_color_mode'),
                              'variants': len(state.get('variants') or []),
                              'follow_server': settings.presentation_options()['inherit']}
                    samples.append(sample)
                    event_stream.write(json.dumps(sample) + '\n'); event_stream.flush()
                sys.setprofile(observe)
                try: return super()._gui_main()
                finally: sys.setprofile(None)
        app.ExternalAlbumArtWindow = ObservedRenderer
        import PAFPlayer_tray as tray
        original_start = tray.TrayController.start
        def start(controller):
            result = original_start(controller)
            option_timer = threading.Timer(8, lambda: controller.dispatch('options'))
            option_timer.daemon = True; option_timer.start()
            for seconds, mode in ((12, 'off'), (15, 'on'), (18, 'server')):
                change = threading.Timer(seconds, lambda value=mode: controller.runtime.app.set_presentation_option('artwork_lyrics', value))
                change.daemon = True; change.start()
            timer = threading.Timer(24, lambda: controller.dispatch('exit'))
            timer.daemon = True
            timer.start()
            return result
        tray.TrayController.start = start
        args = ['--tray-only', address, '--foreground']
    else:
        # Only silent generated media; disable optional outbound integrations.
        app.load_lastfm_credentials = lambda *a, **kw: None
        update = threading.Timer(22, lambda: pref.update({'ExternalAlbumArtKaraokeColorMode': 1}))
        update.daemon = True; update.start()
        runtime = app.paf_workflows()
        runtime.settings['monkeymote'] = {'enabled': False, 'port': 19371}
        args = ['--no-tray', '--no-visualizers', '--no-album-art', '--no-external-album-art',
                '--no-trim-edge-silence', '--no-loop', '--web-host=127.0.0.1', '--web-port=' + address.rsplit(':', 1)[1], str(stage / 'remote-test.wav')]
    started = time.monotonic()
    try:
        result = app.main(args)
    except BaseException as exc:
        import traceback
        errors.append(traceback.format_exc())
        result = 1
    finally:
        event_stream.close()
        with report.open('x', encoding='utf-8') as output:
            json.dump({'role': role, 'version': app.PROGRAM_VERSION, 'arguments': args,
                       'seconds': time.monotonic() - started, 'events': dict(events),
                       'samples': samples, 'errors': errors, 'blocked_writes': blocked}, output, indent=2)
    return result or 0


def run():
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    stage = unique(ROOT / 'tests/runs' / ('remote-artwork-v580-' + stamp))
    stage.mkdir(parents=True)
    source = ROOT / 'PAFPlayer.py'
    data = source.read_bytes()
    with (stage / source.name).open('xb') as output: output.write(data)
    assert hashlib.sha256(data).digest() == hashlib.sha256((stage / source.name).read_bytes()).digest()
    from PIL import Image
    Image.new('RGB', (360, 360), '#274060').save(stage / 'folder.jpg')
    with wave.open(str(stage / 'remote-test.wav'), 'wb') as wav:
        wav.setnchannels(2); wav.setsampwidth(2); wav.setframerate(44100)
        wav.writeframes(b'\0' * 44100 * 4 * 30)
    with (stage / 'remote-test.lrc').open('x', encoding='utf-8') as stream:
        stream.write('[00:00.00]First steady lyric\n[00:04.00]Whip it with a rainbow\n'
                     '[00:12.00]Second steady lyric\n[00:20.00]Whip it again\n[00:29.00]End\n')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    address = '127.0.0.1:' + str(port)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    processes = []
    records = []
    try:
        for role in ('server', 'client'):
            report = unique(ROOT / 'tests/reports' / (f'remote-artwork-v580-{stamp}-{role}.json'))
            log = report.with_suffix('.log')
            with log.open('xb') as output:
                process = subprocess.Popen([sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()),
                    '--child', role, str(stage), address, str(report)], stdout=output, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            processes.append(process)
            records.append({'role': role, 'pid': process.pid, 'report': str(report), 'log': str(log)})
            if role == 'server':
                deadline = time.monotonic() + 35
                while time.monotonic() < deadline and process.poll() is None:
                    try:
                        with opener.open('http://' + address + '/api/remote-tray/hello?timeline=0', timeout=1) as response:
                            hello = json.load(response)
                        if hello.get('official'):
                            records[-1]['verified_official'] = True
                            break
                    except Exception: pass
                    time.sleep(.25)
                else: raise RuntimeError('Isolated --no-tray server did not start: ' + str(log))
        for process in reversed(processes):
            process.wait(timeout=45)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate(); process.wait(timeout=10)
        summary = unique(ROOT / 'tests/reports' / (f'remote-artwork-v580-{stamp}-processes.json'))
        with summary.open('x', encoding='utf-8') as output:
            json.dump({'stage': str(stage), 'address': address, 'processes': records,
                       'source_sha256': hashlib.sha256(data).hexdigest(),
                       'exit_codes': [p.returncode for p in processes]}, output, indent=2)
        print(summary, flush=True)
        for record in records: print(record['log'], flush=True)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--child']:
        raise SystemExit(child(sys.argv[2], Path(sys.argv[3]), sys.argv[4], Path(sys.argv[5])))
    run()
