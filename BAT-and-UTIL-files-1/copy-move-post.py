"""
        COPY/MOVE postprocessor

        USAGE:  {command} | copy-move-post
        USAGE:  {command} | copy-move-post -n or “nomoji” ————— doesn't add the emoji prefixes to lines
        USAGE:  {command} | copy-move-post -tFilename.txt ————— save output to Filename.txt —— saving the trouble of ever using the tee command
        USAGE:  {command} | copy-move-post -v or “verbose” ———— verbose mode
        USAGE:  {command} | copy-move-post -w or “WhisperAI” —— post-process WhisperAI transcription

        [Note: Use “|:u8” instead of “|” in TCC, for best unicode/emoji support]

        POSSIBLE FUTURE MODES:

        USAGE:  {command} |copy-move-post -c123 —————————————— assume screen console width of 123

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
from io import StringIO
import threading
import queue
import time
import os
import struct
import ctypes
import logging

import signal
signal.signal(signal.SIGINT , lambda *args: (show_cursor(), enable_vt_support(), sys.exit(0)))
signal.signal(signal.SIGTERM, lambda *args: (show_cursor(), enable_vt_support(), sys.exit(0)))

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


#————————————————————————————————————————————————————————————————————
#screen_columns, screen_rows = os.get_terminal_size()
import shutil
try:
    screen_columns, screen_rows = shutil.get_terminal_size()
except Exception:
    print(f"Error: {e}")
#————————————————————————————————————————————————————————————————————
#────────────────────────────────────────────────────────────────────
SPECIAL_TREATMENT_FOR_QUESTION_LINES = True       # Set to False to suppress special treatment of lines with '?'
COLOR_QUESTION_BACKGROUNDS           = True       #whether to highlight lines with "?" with a random background character and other stuff —— originally developed for Y/N/R/A-type prompts when copying files, but annoying in other situations

DEFAULT_COLOR_CYCLE_MODE   = "fg"                 #whether to color-cycle foreground ("fg"), background ("bg"), or both ("both").
EMOJIS_COPY                = '⭢︋📂 '
EMOJIS_PROMPT              = '❓❓ '
#MOJIS_DELETE              = '👻⛔'               #"ghost" + "no" = dead file? no more file? File is now a ghost?
EMOJIS_DELETE              = '👻⛔ '              #"ghost" + "no" = dead file? no more file? File is now a ghost?
EMOJIS_SUMMARY             = '✔️ '
EMOJIS_ERROR               = '🛑🛑'
tee                        = False                #set to True to disable [some] emoji decoration of lines
nomoji                     = False                #set to True to disable [some] emoji decoration of lines
whisper_ai                 = False                #set to True to run in WhisperAI mode
whisper_decorator_title    = "🚀🚀🚀"             #decorator for Whisper title
#Note to self: either maintain a simultaneous update of these 4 values in set-colors.bat or create env-var overrides:
MIN_RGB_VALUE_FG =  88;  MIN_RGB_VALUE_BG = 12    #\__ range of random values we
MAX_RGB_VALUE_FG = 255;  MAX_RGB_VALUE_BG = 40    #/   choose random colors from


# ANSI codes
CURSOR_RESET         = "\033[ q"
ANSI_RESET           = "\033[39m\033[49m\033[0m"
ANSI_COLORDEF_RESET  = "]10;rgb:c0/c0/c0\\]11;rgb:00/00/00\\"
#NSI_RESET_FULL      = "\033[39m\033[49m\033[0m\033[?25h\033[ q\033]12;#\033]10;rgb:c0/c0/c0\033\\\033]11;rgb:00/00/01\033\\\033]10;rgb:c0/c0/c1\033\\"             #this got too unmangeable
ANSI_RESET_FULL      = CURSOR_RESET + ANSI_RESET + ANSI_COLORDEF_RESET         #more thorough version
BOLD_ON              = "\033[1m"
BOLD_OFF             = "\033[22m"
BIG_TOP              = "\033#3"
BIG_BOT              = "\033#4"
BIG_OFF              = "\033#0"
BLINK_ON             = "\033[6m"
BLINK_OFF            = "\033[25m"
COLOR_BRIGHT_GREEN   = "\033[92m"
COLOR_GREY           = "\033[90m"
COLOR_GREEN          = "\033[32m"
CONCEAL_ON           = "\033[8m"
CONCEAL_OFF          = "\033[28m"
CR                   = "\015"
CURSOR_INVISIBLE     = "\033[?25l"
CURSOR_VISIBLE       = "\033[?25h"
DOUBLE_UNDERLINE_OFF = "\033[24m"
DOUBLE_UNDERLINE_ON  = "\033[21m"
ERASE_TO_EOL         = "\033[0K"
FAINT_ON             = "\033[2m"
FAINT_OFF            = "\033[22m"
ITALICS_ON           = "\033[3m"
ITALICS_OFF          = "\033[23m"
#OVE_TO_COL_1        = "\033[1G"
MOVE_TO_COL_1        = "\r"
MOVE_TO_COL_1        = "\033[1G"
MOVE_UP_1            = "\033M"
REVERSE_ON           = "\033[7m"
REVERSE_OFF          = "\033[27m"
UNDERLINE_ON         = "\033[4m"
UNDERLINE_OFF        = "\033[24m"

PRENEWLINE = ERASE_TO_EOL


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
           "Standalone Faster-Whisper-XXL r"
          ]

file_removals  = ["\\recycled\\","\\recycler\\","Removing ","Deleting "]                                    #values that indicate a file deletion/removal
#sys.stdout     = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')                    #utf-8 fix
move_decorator_from_environment_variable = os.environ.get('move_decorator_from_environment_variable', '')   #fetch user-specified decorator (if any)

if os.environ.get('no_tick') == "1": TICK = False
else                               : TICK = True
#print(f"tick is {TICK} .. {os.environ.get('no_tick')}")

if os.environ.get('no_double_lines',0) == "1": DOUBLE_LINES_ENABLED = False
else                                         : DOUBLE_LINES_ENABLED = True                                  #DEBUG: print(f"DOUBLE_LINES_ENABLED={DOUBLE_LINES_ENABLED}")

#vars
current_processing_segment = 0
spacer = ""

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Set up logging to both console and file
#def setup_logging():                                                                        #DEPRECATED 🤠
#    global tee, output_file
#    if tee:
#        #print(f" 🌔 output_file is {output_file}")
#        logging.basicConfig(
#            level=logging.INFO,
#            format='%(message)s',
#            handlers=[
#                logging.FileHandler(output_file, mode='a'),  # Append mode
#                #NO loggging.StreamHandler(sys.stdout)  # Also print to console
#            ]
#        )

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class DualOutput:
    def __init__(self, file_name):
        self.file = open(file_name, "a", encoding='utf-8', newline="")  # Open file in append mode, prevent extra newlines
        self.stdout = sys.stdout  # Save the original stdout

    def write(self, message):
        self.file  .write(message)  # Write to the log file
        self.stdout.write(message)  # Write to the console

    def flush(self):
        #self.file  .flush()  # Ensure data is written to the file
        self.stdout.flush()  # Ensure data is written to the console

def setup_output():
    global tee, output_file
    if tee and output_file:
        sys.stdout = DualOutput(output_file)

#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def hide_cursor():
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()

def show_cursor():
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


def is_console_output():
    """
    Check if the standard output is attached to a console screen buffer.
    """
    h = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    # Use GetFileType to check the type of the handle
    FILE_TYPE_CHAR = 0x0002
    FILE_TYPE_PIPE = 0x0003
    file_type = ctypes.windll.kernel32.GetFileType(h)
    return file_type == FILE_TYPE_CHAR


def set_cursor_position(x, y):
    h = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
    pos = (y << 16) | x  # Combine x and y into a single integer
    ctypes.windll.kernel32.SetConsoleCursorPosition(h, pos)

    # Example: Move to column 1, row 0
    #set_cursor_position(0, 0)

def set_cursor_column_helper(x):
    # Define necessary structures and constants
    class COORD(ctypes.Structure):
        _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]

    class CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
        _fields_ = [
            ("dwSize", COORD),
            ("dwCursorPosition", COORD),
            ("wAttributes", ctypes.c_ushort),
            ("srWindow", ctypes.c_short * 4),
            ("dwMaximumWindowSize", COORD),
        ]

    h = ctypes.windll.kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE

    # Get current screen buffer info
    csbi = CONSOLE_SCREEN_BUFFER_INFO()
    if not ctypes.windll.kernel32.GetConsoleScreenBufferInfo(h, ctypes.byref(csbi)):
        raise ctypes.WinError()

    # Set the cursor to the desired column and keep the current row
    #x = x - 1
    new_position = COORD(x, csbi.dwCursorPosition.Y)
    if not ctypes.windll.kernel32.SetConsoleCursorPosition(h, new_position):
        raise ctypes.WinError()

def set_cursor_column_unsafe(x):
    """
    Example: Move to column 0, keeping the current row
    """
    if is_console_output():
        try:
            #print("Moving cursor to column 0 without changing the row!")
            set_cursor_column_helper(0)
        except Exception as e:
            print(f"Error: {e}")
    else:
        #print("output is not console, skipping cursor manipulation")
        pass

cursor_mutex = threading.Lock()
output_mutex = threading.Lock()

def set_cursor_column(x):
    with cursor_mutex:
        #TODO: can also do the ansi move to col[x] here! 🐐
        set_cursor_column_unsafe(x)

#def flush():
#    #print(f"Buffered data: {sys.stdout.buffer.getvalue()}")     # Inspect buffered data
#    sys.stdout.flush()


class CapturingStdout:
    def __init__(self):
        self.buffer = StringIO()
        self.last_buffer = ""
        self.original_stdout = sys.stdout

    def write(self, data):
        self.buffer.write(data)  # Capture the data
        self.original_stdout.write(data)  # Forward it to the original stdout

    def flush(self):
        self.original_stdout.flush()  # Flush the original stdout

    def flush_nope(self):
        buffer = self.buffer.getvalue()
        if len(buffer) > 200 and buffer != self.last_buffer:  # Check buffer length and avoid duplicates
            #buffer = buffer.replace("Faster","Asshole") #this worked
            #print(f"Buffered data: {buffer}")
            self.last_buffer = buffer
        self.original_stdout.flush()  # Flush the original stdout

    def get_buffer_value(self):
        """Expose the current buffer value."""
        return self.buffer.getvalue()

    def set_buffer_value(self, new_value):
        """Replace the buffer's content with a new value."""
        self.buffer = StringIO(new_value)

    def string_in_buffer(self, search_string):
        """Check if a string is in the buffer."""
        return search_string in self.buffer.getvalue()

