"""
        COPY/MOVE postprocessor

        USAGE:  {command} | copy-move-post
        USAGE:  {command} | copy-move-post nomoji ————— doesn't add the emoji prefixes to lines
        USAGE:  {command} | copy-move-post WhisperAI —— post-process WhisperAI transcription

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
try:
    import clairecjs_utils as claire
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path: sys.path.insert(0, script_dir)
    try:
        import clairecjs_utils as claire
    except ImportError:
        raise ImportError("Cannot find 'clairecjs_utils' module in site-packages or the local directory.")

from colorama import init
init(autoreset=False)

SPECIAL_TREATMENT_FOR_QUESTION_LINES = True       # Set to False to suppress special treatment of lines with '?'
COLOR_QUESTION_BACKGROUNDS           = True       #whether to highlight lines with "?" with a random background character and other stuff —— originally developed for Y/N/R/A-type prompts when copying files, but annoying in other situations

DEFAULT_COLOR_CYCLE_MODE   = "fg"                 #whether to color-cycle foreground ("fg"), background ("bg"), or both ("both").
EMOJIS_COPY                = '⭢︋📂 '
EMOJIS_PROMPT              = '❓❓ '
EMOJIS_DELETE              = '👻⛔'               #"ghost" + "no" = dead file? no more file? File is now a ghost?
EMOJIS_SUMMARY             = '✔️ '
EMOJIS_ERROR               = '🛑🛑'
nomoji                     = False                #set to True to disable [some] emoji decoration of lines
whisper_ai                 = False                #set to True to run in WhisperAI mode
#Note to self: either maintain a simultaneous update of these 4 values in set-colors.bat or create env-var overrides:
MIN_RGB_VALUE_FG = 88;   MIN_RGB_VALUE_BG = 12                                                                  #\__ range of random values we
MAX_RGB_VALUE_FG = 255;  MAX_RGB_VALUE_BG = 40                                                                  #/   choose random colors from

# ANSI codes
BOLD_ON              = "\033[1m"
BOLD_OFF             = "\033[22m"
BIG_TOP              = "\033#3"
BIG_BOT              = "\033#4"
BIG_OFF              = "\033#0"
BLINK_ON             = "\033[6m"
BLINK_OFF            = "\033[25m"
FAINT_ON             = "\033[2m"
FAINT_OFF            = "\033[22m"
COLOR_GREY           = "\033[90m"
ANSI_RESET           = "\033[39m\033[49m\033[0m"
ITALICS_ON           = "\033[3m"
ITALICS_OFF          = "\033[23m"
REVERSE_ON           = "\033[7m"
REVERSE_OFF          = "\033[27m"
CURSOR_RESET         = "\033[ q"
UNDERLINE_ON         = "\033[4m"
UNDERLINE_OFF        = "\033[24m"
MOVE_TO_COL_1        = "\033[1G"
DOUBLE_UNDERLINE_OFF = "\033[24m"
DOUBLE_UNDERLINE_ON  = "\033[21m"

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
           "Standalone Faster-Whisper-XXL r192.3.4 running on: CUDA"
          ]
file_removals  = ["\\recycled\\","\\recycler\\","Removing ","Deleting "]                                    #values that indicate a file deletion/removal
sys.stdout     = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')                    #utf-8 fix
move_decorator_from_environment_variable = os.environ.get('move_decorator_from_environment_variable', '')   #fetch user-specified decorator (if any)

if os.environ.get('no_tick') == "1": TICK = False
else                               : TICK = True
#print(f"tick is {TICK} .. {os.environ.get('no_tick')}")

if os.environ.get('no_double_lines',0) == "1": DOUBLE_LINES_ENABLED = False
else                                         : DOUBLE_LINES_ENABLED = True                                  #DEBUG: print(f"DOUBLE_LINES_ENABLED={DOUBLE_LINES_ENABLED}")

#vars
current_processing_segment = 0
spacer = ""





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
    else  : return                                           rand_r, rand_g, rand_b

def enclose_numbers(line): return re.sub(r'(\d+)', DOUBLE_UNDERLINE_ON + r'\1' + DOUBLE_UNDERLINE_OFF, line)                                 #ansi-stylize numbers - italics + we choose double-underline in this example



def print_line(line_buffer, r, g, b, additional_beginning_ansi=""):
    #sys.stderr.write(f"DEBUG: called print_line({line_buffer}, {r}, {g}, {b}, {additional_beginning_ansi})\n")
    
    original_line_buffer = line_buffer
    global current_processing_segment
    color_change_ansi = f'\033[38;2;{r};{g};{b}m'
    our_ansi_reset = ANSI_RESET + move_decorator_from_environment_variable

    double  = False
    summary = False

    if whisper_ai:
        additional_beginning_ansi=""         #kludging a situation
    else:
        if any(substring in line_buffer for substring in FOOTERS):                                                  #identify if we're in a footer/summary line
            line_buffer = enclose_numbers(line_buffer)
            double      = True
            summary     = True

    line = ""
    if nomoji is True:                                                                                          # Start the line off
        line = ""
    else:
        line = move_decorator_from_environment_variable                                                                                                      #decorate with environment-var-supplied decorator if applicable
        if   any(substring in line_buffer for substring in file_removals ): line += EMOJIS_DELETE                                  #treatment for file deletion lines
        elif any(substring in line_buffer for substring in ["Y/N/A/R)"]  ):
            line += EMOJIS_PROMPT                                  #treatment for  user prompt  lines
            #print(f"[line buffer={line_buffer}")
        elif any(substring in line_buffer for substring in ["=>","->"]   ): line += EMOJIS_COPY                                    #treatment for   file copy   lines
        elif any(substring in line_buffer for substring in ["TCC: (Sys)"]):                                                        #treatment for error message lines
            double = True;                                                  line += EMOJIS_ERROR + f'{BLINK_ON}{ITALICS_ON}{UNDERLINE_ON}{REVERSE_ON}'
        elif summary:                                                       line += EMOJIS_SUMMARY                                 #treatment for summary lines
        else:                                                               line += f'  '                                          #TODO figure out why this line is here

    original_line  = original_line_buffer.rstrip()
    original_line2 =          line_buffer.rstrip()

    if not whisper_ai:
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

    #line += f'{color_change_ansi}{additional_beginning_ansi}{original_line}{ANSI_RESET}\n'                       #make line be our random color
    line = f'{line}{color_change_ansi}{additional_beginning_ansi}{original_line}{ANSI_RESET}\n'                       #make line be our random color

    # postprocess line:
    if not nomoji:
        line = line.replace(' => ' , f'{our_ansi_reset} => {color_change_ansi}')                                  #\
        line = line.replace(' -> ' , f'{our_ansi_reset} -> {color_change_ansi}')                                  # \      Keep all these characters in the default font color, which
        line = line.replace( '=>>' , f'{our_ansi_reset}↪️{   color_change_ansi}')  #this arrow looks better here   #  \     is the one succeptible to the color-cycling that we use
        line = line.replace(   '.' , f'{our_ansi_reset}.{   color_change_ansi}')                                  #   >---
        line = line.replace(   ':' , f'{our_ansi_reset}:{   color_change_ansi}')                                  #  /
        line = line.replace( ' - ' , f'{our_ansi_reset} - { color_change_ansi}')                                  # /
        line = line.replace(  '\\' , f'{our_ansi_reset}\\{  color_change_ansi}')                                  #/

    if whisper_ai:
            #DEBUG: if additional_beginning_ansi: print(f"additional beginning ansi={additional_beginning_ansi.lstrip(1)}")         #
            spacer = "                "
            spacer_less = "           "
            if verbose: print(f"orig_line is [orig={original_line}][line={line}]")
            #if "[ctranslate2]" in line: just won't work!
            if "[ctranslate2]" in original_line:
                #ine = FAINT_ON + COLOR_GREY + spacer + "⭐" + COLOR_GREY + line.replace("[",f"{COLOR_GREY}[") + FAINT_OFF
                #ine =                         spacer + COLOR_GREY + "⭐" + line.replace("[",f"{COLOR_GREY}[") + FAINT_OFF
                line =                         spacer + FAINT_ON + f"{COLOR_GREY}⭐" + line + FAINT_OFF
                line = re.sub(r'(\[[23]\d{3}.[01]\d.[0-3]\d )', f'{COLOR_GREY}\1', line)
                #DEBUG: print ("ctranslate line found!")#
            line = re.sub(r'(\[[23]\d{3}.[01]\d.[0-3]\d )', f'{COLOR_GREY}\1', line)    #todo experimental: just do this, won't affecti f there isn't a match
            if  original_line.startswith("Standalone Faster-Whisper-XXL "):
                line = line.replace("Standalone Faster-Whisper-XXL", "\n🚀 Standalone Faster-Whisper-XXL 🚀").replace(" running on:",":")
            if  original_line.startswith("Starting work on: "):
                line = line.replace("Starting work on: ",f"Starting work on: {ITALICS_ON}")
            if  original_line.startswith("Transcription speed: "):
                line = line.replace("Transcription speed: ",f"{FAINT_ON}{COLOR_GREY}⭐Transcription speed: {ITALICS_ON}")
            if  original_line.startswith("Subtitles are written to '"):
                line = line.replace("Subtitles are written to '",f"✅ Subtitles are written to '{ITALICS_ON}{BOLD_ON}").replace("' directory.",f"{BOLD_OFF}{ITALICS_OFF}' directory. ✅")
            if  original_line.startswith("  Processing segment at "):
                current_processing_segment += 1
                if current_processing_segment > 1: print("")
                line = line.replace(    f"  Processing segment at ",f"{COLOR_GREY}{FAINT_ON}{spacer_less}♬ Processing segment at: {ITALICS_ON}" ) + ITALICS_OFF + FAINT_OFF
            if  original_line.startswith("* Compression ratio threshold is not"):
                line = line.replace(    f"* Compression ratio threshold is not",f"{spacer}{FAINT_ON}{COLOR_GREY}⭐ Compression ratio threshold is not") + FAINT_OFF
            if  original_line.startswith("* Log probability threshold is not"):
                line = line.replace(    f"* Log probability threshold is not"  ,f"{spacer}{FAINT_ON}{COLOR_GREY}⭐ Log probability threshold is not"  ) + FAINT_OFF
            #bad syntax:                              ["Reset prompt. prompt_reset_on_temperature threshold is met", "Reset prompt. prompt_reset_on_no_end is triggered"] in line:
            if any(substring in line for substring in ["Reset prompt. prompt_reset_on_temperature threshold is met", "Reset prompt. prompt_reset_on_no_end is triggered"]):
                line = line.replace("* Reset prompt. ",COLOR_GREY + FAINT_ON + spacer + "* Reset prompt. ") + FAINT_OFF
            if " --> " in line: #🐐 possibly restrict this to if whisper_ai
                line = f"🌟 {BLINK_ON}" + line.replace("]  ",f"]{BLINK_OFF}{ANSI_RESET}{ITALICS_ON}  ")

    lines_to_print = line.split('\n')                                                                         #there really shouldn't be a \n in our line, but things happen
    i = 0
    for myline in lines_to_print:                                                                             #print our line, but do it double-height if we're supposed to
        if myline != '\n' and myline != '':
            if not double or not DOUBLE_LINES_ENABLED:
                sys.stdout.write(f'{myline}')
            else:
                enable_vt_support()                                                                            #suggestion from https://github.com/microsoft/terminal/issues/15838
                #ys.stdout.write(f'{MOVE_TO_COL_1}')   #20240324: adding '{MOVE_TO_COL_1}' as ??bugfix?? for ansi creeping out due to TCC error and mis-aligning our double-height lines - prepend the ansi code to move to column 1 first, prior to printing our line
                #ys.stdout.write(f'{MOVE_TO_COL_1}{BIG_TOP}\033[38;2;{r};{g};{b}m{myline}\n{BIG_BOT}\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}\n')
                sys.stdout.write(f'{MOVE_TO_COL_1}{BIG_TOP}\033[38;2;{r};{g};{b}m{myline}\n')
                sys.stdout.write(               f'{BIG_BOT}\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}\n')
                sys.stdout.flush()
    sys.stdout.write('\n')


def reader_thread(q):
    global BLINK_ON
    while True:
        char = sys.stdin.read(1)
        if char:
            q.put(char)
        else:
            q.put(None)
            break

## MAIN #######################################################################################################################################################

# Create a queue and start the reader thread
q = queue.Queue()
t = threading.Thread(target=reader_thread, args=(q,))
t.start()

line_buffer               = ""
in_prompt                 = False               #used to determine if the script is currently processing a "propmt" (a line containing ?) in order to highhlight when copy commands ask us something in a window we aren't paying attention to. It's a 4-monitors-totallying-29-sq-ft problem...
additional_beginning_ansi = move_decorator_from_environment_variable

# random color hex testing
#r, g, b = get_random_color()
#rgbhex_with_pound_sign = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)
##r_hex, g_hex, b_hex = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)
##sys.stdout.write(f"rgbhex_with_pound_sign is {rgbhex_with_pound_sign}\n")
##sys.stdout.write(f"sys.argv is {sys.argv}\n")

# initialize various variables
verbose                       = False
whisper_ai                    = False
current_processing_segment    = 0
my_mode                       = DEFAULT_COLOR_CYCLE_MODE
background_color_switch_maybe = ""
r                             = ""
g                             = ""
b                             = ""


#sys.stdout.write(f"sys.argv is {sys.argv}\n")
if len(sys.argv) > 1:
    #sys.stdout.write(f"sys.argv[1] is {sys.argv[1]}\n")
    if sys.argv[1] == 'bg' or sys.argv[1] == 'both': my_mode = sys.argv[1]
    for arg in sys.argv[1:]:
        if arg.lower() in ["n", "-n", "--n", "nomoji", "-nomoji", "--nomoji", "no-emoji", "-no-emoji", "--no-emoji"]: nomoji  = True
    for arg in sys.argv[1:]:
        if arg.lower() in ["v", "-v", "--v", "verbose", "-verbose", "--verbose"]: verbose = True
    for arg in sys.argv[1:]:
        if arg.lower() in ["w", "-w", "--w", "whisperai", "-whisperai", "--whisperai", "whisper", "-whisper", "--whisper"]:
            whisper_ai = True
            nomoji     = True

if whisper_ai:
    import re
    COLOR_QUESTION_BACKGROUNDS = False


if verbose:
    sys.stdout.write(f"    * verbose    is {verbose                   }\n")
    sys.stdout.write(f"    * my_mode    is {my_mode                   }\n")
    sys.stdout.write(f"    * nomoji     is {nomoji                    }\n")
    sys.stdout.write(f"    * whisper_ai is {whisper_ai                }\n")
    sys.stdout.write(f"    * color ? bg is {COLOR_QUESTION_BACKGROUNDS}\n")
#enable_vt_support()

#whether to blink text or not
blink_maybe = BLINK_ON;                          #failed attempt to solve blinking questions in Whisper mode
if nomoji or whisper_ai: BLINK_ON=""             #failed attempt to solve blinking questions in Whisper mode

char_read_time_out=0.008;                        #most of the time, read characters as fast as we can! testing gave 0.008
#f whisper_ai: char_read_time_out=0.2            #go slower when postprocessing whisper transcription because there's hardly any screen output, and it's not interactive, so speed is less important, and we want to keep the CPU as free as possible. Even though the claire.tick() function has adaptive throttling based on how often it's called, tested to ensure we don't hammer our CPU harder for the pretty colors than for our actual calculations, it's still more efficient to not call it aso ften.
if whisper_ai: 
    char_read_time_out=0.064                     #go slower when postprocessing whisper transcription because there's hardly any screen output, and it's not interactive, so speed is less important, and we want to keep the CPU as free as possible. Even though the claire.tick() function has adaptive throttling based on how often it's called, tested to ensure we don't hammer our CPU harder for the pretty colors than for our actual calculations, it's still more efficient to not call it aso ften.
    SPECIAL_TREATMENT_FOR_QUESTION_LINES = False # Set to False to suppress special treatment of lines with '?'




while t.is_alive() or not q.empty():
#hile True:
    # It's tempting to process things line-by-line, but due to prompts and such, we must process things char-by-char
    try:
        char = q.get(timeout=char_read_time_out)                                                                                                     # grab the characters *this* fast!
        if char is None: break                                                                                                          # but not much faster because we're probably coming right back if no chars are in the buffer yet
        line_buffer += char

        if TICK: claire.tick(mode=my_mode)

        if (char == '?' and not in_prompt) or (char == '\n' and not in_prompt):
            r ,  g,  b = get_random_color()                                                      # Generate random colors for the branches below that need them [a refactoring]

        if char == '?' and not in_prompt and SPECIAL_TREATMENT_FOR_QUESTION_LINES:               #coloring for copy/move prompts, so we can make them blinky & attention-get'y
            in_prompt = True

            #color switching logic: background colors:
            if not whisper_ai:
                if COLOR_QUESTION_BACKGROUNDS:                                          # (for file copies, but not for other things)
                    bgr, bgg, bgb = get_random_color(bg=True)                           # Reset for the next line
                    background_color_switch_maybe = f"\033[48;2;{bgr};{bgg};{bgb}"
                else:
                    background_color_switch_maybe = ""

            #color switching logic: foreground colors:
            #r ,  g,  b = get_random_color()                                                      # Reset for the next line
            foreground_color_switch = f"\033[38;2;{r};{g};{b}m"

            #color switching logic: cursor: Ansi code for changing cursor color to a hex rgb is: [ESCAPE][ q[ESCAPE]]12;#FF00ff[BELL]
            rgbhex_with_pound_sign = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)
            #ys.stdout.write(f'\033[48;2;{bgr};{bgg};{bgb}m\033[38;2;{r};{g};{b}m{additional_beginning_ansi}❓❓   {BLINK_ON}{line_buffer} {ANSI_RESET}') #\033[0m
            cursor_color_switch_by_hex = f"{CURSOR_RESET}\033" + f"]12;{rgbhex_with_pound_sign}\007"              #*[ q*12;#FFFFFF{beep}

            #color switching logic: blinking text — needs to happen in this loop repeatedly, not just once:
            blink_maybe = BLINK_ON;
            if nomoji: BLINK_ON=""

            #spacer logic
            line_spacer = ""
            if not whisper_ai: line_spacer = "   "

            ##### ACTUALLY PRINT OUT THE LINE: 
            if   any(substring in line_buffer for substring in file_removals): line_spacer = EMOJIS_DELETE                                 #treatment for file deletion lines
            elif any(substring in line_buffer for substring in ["Y/N/A/R)"," (Y/N)"] ): line_spacer = EMOJIS_PROMPT                                  #treatment for  user prompt  lines
            elif any(substring in line_buffer for substring in ["=>","->"]  ): line_spacer = EMOJIS_COPY                                    #treatment for   file copy   lines

            sys.stdout.write(f'{background_color_switch_maybe}{foreground_color_switch}{CURSOR_RESET}{cursor_color_switch_by_hex}{additional_beginning_ansi}'    + f'{line_spacer}{blink_maybe}{line_buffer} {ANSI_RESET}') #\033[0m #\033[1C
            #moved to end of loop: sys.stdout.flush()                                                                                   # Flush the output buffer to display the prompt immediately
            sys.stdout.flush()                    #added 2024/10/31 and unsure of necesity
            line_buffer = ""
        elif in_prompt and char == '\n':          #if we hit end-of-line in a copy/move user prompt, flush the output so the user can see the prompt... promptly
            in_prompt = False
            #ys.stdout.write(f'\033[1D{line_buffer.rstrip()}[0m\n')
            sys.stdout.write(f'\033[1D{line_buffer.rstrip()}{ANSI_RESET}\n')
            sys.stdout.flush()
            line_buffer = ""
        elif char == '\n':                        #if we hit end of line NOT in a copy/move user prompt
            if not nomoji:
                if any(substring in line_buffer for substring in FOOTERS): additional_beginning_ansi += BLINK_ON                        # make it blink
            print_line(line_buffer, r, g, b, additional_beginning_ansi)
            line_buffer               = ""                                                                                              # Reset for the next line
            additional_beginning_ansi = ""                                                                                              # Reset for the next line
            #r, g, b = get_random_color()                                                                                               # Reset for the next line

            #REFERENCE: function ANSI_CURSOR_CHANGE_COLOR_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`                                 # with "#" in front of color
            #rgbhex_with_pound_sign = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)                                                  # Reset for the next line
            #additional_beginning_ansi = f"{CURSOR_RESET}\033]" + "12;" + rgbhex_with_pound_sign + f"\007"                              # Reset for the next line: make cursor same color

    except queue.Empty:
        if TICK: claire.tick(mode=my_mode)                                                                                              # color-cycle the default-color text using my library
        try:
            sys.stdout.flush()
        except:
            pass

    #final flush just in case ... 🐐 might not be necessary...
    try:
        sys.stdout.flush()
    except:
        pass


# Flush any remaining content in line_buffer after the loop
# After exiting the main loop, print any remaining line content
if line_buffer.strip():  # Ensure any remaining line without \n is printed
    print_line(line_buffer, r, g, b, additional_beginning_ansi)
    
    
# Reset the ansi? #kind of equivalent of: if TICK: claire.tock()
#sys.stdout.write(ANSI_RESET + "\n")  # Reset any leftover ANSI styles

# Final flush?
#sys.stdout.flush()




