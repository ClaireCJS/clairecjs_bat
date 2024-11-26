#import clairecjs_utils as claire



#TODO incorporate proper full ansi_full_reset string

#IDEA: start with whatever precomputed value is closest to our current rgb value of color based on our internal mapping table rather than the start of our computed rgb value matrix

#IDEA: adaptive algorithm on how often we check elapsed time to reduce loop slowdowns when included in intensive loops ... of course, one could just... NOT CALL IT TOO OFTEN to fix that problem

#MAYBE new rainbow precomputed values for other color slide variations?



import os
import sys
import time
import atexit
import ctypes
import colorsys
import subprocess
import msvcrt
import colorama
from colorama import init, Fore, Back, Style
init(autoreset=True)


PRODUCTION = True
DEBUG_CLAIRE_CONSOLE = False

blink_on             = "\033[6m"
blink_off            = "\033[25m"



def get_console_fg_rgb():
    """    Get the RGB value of the current console foreground color. Only works on Windows platform.    """
    STD_OUTPUT_HANDLE = -11                                                          # Windows Console API constants
    FG_RED            = 0x0004
    FG_GREEN          = 0x0002
    FG_BLUE           = 0x0001
    handle            = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)       # Retrieve the handle to the console output
    csbi              = ctypes.create_string_buffer(22)                              # Retrieve the current console screen buffer info
    ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, csbi)
    rgb               = csbi.raw[10:13]                                              # Extract the RGB values from the console screen buffer info
    red, green, blue  = rgb                                                          # Convert RGB values to integers
    return red, green, blue


def get_console_bg_rgb():
    """      Get the RGB value of the current console background color.   Only works on Windows platform.    """
    STD_OUTPUT_HANDLE = -11
    BG_RED            = 0x0040
    BG_GREEN          = 0x0020
    BG_BLUE           = 0x0010
    handle            = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    csbi              = ctypes.create_string_buffer(22)
    ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, csbi)
    rgb               = csbi.raw[14:17]
    red, green, blue  = rgb
    return red, green, blue







def print_all_ansi_colors():
    colors_front = [Fore.BLACK, Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE, Fore.LIGHTBLACK_EX, Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTWHITE_EX]
    colors_back  = [Back.BLACK, Back.RED, Back.GREEN, Back.YELLOW, Back.BLUE, Back.MAGENTA, Back.CYAN, Back.WHITE, Back.LIGHTBLACK_EX, Back.LIGHTRED_EX, Back.LIGHTGREEN_EX, Back.LIGHTYELLOW_EX, Back.LIGHTBLUE_EX, Back.LIGHTMAGENTA_EX, Back.LIGHTCYAN_EX, Back.LIGHTWHITE_EX]
    colorama.init(autoreset=True)
    for i,     our_fg_color in enumerate(colors_front, start=0):
        for j, our_bg_color in enumerate(colors_back , start=0):
            print(f"{our_bg_color}{our_fg_color} {str(i):>02}/{str(j):>02}  ", end='')
        print(Style.RESET_ALL)




def cls():
    sys.stdout.write("\033[2J")
    sys.stdout.flush()
clear_screen = cls


def set_screen_rgb(r,g,b,code="11",testing=False, mode="something", count=1):
    sys.stdout.write(f'\x1b]{code};rgb_value:{r:x}/{g:x}/{b:x}\x1b\\')
    sys.stdout.flush()
    if testing: sys.stdout.write(   f'\r* New {mode} r: {r:3}/{g:3}/{b:3} count={count}')
    sys.stdout.flush()
set_rgb = set_screen_rgb

def screen_color_reset():
    sys.stdout.write('\x1b[0m')
    sys.stdout.flush()
    STD_OUTPUT_HANDLE = -11
    console_handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
    ctypes.windll.kernel32.SetConsoleTextAttribute(console_handle, 7)  # 7 is the default color code


def get_console_color_codes():
    STD_OUTPUT_HANDLE = -11
    class _COORD                    (ctypes.Structure): _fields_ = [(     "X", ctypes.c_short),(     "Y",    ctypes.c_short),]                                                                                                      # Define the _COORD structure
    class _SMALL_RECT               (ctypes.Structure): _fields_ = [(  "Left", ctypes.c_short),(   "Top",    ctypes.c_short),("Right"      ,ctypes.c_short ),("Bottom",ctypes.c_short)]                                             # Define the _SMALL_RECT structure
    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure): _fields_ = [("dwSize", ctypes.c_ulong),("dwCursorPosition", _COORD),("wAttributes",ctypes.c_ushort),("srWindow", _SMALL_RECT), ("dwMaximumWindowSize", ctypes.c_ulong)]    # Define the CONSOLE_SCREEN_BUFFER_INFO structure
    handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)                     # Retrieve the handle to the console output
    csbi   = CONSOLE_SCREEN_BUFFER_INFO()                                               # Retrieve the console screen buffer info
    ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(csbi))
    foreground_color =  csbi.wAttributes & 0x0F                                         # Extract the foreground and background color attributes
    background_color = (csbi.wAttributes & 0xF0) >> 4
    return foreground_color, background_color

