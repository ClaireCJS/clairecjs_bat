"""Tray presentation settings and native options; never sends playback commands."""
from __future__ import annotations

import gc
import time


def portable_preference(name):
    """Only presentation values travel; desktop placement and visibility stay local."""
    return (isinstance(name, str) and len(name) < 160
            and name.startswith(('ExternalAlbumArt', 'ExternalFloating', 'ArtworkLyricSolution', 'FloatingLyricSolution'))
            and not any(part in name for part in ('Geometry', 'Placement', 'Position',
                                                   'LayoutSize', 'ManualSize', 'LyricsMode')))


def validated_preferences(value):
    if not isinstance(value, dict):
        return None
    result = {}
    for name, item in list(value.items())[:256]:
        if not portable_preference(name) or not isinstance(item, dict):
            continue
        kind, data = item.get('type'), item.get('value')
        if kind == 4 and type(data) is int and 0 <= data <= 0xffffffff:
            result[name] = {'type': 4, 'value': data}
        elif kind == 1 and isinstance(data, str) and len(data) <= 4096:
            result[name] = {'type': 1, 'value': data}
    return result


def server_presentation(app, owner):
    """Cache HTTP-thread registry work; omit all non-presentation values."""
    now = time.monotonic()
    cached = getattr(owner, '_remote_presentation_cache', None)
    if cached and now - cached[0] < 1.0:
        return cached[1]
    values = app._global_config_registry_value_snapshot()
    reverse = {'\\'.join(location): name for name, location in app._PAF_REGISTRY_EXACT_LOCATIONS.items()}
    candidates = {}
    for qualified, record in values.items():
        name = reverse.get(qualified, qualified.rsplit('\\', 1)[-1])
        if portable_preference(name) and isinstance(record, dict):
            candidates[name] = {'type': 4 if record.get('kind') == 'REG_DWORD' else 1,
                                'value': record.get('value')}
    # These defaults depend on server state/platform and must travel explicitly.
    for name, loader in ((app.EXTERNAL_ALBUM_ART_KARAOKE_ENABLED_VALUE, app.load_external_album_art_karaoke_enabled),
                         (app.EXTERNAL_ALBUM_ART_POPUP_COLOR_EMOJI_VALUE, app.load_external_album_art_popup_color_emoji)):
        candidates[name] = {'type': 4, 'value': int(loader())}
    result = validated_preferences(candidates)
    owner._remote_presentation_cache = (now, result)
    return result


MACHINE_LABELS = {
    'lyrics_tooltip': 'Show sung lyrics above the tray',
    'album_wallpaper': 'Use album artwork as this computer’s wallpaper',
    'remote_hotkeys': 'Capture playback and overlay hotkeys on this computer',
    'remote_floating_lyrics': 'Show Floating Lyrics on this computer',
    'remote_album_art': 'Show album artwork on this computer',
}


