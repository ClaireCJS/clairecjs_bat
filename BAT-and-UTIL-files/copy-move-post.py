"""
        COPY/MOVE postprocessor

        USAGE:  {command} | copy-move-post
        USAGE:  {command} | copy-move-post nomoji —— doesn't add the emoji prefixes to lines

                    * makes each line a random color (to increase visual accessibility to boundaries between filenames)

                    * color cycles delimiter characters (to ease anxiety that things are hung)

                    * Inserts relevant emoji at the beginning of the line (to decrease visual processing energy)

                    * blinks and double-heightens errors (to decrease required attention level & grab attention for addressing errors sooner)

                    * double-heightens summaries (to increase visual accessibility to the part that matters more than the details)

"""

import random
import sys
import re
import io
import threading
import queue
import time
import os
import clairecjs_utils as claire                                                                                #my library that has color-cycling-by-ANSI functionality used
from colorama import init
init(autoreset=False)

DEFAULT_MODE   = "fg"                                                                                           #whether to color-cycle foreground ("fg"), background ("bg"), or both ("both").
EMOJIS_COPY    = '⭢︋📂'
EMOJIS_PROMPT  = '❓❓ '
EMOJIS_DELETE  = '👻⛔'
EMOJIS_SUMMARY = '✔️ '
EMOJIS_ERROR   = '🛑🛑'
nomoji         = False                                                                                          #set to True to disable [some] emoji decoration of lines

#Note to self: either maintain a simultaneous update of these 4 values in set-colors.bat or create env-var overrides:
MIN_RGB_VALUE_FG = 88;   MIN_RGB_VALUE_BG = 12                                                                  #\__ range of random values we
MAX_RGB_VALUE_FG = 255;  MAX_RGB_VALUE_BG = 40                                                                  #/   choose random colors from

FOOTERS = [                                                                                                     #values that indicate a copy/move summary line,
           "files copied"          , "file copied"           ,                                                 #which we like to identify for special treatment
           "files moved"           , "file moved"            ,
           "files deleted"         , "file deleted"          ,
           "dirs copied"           , "dir copied"            ,
           "dirs moved"            , "dir moved"             ,
           "files would be copied" , "file would be copied"  ,
           "files would be moved"  , "file would be moved"   ,
           "files would be deleted", "file would be deleted" ,
           "dirs would be copied"  , "dir would be copied"   ,
           "dirs would be moved"   , "dir would be moved"    ,
           "dirs would be deleted" , "dir would be deleted"  ,
          ]
file_removals = ["\\recycled\\","\\recycler\\","Removing ","Deleting "]                                         #values that indicate a file deletion/removal


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')                            #utf-8 fix

move_decorator = os.environ.get('move_decorator', '')                                                           #fetch user-specified decorator (if any)

if os.environ.get('no_tick') == "1": TICK = False
else                               : TICK = True
#print(f"tick is {TICK} .. {os.environ.get('no_tick')}")

if os.environ.get('no_double_lines',0) == "1": DOUBLE_LINES_ENABLED = False
else                                         : DOUBLE_LINES_ENABLED = True                                       #DEBUG: print(f"DOUBLE_LINES_ENABLED={DOUBLE_LINES_ENABLED}")


def enable_vt_support():                                                                                        #this was painful to figure out
    import os
    if os.name == 'nt':
        import ctypes
        hOut = ctypes.windll.kernel32.GetStdHandle(-11)
        out_modes = ctypes.c_uint32()
        ENABLE_VT_PROCESSING = ctypes.c_uint32(0x0004)
        # ctypes.addressof()
        ctypes.windll.kernel32.GetConsoleMode(hOut, ctypes.byref(out_modes))
        out_modes = ctypes.c_uint32(out_modes.value | 0x0004)
        ctypes.windll.kernel32.SetConsoleMode(hOut, out_modes)

def convert_rgb_tuple_to_hex_string_with_hash(r, g, b): return "#{:02X}{:02X}{:02X}".format(r, g, b)

def get_random_color(bg=False, hex=False):                                                                      #return random rgb values within our confifured threshold
    if bg: min_rgb_value = MIN_RGB_VALUE_BG; max_rgb_value = MAX_RGB_VALUE_BG
    else:  min_rgb_value = MIN_RGB_VALUE_FG; max_rgb_value = MAX_RGB_VALUE_FG
    rand_r = random.randint(min_rgb_value,max_rgb_value)
    rand_g = random.randint(min_rgb_value,max_rgb_value)
    rand_b = random.randint(min_rgb_value,max_rgb_value)
    if hex: return convert_rgb_tuple_to_hex_string_with_hash(rand_r, rand_g, rand_b)
    else  : return            rand_r, rand_g, rand_b

