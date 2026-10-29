"""ICGF artwork discovery, taskbar identity and tray integration on Windows.

This is ICGF application code: the native messages only reveal ICGF artwork;
they never approve, rename, recycle or otherwise act on an image. No socket,
registry setting, shared job file, global hotkey or background service is used.
All Tk work and native window subclass ownership stay on the artwork thread.
"""
from functools import lru_cache
import os
import queue

GROUP='ClaireCJS.ICGF.Artwork.v1'
_live_shells=set()


@lru_cache(maxsize=1)
def native():
    import ctypes as c
    from ctypes import wintypes as w
    class Guid(c.Structure):_fields_=[('a',w.DWORD),('b',w.WORD),('d',w.WORD),('e',c.c_ubyte*8)]
    class IconData(c.Structure):
        _fields_=[('cbSize',w.DWORD),('hWnd',w.HWND),('uID',w.UINT),('uFlags',w.UINT),
                  ('uCallbackMessage',w.UINT),('hIcon',w.HICON),('szTip',w.WCHAR*128),
                  ('dwState',w.DWORD),('dwStateMask',w.DWORD),('szInfo',w.WCHAR*256),
                  ('uVersion',w.UINT),('szInfoTitle',w.WCHAR*64),('dwInfoFlags',w.DWORD),
                  ('guidItem',Guid),('hBalloonIcon',w.HICON)]
    class Identifier(c.Structure):
        _fields_=[('cbSize',w.DWORD),('hWnd',w.HWND),('uID',w.UINT),('guidItem',Guid)]
    proc=c.WINFUNCTYPE(c.c_ssize_t,w.HWND,w.UINT,w.WPARAM,w.LPARAM,c.c_size_t,c.c_size_t)
    enum=c.WINFUNCTYPE(w.BOOL,w.HWND,w.LPARAM)
    user=c.WinDLL('user32',use_last_error=True)
    shell=c.WinDLL('shell32',use_last_error=True)
    controls=c.WinDLL('comctl32',use_last_error=True)
    definitions=[
        (user,'RegisterWindowMessageW',[w.LPCWSTR],w.UINT),
        (user,'SetPropW',[w.HWND,w.LPCWSTR,w.HANDLE],w.BOOL),
        (user,'GetPropW',[w.HWND,w.LPCWSTR],w.HANDLE),
        (user,'IsWindow',[w.HWND],w.BOOL),
        (user,'RemovePropW',[w.HWND,w.LPCWSTR],w.HANDLE),
        (user,'EnumWindows',[enum,w.LPARAM],w.BOOL),
        (user,'PostMessageW',[w.HWND,w.UINT,w.WPARAM,w.LPARAM],w.BOOL),
        (user,'GetWindowThreadProcessId',[w.HWND,c.POINTER(w.DWORD)],w.DWORD),
        (user,'AllowSetForegroundWindow',[w.DWORD],w.BOOL),
        (user,'LoadIconW',[w.HINSTANCE,c.c_void_p],w.HICON),
        (user,'SendMessageW',[w.HWND,w.UINT,w.WPARAM,w.LPARAM],c.c_ssize_t),
        (user,'SetWindowPos',[w.HWND,w.HWND,c.c_int,c.c_int,c.c_int,c.c_int,w.UINT],w.BOOL),
        (controls,'SetWindowSubclass',[w.HWND,proc,c.c_size_t,c.c_size_t],w.BOOL),
        (controls,'RemoveWindowSubclass',[w.HWND,proc,c.c_size_t],w.BOOL),
        (controls,'DefSubclassProc',[w.HWND,w.UINT,w.WPARAM,w.LPARAM],c.c_ssize_t),
        (shell,'Shell_NotifyIconW',[w.DWORD,c.POINTER(IconData)],w.BOOL),
        (shell,'Shell_NotifyIconGetRect',[c.POINTER(Identifier),c.POINTER(w.RECT)],w.LONG),
        (shell,'SetCurrentProcessExplicitAppUserModelID',[w.LPCWSTR],w.LONG),
    ]
    for dll,name,args,result in definitions:
        method=getattr(dll,name);method.argtypes=args;method.restype=result
    return c,w,user,shell,controls,proc,enum,IconData,Identifier


@lru_cache(maxsize=1)
def prepare_instance():
    if os.name!='nt':return None
    shell=native()[3]
    appid='ClaireCJS.ICGF.Artwork.'+str(os.getpid())
    result=shell.SetCurrentProcessExplicitAppUserModelID(appid)
    if result<0:raise OSError('Could not establish the ICGF taskbar identity: '+str(result))
    return appid


def windows(group=GROUP):
    if os.name!='nt':return []
    c,w,user,_,_,_,enum,_,_=native();found=[]
    @enum
    def visit(hwnd,_):
        if user.GetPropW(hwnd,group):found.append(int(hwnd))
        return True
    if not user.EnumWindows(visit,0):raise c.WinError(c.get_last_error())
    return found


def reveal_all(group=GROUP,exclude_pid=None):
    """Post a reveal request to each live ICGF artwork on this desktop."""
    if os.name!='nt':return 0
    c,w,user,_,_,_,_,_,_=native()
    message=user.RegisterWindowMessageW(group+'.ShowAll')
    if not message:raise c.WinError(c.get_last_error())
    count=0
    for hwnd in windows(group):
        pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,c.byref(pid))
        if pid.value==exclude_pid:continue
        user.AllowSetForegroundWindow(pid.value)
        if user.PostMessageW(hwnd,message,0,0):count+=1
    return count