def run_options_dialog(tray, overlays=None, stop_event=None):
    """One owned Tk interpreter; usable from either tray without touching playback."""
    import tkinter as tk
    from tkinter import ttk
    from PAFPlayer_tray import icon_catalog
    root = tk.Tk()
    root.title('PAFPlayer — Tray Options')
    root.geometry('660x590')
    root.minsize(600, 540)
    panel = ttk.Frame(root, padding=16)
    panel.pack(fill='both', expand=True)
    remote = overlays is not None
    settings = tray.runtime.app
    ttk.Label(panel, text='Tray Options', font=('Segoe UI', 17, 'bold')).pack(anchor='w')
    ttk.Label(panel, text=('This computer · ' + tray.runtime.server.label if remote
                          else 'This computer · official player')).pack(anchor='w', pady=(0, 12))
    error = tk.StringVar(master=root)
    def invoke(function):
        try:
            function()
            error.set('')
        except Exception as exc:
            error.set(str(exc))
    variables = {}
    for name, label in MACHINE_LABELS.items():
        if not remote and name.startswith('remote_'):
            continue
        variable = tk.BooleanVar(master=root, value=tray._machine.options.get(name, False))
        variables[name] = variable
        def toggle(key=name, var=variable):
            if bool(var.get()) != bool(tray._machine.options.get(key)):
                tray.dispatch('machine_' + key)
        ttk.Checkbutton(panel, text=label, variable=variable,
                        command=lambda f=toggle: invoke(f)).pack(anchor='w', pady=3)
    info = tk.BooleanVar(master=root, value=tray.full_info_tooltip_enabled())
    ttk.Checkbutton(panel, text='Full track information on hover', variable=info,
                    command=lambda: invoke(lambda: tray.set_full_info_tooltip(info.get()))).pack(anchor='w', pady=3)
    catalog = icon_catalog()
    row = ttk.Frame(panel); row.pack(fill='x', pady=8)
    ttk.Label(row, text='Tray icon:').pack(side='left')
    picker = ttk.Combobox(row, state='readonly', width=40,
                          values=[entry['label'] for entry in catalog])
    picker.pack(side='left', padx=8)
    picker.current(tray.selected_icon_style())
    picker.bind('<<ComboboxSelected>>', lambda _e: invoke(lambda: tray.set_icon_style(picker.current())))
    if remote:
        ttk.Separator(panel).pack(fill='x', pady=8)
        follow = tk.BooleanVar(master=root, value=settings.presentation_options()['inherit'])
        def save_follow():
            settings.set_presentation_option('inherit', follow.get())
        ttk.Checkbutton(panel, text='Follow the server’s artwork and lyric appearance',
                        variable=follow, command=lambda: invoke(save_follow)).pack(anchor='w', pady=4)
        lyric_row = ttk.Frame(panel); lyric_row.pack(fill='x', pady=6)
        ttk.Label(lyric_row, text='Lyrics over album artwork:').pack(side='left')
        lyric_choices = ('Use server setting', 'On', 'Off')
        lyric_values = ('server', 'on', 'off')
        lyrics = ttk.Combobox(lyric_row, state='readonly', values=lyric_choices, width=20)
        lyrics.pack(side='left', padx=8)
        lyrics.current(lyric_values.index(settings.presentation_options()['artwork_lyrics']))
        lyrics.bind('<<ComboboxSelected>>', lambda _e: invoke(lambda:
                    settings.set_presentation_option('artwork_lyrics', lyric_values[lyrics.current()])))
        ttk.Label(panel, text='Window placement stays local. Local appearance edits stop following the server.',
                  wraplength=610).pack(anchor='w', pady=4)
        buttons = ttk.Frame(panel); buttons.pack(fill='x', pady=8)
        def configure(target):
            settings.set_presentation_option('inherit', False)
            follow.set(False)
            overlays.configure(target)
        for target, label in (('artwork', 'Artwork appearance…'), ('floating', 'Floating lyric appearance…')):
            ttk.Button(buttons, text=label, command=lambda t=target: invoke(lambda: configure(t))).pack(side='left', padx=(0, 8))
        center = ttk.Frame(panel); center.pack(fill='x', pady=6)
        ttk.Button(center, text='Center artwork', command=lambda: overlays.center(False)).pack(side='left', padx=(0, 8))
        ttk.Button(center, text='Center floating lyrics', command=lambda: overlays.center(True)).pack(side='left')
    else:
        saved = tk.BooleanVar(master=root, value=bool(settings.load_player_settings().get('TrayIconEnabled', 1)))
        def save_enabled():
            settings.save_player_settings({'TrayIconEnabled': int(saved.get())})
            tray.refresh()
        ttk.Checkbutton(panel, text='Enable tray icon by default', variable=saved,
                        command=lambda: invoke(save_enabled)).pack(anchor='w', pady=5)
    ttk.Label(panel, text='Triple left-click: Previous · Triple right-click: Next\nDouble-click: Pause / Play',
              wraplength=610).pack(anchor='w', pady=10)
    ttk.Label(panel, textvariable=error, foreground='#a02020', wraplength=610).pack(anchor='w')
    ttk.Button(panel, text='Close', command=root.destroy).pack(side='bottom', anchor='e', pady=8)
    def refresh():
        if tray._closing or (stop_event and stop_event.is_set()):
            root.destroy(); return
        for name, var in variables.items():
            var.set(bool(tray._machine.options.get(name)))
        info.set(tray.full_info_tooltip_enabled())
        if remote:
            options = settings.presentation_options()
            follow.set(options['inherit'])
            lyrics.current(lyric_values.index(options['artwork_lyrics']))
        root.after(500, refresh)
    root.after(500, refresh)
    try:
        root.mainloop()
    finally:
        try: root.destroy()
        except tk.TclError: pass


def options_thread(tray):
    try:
        run_options_dialog(tray)
    except Exception as exc:
        tray.runtime.log('tray.options-error', reason=str(exc))
    finally:
        gc.collect()
