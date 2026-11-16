"""Focused artwork-chrome edit; verified sibling backups are archived, never deleted."""
from pathlib import Path
from datetime import datetime
import ast
import hashlib
import sys

ROOT=Path(__file__).resolve().parents[1]
def unique(p):
    original=p;n=0
    while p.exists():
        n+=1;p=original.with_name(f'{original.stem} ({n}){original.suffix}')
    return p
def write(name,text):
    p=ROOT/name;data=text.encode('utf-8');p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():
        old=p.read_bytes()
        if old==data:return
        backup=unique(p.with_name(p.name+datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')))
        with backup.open('xb') as f:f.write(old)
        assert hashlib.sha256(backup.read_bytes()).digest()==hashlib.sha256(old).digest()
        assert p.read_bytes()==old,'Concurrent edit detected'
    with p.open('wb' if p.exists() else 'xb') as f:f.write(data)
    assert p.read_bytes()==data
    if 'backup' in locals():
        folder=ROOT/'releases' if p.name=='PAFPlayer.py' else ROOT/'backups' if p.name in ('PAFPlayer_changelog.md','PAFPlayer_TODO.md') else ROOT/'docs' if p.suffix=='.md' else p.parent
        if folder!=backup.parent:
            target=unique(folder/backup.name)
            assert ROOT in backup.resolve().parents and ROOT in target.resolve().parents
            backup.rename(target);backup=target
        print('BACKUP',backup)
    print('WROTE',p)

def main():
    p=ROOT/'PAFPlayer.py';source=p.read_text(encoding='utf-8')
    assert hashlib.sha256(p.read_bytes()).hexdigest()=='743c9c47dbb6235775acad26adeca040474d85d63254d8d7c2dc82057729d0c1'
    def change(before,after):
        nonlocal source
        assert source.count(before)==1,(before[:90],source.count(before))
        source=source.replace(before,after,1)
    def replace_function(name,body):
        nonlocal source
        tree=ast.parse(source)
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='ExternalAlbumArtWindow')
        gui=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_gui_main')
        fn=next(n for n in gui.body if isinstance(n,ast.FunctionDef) and n.name==name)
        lines=source.splitlines(True)
        source=''.join(lines[:fn.lineno-1])+body+'\n'+''.join(lines[fn.end_lineno:])
    change("'2026-11-02-v641-emojimax-solution-color-parity'","'2026-11-04-v642-artwork-popup-chrome'")
    change("PROGRAM_VERSION                = 'V641'","PROGRAM_VERSION                = 'V642'")
    change("PROGRAM_RELEASE_LABEL          = 'V641'","PROGRAM_RELEASE_LABEL          = 'V642'")
    change('        root.title("PAFPlayer Album Art")','''        root.withdraw()
        # Keep one borderless native style for the entire lifetime. Focus changes
        # only repaint our transparent wrapper, never recreate the HWND.
        root.overrideredirect(True)
        root.title("PAFPlayer Album Art")''')
    a=source.index('        # A normal client-area command strip')
    b=source.index('        # V181 owns exactly one',a)
    source=source[:a]+'''        control_strip = tk.Frame(root, background="#f0f0f0", borderwidth=0, height=44)
        control_strip.pack(fill="x", side="top", padx=5, pady=(5, 0))
        control_strip.pack_propagate(False)
        control_strip.grid_propagate(False)
'''+source[b:]
    replace_function('suppress_native_windows_border','''        def suppress_native_windows_border() -> None:
            """Retain taskbar access without adding a native caption, edge or shadow."""
            if os.name != "nt":
                return
            hwnd = widget_root_hwnd(root)
            if not hwnd or state.get("native_border_style_hwnd") == hwnd:
                return
            try:
                from ctypes import wintypes
                # Private prototypes cannot be overwritten by another popup's
                # WNDPROC bindings on ctypes.windll.user32.
                user32 = ctypes.WinDLL("user32", use_last_error=True)
                get_long = user32.GetWindowLongPtrW
                set_long = user32.SetWindowLongPtrW
                get_long.argtypes = [wintypes.HWND, ctypes.c_int]
                get_long.restype = ctypes.c_ssize_t
                set_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
                set_long.restype = ctypes.c_ssize_t
                style = int(get_long(hwnd, -20))
                # APPWINDOW keeps Alt-Tab/taskbar access; strip TOOLWINDOW and
                # all extended edges. The permanent Tk override removes caption.
                clean = (style | 0x00040000) & ~(0x00000080 | 0x00000100 | 0x00000200 | 0x00020000)
                set_long(hwnd, -20, clean)
                pos = user32.SetWindowPos
                pos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
                pos.restype = wintypes.BOOL
                pos(hwnd, None, 0, 0, 0, 0, 0x0037)  # FRAMECHANGED, no move/size/z-order/activation
                with contextlib.suppress(Exception):
                    dwm = ctypes.WinDLL("dwmapi")
                    attr = dwm.DwmSetWindowAttribute
                    attr.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
                    attr.restype = ctypes.c_long
                    disabled = ctypes.c_int(1)  # DWMNCRP_DISABLED, supported by Windows 10
                    attr(hwnd, 2, ctypes.byref(disabled), ctypes.sizeof(disabled))
                state["native_border_style_hwnd"] = hwnd
            except (AttributeError, OSError, ValueError, TypeError):
                return
''')
    replace_function('window_is_active','''        def window_is_active() -> bool:
            """Compare full-width HWNDs; a failed query must not leave stale chrome."""
            if os.name == "nt":
                try:
                    from ctypes import wintypes
                    get_foreground = ctypes.WinDLL("user32").GetForegroundWindow
                    get_foreground.argtypes = []
                    get_foreground.restype = wintypes.HWND
                    return bool(int(get_foreground() or 0) == int(state.get("native_hwnd", 0) or 0))
                except (AttributeError, OSError, ValueError, TypeError):
                    return False
            with contextlib.suppress(Exception):
                return root.focus_displayof() is not None
            return False
''')
    replace_function('apply_focus_chrome','''        def apply_focus_chrome() -> None:
            """Keep the header visible, with one transparent outer border when inactive."""
            active = bool(window_is_active())
            state["window_active"] = active
            set_native_focus_chrome(active)
            border_color = "#909090" if active else EXTERNAL_ALBUM_ART_TRANSPARENT_KEY
            root.configure(background=border_color)
            art_border_frame.configure(background=border_color)
''')
    replace_function('hide_focus_chrome_immediately','''        def hide_focus_chrome_immediately(_event=None) -> None:
            """Erase the complete custom frame without hiding the title/web row."""
            state["window_active"] = False
            set_native_focus_chrome(False)
            root.configure(background=EXTERNAL_ALBUM_ART_TRANSPARENT_KEY)
            art_border_frame.configure(background=EXTERNAL_ALBUM_ART_TRANSPARENT_KEY)
            schedule_focus_chrome_update()
''')
    change('''                    canvas.pack_configure(padx=border, pady=border)
            apply_focus_chrome()''','''                    canvas.pack_configure(padx=border, pady=border)
                    control_strip.pack_configure(padx=border, pady=(border, 0))
            control_strip.configure(height=max(32, round(44 * dpi / EXTERNAL_ALBUM_ART_BASE_DPI)))
            fitter = state.get("fit_identity_label")
            if callable(fitter): root.after_idle(fitter)
            apply_focus_chrome()''')
    replace_function('ensure_titlebar_lyrics_button','''        def ensure_titlebar_lyrics_button() -> None:
            """One fixed-height song-title row with one Artwork web-config button."""
            if state.get("artwork_web_button") is not None:
                apply_focus_chrome()
                return
            import tkinter.font as tkfont
            control_strip.columnconfigure(0, weight=1)
            control_strip.rowconfigure(0, weight=1)
            identity_label = tk.Label(control_strip, text="", width=1, anchor="w",
                background="#f0f0f0", foreground="#202020", padx=7, pady=0,
                borderwidth=0, cursor="fleur")
            identity_label.grid(row=0, column=0, sticky="nsew")
            web_button = tk.Button(control_strip, text="🌐", padx=6, pady=0,
                relief="raised", borderwidth=1, font=("Segoe UI Emoji", 14),
                takefocus=False, command=lambda: open_web_interface("artworkPopupSection"))
            web_button.grid(row=0, column=1, sticky="ns", padx=(2, 2), pady=2)
            state["artwork_web_button"] = web_button
            state["identity_label"] = identity_label
            install_tooltip(web_button, "Open Artwork settings in the web interface")
            font = tkfont.Font(root=root, family="Segoe UI", size=-28, weight="bold")
            identity_label.configure(font=font)

            def fit_identity_label(_event=None) -> None:
                # Font height follows the row. Long names ellipsize horizontally
                # rather than shrinking to a tiny second line or pushing buttons.
                height = max(12, control_strip.winfo_height() - 4)
                size = height
                font.configure(size=-size)
                while size > 8 and font.metrics("linespace") > height:
                    size -= 1
                    font.configure(size=-size)
                text = str(state.get("track_identity") or "")
                available = max(1, identity_label.winfo_width() - 14)
                if font.measure(text) > available:
                    lo, hi = 0, len(text)
                    while lo < hi:
                        mid = (lo + hi + 1) // 2
                        if font.measure(text[:mid] + "…") <= available: lo = mid
                        else: hi = mid - 1
                    text = text[:lo] + "…"
                identity_label.configure(text=text)

            identity_label.bind("<Configure>", fit_identity_label, add="+")
            state["fit_identity_label"] = fit_identity_label
            root.after_idle(fit_identity_label)

            def begin_drag(event, move=False):
                if event.widget.winfo_toplevel() is not root: return
                rect = windows_window_rect(int(state.get("native_hwnd", 0) or 0))
                if rect is None: return
                left, top, right, bottom = rect
                border = int(state.get("border_pixels", 5))
                edges = (event.x_root < left + border, event.y_root < top + border,
                         event.x_root >= right - border, event.y_root >= bottom - border)
                if not move and not any(edges): return
                root.focus_force()
                state["chrome_drag"] = (event.x_root, event.y_root, rect, None if move else edges)
                root.grab_set()
                return "break"

            def drag(event):
                start = state.get("chrome_drag")
                if not start: return
                x, y, rect, edges = start
                dx, dy = event.x_root - x, event.y_root - y
                left, top, right, bottom = rect
                if edges is None:
                    result = (left+dx, top+dy, right+dx, bottom+dy)
                else:
                    a,b,c,d = edges
                    minimum = EXTERNAL_ALBUM_ART_MIN_SIZE
                    left = min(right-minimum, left+dx) if a else left
                    right = max(left+minimum, right+dx) if c else right
                    top = min(bottom-minimum, top+dy) if b else top
                    bottom = max(top+minimum, bottom+dy) if d else bottom
                    if ctrl_is_down():
                        size = max(minimum, right-left, bottom-top)
                        if a: left=right-size
                        else: right=left+size
                        if b: top=bottom-size
                        else: bottom=top+size
                    result = (left,top,right,bottom)
                windows_set_window_rect(int(state.get("native_hwnd", 0) or 0), result)
                return "break"

            def end_drag(_event):
                if state.pop("chrome_drag", None):
                    with contextlib.suppress(Exception): root.grab_release()
                    return "break"

            identity_label.bind("<ButtonPress-1>", lambda event: begin_drag(event, True))
            root.bind("<ButtonPress-1>", begin_drag, add="+")
            root.bind("<B1-Motion>", drag, add="+")
            root.bind("<ButtonRelease-1>", end_drag, add="+")
            # The one-button header retains window commands in its context menu.
            menu = tk.Menu(root, tearoff=False)
            topmost = tk.BooleanVar(master=root, value=bool(state.get("art_topmost", False)))
            menu.add_checkbutton(label="Always on top", variable=topmost,
                command=lambda: apply_art_topmost_setting(bool(topmost.get())))
            menu.add_separator()
            menu.add_command(label="Close artwork popup", command=lambda: user_closed_window())
            def context_menu(event):
                topmost.set(bool(state.get("art_topmost", False)))
                try: menu.tk_popup(event.x_root, event.y_root)
                finally: menu.grab_release()
                return "break"
            identity_label.bind("<Button-3>", context_menu)
            root.bind("<Alt-F4>", lambda event: (user_closed_window(), "break")[-1])
            apply_focus_chrome()
''')
    replace_function('titlebar_control_min_width','''        def titlebar_control_min_width() -> int:
            """Long titles ellipsize; they never dictate artwork window width."""
            return 320
''')
    change('int(title_strip.winfo_reqheight()) + int(control_strip.winfo_reqheight())','int(control_strip.winfo_reqheight())')
    change('''                                label.configure(text=state["track_identity"])
                                fitter = state.get("fit_identity_label")''','''                                fitter = state.get("fit_identity_label")''')
    change('''  frame.addEventListener('scroll',()=>{if(!configTabScrollRaf)configTabScrollRaf=requestAnimationFrame(refresh)},{passive:true});refresh();
}''','''  frame.addEventListener('scroll',()=>{if(!configTabScrollRaf)configTabScrollRaf=requestAnimationFrame(refresh)},{passive:true});refresh();
  const openHash=()=>{let id;try{id=decodeURIComponent(location.hash.slice(1))}catch(_){return}const entry=entries.find(([section])=>section.id===id);if(entry)entry[1].click()};
  if(window.pafConfigHashHandler)window.removeEventListener('hashchange',window.pafConfigHashHandler);
  window.pafConfigHashHandler=openHash;window.addEventListener('hashchange',openHash);
  requestAnimationFrame(openHash);
}''')
    change('usage_line("Focused art zoom −/+", "zoom buttons appear in the artwork control strip only while that window has focus")','usage_line("Artwork 🌐 / title drag", "open web Artwork settings; drag the title to move, focused edges to resize; right-click title for window options")')
    compile(source,str(p),'exec')
    write('PAFPlayer.py',source)

if __name__=='__main__': main()
