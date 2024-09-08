import sys
import time
import colorsys

code = "11";
if len(sys.argv) > 1:
    if sys.argv[1].lower() == "background": code="11"
    if sys.argv[1].lower() == "foreground": code="10"

for i in range(0, 2560):
    h = i / 256.0
    (r, g, b) = tuple(round(j * 255) for j in colorsys.hsv_to_rgb(h,1.0,1.0))
    sys.stdout.write(f'\x1b]{code};rgb:{r:x}/{g:x}/{b:x}\x1b\\')
    sys.stdout.write(f'\rrgb:{r:x}/{g:x}/{b:x}')
    sys.stdout.flush()
    time.sleep(.05)
