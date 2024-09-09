import random
import sys
import re
import io
import threading
import queue
import time
import clairecjs_utils as claire
from colorama import init
init(autoreset=False)




sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


FOOTERS = [
           "files copied", "file copied",
           "files moved" , "file moved" ,
           "dirs copied" , "dir copied" ,
           "dirs moved"  , "dir moved"  ,
          ]

MIN_RGB_VALUE_FG = 64; MAX_RGB_VALUE_FG = 255
MIN_RGB_VALUE_BG = 16; MAX_RGB_VALUE_BG = 64

EMOJIS_SUMMARY = '✔️ '
EMOJIS_COPY    = f'⭢︋📂' #'-->📂 '

def enable_vt_support():
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

def get_random_color(bg=False):
    if bg: min_rgb_value = MIN_RGB_VALUE_BG; max_rgb_value = MAX_RGB_VALUE_BG
    else:  min_rgb_value = MIN_RGB_VALUE_FG; max_rgb_value = MAX_RGB_VALUE_FG
    return random.randint(min_rgb_value,max_rgb_value), \
           random.randint(min_rgb_value,max_rgb_value), \
           random.randint(min_rgb_value,max_rgb_value)

def enclose_numbers(line): return re.sub(r'(\d+)', r'\033[21m\1\033[24m', line)                                             # ansi-stylize numbers - italics + double-underline

def print_line_OLD_beforesummarysplits(line_buffer, r, g, b, additional_beginning_ansi=""):
    double  = False                                                                                                         # double height or not?
    summary = False                                                                                                         # copy/mv summary line?
    if any(substring in line_buffer for substring in FOOTERS):
        line_buffer = enclose_numbers(line_buffer)
        double      = True
        summary     = True
    #line = f'\033[93m'                                                                                                      # i liked my arrow yellow
    line = ''
    if   any(substring in line_buffer for substring in ["Y/N/A/R"]):     line += f'❓❓ '                                     # emojis at beginning of prompty  lines
    if   any(substring in line_buffer for substring in ["=>","->"]):     line += EMOJIS_COPY                                 # emojis at beginning of filename lines
    elif any(substring in line_buffer for substring in ["TCC: (Sys)"]):
        double = True;                                                   line += f'🛑🛑\033[6m\033[3m\033[4m\033[7m'        # emojis at beginning of error    lines during copying
    elif any(substring in line_buffer for substring in ["Deleting "]):   line += f'﻿👻⛔'

    elif summary:                                                        line += EMOJIS_SUMMARY                             # emojis at beginning of summary  lines of how many files copied
    else:                                                                line += f'  '                                      # normal lines get prefixed with this
    line += f'\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{line_buffer.rstrip()}\033[0m\n'                             # print line in our random-RGB color
    line = line.replace("=>>","↪️") #.replace("=>","⭢︋")
    if not double: sys.stdout.write(line)                                                                                   # normal height line
    else:          sys.stdout.write(f'\033#3{line}\033#4{line}')                                                            # double height line


def print_line(line_buffer, r, g, b, additional_beginning_ansi=""):

    double  = False
    summary = False

    if any(substring in line_buffer for substring in FOOTERS):
        line_buffer = enclose_numbers(line_buffer)
        double      = True
        summary     = True

    line = ''
    if   any(substring in line_buffer for substring in ["Y/N/A/R)"]): line += f'❓❓ '
    elif any(substring in line_buffer for substring in ["=>","->"]): line += EMOJIS_COPY
    elif any(substring in line_buffer for substring in ["TCC: (Sys)"]):
        double = True; line += f'🛑🛑\033[6m\033[3m\033[4m\033[7m'
    elif any(substring in line_buffer for substring in ["Deleting "]): line += f'👻⛔'
    elif summary: line += EMOJIS_SUMMARY
    else: line += f'  '

    # Handle transformation for FOOTERS
    if summary:
        pattern = "|".join(re.escape(footer) for footer in FOOTERS)
        segments = re.split(pattern, line_buffer)

        # Remove empty segments and strip spaces from the rest
        segments = [seg.strip() for seg in segments if seg.strip()]

        lines = []
        for segment in segments:
            footer_match = re.search(pattern, line_buffer)
            if footer_match:
                footer = footer_match.group(0)
                lines.append(f"{segment} {footer}")
                # Update line_buffer to remove the footer we just matched
                line_buffer = line_buffer.replace(footer, "", 1).strip()

        line_buffer = f'\n{EMOJIS_SUMMARY}'.join(lines)

    line += f'\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{line_buffer.rstrip()}\033[0m\n'
    line = line.replace("=>>", "↪️")


    lines_to_print = line.split('\n')
    i = 0
    for myline in lines_to_print:
        #print(f"myline is ((({myline})))")
        if myline != '\n' and myline != '':
            #i += 1
            #sys.stdout.write(f'{i}"LINE={line}"')
            if not double:
                sys.stdout.write(f'{myline}')
            else:
                enable_vt_support()                 #suggestion from https://github.com/microsoft/terminal/issues/15838
                sys.stdout.write(f'\033#3\033[38;2;{r};{g};{b}m{myline}\n\033#4\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}\n')
    sys.stdout.write('\n')




################################################################################################################################################################

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
additional_beginning_ansi = ""
r, g, b = get_random_color()

while t.is_alive() or not q.empty():
#hile True:                                                                                                                         # It's tempting to process things line-by-line, but due to prompts and such, we must process things char-by-char
    try:
        char = q.get(timeout=0.008)
        if char is None: break
        claire.tick(mode="fg")
        line_buffer += char

        if char == '?' and not in_prompt:
            in_prompt = True
            bgr, bgg, bgb = get_random_color(bg=True)                                                                                   # Reset for the next line
            r  ,   g,   b = get_random_color()                                                                                          # Reset for the next line
            #ys.stdout.write(f'\033[38;2;{r};{g};{b}m{additional_beginning_ansi}❓❓   \033[6m{line_buffer}\033[0m ') #\033[1C
            #ys.stdout.write(f'\033[48;2;{r};{g};{b}m{additional_beginning_ansi}❓❓   \033[6m{line_buffer}\033[0m ') #\033[1C
            sys.stdout.write(f'\033[48;2;{bgr};{bgg};{bgb}m\033[38;2;{r};{g};{b}m{additional_beginning_ansi}❓❓   \033[6m{line_buffer} \033[0m') #\033[0m #\033[1C
            #moved to end of loop: sys.stdout.flush()                                                                                   # Flush the output buffer to display the prompt immediately
            line_buffer = ""
        elif in_prompt and char == '\n':
            in_prompt = False
            sys.stdout.write(f'\033[1D{line_buffer.rstrip()}\033[0m\n')
            sys.stdout.flush()
            line_buffer = ""
        elif char == '\n':
            if any(substring in line_buffer for substring in FOOTERS): additional_beginning_ansi += "\033[6m"                           # make it blink
            print_line(line_buffer, r, g, b, additional_beginning_ansi)
            line_buffer               = ""                                                                                              # Reset for the next line
            additional_beginning_ansi = ""                                                                                              # Reset for the next line
            r, g, b = get_random_color()                                                                                                # Reset for the next line


    except queue.Empty:
        claire.tick(mode="fg")
        sys.stdout.flush()

    sys.stdout.flush()
claire.tock()