def enclose_numbers(line): return re.sub(r'(\d+)', r'\033[21m\1\033[24m', line)                                 #ansi-stylize numbers - italics + we choose double-underline in this example



def print_line(line_buffer, r, g, b, additional_beginning_ansi=""):
    color_change_ansi = f'\033[38;2;{r};{g};{b}m'
    ansi_reset = '\033[0m' + move_decorator

    double  = False
    summary = False

    if any(substring in line_buffer for substring in FOOTERS):                                                  #identify if we're in a footer/summary line
        line_buffer = enclose_numbers(line_buffer)
        double      = True
        summary     = True

    if nomoji is True:
        line = ""
    else:
        line = move_decorator                                                                                                      #decorate with environment-var-supplied decorator if applicable
        if   any(substring in line_buffer for substring in file_removals ): line += EMOJIS_DELETE                                  #treatment for file deletion lines
        elif any(substring in line_buffer for substring in ["Y/N/A/R)"]  ): line += EMOJIS_PROMPT                                  #treatment for  user prompt  lines
        elif any(substring in line_buffer for substring in ["=>","->"]   ): line += EMOJIS_COPY                                    #treatment for   file copy   lines
        elif any(substring in line_buffer for substring in ["TCC: (Sys)"]):                                                        #treatment for error message lines
            double = True;                                                  line += EMOJIS_ERROR + f'\033[6m\033[3m\033[4m\033[7m'
        elif summary:                                                       line += EMOJIS_SUMMARY                                 #treatment for summary lines
        else:                                                               line += f'  '                                          #TODO figure out why this line is here

    if summary:                                                                                                # Handle transformation for summary lines
        pattern = "|".join(re.escape(footer) for footer in FOOTERS)
        segments = re.split(pattern, line_buffer)
        segments = [seg.strip() for seg in segments if seg.strip()]                                            # Remove empty segments and strip spaces from the rest
        lines = []
        for segment in segments:
            footer_match = re.search(pattern, line_buffer)
            if footer_match:
                footer = footer_match.group(0)
                lines.append(f"{segment} {footer}")
                line_buffer = line_buffer.replace(footer, "", 1).strip()                                       # Update line_buffer to remove the footer we just matched
        line_buffer = f'\n{EMOJIS_SUMMARY}'.join(lines)

    line += f'{color_change_ansi}{additional_beginning_ansi}{line_buffer.rstrip()}\033[0m\n'

    if not nomoji:
        line = line.replace(' => ' , f'{ansi_reset} => {color_change_ansi}')                                  #\
        line = line.replace(' -> ' , f'{ansi_reset} -> {color_change_ansi}')                                  # \      Keep all these characters in the default font color, which
        line = line.replace( '=>>' , f'{ansi_reset}↪️{   color_change_ansi}')  #this arrow looks better here   #  \     is the one succeptible to the color-cycling that we use
        line = line.replace(   '.' , f'{ansi_reset}.{   color_change_ansi}')                                  #   >---
        line = line.replace(   ':' , f'{ansi_reset}:{   color_change_ansi}')                                  #  /
        line = line.replace( ' - ' , f'{ansi_reset} - { color_change_ansi}')                                  # /
        line = line.replace(  '\\' , f'{ansi_reset}\\{  color_change_ansi}')                                  #/

    lines_to_print = line.split('\n')                                                                         #there really shouldn't be a \n in our line, but things happen
    i = 0
    for myline in lines_to_print:                                                                             #print our line, but do it double-height if we're supposed to
        if myline != '\n' and myline != '':
            if not double or not DOUBLE_LINES_ENABLED:
                sys.stdout.write(f'{myline}')
            else:
                enable_vt_support()                                                                            #suggestion from https://github.com/microsoft/terminal/issues/15838
                #sys.stdout.write(f'\033[1G')   #20240324: adding '\033[1G' as ??bugfix?? for ansi creeping out due to TCC error and mis-aligning our double-height lines - prepend the ansi code to move to column 1 first, prior to printing our line
                #sys.stdout.write(f'\033[1G\033#3\033[38;2;{r};{g};{b}m{myline}\n\033#4\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}\n')
                sys.stdout.write(f'\033[1G\033#3\033[38;2;{r};{g};{b}m{myline}\n\033#4\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}\n')
                sys.stdout.flush()
    sys.stdout.write('\n')



## MAIN #######################################################################################################################################################

def reader_thread(q):
    while True:
        char = sys.stdin.read(1)
        if char:
            q.put(char)
        else:
            q.put(None)
            break

