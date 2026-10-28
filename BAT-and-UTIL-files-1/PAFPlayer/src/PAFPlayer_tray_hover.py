"""Native Win32 tray hover card; shares the tray thread's message pump."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import struct
import time
from functools import lru_cache


class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [('hdc', wintypes.HDC), ('fErase', wintypes.BOOL), ('rcPaint', wintypes.RECT),
                ('fRestore', wintypes.BOOL), ('fIncUpdate', wintypes.BOOL), ('rgbReserved', ctypes.c_byte * 32)]


@lru_cache(maxsize=1)
def _native():
    """Private ctypes wrappers: other features cannot change our prototypes.

    In particular wallpaper's text pvParam and SPI_GETWORKAREA's RECT pvParam
    must not compete on ctypes.windll.user32.SystemParametersInfoW.
    """
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
    shell32 = ctypes.WinDLL('shell32', use_last_error=True)
    def bind(dll, name, result, *args):
        function = getattr(dll, name)
        function.argtypes, function.restype = list(args), result
    ptr, integer = ctypes.c_void_p, ctypes.c_int
    bind(kernel32, 'GetModuleHandleW', wintypes.HMODULE, wintypes.LPCWSTR)
    bind(user32, 'DefWindowProcW', ctypes.c_ssize_t, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
    bind(user32, 'RegisterClassW', wintypes.ATOM, ptr)
    bind(user32, 'UnregisterClassW', wintypes.BOOL, wintypes.LPCWSTR, wintypes.HINSTANCE)
    bind(user32, 'CreateWindowExW', wintypes.HWND, wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
         wintypes.DWORD, integer, integer, integer, integer, wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ptr)
    bind(user32, 'SystemParametersInfoW', wintypes.BOOL, wintypes.UINT, wintypes.UINT, ptr, wintypes.UINT)
    bind(user32, 'GetCursorPos', wintypes.BOOL, ctypes.POINTER(wintypes.POINT))
    bind(user32, 'SetWindowPos', wintypes.BOOL, wintypes.HWND, wintypes.HWND, integer, integer, integer, integer, wintypes.UINT)
    bind(user32, 'InvalidateRect', wintypes.BOOL, wintypes.HWND, ctypes.POINTER(wintypes.RECT), wintypes.BOOL)
    bind(user32, 'ShowWindow', wintypes.BOOL, wintypes.HWND, integer)
    bind(user32, 'DestroyWindow', wintypes.BOOL, wintypes.HWND)
    bind(user32, 'BeginPaint', wintypes.HDC, wintypes.HWND, ctypes.POINTER(PAINTSTRUCT))
    bind(user32, 'EndPaint', wintypes.BOOL, wintypes.HWND, ctypes.POINTER(PAINTSTRUCT))
    bind(user32, 'FillRect', integer, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.HBRUSH)
    bind(user32, 'DrawTextW', integer, wintypes.HDC, wintypes.LPCWSTR, integer, ctypes.POINTER(wintypes.RECT), wintypes.UINT)
    bind(gdi32, 'CreateFontW', wintypes.HANDLE, *([integer]*5 + [wintypes.DWORD]*8 + [wintypes.LPCWSTR]))
    bind(gdi32, 'CreateSolidBrush', wintypes.HBRUSH, wintypes.DWORD)
    bind(gdi32, 'SelectObject', wintypes.HANDLE, wintypes.HDC, wintypes.HANDLE)
    bind(gdi32, 'DeleteObject', wintypes.BOOL, wintypes.HANDLE)
    bind(gdi32, 'SetBkMode', integer, wintypes.HDC, integer)
    bind(gdi32, 'SetTextColor', wintypes.DWORD, wintypes.HDC, wintypes.DWORD)
    bind(gdi32, 'StretchDIBits', integer, wintypes.HDC, *([integer]*8), ptr, ptr, wintypes.UINT, wintypes.DWORD)
    bind(shell32, 'Shell_NotifyIconGetRect', ctypes.c_long, ptr, ctypes.POINTER(wintypes.RECT))
    return user32, kernel32, gdi32, shell32


def _work_area():
    work = wintypes.RECT()
    if not _native()[0].SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return work


def tray_icon_rect(tray_hwnd, icon_id):
    """Return the notification-area icon bounds, including overflow icons."""
    class NII(ctypes.Structure):
        _fields_ = [('cbSize', wintypes.DWORD), ('hWnd', wintypes.HWND),
                    ('uID', wintypes.UINT), ('guidItem', ctypes.c_byte * 16)]
    icon, rect = NII(), wintypes.RECT()
    icon.cbSize, icon.hWnd, icon.uID = ctypes.sizeof(icon), tray_hwnd, icon_id
    try:
        shell32 = _native()[3]
        return rect if shell32.Shell_NotifyIconGetRect(ctypes.byref(icon), ctypes.byref(rect)) == 0 else None
    except (AttributeError, OSError):
        return None


class LyricBubble:
    """Non-activating, click-through lyric tooltip positioned above the tray icon."""
    WM_PAINT = 0x000F
    WIDTH, HEIGHT, GAP = 620, 104, 12
    SWP = 0x0010 | 0x0040  # SWP_NOACTIVATE | SWP_SHOWWINDOW

    def __init__(self, tray_hwnd, icon_id, owner_name):
        self.tray_hwnd, self.icon_id = tray_hwnd, icon_id
        self.text = ''
        self.visible = False
        self.hwnd = None
        self.font = None
        self._proc = None
        if os.name == 'nt':
            self._create(owner_name)

    def _create(self, owner_name):
        user32, kernel32, gdi32 = _native()[0], _native()[1], _native()[2]
        LRESULT = ctypes.c_ssize_t
        WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        class WNDCLASSW(ctypes.Structure):
            _fields_ = [('style', wintypes.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', ctypes.c_int),
                        ('cbWndExtra', ctypes.c_int), ('hInstance', wintypes.HINSTANCE), ('hIcon', wintypes.HICON),
                        ('hCursor', wintypes.HANDLE), ('hbrBackground', wintypes.HANDLE),
                        ('lpszMenuName', wintypes.LPCWSTR), ('lpszClassName', wintypes.LPCWSTR)]
        @WNDPROC
        def proc(hwnd, message, wp, lp):
            if message == self.WM_PAINT:
                self._paint(hwnd)
                return 0
            return user32.DefWindowProcW(hwnd, message, wp, lp)
        self._proc = proc
        name = owner_name + '-LyricBubble'
        klass = WNDCLASSW()
        klass.lpfnWndProc = proc
        klass.hInstance = kernel32.GetModuleHandleW(None)
        klass.lpszClassName = name
        self._class_name, self._hinstance = name, klass.hInstance
        user32.RegisterClassW(ctypes.byref(klass))
        self.hwnd = user32.CreateWindowExW(
            0x00000008 | 0x00000020 | 0x00000080 | 0x08000000,
            name, 'PAFPlayer lyric', 0x80000000 | 0x00800000,
            0, 0, self.WIDTH, self.HEIGHT, self.tray_hwnd, None, klass.hInstance, None,
        )
        try:
            self.font = gdi32.CreateFontW(-25, 0, 0, 0, 700, 0, 0, 0, 1, 0, 0, 5, 0, 'Segoe UI')
        except (AttributeError, OSError):
            self.font = None

    def _paint(self, hwnd):
        user32, gdi32 = _native()[0], _native()[2]
        ps = PAINTSTRUCT()
        dc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        if not dc: return
        background = gdi32.CreateSolidBrush(0x0028201C)
        border = gdi32.CreateSolidBrush(0x005A5048)
        outer = wintypes.RECT(0, 0, self.WIDTH, self.HEIGHT)
        inner = wintypes.RECT(2, 2, self.WIDTH - 2, self.HEIGHT - 2)
        user32.FillRect(dc, ctypes.byref(outer), border)
        user32.FillRect(dc, ctypes.byref(inner), background)
        old_font = gdi32.SelectObject(dc, self.font) if self.font else None
        gdi32.SetBkMode(dc, 1)
        gdi32.SetTextColor(dc, 0x0050EBFF)  # bright yellow (COLORREF/BGR)
        text_rect = wintypes.RECT(18, 13, self.WIDTH - 18, self.HEIGHT - 10)
        user32.DrawTextW(dc, self.text[:500], -1, ctypes.byref(text_rect),
                         0x00000001 | 0x00000010 | 0x00000800 | 0x00008000)
        if old_font: gdi32.SelectObject(dc, old_font)
        gdi32.DeleteObject(background)
        gdi32.DeleteObject(border)
        user32.EndPaint(hwnd, ctypes.byref(ps))

    def show(self, text):
        value = ' '.join(str(text or '').split()).strip()
        if not value or not self.hwnd:
            self.hide()
            return
        self.text = value
        user32 = _native()[0]
        rect = tray_icon_rect(self.tray_hwnd, self.icon_id)
        work = _work_area()
        if rect is None:
            rect = wintypes.RECT(work.right - 32, work.bottom, work.right, work.bottom + 1)
        x = max(work.left, min((rect.left + rect.right - self.WIDTH) // 2, work.right - self.WIDTH))
        above, below = rect.top - self.HEIGHT - self.GAP, rect.bottom + self.GAP
        y = above if above >= work.top else below
        y = max(work.top, min(y, work.bottom - self.HEIGHT))
        user32.SetWindowPos(self.hwnd, -1, x, y, self.WIDTH, self.HEIGHT, self.SWP)
        user32.InvalidateRect(self.hwnd, None, True)
        self.visible = True

    def hide(self):
        if self.hwnd and self.visible:
            _native()[0].ShowWindow(self.hwnd, 0)
        self.visible = False

    def close(self):
        self.hide()
        if self.hwnd:
            user32 = _native()[0]
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None
        if getattr(self, '_class_name', None):
            _native()[0].UnregisterClassW(self._class_name, self._hinstance)
            self._class_name = None
        if self.font:
            _native()[2].DeleteObject(self.font)
            self.font = None


def hover_facts(state):
    tags = {str(key).casefold(): value for key, value in (state.get('metadata') or {}).items()}
    def first(*keys):
        for key in keys:
            value = tags.get(key.casefold())
            if value: return str(value).strip()
        return '—'
    try:
        total = max(0, int(float(state.get('duration_seconds') or 0)))
        length = '%d:%02d' % divmod(total, 60) if total else '—'
    except (TypeError, ValueError): length = '—'
    track = state.get('track') or {}
    title = first('Song', 'Title', 'title', 'song')
    if title == '—': title = str(track.get('filename') or '—')
    year = first('Year', 'Date')
    if len(year) >= 4 and year[:4].isdigit(): year = year[:4]
    return {'artist': first('Artist'), 'title': title,
            'album': first('Album'), 'year': year,
            'genre': first('Genre', 'genre'), 'length': length}


class HoverCard:
    WM_PAINT = 0x000F
    SWP = 0x0010 | 0x0040  # no activate, show
    HOVER_DELAY_SECONDS = .666
    ICON_GAP = 12
    def __init__(self, tray_hwnd, icon_id, owner_name, art_size=196):
        self.tray_hwnd, self.icon_id = tray_hwnd, icon_id
        self.art_size = max(64, min(400, int(art_size)))
        self.facts = hover_facts({})
        self.state = {}
        self.bitmap = None
        self.visible = False
        self.last_seen = 0.0
        self.requested_at = None
        self.pending_state = None
        self.hwnd = None
        self._proc = None
        if os.name == 'nt': self._create(owner_name)

    def _create(self, owner_name):
        user32, kernel32 = _native()[0], _native()[1]
        LRESULT = ctypes.c_ssize_t
        WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
        class WNDCLASSW(ctypes.Structure):
            _fields_ = [('style', wintypes.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', ctypes.c_int),
                        ('cbWndExtra', ctypes.c_int), ('hInstance', wintypes.HINSTANCE), ('hIcon', wintypes.HICON),
                        ('hCursor', wintypes.HANDLE), ('hbrBackground', wintypes.HANDLE),
                        ('lpszMenuName', wintypes.LPCWSTR), ('lpszClassName', wintypes.LPCWSTR)]
        @WNDPROC
        def proc(hwnd, message, wp, lp):
            if message == self.WM_PAINT:
                self._paint(hwnd)
                return 0
            return user32.DefWindowProcW(hwnd, message, wp, lp)
        self._proc = proc
        name = owner_name + '-Hover'
        klass = WNDCLASSW()
        klass.lpfnWndProc = proc
        klass.hInstance = kernel32.GetModuleHandleW(None)
        klass.lpszClassName = name
        self._class_name, self._hinstance = name, klass.hInstance
        user32.RegisterClassW(ctypes.byref(klass))
        # WS_EX_TRANSPARENT makes the informational card click-through. Even if
        # Windows moves the taskbar while it is open, it cannot steal tray clicks.
        self.hwnd = user32.CreateWindowExW(0x00000008 | 0x00000020 | 0x00000080 | 0x08000000,
             name, 'PAFPlayer now playing', 0x80000000 | 0x00800000,
             0, 0, self.card_width, self.card_height, self.tray_hwnd, None, klass.hInstance, None)

    @property
    def card_width(self): return self.art_size + 254

    @property
    def card_height(self): return max(112, self.art_size + 24)

    def set_art_size(self, value):
        self.art_size = max(64, min(400, int(value)))
        if self.hwnd and self.visible: self.show(self.state)

    def _paint(self, hwnd):
        user32, gdi32 = _native()[0], _native()[2]
        ps = PAINTSTRUCT()
        dc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        if not dc: return
        brush = gdi32.CreateSolidBrush(0x0028201C)
        rect = wintypes.RECT(0, 0, self.card_width, self.card_height)
        user32.FillRect(dc, ctypes.byref(rect), brush)
        gdi32.DeleteObject(brush)
        gdi32.SetBkMode(dc, 1)
        gdi32.SetTextColor(dc, 0x00FFFFFF)
        def line(text, x, y, width=None):
            width = self.card_width - x - 12 if width is None else width
            bounds = wintypes.RECT(x, y, x + width, y + 44)
            user32.DrawTextW(dc, str(text)[:180], -1, ctypes.byref(bounds), 0x00000010 | 0x00008000)
        if self.bitmap:
            try:
                raw = self.bitmap
                if raw[:2] == b'BM' and len(raw) >= 54:
                    offset = struct.unpack_from('<I', raw, 10)[0]
                    width, height, planes, depth, compression = struct.unpack_from('<iiHHI', raw, 18)
                    if width > 0 and height > 0 and planes == 1 and depth in (24, 32) and compression == 0 and offset < len(raw):
                        buffer = ctypes.create_string_buffer(raw)
                        gdi32.StretchDIBits(dc, 12, 12, self.art_size, self.art_size, 0, 0, width, abs(height),
                             ctypes.byref(buffer, offset), ctypes.byref(buffer, 14), 0, 0x00CC0020)
            except (ValueError, struct.error): pass
        facts = self.facts
        text_x = self.art_size + 22
        line(facts['artist'] + ' — ' + facts['title'], text_x, 18)
        line('Album: ' + facts['album'], text_x, 68)
        line('Year: ' + facts['year'], text_x, 101)
        line('Genre: ' + facts['genre'], text_x, 134)
        line('Length: ' + facts['length'], text_x, 167)
        user32.EndPaint(hwnd, ctypes.byref(ps))

    def _icon_rect(self):
        return tray_icon_rect(self.tray_hwnd, self.icon_id)

    def request(self, state):
        self.pending_state = state
        self.last_seen = time.monotonic()
        if self.requested_at is None: self.requested_at = self.last_seen

    def show(self, state, icon_rect=None):
        if not self.hwnd: return
        self.state = dict(state or {})
        self.facts = hover_facts(state)
        self.last_seen = time.monotonic()
        user32 = _native()[0]
        rect = icon_rect or self._icon_rect()
        work = _work_area()
        if not rect:
            point = wintypes.POINT(); user32.GetCursorPos(ctypes.byref(point))
            rect = wintypes.RECT(point.x, point.y, point.x + 1, point.y + 1)
        x = (rect.left + rect.right - self.card_width) // 2
        x = max(work.left, min(x, work.right - self.card_width))
        above, below = rect.top - self.card_height - self.ICON_GAP, rect.bottom + self.ICON_GAP
        y = above if above >= work.top else below
        y = max(work.top, min(y, work.bottom - self.card_height))
        user32.SetWindowPos(self.hwnd, -1, x, y, self.card_width, self.card_height, self.SWP)
        user32.InvalidateRect(self.hwnd, None, True)
        self.visible = True
        self.requested_at = None

    def hide(self):
        self.requested_at = None
        self.pending_state = None
        if self.hwnd and self.visible:
            _native()[0].ShowWindow(self.hwnd, 0)
            self.visible = False

    def tick(self):
        # A stationary pointer still counts as hovering. Shell_NotifyIconGetRect
        # provides the actual icon rectangle, including taskbar overflow icons.
        rect = self._icon_rect()
        point = wintypes.POINT()
        user32 = _native()[0]
        inside = False
        try:
            if rect:
                user32.GetCursorPos(ctypes.byref(point))
                inside = rect.left <= point.x < rect.right and rect.top <= point.y < rect.bottom
        except (AttributeError, OSError): pass
        now = time.monotonic()
        if not inside:
            if self.visible and now - self.last_seen <= .5: return
            self.hide()
        elif not self.visible and self.requested_at is not None and now - self.requested_at >= self.HOVER_DELAY_SECONDS:
            self.show(self.pending_state or {}, rect)

    def set_bitmap(self, bitmap):
        self.bitmap = bitmap
        if self.hwnd and self.visible: _native()[0].InvalidateRect(self.hwnd, None, True)

    def close(self):
        if self.hwnd:
            user32 = _native()[0]
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None
        if getattr(self, '_class_name', None):
            _native()[0].UnregisterClassW(self._class_name, self._hinstance)
            self._class_name = None