# Replace sys.stdout with our custom class
#sys.stdout = CapturingStdout()

def enclose_numbers(line): return re.sub(r'(\d+)', DOUBLE_UNDERLINE_ON + r'\1' + DOUBLE_UNDERLINE_OFF, line)                                 #ansi-stylize numbers - italics + we choose double-underline in this example

def flush():
    #sys.stdout.flush()
    #with output_mutex: sys.stdout.flush()
    sys.stdout.flush()

def enable_vt_support():                                                                                        #this was painful to figure out
    import os
    if os.name == 'nt':
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


our_ansi_reset = ANSI_RESET + move_decorator_from_environment_variable

def print_line(line_buffer, r, g, b, additional_beginning_ansi=""):
    global whisper_decorator_title

    #sys.stderr.write(f"DEBUG: called print_line({line_buffer}, {r}, {g}, {b}, {additional_beginning_ansi}){PRENEWLINE}\n")
    color_change_ansi = f'\033[38;2;{r};{g};{b}m'

    original_line_buffer = line_buffer
    global current_processing_segment, whisper_decorator_title, our_ansi_reset
    double  = False
    summary = False

    if whisper_ai:
        additional_beginning_ansi=""         #kludging a situation
    else:
        #🐐🐄could add translate like a footer but with faint or indent or something and only in whisperai mode
        if any(substring in line_buffer for substring in FOOTERS):                                                  #identify if we're in a footer/summary line
            line_buffer = enclose_numbers(line_buffer)
            double      = True
            summary     = True

    line = ""
    #as of TCC v33 the copy /G now outputs to screen directly which leaves detritus that we WANT until we don’t want it
    #so now we have to move to column 1
    if nomoji is True:                                                                                          # Start the line off
        line = MOVE_TO_COL_1
    else:
        line = line + MOVE_TO_COL_1 + move_decorator_from_environment_variable                                                                                                      #decorate with environment-var-supplied decorator if applicable
        if   any(substring in line_buffer for substring in file_removals ): line += EMOJIS_DELETE                                  #treatment for file deletion lines
        elif any(substring in line_buffer for substring in ["Y/N/A/R)"]  ):
            line += EMOJIS_PROMPT + CURSOR_VISIBLE                                  #treatment for  user prompt  lines
            with output_mutex:
                enable_vt_support()
                sys.stdout.write(CURSOR_VISIBLE)    #timing
                flush()
            #print(f"[line buffer={line_buffer}")
        elif any(substring in line_buffer for substring in ["=>","->"]   ): line += EMOJIS_COPY                                    #treatment for   file copy   lines
        elif any(substring in line_buffer for substring in ["TCC: (Sys)"]):                                                        #treatment for error message lines
            double = True;                                                  line += EMOJIS_ERROR + f'{BLINK_ON}{ITALICS_ON}{UNDERLINE_ON}{REVERSE_ON}'
        elif summary:                                                       line += EMOJIS_SUMMARY                                 #treatment for summary lines
        else:                                                               line += f'  '                                          #TODO figure out why this line is here


    # Fix excessive indentation in ctranslate2 logs
    #if whisper_ai and "[ctranslate2]" in line_buffer:
    #    line_buffer = re.sub(r'^[ ]{10,}', '', line_buffer)

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
            #ine_buffer = f'{ERASE_TO_EOL}{PRENEWLINE}\n{EMOJIS_SUMMARY}'.join(lines)           # production
            line_buffer = f'{ERASE_TO_EOL}{PRENEWLINE}{EMOJIS_SUMMARY}'  .join(lines)           # chatgpt attempt to fix newline problem:

    #line     += f'{color_change_ansi}{additional_beginning_ansi}{original_line}{ANSI_RESET}{PRENEWLINE}\n'                   #make line be our random color
    line = f'{line}{color_change_ansi}{additional_beginning_ansi}{original_line}{ERASE_TO_EOL}{ANSI_RESET}\n'                   #make line be our random color

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
        decorator_title = whisper_decorator_title
        #DEBUG: if additional_beginning_ansi: print(f"additional beginning ansi={additional_beginning_ansi.lstrip(1)}")         #
        spacer           = "                              "
        spacer2          = "                           "
        spacer_less      = "           "
        spacer_even_less =    "   "
        if verbose: print(f"orig_line is [orig={original_line}][line={line}]")

        #f "[ctranslate2]" in line: just won't work!
        #f "[ctranslate2]" in original_line:

        #if sys.stdout.string_in_buffer("ctranslate"):
        #    #this fails to find it!!!!!
        #    sys.stdout.print(f"FOUND IT!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ")
        #   #pass

        if  "ctranslate" in original_line:
            line = spacer + FAINT_ON   + COLOR_GREY + "⭐" + line + FAINT_OFF               #+ "HEYOOOOOOOOOOO"
            line = re.sub(r'(\[[23]\d{3}.[01]\d.[0-3]\d )', f'{COLOR_GREY}\1', line)
            #DEBUG: print ("ctranslate line found!")#
        line = re.sub(r'(\[[23]\d{3}.[01]\d.[0-3]\d )', f'{COLOR_GREY}\1', line)    #todo experimental: just do this, won't affecti f there isn't a match
        if  original_line.startswith("Standalone Faster-Whisper-XXL "):
            #### = line.replace("Standalone Faster-Whisper-XXL", "\n\n🚀 Standalone Faster-Whisper-XXL 🚀\n").replace(" running on:",":")
            line = decorator_title + " " + line.rstrip('\n').replace(" running on:"," ━━ on").replace("Standalone",f"{decorator_title} Standalone") + " " + decorator_title
            #ys.stdout.write(f"\n{BIG_TOP}{line}\n{BIG_BOT}{line}\n\n");
            enable_vt_support()
            with output_mutex:
                sys.stdout.write(f"\n\n{BIG_TOP}{line}{ERASE_TO_EOL}{PRENEWLINE}\n{BIG_BOT}🚀🚀🚀 {line}{ERASE_TO_EOL}{PRENEWLINE}\n");
                flush()
            line=""


        # not working:
        #ine = line.replace("MDX Kim_Vocal_2" ,f"{MOVE_UP_1}MDX Kim-Vocal 2")  #was needed for a bit, but not now
        line = line.replace("MDX Kim_Vocal_2" ,f"MDX Kim-Vocal 2")

        # patterned substitutions: (in alphabetical order):
        line = line.replace("Starting work on: "                                      ,f"{FAINT_OFF}🎤 Starting transcription work on: {ITALICS_ON}")
        line = line.replace("* Compression ratio threshold is not"                    ,f"{FAINT_OFF}{spacer}{FAINT_ON}{COLOR_GREY}⭐ Compression ratio threshold is not") + FAINT_OFF
        line = line.replace("* Log probability threshold is not"                      ,f"{FAINT_OFF}{spacer}{FAINT_ON}{COLOR_GREY}⭐ Log probability threshold is not"  ) + FAINT_OFF
        line = line.replace("* No speech threshold is met"                            ,f"{FAINT_OFF}{spacer}{FAINT_ON}{COLOR_GREY}⭐ No speech threshold is met")         + FAINT_OFF
        line = line.replace("Audio filtering finished in: "                           ,f"{FAINT_OFF}⏱  Audio filtering finished in: {ITALICS_ON}")
        line = line.replace("Audio filtering is in progress"                          ,f"{FAINT_OFF}{MOVE_UP_1}🔊 {COLOR_BRIGHT_GREEN}Audio filtering is {ANSI_RESET}{ITALICS_ON}in progress{ITALICS_OFF}{COLOR_BRIGHT_GREEN}") + "\n"
        line = line.replace("CUDA"                                                    ,f"{FAINT_OFF}{ITALICS_ON}CUDA{ITALICS_OFF}")
        line = line.replace("Estimating duration from bitrate"                        ,f"{FAINT_OFF}🤔 Estimating duration from bitrate {FAINT_ON}") + "\n"
        line = line.replace("invalid new backstep"                                    ,f"{FAINT_OFF}⚠ Invalid new backstep" + "\n")
        line = line.replace("Model loaded in: "                                       ,f"{FAINT_OFF}💾 Model loaded in: {ITALICS_ON}") + "\n"
        line = line.replace("Number of visible GPU devices: "                         ,f"{FAINT_OFF}🖥️ Number of visible GPU devices: {ITALICS_ON}") + "\n"
        line = line.replace("Operation finished in: "                                 ,f"{FAINT_OFF}{MOVE_UP_1}{MOVE_UP_1}{COLOR_BRIGHT_GREEN}🏁 Operation finished in: {COLOR_GREEN}{ITALICS_ON}")
        line = line.replace("Processing audio with duration"                          ,f"{FAINT_OFF}👂 Processing audio with duration{ITALICS_ON}") + "\n"
        line = line.replace("Subtitles are written to '"                              ,f"{FAINT_OFF}✅ Subtitles are written to '{ITALICS_ON}{BOLD_ON}").replace("' directory.",f"{BOLD_OFF}{ITALICS_OFF}' directory. ✅")
        line = line.replace("Supported compute types by GPU:"                         ,f"{FAINT_OFF}🖥️ Supported compute types by GPU: {ITALICS_ON}") + "\n"
        line = line.replace("Transcription speed: "                                   ,f"{FAINT_OFF}{FAINT_ON}{COLOR_GREY}⏱  Transcription speed: {ITALICS_ON}")
        line = line.replace("VAD filter removed "                                     ,f"{FAINT_OFF}✔  VAD filter audio removal duration: {ITALICS_ON}").replace("of audio","")
        line = line.replace("VAD filter kept the following audio segments: "          ,f"{FAINT_OFF}✔️ VAD filter kept the following audio segments: {FAINT_ON}") #for some reason this needs 1 less space before “VAD” ... not a mistake
        line = line.replace("VAD finished in: "                                       ,f"{FAINT_OFF}{MOVE_UP_1}{MOVE_TO_COL_1}🏁 VAD finished in: {ITALICS_ON}")
        line = line.replace("VAD timestamps are dumped to "                           ,f"{FAINT_OFF}{MOVE_UP_1}✍  VAD timestamps are dumped to: {ITALICS_ON}")

        # unique substitutions: multi-line:
        if  original_line.startswith("  Processing segment at "):
            current_processing_segment += 1
            #f current_processing_segment > 1: print("")
            if current_processing_segment > 1: pass
            #ine = line.replace(f"  Processing segment at ",f"{COLOR_GREY}{FAINT_ON}{spacer_even_less}♬♬ Processing segment at:  {ITALICS_ON}") + ITALICS_OFF + FAINT_OFF
            #ine = line.replace(f"  Processing segment at ",f"{COLOR_GREY}{FAINT_ON}{spacer          }♬♬ Processing segment at:  {ITALICS_ON}") + ITALICS_OFF + FAINT_OFF
            line = line.replace(f"  Processing segment at ",f"{COLOR_GREY}{FAINT_ON}{spacer2         }♬♬ Processing segment at:  {ITALICS_ON}") + ITALICS_OFF + FAINT_OFF
        # unique substitutions: oneliners:
        if " --> " in line: line = f"🌟 {BLINK_ON}" + line.replace("]  ",f"]{BLINK_OFF}{ANSI_RESET}{ITALICS_ON}  ")
        if any(substring in line for substring in ["Reset prompt. prompt_reset_on_temperature threshold is met", "Reset prompt. prompt_reset_on_no_end is triggered"]):                line = line.replace("* Reset prompt. ",COLOR_GREY + FAINT_ON + spacer + "⭐  Reset prompt. ") + FAINT_OFF            #bad syntax:                              ["Reset prompt. prompt_reset_on_temperature threshold is met", "Reset prompt. prompt_reset_on_no_end is triggered"] in line:

        #moving this one later because it seemed to be hitting other things:


    lines_to_print = line.split(f'\n')                                                             #there really shouldn't be a \n in our line, but things happen
    i = 0
    for myline in lines_to_print:                                                                             #print our line, but do it double-height if we're supposed to
        if myline != '\n' and myline != '':
            if not double or not DOUBLE_LINES_ENABLED or not whisper_ai:
                msg = myline
                set_cursor_column(0)
                with output_mutex:
                    column_target = screen_columns - 5
                    sys.stdout.write(msg + f"\033[{column_target}G     \b\b\b\b\b{CONCEAL_ON}")
                    flush()
            else:
                enable_vt_support()                                                                            #suggestion from https://github.com/microsoft/terminal/issues/15838 to fix double height lines sometimes not rendering
                #ys.stdout.write(f'{MOVE_TO_COL_1}')   #20240324: adding '{MOVE_TO_COL_1}' as ??bugfix?? for ansi creeping out due to TCC error and mis-aligning our double-height lines - prepend the ansi code to move to column 1 first, prior to printing our line
                #ys.stdout.write(f'{MOVE_TO_COL_1}{BIG_TOP}\033[38;2;{r};{g};{b}m{myline}\n{BIG_BOT}\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}\n')

                #prod long time but leaky
                #sys.stdout.write(f'{MOVE_TO_COL_1}{BIG_TOP}\033[38;2;{r};{g};{b}m{myline}\n')
                #sys.stdout.write(               f'{BIG_BOT}\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}\n')
                #still leaky but more likely for summary lines to be in correct column?
                #ys.stdout.write(f'           {CR}{BIG_TOP}\033[38;2;{r};{g};{b}m{myline}\n')
                ###sys.stdout.write(f'           {CR}{BIG_TOP}\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}{ERASE_TO_EOL}\n')    #2024/12/12 — not sure why we weren’t inserting additional-begining-ansi into the top-line... but this section had to be updated anyway because TCC v33 “fixes” the /G option on the copy command so that it outputs, which leaves screen destritus, so we have to  add ansi-clear-to-eol at the end of these 2 lines:
                #2024/12/12^^^^^^^^^^^^^^^^^^^^^^^^^ I forget why those spaces were in there, but as of TCCv33 with the /G in copy “fixed”, things seem to be working fine without the spaces here.. in fact better
                #2024/12/12 — not sure why we weren’t inserting additional-begining-ansi into the top-line... but this section had to be updated anyway because TCC v33 “fixes” the /G option on the copy command so that it outputs, which leaves screen destritus, so we have to  add ansi-clear-to-eol at the end of these 2 lines.. then we made them 1 line of code
                with output_mutex:
                    set_cursor_column(0)
                    sys.stdout.write(f'{CR}{MOVE_TO_COL_1}{BIG_TOP}\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}{ERASE_TO_EOL}{PRENEWLINE}\n{CR}{MOVE_TO_COL_1}{BIG_BOT}\033[38;2;{r};{g};{b}m{additional_beginning_ansi}{myline}{ERASE_TO_EOL}{PRENEWLINE}\n')
                    set_cursor_column(0)
                    flush()
    with output_mutex:
        #rem chatgpt says remove this to fix my extra blank lines problem, but it is wrong:
        sys.stdout.write(f'\n')
        #set_cursor_column(0)
        flush()


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