def get_rgb_values(color_code):
    if color_code < 0 or color_code >= len(default_rgb_for_color_code): raise ValueError("Invalid color code")
    return default_rgb_for_color_code[color_code]



class ColorControl:
    rgb_values      = [tuple(round(j * 255) for j in colorsys.hsv_to_rgb(i / 256.0, 1.0, 1.0)) for i in range(2560)]  # Precompute RGB values
    rgb_index       = 0                                                                                               # Initialize index

    test_name       = "None"
    last_cycle_time =  None
    min_cycle_delta =  0.1                                                                                            # minimum time interval between color changes

    current_color_code = "???"       # Represents the currently set color code
    last_color_changed_code = None   # Represents the last color code that was changed

    def color_cycle(self, mode="fg", count=1000, sleep=None, now=None, prevent_machine_slowdown=True, testing=False, suppress_testing_header=False, test_name='None', j=None, color_step=1):
        if testing and not suppress_testing_header:
            parameters = ", ".join([f"{param}: {value}" for param, value in locals().items() if param != 'self'])
            print(f"\n\n* Color Cycle Test:\n\t{parameters}")
            input("\t\tHit [ENTER] to continue...")
        if   mode ==  "fg" : code =  "10"
        elif mode ==  "bg" : code =  "11"
        elif mode == "both": code = "both"
        else:                code =  mode
        self.current_color_code = code

        if self.last_color_changed_code is None or self.last_color_changed_code != code:
            self.last_color_changed_code = code

        if self.last_color_changed_code is None or self.last_color_changed_code != code:
                self.last_color_changed_code = code

        def offset_rgb(r, g, b):
            r = (r + 128) % 256
            g = (g + 128) % 256
            b = (b + 128) % 256
            #todo something to make the blinkyness go away
            return r, g, b

        def convert_rgb_tuple_to_hex_string_with_hash(r, g, b):
            return "#{:02X}{:02X}{:02X}".format(r, g, b)

        r2, g2, b2, rgb_hex2 = None, None, None, None
        for i in range(count):
            r1, g1, b1 = self.rgb_values[self.rgb_index]
            rgb_hex1 = convert_rgb_tuple_to_hex_string_with_hash(r1,g1,b1)
            if code != "both":
                #sys.stdout.write(f'\n [{code};rgb:{r1:x}/{g1:x}/{b1:x}]')
		
                sys .stdout.write(f'\x1b]{code};rgb:{r1:x}/{g1:x}/{b1:x}\x1b\\')	#change main color
                #2022/11/26 removing: sys .stdout.write(f'\x1b[ q\x1b]12;{rgb_hex1}\x07')			#cursor cursor color to match
                #sys.stdout.write( f'\x1b]1;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write( f'\x1b]2;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write( f'\x1b]3;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write( f'\x1b]4;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write( f'\x1b]5;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write( f'\x1b]6;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write( f'\x1b]7;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write( f'\x1b]8;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write( f'\x1b]9;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write(f'\x1b]12;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write(f'\x1b]13;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write(f'\x1b]14;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write(f'\x1b]15;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
                #sys.stdout.write(f'\x1b]16;rgb:{r1:x}/{g1:x}/{b1:x}\x07\x1b\\')
            else:
                r2, g2, b2 = offset_rgb(r1, g1, b1)
                rgb_hex2 = convert_rgb_tuple_to_hex_string_with_hash(r2,g2,b2)
                sys.stdout.write(f'\x1b]10;rgb:{r1:x}/{g1:x}/{b1:x}\x1b\\ TEST1')
                sys.stdout.write(f'\x1b]11;rgb:{r2:x}/{g2:x}/{b2:x}\x1b\\ TEST2')
            #ys.stdout.write( f'\n ]{code};rgb:{r:x}/{g:x}/{b:x}\t\t')
            if testing: sys.stdout.write(f'\r*\t New {mode} r/g/b: {r1:3}/{g1:3}/{b1:3} count={count} i={i} \t testname={self.test_name} \t j={j}')
            sys.stdout.flush()
            if sleep: time.sleep(sleep)
            if prevent_machine_slowdown:
                if now: self.last_time = now                              # Update 'last_time' after changing color and optional sleeping
                else:   self.last_time = time.time()
            self.rgb_index = (self.rgb_index + color_step) % len(self.rgb_values)  # Update index, roll over to 0 when reaching the end of rgb_values
        return r1, g1, b1, rgb_hex1, r2, g2, b2, rgb_hex2


    def tock_old(self):
        #r, g, b = self.rgb_values[self.rgb_index]
        #rgb_values = default_rgb_for_color_code[self.last_color_code]              # Look up the corresponding RGB values from the lookup table

        the_last_color_console_code = self.current_color_code
        if self.last_color_changed_code is not None:
            the_last_color_console_code = self.last_color_changed_code

        print(f"the_last_color_console_code={the_last_color_console_code}")

        the_last_color_ansi_code    = mapping_console_color_to_ansi_color[the_last_color_console_code]
        r, g, b = default_rgb_for_color_code[the_last_color_ansi_code]                   # Look up the corresponding RGB values from the lookup table

        print(f"got rgb of {r} / {g} / {b} for console code {self.current_color_code}   \t ")
        sys.stdout.write(f'RESTORE code={self.current_color_code};rgb:{r:x}/{g:x}/{b:x}\x1b\\')
        sys.stdout.write(f'\x1b]{self.current_color_code};rgb:{r:x}/{g:x}/{b:x}\x1b\\')
        screen_color_reset()                                                        # generic console reset function to start with
        

    def tick(self, sleep=None, mode=None, testing=False, test_name="None", j=None, count=1, color_step=1):
        now = time.time()
        self.test_name = test_name
        if self.last_cycle_time is None or now - self.last_cycle_time >= self.min_cycle_delta:
            #elf.color_cycle(mode= 3  , count=  1  , testing=testing, suppress_testing_header=True, sleep=sleep, now=now, j=j)
            self.color_cycle(mode=mode, count=count, testing=testing, suppress_testing_header=True, sleep=sleep, now=now, j=j, color_step=color_step)
            self.last_cycle_time = now
        #return r, g, b 🐐

    def tock_closer(self):
        for color_code, rgb_values in enumerate(default_rgb_for_color_code):
            ansi_code = mapping_console_color_to_ansi_color.get(color_code, color_code)
            r, g, b = rgb_values
            sys.stdout.write(f'TOCK RESTORE: color_code={color_code:>2}, ansi_code={ansi_code:>2} ........ rgb:{r:3}/{g:3}/{b:3}\x1b\\\n')
            sys.stdout.write(f'\x1b]{ansi_code};rgb:{r:x}/{g:x}/{b:x}\x1b\\')
        screen_color_reset()  # Reset the console color

    def tock(self):
        global PRODUCTION      
        if     PRODUCTION == False: print("TOCK!")      
        method     = "hard"                 #hard-coded method? or just reset them with our code       
        if method == "hard":
            #goatgoat let's try skipping this for now 2024/11/23
            #sys.stdout.write("\x1b]10;rgb:c0/c0/c0\x1b\\");  sys.stdout.flush()
            #sys.stdout.write("\x1b]11;rgb:00/00/00\x1b\\");  sys.stdout.flush()
            #sys.stdout.write("hello!")
            pass
        else:            
            for color_code, rgb_values in enumerate(default_rgb_for_color_code):
                r, g, b = default_rgb_for_color_code[color_code]
                #color_code = mapping_console_color_to_ansi_color.get(color_code, color_code)
                sys.stdout.write(f"\ncolor_code_tock={color_code:>2}, rgb_values={r:2x}{g:2x}{b:2x}    ")
                sys.stdout.write(f'\\x1b]{color_code}; \trgb:{r:0x}/{g:0x}/{b:0x}\\x1b\\') #rem escaped the 2 escapes and put \t before rgb:
                sys.stdout.write( f'\x1b]{color_code};rgb:{r:x}/{g:x}/{b:x}\x1b\\')  #normal
                sys.stdout.flush()
                #print("\n")

        #FOR MORE INFO: https://stackoverflow.com/questions/27159322/rgb-values-of-the-colors-in-the-ansi-extended-colors-index-17-255

        #UNTESTED:
                #the following loop will reset all colors from 0 to 255 to their configured or default value:
                    #for c in {0..255}; do
                    #  echo -en "\e]104;$c\a"
                    #done

        #reset the foreground and background to white/black
        #ys.stdout.write(f'\x1b]10;rgb:{r:x}/{g:x}/{b:x}\x1b\\')

        #2024/11/02 — for whatever reasons these are now leaking out where they shouldn't, let's try taking this reset out
        #sys.stdout.write(f'\x1b]10;rgb:c0/c0/c0\x1b\\')
        #sys.stdout.write(f'\x1b]11;rgb:00/00/00\x1b\\')
        #screen_color_reset()  # Reset the console color
        #2024/11/18 — put this back in, but above


