"""
        COPY/MOVE postprocessor

                    * makes each line a random color (to increase visual accessibility to boundaries between filenames)

                    * color cycles delimiter characters (to ease anxiety that things are hung)

                    * Inserts relevant emoji at the beginning of the line (to decrease visual processing energy)

                    * blinks and double-heightens errors (to decrease required attention level)

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


EMOJIS_COPY    = '⭢︋📂'
EMOJIS_PROMPT  = '❓❓ '
EMOJIS_DELETE  = '👻⛔'
EMOJIS_SUMMARY = '✔️ '
EMOJIS_ERROR   = '🛑🛑'

MIN_RGB_VALUE_FG = 88;   MIN_RGB_VALUE_BG = 12                                                                  #\__ range of random values we
MAX_RGB_VALUE_FG = 255;  MAX_RGB_VALUE_BG = 40                                                                  #/   choose random colors from

FOOTERS = [                                                                                                     #values that indicate a copy/move summary line,
           "files copied"         , "file copied",                                                              #which we like to identify for special treatment
           "files moved"          , "file moved" ,
           "dirs copied"          , "dir copied" ,
           "dirs moved"           , "dir moved"  ,
           "files would be copied", "file would be copied",
           "files would be moved" , "file would be moved" ,
           "dirs would be copied" , "dir would be copied" ,
           "dirs would be moved"  , "dir would be moved"  ,
          ]
file_removals = ["\\recycled\\","\\recycler\\","Removing ","Deleting "]                                         #values that indicate a file deletion/removal


sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')                            #utf-8 fix

move_decorator = os.environ.get('move_decorator', '')                                                           #fetch user-specified decorator (if any)

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

def get_random_color(bg=False):                                                                                 #return random rgb values within our confifured threshold
    if bg: min_rgb_value = MIN_RGB_VALUE_BG; max_rgb_value = MAX_RGB_VALUE_BG
    else:  min_rgb_value = MIN_RGB_VALUE_FG; max_rgb_value = MAX_RGB_VALUE_FG
    return random.randint(min_rgb_value,max_rgb_value), \
           random.randint(min_rgb_value,max_rgb_value), \
           random.randint(min_rgb_value,max_rgb_value)

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

    line = move_decorator                                                                                                      #decorate with environment-var-supplied ecorator if applicable
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

    line = line.replace(' => ' , f'{ansi_reset} => {color_change_ansi}')                                      #\
    line = line.replace(' -> ' , f'{ansi_reset} -> {color_change_ansi}')                                      # \      Keep all these characters in the default font color, which
    line = line.replace( '=>>' , f'{ansi_reset}↪️{   color_change_ansi}')  #this arrow looks better here       #  \     is the one succeptible to the color-cycling that we use
    line = line.replace(   '.' , f'{ansi_reset}.{   color_change_ansi}')                                      #   >---
    line = line.replace(   ':' , f'{ansi_reset}:{   color_change_ansi}')                                      #  /
    line = line.replace( ' - ' , f'{ansi_reset} - { color_change_ansi}')                                      # /
    line = line.replace(  '\\' , f'{ansi_reset}\\{  color_change_ansi}')                                      #/

    lines_to_print = line.split('\n')                                                                         #there really shouldn't be a \n in our line, but things happen
    i = 0
    for myline in lines_to_print:                                                                             #print our line, but do it double-height if we're supposed to
        if myline != '\n' and myline != '':
            if not double:
                sys.stdout.write(f'{myline}')
            else:
                enable_vt_support()                                                                            #suggestion from https://github.com/microsoft/terminal/issues/15838
                sys.stdout.write(f'\033#3\033[38;2;{r};{g};{b}m{myline}\n\033#4\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}\n')
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

while t.is_alive() or not q.empty():
#hile True:
    # It's tempting to process things line-by-line, but due to prompts and such, we must process things char-by-char
    try:
        char = q.get(timeout=0.008)
        if char is None: break
        claire.tick(mode="fg")
        line_buffer += char

        if char == '?' and not in_prompt:         #coloring for copy/move prompts, so we can make them blinky & attention-get'y
            in_prompt = True
            bgr, bgg, bgb = get_random_color(bg=True)                                                                                   # Reset for the next line
            r  ,   g,   b = get_random_color()                                                                                          # Reset for the next line
            sys.stdout.write(f'\033[48;2;{bgr};{bgg};{bgb}m\033[38;2;{r};{g};{b}m{additional_beginning_ansi}❓❓   \033[6m{line_buffer} \033[0m') #\033[0m #\033[1C
            #moved to end of loop: sys.stdout.flush()                                                                                   # Flush the output buffer to display the prompt immediately
            line_buffer = ""
        elif in_prompt and char == '\n':          #if we hit end-of-line in a copy/move user prompt, flush the output so the user can see the prompt... promptly
            in_prompt = False
            sys.stdout.write(f'\033[1D{line_buffer.rstrip()}\033[0m\n')
            sys.stdout.flush()
            line_buffer = ""
        elif char == '\n':                        #if we hit end of line NOT in a copy/move user prompt
            if any(substring in line_buffer for substring in FOOTERS): additional_beginning_ansi += "\033[6m"                           # make it blink
            print_line(line_buffer, r, g, b, additional_beginning_ansi)
            line_buffer               = ""                                                                                              # Reset for the next line
            additional_beginning_ansi = ""                                                                                              # Reset for the next line
            r, g, b = get_random_color()                                                                                                # Reset for the next line

    except queue.Empty:
        claire.tick(mode="fg")                                                                                                          # color-cycle the default-color text using my library
        sys.stdout.flush()

    sys.stdout.flush()
claire.tock()
