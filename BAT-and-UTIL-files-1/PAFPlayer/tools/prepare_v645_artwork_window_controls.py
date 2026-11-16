"""Add border cursors and focus-only maximize without native frame changes."""
import hashlib
from prepare_v642_artwork_chrome import ROOT, write


def main():
    path = ROOT/'PAFPlayer.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == 'df254a38b04578414ebfc2740f9cdb03abad26eec04b25d7a94cddf9ade79a58'
    source = path.read_text(encoding='utf-8')

    def change(old, new):
        nonlocal source
        assert source.count(old) == 1, (old[:90], source.count(old))
        source = source.replace(old, new, 1)

    change("'2026-11-05-v644-emojimax-bigger-text'", "'2026-11-06-v645-artwork-window-controls'")
    change("PROGRAM_VERSION                = 'V644'", "PROGRAM_VERSION                = 'V645'")
    change("PROGRAM_RELEASE_LABEL          = 'V644'", "PROGRAM_RELEASE_LABEL          = 'V645'")
    change('''            art_border_frame.configure(background=border_color)
''', '''            art_border_frame.configure(background=border_color)
            sync = state.get("sync_artwork_window_controls")
            if callable(sync): sync(active)
''')
    change('''            art_border_frame.configure(background=EXTERNAL_ALBUM_ART_TRANSPARENT_KEY)
            schedule_focus_chrome_update()''', '''            art_border_frame.configure(background=EXTERNAL_ALBUM_ART_TRANSPARENT_KEY)
            sync = state.get("sync_artwork_window_controls")
            if callable(sync): sync(False)
            schedule_focus_chrome_update()''')
    change('''            def begin_drag(event, move=False):
''', '''            def resize_edges(x, y, rect):
                if not bool(state.get("window_active")) or bool(state.get("chrome_maximized")):
                    return (False, False, False, False)
                left, top, right, bottom = rect
                if not (left <= x < right and top <= y < bottom):
                    return (False, False, False, False)
                border = int(state.get("border_pixels", 5))
                return (x < left + border, y < top + border,
                        x >= right - border, y >= bottom - border)

            def update_resize_cursor(event=None):
                # The root cursor is inherited by the transparent frame. Child
                # controls retain their own cursor, and interior motion resets it.
                edges = (False, False, False, False)
                if bool(state.get("window_active")) and not bool(state.get("chrome_maximized")):
                    start = state.get("chrome_drag")
                    if start and start[3] is not None:
                        edges = start[3]
                    elif event is not None and event.widget.winfo_toplevel() is root:
                        rect = windows_window_rect(int(state.get("native_hwnd", 0) or 0))
                        if rect is not None:
                            edges = resize_edges(event.x_root, event.y_root, rect)
                left, top, right, bottom = edges
                cursor = ("size_nw_se" if (left and top) or (right and bottom) else
                          "size_ne_sw" if (right and top) or (left and bottom) else
                          "size_we" if left or right else "size_ns" if top or bottom else "")
                if root.cget("cursor") != cursor:
                    root.configure(cursor=cursor)

            def sync_window_controls(active):
                maximized = bool(state.get("chrome_maximized"))
                maximize_button.configure(text="❐" if maximized else "□")
                identity_label.configure(cursor="arrow" if maximized else "fleur")
                if active:
                    maximize_button.place(relx=1.0, x=-2, y=2, anchor="ne",
                        width=max(32, round(control_strip.winfo_height() * .8)), relheight=1.0, height=-4)
                    maximize_button.lift()
                else:
                    maximize_button.place_forget()
                update_resize_cursor()

            def toggle_maximize():
                if not bool(state.get("window_active")):
                    return
                hwnd = int(state.get("native_hwnd", 0) or 0)
                maximized = bool(state.get("chrome_maximized"))
                if bool(state.get("idle_promoted")):
                    end_idle_art_routine()
                rect = windows_window_rect(hwnd)
                if rect is None:
                    return
                monitors = external_album_art_monitor_work_areas()
                if maximized:
                    target = state.get("chrome_restore_rect")
                    if target is None:
                        return
                    x, y, right, bottom = target
                    geometry = clamp_external_album_art_geometry(
                        f"{right-x}x{bottom-y}{x:+d}{y:+d}", monitors)
                    width, height, x, y = _parse_external_album_art_geometry(geometry)
                    target = (x, y, x+width, y+height)
                else:
                    monitor = external_album_art_idle_monitor_for_rect(rect, monitors)
                    if monitor is None:
                        return
                    target = tuple(monitor[:4])
                    # Snapshot before SetWindowPos can deliver Configure events.
                    save_geometry_now()
                    state["chrome_restore_rect"] = rect
                clear_native_aspect_constraint()
                previous_programmatic = bool(state.get("programmatic_geometry"))
                state["programmatic_geometry"] = True
                state["chrome_maximized"] = not maximized
                if not windows_set_window_rect(hwnd, target):
                    state["chrome_maximized"] = maximized
                    state["programmatic_geometry"] = previous_programmatic
                    if not maximized: state.pop("chrome_restore_rect", None)
                    return
                with self._lock:
                    self._native_rect_transient = not maximized
                if maximized:
                    state.pop("chrome_restore_rect", None)
                root.after_idle(lambda: state.__setitem__("programmatic_geometry", False))
                sync_window_controls(bool(state.get("window_active")))

            # Overlay the title only while focused: hiding this control never
            # changes header/artwork geometry or recreates the native window.
            maximize_button = tk.Button(identity_label, text="□", padx=2, pady=0,
                font=("Segoe UI", 14), takefocus=False, cursor="arrow", command=toggle_maximize)
            state["artwork_maximize_button"] = maximize_button
            state["sync_artwork_window_controls"] = sync_window_controls
            install_tooltip(maximize_button, "Maximize / restore artwork window")
            root.bind("<Motion>", update_resize_cursor, add="+")
            root.bind("<Leave>", lambda event: update_resize_cursor(), add="+")

            def begin_drag(event, move=False):
''')
    change('''                if event.widget.winfo_toplevel() is not root: return
                rect = windows_window_rect''', '''                if event.widget.winfo_toplevel() is not root or bool(state.get("chrome_maximized")): return
                rect = windows_window_rect''')
    change('''                border = int(state.get("border_pixels", 5))
                edges = (event.x_root < left + border, event.y_root < top + border,
                         event.x_root >= right - border, event.y_root >= bottom - border)''', '''                edges = resize_edges(event.x_root, event.y_root, rect)''')
    change('''                root.grab_set()
                return "break"

            def drag(event):''', '''                root.grab_set()
                update_resize_cursor(event)
                return "break"

            def drag(event):''')
    change('''                    with contextlib.suppress(Exception): root.grab_release()
                    return "break"''', '''                    with contextlib.suppress(Exception): root.grab_release()
                    update_resize_cursor(_event)
                    return "break"''')
    change('''            if not ctrl_is_down() or not bool(state.get("aspect_constraint_supported", True)):''', '''            if bool(state.get("chrome_maximized")) or not ctrl_is_down() or not bool(state.get("aspect_constraint_supported", True)):''')
    change('''            state["save_after"] = None
            geometry = current_geometry()
''', '''            state["save_after"] = None
            restore_rect = state.get("chrome_restore_rect") if bool(state.get("chrome_maximized")) else None
            geometry = current_geometry()
            if restore_rect is not None:
                left, top, right, bottom = restore_rect
                geometry = f"{right-left}x{bottom-top}{left:+d}{top:+d}"
''')
    change('''                outer_rect = windows_window_rect(hwnd)
                if outer_rect is not None and not bool(state.get("idle_promoted")):''', '''                outer_rect = restore_rect if restore_rect is not None else windows_window_rect(hwnd)
                if outer_rect is not None and not bool(state.get("idle_promoted")):''')
    change('''            if state.get("art_fit_key") == art_key:
''', '''            if bool(state.get("chrome_maximized")):
                return False
            if state.get("art_fit_key") == art_key:
''')
    change('''            state["last_configure_size"] = current_size
''', '''            state["last_configure_size"] = current_size
            if bool(state.get("chrome_maximized")):
                # A maximized rectangle is temporary; keep the normal saved
                # placement and avoid Ctrl-square snapping on this resize.
                refresh_monitor_scaled_chrome()
                schedule_render()
                return
''')
    change('''            if get_monitor(sys.modules[__name__]).block_gallery():
''', '''            if bool(state.get("chrome_maximized")) or get_monitor(sys.modules[__name__]).block_gallery():
''')
    # Keep work-area maximization correct after a taskbar/monitor layout change.
    change('''            if previous is not None and signature != previous:
                placement = load_external_album_art_placement()''', '''            if previous is not None and signature != previous and bool(state.get("chrome_maximized")):
                hwnd = int(state.get("native_hwnd", 0) or 0)
                rect = windows_window_rect(hwnd)
                monitor = external_album_art_idle_monitor_for_rect(rect, list(signature)) if rect else None
                if monitor is not None:
                    windows_set_window_rect(hwnd, tuple(monitor[:4]))
            elif previous is not None and signature != previous:
                placement = load_external_album_art_placement()''')
    compile(source, str(path), 'exec')
    write('PAFPlayer.py', source)


if __name__ == '__main__':
    main()
