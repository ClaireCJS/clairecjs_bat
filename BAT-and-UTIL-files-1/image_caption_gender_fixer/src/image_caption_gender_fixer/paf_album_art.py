r"""ICGF-owned COPY/ADAPTATION of PAFPlayer's external album-art renderer.

Original: C:\BAT\PAFPlayer\PAFPlayer.py, PROGRAM_VERSION V567.
Copied 2026-10-27. Source SHA-256: 9ddb9ba5f0dce14303d6c209cb03ba0c5e1b8aed796e71852b4e9c98baf644a1
The named routines below are copied from ExternalAlbumArtWindow._gui_main and
its geometry helpers. Original function names and line ranges are retained.
Adaptations: EXIF orientation for standalone images; explicit 64-bit Win32 API
signatures; a project-specific static image gallery, captions, and review controls.
No music playback, registry/settings changes, global PAFPlayer imports, Chafa,
network access, or detached renderer process is involved. ICGF's explicit viewer
action uses Windows file associations; artwork_shell owns its taskbar/tray UI.
Keep this attribution when editing this ICGF-owned copy.
"""
from __future__ import annotations
import io
import os
import re
from pathlib import Path

from .errors import DependencyUnavailable,IntegrityError

EXTERNAL_ALBUM_ART_DEFAULT_SIZE = 520
EXTERNAL_ALBUM_ART_MIN_SIZE = 160

# COPIED FROM PAFPlayer: external_album_art_monitor_work_areas, original lines 36239-36281.
def external_album_art_monitor_work_areas() -> list[tuple[int, int, int, int, bool, str]]:
    """Return current work areas as (left, top, right, bottom, primary, device)."""
    if os.name != "nt":
        return []
    try:
        import ctypes
        from ctypes import wintypes

        class MONITORINFOEXW(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
                ("szDevice", wintypes.WCHAR * 32),
            ]

        callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL,
            wintypes.HANDLE,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        )
        user32 = ctypes.windll.user32
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFOEXW)]
        user32.GetMonitorInfoW.restype = wintypes.BOOL
        user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.c_void_p, callback_type, wintypes.LPARAM]
        user32.EnumDisplayMonitors.restype = wintypes.BOOL
        monitors: list[tuple[int, int, int, int, bool, str]] = []

        @callback_type
        def callback(hmonitor, _hdc, _rect, _data):
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(info)
            if user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                work = info.rcWork
                monitors.append((
                    int(work.left), int(work.top), int(work.right), int(work.bottom),
                    bool(info.dwFlags & 1), str(info.szDevice),
                ))
            return True

        user32.EnumDisplayMonitors(0, 0, callback, 0)
        return monitors
    except (AttributeError, OSError, ValueError, TypeError):
        return []