#              vvv---- this is the default mode if we lazily call claire.tick() from somewhere external
def tick(mode="fg", testing=False,test_name="None",sleep=None, j=None, count=1, color_step=1):  color_control.tick(mode=mode, testing=testing, test_name=test_name, sleep=sleep, j=j, count=count, color_step=color_step)
def tock():                                                                                     color_control.tock()


default_rgb_for_color_code = [          # tried to get the "official" versions of the colors here, but this WON'T be what some people might want, if they use alternate colors!
    #colors_front = [Fore.BLACK, Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE, Fore.LIGHTBLACK_EX, Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTWHITE_EX]
    (  0,   0,   0),                    # Color code  0 - Black
    (128,   0,   0),                    # Color code  1 - Red
    (  0, 128,   0),                    # Color code  2 - Green
    (128, 128,   0),                    # Color code  3 - Yellow
    (  0,   0, 128),                    # Color code  4 - Blue
    (128,   0, 128),                    # Color code  5 - Magenta
    (  0, 128, 128),                    # Color code  6 - Cyan
    (192, 192, 192),                    # Color code  7 - Light Gray
    (128, 128, 128),                    # Color code  8 - Dark Gray
    (255,   0,   0),                    # Color code  9 - Bright Red
    (  0, 255,   0),                    # Color code 10 - Bright Green
    (255, 255,   0),                    # Color code 11 - Bright Yellow
    (  0,   0, 255),                    # Color code 12 - Bright Blue
    (255,   0, 255),                    # Color code 13 - Bright Magenta
    (  0, 255, 255),                    # Color code 14 - Bright Cyan
    (255, 255, 255),                    # Color code 15 - White
]