print(CURSOR_INVISIBLE,end="")


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
verbose                       = False                                   #whether we are in verbose mode or not
whisper_ai                    = False                                   #whether we are in WhisperAi postprocessing mode or not
tee                           = False
current_processing_segment    = 0
my_mode                       = DEFAULT_COLOR_CYCLE_MODE
background_color_switch_maybe = ""
r                             = ""
g                             = ""
b                             = ""
tee                           = False       # for -t option
output_file                   = None        # for -t option


#sys.stdout.write(f"sys.argv is {sys.argv}\n")

#if len(sys.argv) > 1:
#    #sys.stdout.write(f"sys.argv[1] is {sys.argv[1]}\n")
#    if sys.argv[1] == 'bg' or sys.argv[1] == 'both': my_mode = sys.argv[1]
#    for arg in sys.argv[1:]:
#        if arg.lower() in ["n", "-n", "--n", "nomoji", "-nomoji", "--nomoji", "no-emoji", "-no-emoji", "--no-emoji"]: nomoji  = True
#    for arg in sys.argv[1:]:
#        if arg.lower() in ["v", "-v", "--v", "verbose", "-verbose", "--verbose"]: verbose = True
#    for arg in sys.argv[1:]:
#        if arg.lower() in ["w", "-w", "--w", "whisperai", "-whisperai", "--whisperai", "whisper", "-whisper", "--whisper"]:
#            whisper_ai = True
#            nomoji     = True


