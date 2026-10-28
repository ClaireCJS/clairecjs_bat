"""Native Win32 tray hover card; shares the tray thread's message pump."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import struct
import time


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
    def __init__(self, tray_hwnd, icon_id, owner_name):
        self.tray_hwnd, self.icon_id = tray_hwnd, icon_id
        self.facts = hover_facts({})
        self.bitmap = None
        self.visible = False
        self.last_seen = 0.0
        self.hwnd = None
        self._proc = None
        if os.name == 'nt': self._create(owner_name)

    def _create(self, owner_name):
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
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
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.DefWindowProcW.restype = LRESULT
        user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
             wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
             wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p]
        user32.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
             ctypes.c_int, ctypes.c_int, wintypes.UINT]
        # PAFPlayer_tray also configures this process-global ctypes function, but
        # its locally declared WNDCLASSW is a distinct nominal Python type. Reset
        # the prototype here so tray-only startup accepts this module's class.
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        user32.RegisterClassW.restype = wintypes.ATOM
        name = owner_name + '-Hover'
        klass = WNDCLASSW()
        klass.lpfnWndProc = proc
        klass.hInstance = kernel32.GetModuleHandleW(None)
        klass.lpszClassName = name
        user32.RegisterClassW(ctypes.byref(klass))
        user32.CreateWindowExW.restype = wintypes.HWND
        self.hwnd = user32.CreateWindowExW(0x00000008 | 0x00000080 | 0x08000000,
             name, 'PAFPlayer now playing', 0x80000000 | 0x00800000,
             0, 0, 450, 220, self.tray_hwnd, None, klass.hInstance, None)

    def _paint(self, hwnd):
        user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
        class PAINTSTRUCT(ctypes.Structure):
            _fields_ = [('hdc', wintypes.HDC), ('fErase', wintypes.BOOL), ('rcPaint', wintypes.RECT),
                        ('fRestore', wintypes.BOOL), ('fIncUpdate', wintypes.BOOL), ('rgbReserved', ctypes.c_byte * 32)]
        ps = PAINTSTRUCT()
        user32.BeginPaint.restype = wintypes.HDC
        user32.BeginPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
        user32.EndPaint.argtypes = [wintypes.HWND, ctypes.POINTER(PAINTSTRUCT)]
        user32.FillRect.argtypes = [wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.HBRUSH]
        user32.DrawTextW.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int,
                                   ctypes.POINTER(wintypes.RECT), wintypes.UINT]
        gdi32.CreateSolidBrush.restype = wintypes.HBRUSH
        gdi32.CreateSolidBrush.argtypes = [wintypes.DWORD]
        gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
        gdi32.SetBkMode.argtypes = [wintypes.HDC, ctypes.c_int]
        gdi32.SetTextColor.argtypes = [wintypes.HDC, wintypes.DWORD]
        gdi32.StretchDIBits.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
            wintypes.UINT, wintypes.DWORD]
        dc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        if not dc: return
        brush = gdi32.CreateSolidBrush(0x0028201C)
        rect = wintypes.RECT(0, 0, 450, 220)
        user32.FillRect(dc, ctypes.byref(rect), brush)
        gdi32.DeleteObject(brush)
        gdi32.SetBkMode(dc, 1)
        gdi32.SetTextColor(dc, 0x00FFFFFF)
        def line(text, x, y, width=258):
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
                        gdi32.StretchDIBits(dc, 12, 12, 196, 196, 0, 0, width, abs(height),
                             ctypes.byref(buffer, offset), ctypes.byref(buffer, 14), 0, 0x00CC0020)
            except (ValueError, struct.error): pass
        facts = self.facts
        line(facts['artist'] + ' — ' + facts['title'], 218, 18)
        line('Album: ' + facts['album'], 218, 68)
        line('Year: ' + facts['year'], 218, 101)
        line('Genre: ' + facts['genre'], 218, 134)
        line('Length: ' + facts['length'], 218, 167)
        user32.EndPaint(hwnd, ctypes.byref(ps))

    def show(self, state):
        if not self.hwnd: return
        self.facts = hover_facts(state)
        self.last_seen = time.monotonic()
        position = wintypes.POINT()
        user32 = ctypes.windll.user32
        user32.GetCursorPos(ctypes.byref(position))
        width, height = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        x = max(0, min(position.x - 220, width - 450))
        y = max(0, min(position.y - 230, height - 220))
        user32.SetWindowPos(self.hwnd, -1, x, y, 450, 220, self.SWP)
        user32.InvalidateRect(self.hwnd, None, True)
        self.visible = True

    def hide(self):
        if self.hwnd and self.visible:
            ctypes.windll.user32.ShowWindow(self.hwnd, 0)
            self.visible = False

    def tick(self):
        if not self.visible: return
        # A stationary pointer still counts as hovering. Shell_NotifyIconGetRect
        # provides the actual icon rectangle, including taskbar overflow icons.
        class NII(ctypes.Structure):
            _fields_ = [('cbSize', wintypes.DWORD), ('hWnd', wintypes.HWND),
                        ('uID', wintypes.UINT), ('guidItem', ctypes.c_byte * 16)]
        icon = NII()
        icon.cbSize, icon.hWnd, icon.uID = ctypes.sizeof(icon), self.tray_hwnd, self.icon_id
        rect = wintypes.RECT()
        point = wintypes.POINT()
        shell32, user32 = ctypes.windll.shell32, ctypes.windll.user32
        inside = False
        try:
            shell32.Shell_NotifyIconGetRect.argtypes = [ctypes.POINTER(NII), ctypes.POINTER(wintypes.RECT)]
            if shell32.Shell_NotifyIconGetRect(ctypes.byref(icon), ctypes.byref(rect)) == 0:
                user32.GetCursorPos(ctypes.byref(point))
                inside = rect.left <= point.x < rect.right and rect.top <= point.y < rect.bottom
        except (AttributeError, OSError): pass
        if not inside and time.monotonic() - self.last_seen > .5: self.hide()

    def set_bitmap(self, bitmap):
        self.bitmap = bitmap
        if self.hwnd and self.visible: ctypes.windll.user32.InvalidateRect(self.hwnd, None, True)

    def close(self):
        if self.hwnd:
            ctypes.windll.user32.DestroyWindow(self.hwnd)
            self.hwnd = None