# COPIED FROM PAFPlayer: _parse_external_album_art_geometry, original lines 36284-36291.
def _parse_external_album_art_geometry(
    geometry: str | None,
) -> tuple[int, int, int, int] | None:
    match = re.fullmatch(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", str(geometry or "").strip())
    if not match:
        return None
    width, height, x, y = (int(value) for value in match.groups())
    return width, height, x, y

# COPIED FROM PAFPlayer: clamp_external_album_art_geometry, original lines 36294-36360.
def clamp_external_album_art_geometry(
    geometry: str | None,
    monitors: list[tuple[int, int, int, int, bool, str]],
) -> str:
    """Clamp saved geometry wholly into a work area that exists right now."""
    margin = 8
    parsed = _parse_external_album_art_geometry(geometry)
    valid = [m for m in monitors if m[2] > m[0] and m[3] > m[1]]

    if not valid:
        if parsed is not None:
            width, height, x, y = parsed
            return (
                f"{max(EXTERNAL_ALBUM_ART_MIN_SIZE, width)}x"
                f"{max(EXTERNAL_ALBUM_ART_MIN_SIZE, height)}{x:+d}{y:+d}"
            )
        size = EXTERNAL_ALBUM_ART_DEFAULT_SIZE
        return f"{size}x{size}+40+40"

    if parsed is None:
        target = next((m for m in valid if m[4]), valid[0])
        left, top, right, bottom, _primary, _device = target
        usable_w = max(1, right - left - 2 * margin)
        usable_h = max(1, bottom - top - 2 * margin)
        size = min(EXTERNAL_ALBUM_ART_DEFAULT_SIZE, usable_w, usable_h)
        x = right - margin - size
        y = top + margin
        return f"{size}x{size}{x:+d}{y:+d}"

    width, height, x, y = parsed
    # If the saved rectangle already fits a current monitor, restore it byte-for-byte.
    # In particular, a valid negative X/Y on a secondary monitor is not "repaired"
    # onto the primary display or nudged by an arbitrary margin.
    for left, top, right, bottom, _primary, _device in valid:
        if width > 0 and height > 0 and x >= left and y >= top and x + width <= right and y + height <= bottom:
            return f"{width}x{height}{x:+d}{y:+d}"
    old_right, old_bottom = x + width, y + height

    def overlap(m) -> int:
        left, top, right, bottom, _primary, _device = m
        return (
            max(0, min(old_right, right) - max(x, left))
            * max(0, min(old_bottom, bottom) - max(y, top))
        )

    target = max(valid, key=overlap)
    if overlap(target) == 0:
        cx, cy = x + width / 2.0, y + height / 2.0

        def distance(m) -> float:
            left, top, right, bottom, _primary, _device = m
            nx = min(max(cx, left), right)
            ny = min(max(cy, top), bottom)
            return (cx - nx) ** 2 + (cy - ny) ** 2

        target = min(valid, key=distance)

    left, top, right, bottom, _primary, _device = target
    usable_w = max(1, right - left - 2 * margin)
    usable_h = max(1, bottom - top - 2 * margin)
    min_w = min(EXTERNAL_ALBUM_ART_MIN_SIZE, usable_w)
    min_h = min(EXTERNAL_ALBUM_ART_MIN_SIZE, usable_h)
    width = min(max(min_w, width), usable_w)
    height = min(max(min_h, height), usable_h)
    x = min(max(x, left + margin), right - margin - width)
    y = min(max(y, top + margin), bottom - margin - height)
    return f"{width}x{height}{x:+d}{y:+d}"

# COPIED FROM PAFPlayer: _pillow_fit_canvas_image, original lines 45443-45463.
def _pillow_fit_canvas_image(data: bytes, width: int, height: int):
    """Decode and contain one artwork blob in an exact transparent RGBA frame.

    Crossfading sources of different shapes still requires identical frame
    dimensions, but unused aspect-ratio gutters are alpha=0 so the popup's
    chroma-key background shows the desktop rather than black letterboxing.
    """
    from PIL import Image, ImageOps  # type: ignore
    with Image.open(io.BytesIO(bytes(data))) as opened:
        source = ImageOps.exif_transpose(opened).convert("RGBA").copy()
    fitted = ImageOps.contain(
        source,
        (max(1, width), max(1, height)),
        method=Image.Resampling.LANCZOS,
    )
    canvas_image = Image.new("RGBA", (max(1, width), max(1, height)), (0, 0, 0, 0))
    canvas_image.alpha_composite(
        fitted,
        ((canvas_image.width - fitted.width) // 2, (canvas_image.height - fitted.height) // 2),
    )
    return canvas_image, source

# COPIED FROM PAFPlayer: reuse_or_create_photoimage, original lines 43264-43285.
def reuse_or_create_photoimage(existing, rgba, master):
    """Update a stable Tk photo in place when dimensions are unchanged.

    Creating a new ImageTk.PhotoImage for every animation tick becomes
    disproportionately expensive as lyric font/mask size grows.  Pillow's
    PhotoImage.paste keeps the same Tcl/Tk image object and changes only
    its pixels, preserving byte-identical artwork while avoiding repeated
    large Tk allocations and garbage collection.
    """
    try:
        if (
            existing is not None
            and int(existing.width()) == int(rgba.size[0])
            and int(existing.height()) == int(rgba.size[1])
            and hasattr(existing, "paste")
        ):
            existing.paste(rgba)
            return existing
    except Exception:
        pass
    from PIL import ImageTk  # type: ignore
    return ImageTk.PhotoImage(rgba, master=master)


# ICGF-specific controller around the copied PAFPlayer image/geometry routines.
def availability(root=None):
    """Import-only probe: no window, Tcl interpreter, files, or downloads."""
    result={"renderer":"pafplayer-dual-preview","module":str(Path(__file__)),"available":False}
    try:
        import tkinter
        from PIL import ImageTk
        result.update(available=True,tk_version=tkinter.TkVersion)
        from .paf_backend import status
        result['artwork_backend']=status(root)
    except (ImportError,OSError) as error:
        result["error"]="Python's Tcl/Tk image component is unavailable: "+type(error).__name__
    return result


class _ArtworkActivation:
    """Veto native activation only while this artwork thread updates its UI.

    Thread-scoped WH_CBT / HCBT_ACTIVATE, never a desktop/global hook.
    https://learn.microsoft.com/en-us/windows/win32/winmsg/cbtproc
    User activation between updates, including Alt+Tab, remains ordinary.
    """
    def __init__(self,enabled):
        self.depth=0;self.blocked=0;self.mouse_activations=0;self.handle=None;self.callback=None
        if not enabled or os.name!='nt':return
        import ctypes
        from ctypes import wintypes
        self.ctypes=ctypes;self.api=ctypes.WinDLL('user32',use_last_error=True)
        hook_type=ctypes.WINFUNCTYPE(ctypes.c_ssize_t,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM)
        class Activation(ctypes.Structure):
            _fields_=[('mouse',wintypes.BOOL),('active',wintypes.HWND)]
        self.api.CallNextHookEx.argtypes=[wintypes.HANDLE,ctypes.c_int,wintypes.WPARAM,wintypes.LPARAM]
        self.api.CallNextHookEx.restype=ctypes.c_ssize_t
        self.api.SetWindowsHookExW.argtypes=[ctypes.c_int,hook_type,wintypes.HINSTANCE,wintypes.DWORD]
        self.api.SetWindowsHookExW.restype=wintypes.HANDLE
        self.api.UnhookWindowsHookEx.argtypes=[wintypes.HANDLE];self.api.UnhookWindowsHookEx.restype=wintypes.BOOL
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentThreadId.argtypes=[];kernel.GetCurrentThreadId.restype=wintypes.DWORD
        def hook(code,target,data):
            if code==5:
                # Physical mouse activation is user input. Programmatic Tk
                # activation is refused before Windows changes focus.
                mouse=bool(data and ctypes.cast(data,ctypes.POINTER(Activation)).contents.mouse)
                if mouse:self.mouse_activations+=1
                elif self.depth:self.blocked+=1;return 1
            return self.api.CallNextHookEx(None,code,target,data)
        self.callback=hook_type(hook)
        self.handle=self.api.SetWindowsHookExW(5,self.callback,None,kernel.GetCurrentThreadId())
        if not self.handle:
            self.callback=None
            raise DependencyUnavailable('Windows could not protect artwork updates from activation; use --no-preview.')
        _active_artwork_guards.add(self)

    def __enter__(self):self.depth+=1;return self
    def __exit__(self,*error):self.depth-=1

    def close(self):
        if self.handle:
            if not self.api.UnhookWindowsHookEx(self.handle):
                # Keep the callback alive until this owner thread exits.
                _active_artwork_guards.add(self)
                raise DependencyUnavailable('Artwork activation guard could not be released.')
            self.handle=None;self.callback=None
            _active_artwork_guards.discard(self)


_active_artwork_guards=set()


def _passive_artwork_update(method):
    from functools import wraps
    @wraps(method)
    def protected(self,*args,**kwargs):
        with self._activation:
            self.keep_passive()
            result=method(self,*args,**kwargs)
            # Finish deferred Tk wrapper/layout work before lifting the veto.
            # Nested callbacks share the outer guard rather than flushing again.
            if self._activation.depth==1 and self.root is not None:self.root.update_idletasks()
            self.keep_passive()
            shell=getattr(self,'window_shell',None)
            if shell is not None:shell.refresh()
            return result
    return protected


class AlbumArtReview:
    """PAFPlayer image pipeline with ICGF review controls, owned by one Tk thread."""
    def __init__(self,views,captions=None,*,blocked=False,warnings=(),inspect_only=False,backend=None,floating=False,shell_group=None):
        import tkinter as tk
        from tkinter import ttk
        self.tk=tk;self.views=list(views);self.captions=captions or {}
        from .paf_backend import get_backend
        self.backend=backend or get_backend();self.floating=bool(floating)
        self.blocked=bool(blocked);self.inspect_only=inspect_only
        self.result=None;self._photo=None;self._draw_after=None;self._data={};self._has_drawn=False
        self._callback_error=None;self._poll_after=None;self._review_callback=None;self._review_rules=[]
        self._editing=False;self._portrait=None;self._layout_key=None;self._layout_plan=None;self._dialog=None;self._notes=[]
        self._review_changes=[];self._review_source=None;self._pulse_after=None;self._pulse_highlight=False
        self._activation=_ArtworkActivation(self.floating)
        self._activation.__enter__()
        self.root=None;self.window_shell=None
        try:
            if self.floating and os.name=='nt':
                from .artwork_shell import prepare_instance
                prepare_instance()
            self.root=tk.Tk();self.root.withdraw()
            self.root.title('ICGF — '+Path(self.views[0]['path']).name)
            self.root.protocol('WM_DELETE_WINDOW',self.hide if floating else lambda:self.choose('continue' if inspect_only else 'c'))
            self.root.report_callback_exception=self.callback_exception
            self.root.bind('<Escape>',lambda event:self.hide() if floating else self.choose('continue' if inspect_only else 'c'))
            self.root.bind('<ButtonPress>',self.activate_on_click,add='+')
            self.root.columnconfigure(0,weight=1);self.root.rowconfigure(1,weight=1)
            work=self.backend.monitors() or [(0,0,self.root.winfo_screenwidth(),self.root.winfo_screenheight(),True,'')]
            left,top,right,bottom,*_=next((m for m in work if m[4]),work[0])
            width=max(400,right-left-32);height=max(400,bottom-top-64)
            self.root.geometry(self.backend.clamp(f'{width}x{height}{left+16:+d}{top+16:+d}',work))
            self.root.minsize(min(680,width),min(420,height))
            toolbar=ttk.Frame(self.root,padding=4);self.toolbar=toolbar;toolbar.grid(row=0,column=0,sticky='ew');toolbar.columnconfigure(1,weight=1)
            ttk.Label(toolbar,text='Image:').grid(row=0,column=0,padx=(0,6))
            self.selection=tk.StringVar()
            labels=[f"{i+1}. {v['title']}" for i,v in enumerate(self.views)]
            self.selector=ttk.Combobox(toolbar,state='readonly',values=labels,textvariable=self.selection)
            self.selector.grid(row=0,column=1,sticky='ew');self.selector.current(len(labels)-1)
            self.selector.bind('<<ComboboxSelected>>',self.schedule_draw)
            ttk.Button(toolbar,text='Previous',command=lambda:self.navigate(-1)).grid(row=0,column=2)
            ttk.Button(toolbar,text='Next',command=lambda:self.navigate(1)).grid(row=0,column=3)
            self.body=ttk.Frame(self.root);self.body.grid(row=1,column=0,sticky='nsew',padx=4)
            self.body.rowconfigure(0,weight=1)
            self.root.bind('<Configure>',lambda event:self.schedule_draw() if event.widget is self.root else None,add='+')
            self.canvas=tk.Canvas(self.body,bg='#303030',highlightthickness=0)
            self.canvas.bind('<Configure>',self.schedule_draw)
            from .artwork_clicks import ArtworkClicks
            self.artwork_clicks=ArtworkClicks(self)
            self.caption_frames=[];texts=[]
            for label,fg in [('📖 Detected caption','#8bff9a'),('✨ Proposed caption — edit, then Regenerate','#ffff58')]:
                frame=ttk.LabelFrame(self.body,padding=4);frame.columnconfigure(0,weight=1);frame.rowconfigure(0,weight=1)
                heading=ttk.Label(frame,text=label,wraplength=250);frame.configure(labelwidget=heading)
                frame.heading=heading;frame.grid_propagate(False)
                text=tk.Text(frame,height=9,width=1,wrap='word',font=('Segoe UI',12),bg='#171b22',fg=fg,insertbackground=fg,undo=True)
                scroll=ttk.Scrollbar(frame,orient='vertical',command=text.yview);text.configure(yscrollcommand=scroll.set)
                text.grid(row=0,column=0,sticky='nsew');scroll.grid(row=0,column=1,sticky='ns')
                self.caption_frames.append(frame);texts.append(text)
            self.caption,self.proposed_caption=texts
            self.proposed_caption.bind('<<Modified>>',self.caption_modified)
            self.buttons={}
            controls=ttk.Frame(self.root,padding=4);self.controls=controls
            self.control_banks=[ttk.Frame(self.root,padding=2),ttk.Frame(self.root,padding=2)]
            controls.columnconfigure(0,weight=1);controls.columnconfigure(1,weight=1)
            actions=([('✅ [A] Approve','a'),('[R] Reject changes','r'),('[S] Skip image','s'),('[D] Defer','d'),
                ('➕ [N] New substitution','add_rule'),('✏ [G] Regenerate edits','edit_caption'),('↔ [M] Move/squeeze','m'),('[O] Correct OCR','o'),('[V] Adjust text/image','v'),('[B] Background repairs','b'),
                ('🚫 [I] Ignore substitution…','ignore'),('[C] Cancel job','c'),('[H] Help','help'),('📝 [F2] Rename image…','rename_image'),('🗑 [Del] Delete / Recycle…','recycle_image'),('[Esc] Hide window','hide')] if floating else
                [('Continue','continue')] if inspect_only else [('Approve','a'),('Skip','s'),('Cancel job','c')])
            split=(len(actions)+1)//2
            for index,(label,action) in enumerate(actions):
                bank=self.control_banks[int(index>=split)]
                button=ttk.Button(bank,text=label,command=lambda action=action:self.review_button(action))
                self.buttons[action]=button
            self._hotkeys={'a':'a','r':'r','s':'s','d':'d','n':'add_rule','g':'edit_caption','m':'m','o':'o','v':'v','b':'b','i':'ignore','c':'c','h':'help'}
            self.root.bind('<KeyPress>',self.button_hotkey,add='+')
            from .popup_controls import ControlPanel
            self.control_panel=ControlPanel(self,controls)
            self.notice=tk.Label(self.root,text='',anchor='w',justify='left',bg='#171b22',fg='#ffff58',padx=8,pady=4)
            self.notice.grid(row=3,column=0,sticky='ew')
            if self.floating and os.name=='nt':
                from .artwork_shell import ArtworkShell,GROUP
                self.window_shell=ArtworkShell(self,shell_group or GROUP)
                self.root.bind('<Control-Alt-KeyPress-a>',lambda event:(self.show_all_artwork(),'break')[1])
                self.root.bind('<Control-Alt-KeyPress-A>',lambda event:(self.show_all_artwork(),'break')[1])
            self._set_captions();self.set_review(None,[],blocked,list(warnings))
            self.root.update_idletasks();self.schedule_draw();self.poll_interrupts()
        except BaseException:
            try:
                if self.window_shell is not None:self.window_shell.close();self.window_shell=None
                if self.root is not None:self.root.destroy()
            finally:self._activation.close()
            raise
        finally:self._activation.__exit__()

    @_passive_artwork_update
    def _set_captions(self):
        self._editing=True
        for widget,key in [(self.caption,'detected'),(self.proposed_caption,'proposed')]:
            widget.configure(state='normal');widget.delete('1.0','end');widget.insert('1.0',self.captions.get(key,'(No text supplied)'))
            widget.edit_modified(False)
        self.caption.configure(state='disabled');self.proposed_caption.configure(state='disabled')
        self._editing=False;self._dirty=False
        self.mark_caption_changes()

    def caption_modified(self,event=None):
        if self._editing or not self.proposed_caption.edit_modified():return
        self._dirty=True;self.proposed_caption.edit_modified(False)
        self.mark_caption_changes()
        self.notice.configure(text='✏️ Caption edited — click Regenerate from edits before approving.')
        for key in ('a','p','m','ignore','o','v','b','add_rule','rename_image'):
            if key in self.buttons:self.buttons[key].configure(state='disabled')

    @_passive_artwork_update
    def set_review(self,callback,rules,blocked=False,notes=None,changes=None,source=None):
        self._review_callback=callback;self._review_rules=rules;self.blocked=bool(blocked)
        if notes is not None:self._notes=notes
        if changes is not None:self._review_changes=list(changes);self._review_source=source
        if self._review_source:self.root.title('ICGF — '+Path(self._review_source).name)
        if source is not None:self.artwork_clicks.comparison(source,self.blocked)
        if not self._dirty:self.notice.configure(text='  |  '.join('⚠️ '+n for n in self._notes) or ('Edit the yellow caption, then Regenerate; Approve applies the rendered proposal.' if callback else 'Preparing preview…'),wraplength=self.notice.cget('wraplength') or max(160,self.root.winfo_width()-24))
        active=bool(callback) if self.floating else not self.inspect_only
        self.proposed_caption.configure(state='normal' if active else 'disabled')
        for key,button in self.buttons.items():
            if key in ('hide','continue','help'):continue
            enabled=active and (key not in ('a','p') or (not self.blocked and self._has_drawn and not self._dirty))
            if key in ('m','ignore'):enabled=active and bool(self._review_changes) and not self._dirty
            if key in ('rename_image','recycle_image'):enabled=active and bool(self._review_source)
            if key in ('o','v','b','add_rule','rename_image') and self._dirty:enabled=False
            button.configure(state='normal' if enabled else 'disabled')

    def _native_window(self):
        import ctypes
        from ctypes import wintypes
        api=ctypes.windll.user32
        api.GetAncestor.argtypes=[wintypes.HWND,wintypes.UINT];api.GetAncestor.restype=wintypes.HWND
        hwnd=api.GetAncestor(self.root.winfo_id(),2)
        getter=api.GetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p)==8 else api.GetWindowLongW
        setter=api.SetWindowLongPtrW if ctypes.sizeof(ctypes.c_void_p)==8 else api.SetWindowLongW
        getter.argtypes=[wintypes.HWND,ctypes.c_int];getter.restype=ctypes.c_ssize_t
        setter.argtypes=[wintypes.HWND,ctypes.c_int,ctypes.c_ssize_t];setter.restype=ctypes.c_ssize_t
        return api,hwnd,getter,setter

    def keep_passive(self):
        if self.floating and os.name=='nt' and self.root is not None:
            api,hwnd,getter,setter=self._native_window()
            setter(hwnd,-20,getter(hwnd,-20)|0x08000000)

    def activate_on_click(self,event=None):
        # Automatic updates never activate; a deliberate click permits editing.
        if self.floating and os.name=='nt':
            api,hwnd,getter,setter=self._native_window();setter(hwnd,-20,getter(hwnd,-20)&~0x08000000)
            from ctypes import wintypes
            api.SetForegroundWindow.argtypes=[wintypes.HWND];api.SetForegroundWindow.restype=wintypes.BOOL
            api.SetForegroundWindow(hwnd)
            if event is not None and event.widget.winfo_class() in ('Text','TEntry','TCombobox','Canvas'):event.widget.focus_set()

    @_passive_artwork_update
    def passive_show(self,force=False):
        if self.root.state()!='withdrawn' and not (force and self.root.state()=='iconic'):return
        if self.floating and os.name=='nt':
            import ctypes
            from ctypes import wintypes
            self.root.update_idletasks();api,hwnd,getter,setter=self._native_window()
            setter(hwnd,-20,getter(hwnd,-20)|0x08000000)
            # Tk's deiconify explicitly calls SetForegroundWindow even when
            # NOACTIVATE is set. Show both its client and wrapper directly;
            # WM_SHOWWINDOW synchronizes Tk's normal/withdrawn state.
            api.ShowWindow.argtypes=[wintypes.HWND,ctypes.c_int];api.ShowWindow.restype=wintypes.BOOL
            api.ShowWindow(self.root.winfo_id(),4)
            api.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
            api.SetWindowPos.restype=wintypes.BOOL
            api.ShowWindow(hwnd,4) # SW_SHOWNOACTIVATE; restore without activation
            api.SetWindowPos(hwnd,0,0,0,0,0,0x0010|0x0001|0x0002|0x0004)
        else:self.root.deiconify()

    def navigate(self,offset):
        self.selector.current((self.selector.current()+offset)%len(self.views));self.schedule_draw()

    def hide(self):
        self.artwork_clicks.cancel_click();self.artwork_clicks.hide_tooltip();self.root.withdraw()

    @_passive_artwork_update
    def update_image(self,view,captions):
        self.artwork_clicks.reset()
        self.set_review(None,[],False,[],[]);self.views=[view];self.captions=captions or {};self._data.clear();self._portrait=None;self._layout_key=None
        self.selector.configure(values=['1. '+view['title']]);self.selector.current(0)
        self._set_captions();self.root.title('ICGF — '+Path(view['path']).name)
        self.passive_show();self.schedule_draw()

    @_passive_artwork_update
    def schedule_draw(self,event=None):
        self._has_drawn=False
        for action in ('a','p'):
            if action in self.buttons:self.buttons[action].configure(state='disabled')
        if self._draw_after is not None:self.root.after_cancel(self._draw_after)
        self._draw_after=self.root.after(60,self.draw)

    def poll_interrupts(self):
        if self.window_shell is not None:self.window_shell.poll()
        self._poll_after=self.root.after(100,self.poll_interrupts)

    def callback_exception(self,kind,error,traceback):
        self._callback_error=error;self.blocked=True;self.result='c';self.root.quit()

    def button_hotkey(self,event):
        # Text editing, modal dialogs and value fields keep their own keys.
        if event.widget.winfo_toplevel() is not self.root:return
        if event.keysym!='F2' and event.widget.winfo_class() in ('Text','Entry','TEntry','TCombobox','Listbox','Spinbox','TSpinbox'):return
        if event.state&0x000c:return
        panel=self.control_panel
        if panel.callback is not None:
            key=str(event.char).casefold()
            button=panel.buttons.get(key)
        else:button=self.buttons.get({'F2':'rename_image','Delete':'recycle_image'}.get(event.keysym,self._hotkeys.get(str(event.char).casefold())))
        if button is not None and not button.instate(['disabled']):button.invoke();return 'break'

    def place_controls(self):
        plan=self._layout_plan
        side=bool(plan and plan.side);columns=plan.columns if plan else 3
        panel=getattr(self,'control_panel',None)
        dialog=bool(panel and panel.callback is not None)
        self.controls.grid_remove()
        for index,bank in enumerate(self.control_banks):
            bank.grid_remove()
            for col in range(6):bank.columnconfigure(col,weight=0)
            for number,button in enumerate(bank.winfo_children()):
                button.grid(row=number//columns,column=number%columns,sticky='ew',padx=2,pady=2)
            for col in range(columns):bank.columnconfigure(col,weight=1)
            if not dialog:
                if side:bank.grid(in_=self.caption_frames[index],row=1,column=0,columnspan=2,sticky='ew')
                else:bank.grid(in_=self.controls,row=0,column=index,sticky='nsew')
        if not side and not dialog:self.controls.grid(row=2,column=0,sticky='ew')
        self.notice.grid_forget()
        if side:
            self.notice.configure(wraplength=max(160,self.caption_frames[0].winfo_width()-24))
            self.notice.grid(in_=self.caption_frames[0],row=2,column=0,columnspan=2,sticky='ew')
        else:
            self.notice.configure(wraplength=max(160,self.root.winfo_width()-24))
            self.notice.grid(row=3,column=0,sticky='ew')
        if dialog:
            master=self.caption_frames[1] if side else self.root
            panel.relayout(master,1 if side else 2,columns,
                           plan.right if side else self.root.winfo_width())

    def layout(self,image_size):
        from .artwork_layout import choose_layout
        banks=[bank.winfo_children() for bank in self.control_banks]
        widths=[max([b.winfo_reqwidth()+4 for b in buttons] or [100]) for buttons in banks]
        row_height=max(b.winfo_reqheight()+4 for b in self.buttons.values())
        width=max(1,self.root.winfo_width()-8)
        height=max(1,self.root.winfo_height()-self.toolbar.winfo_reqheight())
        counts=[len(b) for b in banks]
        panel=self.control_panel;dialog=bool(panel.callback is not None)
        if dialog:
            widths=[0,max(widths[1],min(300,max([b.winfo_reqwidth()+4 for b in panel.buttons.values()] or [200])))]
            counts=[0,len(panel.buttons)+len(panel.footer)]
            if panel.spec['kind']=='menu':row_height=max(row_height,48)
        plan=choose_layout(width,height,image_size,widths,counts,row_height,dialog=dialog)
        key=(width,height,plan)
        if key==self._layout_key:return
        self._layout_key=key;self._layout_plan=plan;self._portrait=plan.side
        for widget in [self.canvas,*self.caption_frames]:widget.grid_forget()
        for i in range(4):self.body.columnconfigure(i,weight=0,minsize=0)
        self.body.rowconfigure(0,weight=1,minsize=0);self.body.rowconfigure(1,weight=0,minsize=0)
        if plan.side:
            self.body.columnconfigure(0,weight=1,minsize=plan.left)
            self.body.columnconfigure(1,weight=0,minsize=plan.image_width)
            self.body.columnconfigure(2,weight=1,minsize=plan.right)
            self.caption_frames[0].grid(row=0,column=0,sticky='nsew',padx=(0,4))
            self.canvas.grid(row=0,column=1,sticky='nsew')
            self.caption_frames[1].grid(row=0,column=2,sticky='nsew',padx=(4,0))
            for frame,size in zip(self.caption_frames,(plan.left,plan.right)):
                frame.configure(width=size,height=height);frame.heading.configure(wraplength=max(140,size-24))
        else:
            for i,frame in enumerate(self.caption_frames):
                self.body.columnconfigure(i,weight=1)
                frame.configure(width=1,height=plan.caption_height);frame.heading.configure(wraplength=max(140,width//2-24))
                frame.grid(row=1,column=i,sticky='nsew',pady=(4,0))
            self.canvas.grid(row=0,column=0,columnspan=2,sticky='nsew')
        self.place_controls()

    @_passive_artwork_update
    def draw(self):
        self._draw_after=None
        from PIL import Image,ImageDraw
        try:
            path=str(self.views[self.selector.current()]['path'])
            if path not in self._data:
                from .paf_backend import image_bytes
                self._data[path]=image_bytes(path)
            with Image.open(io.BytesIO(self._data[path])) as source:
                oriented=source.size[::-1] if source.getexif().get(274) in (5,6,7,8) else source.size
                self.layout(oriented)
            self.root.update_idletasks()
            width=max(1,self.canvas.winfo_width());height=max(1,self.canvas.winfo_height())
            rgba,_source=self.backend.fit(self._data[path],width,height)
            background=Image.new('RGBA',rgba.size,(224,224,224,255));draw=ImageDraw.Draw(background);tile=16
            for y in range(0,height,tile):
                for x in range((y//tile%2)*tile,width,tile*2):draw.rectangle((x,y,x+tile-1,y+tile-1),fill=(192,192,192,255))
            background.alpha_composite(rgba);self._photo=self.backend.photo(self._photo,background,self.canvas)
            self.canvas.delete('artwork-base');self.canvas.create_image(width//2,height//2,image=self._photo,anchor='center',tags=('artwork-base',));self.canvas.tag_lower('artwork-base')
            self._has_drawn=True;self.set_review(self._review_callback,self._review_rules,self.blocked)
        except (OSError,ValueError) as error:
            self._render_error=str(error);self.blocked=True;self.set_review(None,[],True)
            self.canvas.delete('artwork-base');self.canvas.create_text(12,12,anchor='nw',fill='white',text='Preview unavailable: '+str(error),width=max(100,self.canvas.winfo_width()-24))

    @_passive_artwork_update
    def set_dialog(self,spec,callback):
        self.control_panel.show(spec,callback)

    def reopen(self,activate=False):
        if not activate:self.passive_show(force=True);return
        # Only the explicit Ctrl+Alt+A action is allowed to raise/focus artwork.
        self.passive_show(force=True)
        if self.floating and os.name=='nt':
            from ctypes import wintypes
            api,hwnd,getter,setter=self._native_window()
            setter(hwnd,-20,getter(hwnd,-20)&~0x08000000)
            api.ShowWindow(hwnd,9)
            api.BringWindowToTop.argtypes=[wintypes.HWND];api.BringWindowToTop.restype=wintypes.BOOL
            api.SetForegroundWindow.argtypes=[wintypes.HWND];api.SetForegroundWindow.restype=wintypes.BOOL
            api.BringWindowToTop(hwnd);api.SetForegroundWindow(hwnd)
        else:self.root.deiconify();self.root.lift()

    def show_all_artwork(self):
        self.reopen(True)
        if self.window_shell is not None:
            from .artwork_shell import reveal_all
            reveal_all(self.window_shell.group,exclude_pid=os.getpid())

    def open_default_viewer(self,event=None):
        from tkinter import messagebox
        try:
            path=Path(self.views[self.selector.current()]['path']).absolute()
            if not path.is_file():raise OSError('The displayed preview file is no longer available.')
            os.startfile(str(path),'open')
        except OSError as error:messagebox.showerror('Could not open image',str(error),parent=self.root)
        return 'break'

    def review_button(self,action):
        if action=='help':
            self.notice.configure(text='Approve applies the rendered proposal. Edit the yellow caption and Regenerate before approving edits. '
                'Move/squeeze retries fitting; Correct OCR, Adjust and Background expose the same menus as the console. '
                'Ignore can save an exception; Reject/Skip leaves the image unchanged. Letter keys activate buttons outside text fields. '
                'Single-click artwork to toggle Before/After; triple-click opens the displayed version in your default viewer. Hover for two seconds for click help. Console: Ctrl+A shows artwork; Ctrl+Alt+A shows all ICGF artwork windows.',wraplength=self.notice.cget('wraplength') or max(160,self.root.winfo_width()-24));return
        if self.floating and action=='c':self.emit('c');return
        self.choose('s' if action=='r' else action)

    def mark_caption_changes(self):
        from difflib import SequenceMatcher
        before=self.caption.get('1.0','end-1c');after=self.proposed_caption.get('1.0','end-1c')
        for widget in (self.caption,self.proposed_caption):widget.tag_remove('changed','1.0','end')
        for op,a,b,c,d in SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
            if op=='equal':continue
            if a<b:self.caption.tag_add('changed',f'1.0+{a}c',f'1.0+{b}c')
            if c<d:self.proposed_caption.tag_add('changed',f'1.0+{c}c',f'1.0+{d}c')
        if self._pulse_after is None:self.pulse_caption_changes()

    @_passive_artwork_update
    def pulse_caption_changes(self):
        # Both phases keep the words visible and keep their green/yellow color.
        self._pulse_highlight=not self._pulse_highlight
        for widget,tint in ((self.caption,'#29452f'),(self.proposed_caption,'#484219')):
            widget.tag_configure('changed',background=tint if self._pulse_highlight else '#171b22')
        self._pulse_after=self.root.after(650,self.pulse_caption_changes)

    def source_file_action(self,action):
        from tkinter import simpledialog,messagebox
        if not self._review_source:return
        source=self._review_source;name=Path(source).name
        if action=='rename_image':
            value=simpledialog.askstring('Rename source image','New filename (keep the image extension):',
                                         initialvalue=name,parent=self.root)
            if value is None:return
            from .file_actions import rename_target
            try:rename_target(Path(source),value)
            except IntegrityError as error:
                messagebox.showerror('Filename was not changed',str(error),parent=self.root);return
            self.emit({'action':'rename_image','source':source,'name':value})
        elif messagebox.askyesno('Recycle source image?',
                'Move this SOURCE image to the Windows Recycle Bin?\n\n'+source+
                '\n\nThe pending correction will be discarded. There is no permanent-delete fallback.',
                parent=self.root,default='no',icon='warning'):
            self.emit({'action':'recycle_image','source':source,'confirmed':True})

    def ignore_substitution(self):
        from tkinter import ttk
        if not self._review_changes:return
        dialog=self.tk.Toplevel(self.root);self._dialog=dialog
        dialog.title('Ignore substitution');dialog.transient(self.root)
        ttk.Label(dialog,text='Ignore a substitution; Skip only skips this image.').grid(row=0,column=0,columnspan=2,padx=12,pady=8)
        choices=ttk.Combobox(dialog,state='readonly',width=60,values=[r['before']+' ➜ '+r['after'] for r in self._review_changes])
        choices.grid(row=1,column=0,columnspan=2,padx=12,pady=8);choices.current(0)
        scope=self.tk.StringVar(master=dialog,value='folder')
        for row,(label,value) in enumerate([('Remember phrase exception in this folder','folder'),('Ignore this substitution once','once'),('Ignore this image for this run','image_run'),('Ignore this image for all future runs','image'),('Ignore this phrase for this job','session'),('Remember a global phrase exception','global')],2):
            ttk.Radiobutton(dialog,text=label,value=value,variable=scope).grid(row=row,column=0,columnspan=2,sticky='w',padx=12)
        def cancel_ignore(event=None):
            if dialog.winfo_exists():dialog.destroy()
            self._dialog=None
            return 'break'
        def save_ignore(event=None):
            if not dialog.winfo_exists():return 'break'
            change=self._review_changes[choices.current()]
            payload={'action':'ignore','index':change['index'],'scope':scope.get()}
            cancel_ignore();self.emit(payload)
            return 'break'
        ttk.Button(dialog,text='🚫 Ignore [Enter]',command=save_ignore).grid(row=8,column=0,padx=12,pady=12)
        ttk.Button(dialog,text='Cancel [Esc]',command=cancel_ignore).grid(row=8,column=1,padx=12,pady=12)
        dialog.protocol('WM_DELETE_WINDOW',cancel_ignore)
        # Widget bindings run before ttk class bindings. ENTER must confirm
        # Ignore even when the Cancel button or a scope radio has focus.
        for widget in (dialog,*dialog.winfo_children()):
            widget.bind('<Return>',save_ignore)
            widget.bind('<KP_Enter>',save_ignore)
            widget.bind('<Escape>',cancel_ignore)
        dialog.grab_set();choices.focus_set()

    def add_substitution(self):
        from tkinter import ttk,messagebox
        from .rules import Rule
        from .rule_editor import ordered,move_rule,validate_payload
        dialog=self.tk.Toplevel(self.root);self._dialog=dialog;dialog.title('Add substitution and set priority');dialog.transient(self.root)
        entries={}
        for i,(key,label,value) in enumerate([('before','Source phrase',''),('after','Replacement phrase',''),('priority','Priority','10')]):
            ttk.Label(dialog,text=label).grid(row=i,column=0,sticky='w',padx=8,pady=4)
            entry=ttk.Entry(dialog,width=52);entry.insert(0,value);entry.grid(row=i,column=1,columnspan=3,sticky='ew',padx=8,pady=4);entries[key]=entry
        ttk.Label(dialog,text='Higher in this list = higher priority. Preview, then use ↑/↓ or PgUp/PgDn.').grid(row=3,column=0,columnspan=4,padx=8)
        listing=self.tk.Listbox(dialog,width=78,height=13,font=('Segoe UI',11),exportselection=False);listing.grid(row=4,column=0,columnspan=4,sticky='nsew',padx=8,pady=6)
        state={'rules':[],'payload':None,'moved':False,'fields':None}
        def refresh():
            listing.delete(0,'end')
            for r in state['rules']:listing.insert('end',f'{r.priority}: "{r.before}" ➜ "{r.after}"')
        def preview():
            state['payload']=None
            try:
                payload={k:e.get() for k,e in entries.items()};payload['priority']=int(payload['priority'])
                rules=[Rule(**r) for r in self._review_rules]
                result,rule=validate_payload(payload,rules,'default')
                for r in result:
                    if r.id==rule.id:r.id='new'
                state.update(rules=result,payload=payload,moved=False,fields=[e.get() for e in entries.values()]);refresh()
                listing.selection_set(next(i for i,r in enumerate(result) if r.id=='new'))
            except (ValueError,KeyError,IntegrityError) as error:messagebox.showerror('Invalid substitution',str(error),parent=dialog)
        def move(offset):
            if not state['rules']:preview()
            selected=listing.curselection()
            if not selected:return
            try:state['rules'],index=move_rule(state['rules'],selected[0],offset)
            except IntegrityError as error:messagebox.showerror('Rule order',str(error),parent=dialog);return
            state['moved']=True;refresh();listing.selection_set(index);listing.see(index)
        def save_rule():
            if state['fields']!=[e.get() for e in entries.values()]:preview()
            if not state['payload']:return
            payload=dict(state['payload'])
            if state['moved']:payload['order']=[r.id for r in state['rules']]
            dialog.destroy();self._dialog=None;self.emit({'action':'add_rule','payload':payload})
        from .errors import IntegrityError
        for key,offset in [('<Up>',-1),('<Down>',1),('<Prior>',-5),('<Next>',5)]:listing.bind(key,lambda event,offset=offset:(move(offset),'break')[1])
        for i,(label,command) in enumerate([('Preview rule list',preview),('↑ Raise',lambda:move(-1)),('↓ Lower',lambda:move(1)),('Save and regenerate',save_rule)]):ttk.Button(dialog,text=label,command=command).grid(row=5,column=i,padx=5,pady=8)
        dialog.columnconfigure(1,weight=1);dialog.rowconfigure(4,weight=1);entries['before'].focus_set()

    def emit(self,action):
        callback=self._review_callback
        if not callback:return
        self.set_review(None,[],self.blocked);callback(action)

    def choose(self,action):
        if action=='hide':self.hide();return
        if (self.blocked or not self._has_drawn or self._dirty) and action in ('a','p'):return
        if self.floating and action!='c':
            if not self._review_callback:return
            if action=='add_rule':self.add_substitution();return
            if action=='ignore':self.ignore_substitution();return
            if action in ('rename_image','recycle_image'):self.source_file_action(action);return
            if action=='m':self.emit({'action':'fit_all'});return
            if action=='edit_caption':self.emit({'action':'edit_caption','text':self.proposed_caption.get('1.0','end-1c')});return
            self.emit(action);return
        self.result=action;self.root.quit()

    def show(self):
        try:
            self.passive_show();self.root.mainloop()
            if self._callback_error is not None:raise self._callback_error
            return self.result or ('continue' if self.inspect_only else 'c')
        finally:
            try:
                if self._draw_after is not None:self.root.after_cancel(self._draw_after)
                if self._poll_after is not None:self.root.after_cancel(self._poll_after)
                if self._pulse_after is not None:self.root.after_cancel(self._pulse_after)
                self.artwork_clicks.close();self.artwork_clicks=None
                self.control_panel.clear()
                if self.window_shell is not None:self.window_shell.close();self.window_shell=None
                self._photo=None;self.root.destroy();self.selection=None;self.buttons.clear()
                self._dialog=None;self.caption_frames.clear();self._review_callback=None
                self.control_panel=None
                self.selector=self.canvas=self.caption=self.proposed_caption=self.body=self.notice=self.toolbar=self.controls=None
                self.control_banks.clear()
                self.root.report_callback_exception=None;self.root=None
            finally:self._activation.close()


def show_images(views,captions=None,**options):
    try:return AlbumArtReview(views,captions,**options).show()
    except Exception as error:
        raise DependencyUnavailable('PAFPlayer-style preview could not open/render. Use --no-preview for console-only review. '+type(error).__name__) from error