if len(sys.argv) > 1:
    if sys.argv[1] in ['bg', 'both']:
        my_mode = sys.argv[1]

    for arg in sys.argv[1:]:
        arg_lower = arg.lower()
        if   arg_lower in ["n", "-n", "--n", "nomoji", "-nomoji", "--nomoji", "no-emoji", "-no-emoji", "--no-emoji"]:
            nomoji = True
        elif arg_lower in ["v", "-v", "--v", "verbose", "-verbose", "--verbose"]:
            verbose = True
        elif arg_lower in ["w", "-w", "--w", "whisperai", "-whisperai", "--whisperai", "whisper", "-whisper", "--whisper"]:
            whisper_ai = True
            nomoji = True
        elif arg.startswith('-t'):  # Detect -t with attached value
            tee = True
            output_file = arg[2:]   # Extract the value after -t


if tee and output_file:
    #setup_logging()
    setup_output()




if verbose:
    sys.stdout.write(f"    * verbose    is {verbose                   }\n")
    sys.stdout.write(f"    * tee        is {tee                       }\n")
    sys.stdout.write(f"    * custom_fil is {output_file               }\n") #if tee = True, anyway
    sys.stdout.write(f"    * my_mode    is {my_mode                   }\n")
    sys.stdout.write(f"    * nomoji     is {nomoji                    }\n")
    sys.stdout.write(f"    * whisper_ai is {whisper_ai                }\n")
    sys.stdout.write(f"    * color ? bg is {COLOR_QUESTION_BACKGROUNDS}\n") #if whisper_ai = True, anyway