# Create a queue and start the reader thread
q = queue.Queue()
t = threading.Thread(target=reader_thread, args=(q,))
t.start()

line_buffer = ""
in_prompt = False
additional_beginning_ansi = move_decorator
r, g, b = get_random_color()
rgbhex = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)
#r_hex, g_hex, b_hex = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)
#sys.stdout.write(f"rgbhex is {rgbhex}\n")
#sys.stdout.write(f"sys.argv is {sys.argv}\n")
verbose = False
my_mode = DEFAULT_MODE
#sys.stdout.write(f"sys.argv is {sys.argv}\n")
if len(sys.argv) > 1:
    #sys.stdout.write(f"sys.argv[1] is {sys.argv[1]}\n")
    if sys.argv[1] == 'bg' or sys.argv[1] == 'both': my_mode = sys.argv[1]
    for arg in sys.argv[1:]:
        if arg in ["nomoji", "no-emoji"]: nomoji  = True
    for arg in sys.argv[1:]:
        if arg in [    "-v",  "verbose"]: verbose = True
if verbose: sys.stdout.write(f"my_mode is {my_mode}\n")
if verbose: sys.stdout.write(f"nomoji  is {nomoji }\n")

#enable_vt_support()

#DEBUG:print(f"nomoji is {nomoji}")

while t.is_alive() or not q.empty():
#hile True:
    # It's tempting to process things line-by-line, but due to prompts and such, we must process things char-by-char
    try:
        char = q.get(timeout=0.008)                                                                                                     # grab the characters *this* fast!

        if char is None: break                                                                                                          # but not much faster because we're probably coming right back if no chars are in the buffer yet

        if TICK: claire.tick(mode=my_mode)
        line_buffer += char

        if char == '?' and not in_prompt:         #coloring for copy/move prompts, so we can make them blinky & attention-get'y
            in_prompt = True
            bgr, bgg, bgb = get_random_color(bg=True)                                                                                   # Reset for the next line
            r  ,   g,   b = get_random_color()                                                                                          # Reset for the next line
            rgbhex        = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)
            #ys.stdout.write(f'\033[48;2;{bgr};{bgg};{bgb}m\033[38;2;{r};{g};{b}m{additional_beginning_ansi}❓❓   \033[6m{line_buffer} \033[0m') #\033[0m #\033[1C
            if nomoji:
                sys.stdout.write(f'\033[48;2;{bgr};{bgg};{bgb}m\033[38;2;{r};{g};{b}m\033[ q\033]12;{rgbhex}\007{additional_beginning_ansi}'    + f'   \033[6m{line_buffer} \033[0m') #\033[0m #\033[1C
            else:
                sys.stdout.write(f'\033[48;2;{bgr};{bgg};{bgb}m\033[38;2;{r};{g};{b}m\033[ q\033]12;{rgbhex}\007{additional_beginning_ansi}❓❓' + f'   \033[6m{line_buffer} \033[0m') #\033[0m #\033[1C
            #moved to end of loop: sys.stdout.flush()                                                                                   # Flush the output buffer to display the prompt immediately
            line_buffer = ""
        elif in_prompt and char == '\n':          #if we hit end-of-line in a copy/move user prompt, flush the output so the user can see the prompt... promptly
            in_prompt = False
            sys.stdout.write(f'\033[1D{line_buffer.rstrip()}\033[0m\n')
            sys.stdout.flush()
            line_buffer = ""
        elif char == '\n':                        #if we hit end of line NOT in a copy/move user prompt
            if not nomoji:
                if any(substring in line_buffer for substring in FOOTERS): additional_beginning_ansi += "\033[6m"                       # make it blink
            print_line(line_buffer, r, g, b, additional_beginning_ansi)
            line_buffer               = ""                                                                                              # Reset for the next line
            additional_beginning_ansi = ""                                                                                              # Reset for the next line
            r, g, b = get_random_color()                                                                                                # Reset for the next line

            #REFERENCE: function ANSI_CURSOR_CHANGE_COLOR_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`                                 # with "#" in front of color
            #rgbhex = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)                                                                  # Reset for the next line
            #additional_beginning_ansi = f"\033[ q\033]" + "12;" + rgbhex + f"\007"                                                     # Reset for the next line: make cursor same color 🐐

    except queue.Empty:
        if TICK: claire.tick(mode=my_mode)                                                                                                          # color-cycle the default-color text using my library
        try:
            sys.stdout.flush()
        except:
            pass

    try:
        sys.stdout.flush()
    except:
        pass

if TICK: claire.tock()


