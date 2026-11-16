"""Read a short credential handoff without terminal echo."""
import ctypes,runpy,sys
from pathlib import Path
kernel=ctypes.windll.kernel32
handle=kernel.GetStdHandle(-10); mode=ctypes.c_uint()
if not kernel.GetConsoleMode(handle,ctypes.byref(mode)):
 print('Secure input unavailable; no keys were read.');raise SystemExit(1)
if not kernel.SetConsoleMode(handle,mode.value & ~4):
 print('Could not disable input echo; no keys were read.');raise SystemExit(1)
try:runpy.run_path(str(Path(__file__).with_name('install_free_dj_keys.py')),run_name='__main__')
finally:kernel.SetConsoleMode(handle,mode.value)