#enable_vt_support()


COLOR_QUESTION_BACKGROUNDS = False

#whether to blink text or not
blink_maybe = BLINK_ON;                          #failed attempt to solve blinking questions in Whisper mode
if nomoji or whisper_ai: BLINK_ON=""             #failed attempt to solve blinking questions in Whisper mode

char_read_time_out=0.008;                        #most of the time, read characters as fast as we can! testing gave 0.008
if whisper_ai: char_read_time_out=0.05           #go slower when postprocessing whisper transcription because there's hardly any screen output, and it's not interactive, so speed is less important, and we want to keep the CPU as free as possible. Even though the claire.tick() function has adaptive throttling based on how often it's called, tested to ensure we don't hammer our CPU harder for the pretty colors than for our actual calculations, it's still more efficient to not call it aso ften.
if whisper_ai:
    CONCEAL_ON  = ""
    CONCEAL_OFF = ""
    char_read_time_out=0.064                     #go slower when postprocessing whisper transcription because there's hardly any screen output, and it's not interactive, so speed is less important, and we want to keep the CPU as free as possible. Even though the claire.tick() function has adaptive throttling based on how often it's called, tested to ensure we don't hammer our CPU harder for the pretty colors than for our actual calculations, it's still more efficient to not call it as often.
    char_read_time_out=0.016                     #go slower when postprocessing whisper transcription because there's hardly any screen output, and it's not interactive, so speed is less important, and we want to keep the CPU as free as possible. Even though the claire.tick() function has adaptive throttling based on how often it's called, tested to ensure we don't hammer our CPU harder for the pretty colors than for our actual calculations, it's still more efficient to not call it as often.
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
            sys.stdout.write(CURSOR_VISIBLE)
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

            if not whisper_ai: line_spacer = "   "                          #spacer logic
            else:              line_spacer = ""

            ##### ACTUALLY PRINT OUT THE LINE:
            if   any(substring in line_buffer for substring in file_removals         ): line_spacer = EMOJIS_DELETE                                 #treatment for file deletion lines
            elif any(substring in line_buffer for substring in ["Y/N/A/R)"," (Y/N)"] ): line_spacer = EMOJIS_PROMPT                                  #treatment for  user prompt  lines
            elif any(substring in line_buffer for substring in ["=>","->"]           ): line_spacer = EMOJIS_COPY                                    #treatment for   file copy   lines

            sys.stdout.write(f'{background_color_switch_maybe}{foreground_color_switch}{CURSOR_RESET}{cursor_color_switch_by_hex}{additional_beginning_ansi}'    + f'{line_spacer}{blink_maybe}{line_buffer} {ANSI_RESET}') #\033[0m #\033[1C
            #moved to end of loop: sys.stdout.flush()                                                                                   # Flush the output buffer to display the prompt immediately
            flush()                    #added 2024/10/31 and unsure of necesity
            line_buffer = ""
        elif in_prompt and char == '\n':          #if we hit end-of-line in a copy/move user prompt, flush the output so the user can see the prompt... promptly
            in_prompt = False
            #ys.stdout.write(f'\033[1D{line_buffer.rstrip()}[0m\n')
            with output_mutex:
                sys.stdout.write(f'\033[1D{line_buffer.rstrip()}{ANSI_RESET}{PRENEWLINE}{CURSOR_INVISIBLE}\n')  #2024/12/12 added cursor_invisible to deal with TCCv33 /g
                flush()
            line_buffer = ""



        #elif char == '\n':                        #if we hit end of line NOT in a copy/move user prompt
        #    if not nomoji:
        #       if any(substring in line_buffer for substring in FOOTERS): additional_beginning_ansi += BLINK_ON                       # make it blink
        #       #r, g, b = get_random_color()                                                                                          # Reset for the next line
        elif char == '\n':
            if not nomoji:
                if any(substring in line_buffer for substring in FOOTERS):
                    additional_beginning_ansi += BLINK_ON

            #f line_buffer.strip() and "[ctranslate2]" not in line_buffer:
            if                         "[ctranslate2]" not in line_buffer:
                print_line(line_buffer, r, g, b, additional_beginning_ansi)
                line_buffer = ""
                additional_beginning_ansi = ""

            #if "[ctranslate2]" in line_buffer:
            #    line_buffer = ""  # completely suppress this line
            #    continue          # skip printing


            #print_line(line_buffer, r, g, b, additional_beginning_ansi)
            #line_buffer = ""
            #additional_beginning_ansi = ""




            #REFERENCE: function ANSI_CURSOR_CHANGE_COLOR_HEX=`%@char[27][ q%@char[27]]12;#%1%@char[7]`                                 # with "#" in front of color
            #rgbhex_with_pound_sign = convert_rgb_tuple_to_hex_string_with_hash(r,g,b)                                                  # Reset for the next line
            #additional_beginning_ansi = f"{CURSOR_RESET}\033]" + "12;" + rgbhex_with_pound_sign + f"\007"                              # Reset for the next line: make cursor same color
        else:
            flush()                 #didn’t seem to fix what i wanted it to, but didn’t seem to hurt (2024/12/19)


    except queue.Empty:
        if TICK: claire.tick(mode=my_mode)                                                                                              # color-cycle the default-color text using my library
        try:
            flush()

        except:
            pass

    #final flush just in case ... 🐐 might not be necessary...
    try:
        flush()
    except:
        pass