class ArtworkShell:
    def __init__(self,viewer,group=GROUP):
        self.viewer=viewer;self.group=group;self.hwnd=None;self.attached=False
        self.tray_added=False;self.tip=None;self.error=None;self.retry=None;self.closed=False
        self.requests=queue.SimpleQueue();self.menu=None
        self.c,self.w,self.user,self.shell,self.controls,proc,_,self.Data,self.Identifier=native()
        self.message=self.user.RegisterWindowMessageW(group+'.ShowAll')
        self.explorer=self.user.RegisterWindowMessageW('TaskbarCreated')
        if not self.message or not self.explorer:raise self.c.WinError(self.c.get_last_error())
        self.callback_message=0x8000+0x49
        self.procedure=proc(self.dispatch)
        try:self.refresh()
        except BaseException:self.close();raise

    def refresh(self):
        if self.closed:return
        _,hwnd,getter,setter=self.viewer._native_window()
        if hwnd!=self.hwnd or not self.attached:
            self.detach()
            if self.attached:raise OSError('Could not detach the previous artwork shell callback.')
            self.hwnd=hwnd
            if not self.controls.SetWindowSubclass(hwnd,self.procedure,0x49434746,0):
                raise self.c.WinError(self.c.get_last_error())
            self.attached=True;_live_shells.add(self)
            if not self.user.SetPropW(hwnd,self.group,1):raise self.c.WinError(self.c.get_last_error())
            # NOACTIVATE windows require APPWINDOW to retain taskbar entries.
            setter(hwnd,-20,(getter(hwnd,-20)|0x00040000)&~0x00000080)
            self.user.SetWindowPos(hwnd,0,0,0,0,0,0x0037)
            self.icon=self.user.LoadIconW(None,self.c.c_void_p(32512))
            if self.icon:
                self.user.SendMessageW(hwnd,0x80,0,self.icon)
                self.user.SendMessageW(hwnd,0x80,1,self.icon)
            self.tip=None
        title=('ICGF ['+str(os.getpid())+'] '+self.viewer.root.title().removeprefix('ICGF — '))[:127]
        if title!=self.tip or not self.tray_added:self.add_tray(title)

    def icon_data(self):
        data=self.Data();data.cbSize=self.c.sizeof(data);data.hWnd=self.hwnd;data.uID=1
        data.uFlags=1|2|4;data.uCallbackMessage=self.callback_message
        data.hIcon=self.icon;data.szTip=self.tip or 'ICGF'
        return data

    def add_tray(self,title):
        self.tip=title;data=self.icon_data()
        ok=self.shell.Shell_NotifyIconW(1 if self.tray_added else 0,self.c.byref(data))
        self.tray_added=bool(ok)
        if not ok and self.retry is None:
            self.error='Windows could not add the ICGF tray icon; retrying.'
            self.retry=self.viewer.root.after(2000,self.retry_tray)
        elif ok:self.error=None

    def retry_tray(self):
        self.retry=None
        if not self.closed:self.refresh()

    def tray_rect(self):
        identity=self.Identifier();identity.cbSize=self.c.sizeof(identity)
        identity.hWnd=self.hwnd;identity.uID=1;rect=self.w.RECT()
        if self.shell.Shell_NotifyIconGetRect(self.c.byref(identity),self.c.byref(rect))==0:
            return rect.left,rect.top,rect.right,rect.bottom
        return None

    def dispatch(self,hwnd,message,wp,lp,identifier,reference):
        try:
            # Never enter Tk from a native window procedure, including after().
            # Tk may be inside its own C message dispatch with a saved GIL state.
            # Its ordinary Python timer drains these plain-data requests instead.
            if message==self.message:
                if not self.closed:self.requests.put('show')
                return 0
            if message==self.explorer:self.requests.put('explorer')
            elif message==self.callback_message:
                if lp in (0x202,0x203,0x405):self.requests.put('show')
                elif lp in (0x205,0x7b):self.requests.put('menu')
                return 0
            elif message==0x82:self.detach()
        except BaseException as error:self.error=type(error).__name__+': '+str(error)
        return self.controls.DefSubclassProc(hwnd,message,wp,lp)

    def poll(self):
        while not self.closed:
            try:request=self.requests.get_nowait()
            except queue.Empty:return
            if request=='show':self.viewer.reopen(True)
            elif request=='menu':self.tray_menu()
            elif request=='explorer':
                self.tray_added=False;self.tip=None;self.refresh()

    def tray_menu(self):
        if self.closed:return
        root=self.viewer.root
        if self.menu is None:
            self.menu=self.viewer.tk.Menu(root,tearoff=False)
            self.menu.add_command(label='Show this artwork',command=lambda:self.viewer.reopen(True))
            self.menu.add_command(label='Show all ICGF artwork',command=self.viewer.show_all_artwork)
            self.menu.add_command(label='Hide this artwork',command=self.viewer.hide)
        menu=self.menu
        try:
            self.viewer.activate_on_click()
            menu.tk_popup(root.winfo_pointerx(),root.winfo_pointery())
        finally:menu.grab_release()

    def detach(self):
        if self.hwnd:
            if self.tray_added:
                data=self.icon_data();self.shell.Shell_NotifyIconW(2,self.c.byref(data))
            self.user.RemovePropW(self.hwnd,self.group)
            if self.attached and not self.controls.RemoveWindowSubclass(self.hwnd,self.procedure,0x49434746) and self.user.IsWindow(self.hwnd):
                # Pin the callback if Windows still owns it. close() releases
                # the Tk reference on this owner thread; WM_NCDESTROY retries.
                self.tray_added=False;self.error='Artwork callback could not be detached.'
                return
        self.tray_added=False;self.attached=False;_live_shells.discard(self)

    def close(self):
        if self.closed:return
        self.closed=True
        if self.retry is not None:self.viewer.root.after_cancel(self.retry);self.retry=None
        self.detach()
        if self.menu is not None:self.menu.destroy();self.menu=None
        self.viewer=None