mapping_console_color_to_ansi_color = {         
    10: 7,                              #voodoo
    11: 0                               #voodoo
}

color_control = ColorControl()
atexit.register(color_control.tock)     # Register tock() function with atexit so it automatically runs when the program ends



def tick_subtest(mode,num_ticks=7500000):
    input(f"\n\nHit [ENTER] for tick **** {mode} **** test... will run tick() {num_ticks} times...")
    for j in range(0, num_ticks):
        #if msvcrt.kbhit():                                                      # Check if a key has been pressed
        #    print("\t\n********** Key pressed, stopping test... ************")
        #    break
        tick(mode=mode,testing=True,sleep=0,j=j)
        #print(f"\tj={j}",end="")
    print("\n...Tick test complete.\n")

def tick_test():
    num_ticks = 7500000
    tick_subtest("fg",num_ticks)
    tick_subtest("bg",num_ticks)


if __name__ == "__main__":
    cls()
    fg_color, bg_color = get_console_color_codes()
    print(f"\n\ncurrent fg rgb is not really (wtf): {get_console_fg_rgb()}")
    print(    f"current bg rgb is not really (wtf): {get_console_bg_rgb()}\n\n")
    print_all_ansi_colors()


    #for i in range(16): print(f"{i:2}: " + get_color_via_subprocess_ansi_echo_which_is_not_a_very_good_way_to_do_things_at_all_and_should_be_avoided(i))

    print(f"Current foreground color: {fg_color}, rgb={get_rgb_values(fg_color)}")
    print(f"Current background color: {bg_color}, rgb={get_rgb_values(bg_color)}")

    color_control = ColorControl()
    tick_test()
    #color_control.color_cycle(testing=True,count=50000          ,prevent_machine_slowdown=True)   #set prevent_machine_slowdown = False so that it just runs through the loop without the more-complicated time-based-cpu-overload-prevention code happening
    #color_control.color_cycle(testing=True,count=400 ,sleep=.001,prevent_machine_slowdown=False)   #set prevent_machine_slowdown = False so that it just runs through the loop without the more-complicated time-based-cpu-overload-prevention code happening
    screen_color_reset()




#function aliases so people with bad memories aren't wrong as often
print_all_colors = print_all_ansi_colors
show_all_colors  = print_all_ansi_colors
all_colors       = print_all_ansi_colors
screen_reset     = screen_color_reset
color_reset      = screen_color_reset
reset_screen     = screen_color_reset
reset_color      = screen_color_reset