# Flush any remaining content in line_buffer after the loop
# After exiting the main loop, print any remaining line content
#f line_buffer.strip():                                                     # Ensure any remaining line without \n is printed
#    print_line(line_buffer, r, g, b, additional_beginning_ansi)
#if line_buffer.strip() and "[ctranslate2]" not in line_buffer:              # Ensure any remaining line without \n is printed
#    print_line(line_buffer, r, g, b, additional_beginning_ansi)
if line_buffer.strip():
    if "[ctranslate2]" not in line_buffer:
        print_line(line_buffer, r, g, b, additional_beginning_ansi)
    # else: silently suppress


# Reset the ansi? #kind of equivalent of: if TICK: claire.tock()
#sys.stdout.write(ANSI_RESET + "\n")  # Reset any leftover ANSI styles

# Final flush?
#flush()

# Restore sys.stdout if needed
#sys.stdout = sys.stdout.original_stdout



print(CURSOR_VISIBLE + ANSI_RESET,end="")

#20241222: got stuck red during get-lyrics:
print(ANSI_RESET_FULL,end="")









#todo goat keep in mind this ansi code exists and may help with the crap chars shoved to the rightmost column trick we use with copy /g on TCC v33ish:
#rem Enable synchronous output mode (Prevents race conditions in multithreaded output)
#        set ENABLE_SYCHRONOUS_MODE=%@CHAR[27][?2026h
