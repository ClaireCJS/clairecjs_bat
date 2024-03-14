import ctypes
from screeninfo import get_monitors
ctypes.windll.user32.ShowWindow(ctypes.windll.user32.FindWindowW(u"Shell_traywnd", None), 1)    #taskbar off
