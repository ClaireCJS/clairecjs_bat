



#TODO: bg color is same as fg color... is that a bug? how would i fix that?

#TODO: deal with situation of lines that are too long. there should not be a ’stripe too long’ error

#TODO: maybe make every other column have a slight background grey hue

##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
##### INIT LIBRARIES:
##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
import re
import os
import sys
import shutil
import hashlib                                                                              # for computing stripe segment colors
import argparse
import textwrap
import colorama
import unicodedata                                                                          # for unicode normalization
from   rich.console import Console                                                          # shutil *and* os do *NOT* get the right console dimensions under Windows Terminal
#rom   colorama     import Fore, Style, init
#rom   wcwidth      import wcswidth
from   math         import ceil
sys.stdin .reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
colorama.init(strip=False)
#print(Fore.RED + "This text should be red." + Style.RESET_ALL)






##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
##### CONFIGURATION:
##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


################ USER CONFIGURATION FOR STRIPE-REPRESENTATIONS: ################
NUMBER_OF_CHARACTERS_TO_CONSIDER_FOR_STRIPE_COLOR = 19                                                  # we don’t need to look very far into words to get unique colors. Wider than 25 we start to get into subtitle-split-word territory where words >25chars get split into 2 lines and become a differently-colored stripe segment even though they were technically the same word.
NUM_CHARS_PER_WORD_ON_STRIPE_SEGMENT              = 3                                                   # max number of characters to show per stripe segment


################ USER CONFIGURATION FOR WORD HILIGHTING: ################
WORD_HIGHLIGHT_LEN_MIN   = 6                                                                            # word hilighting: Minimum length of a word to highlight
#AX_BACKGROUND_INTENSITY = 0.37                                                                         # word hilighting: Maximum background color intensity
#AX_BACKGROUND_INTENSITY = 0.25                                                                         # word hilighting: Maximum background color intensity
#AX_BACKGROUND_INTENSITY = 0.22                                                                         # word hilighting: Maximum background color intensity
MAX_BACKGROUND_INTENSITY = 0.25                                                                         # word hilighting: Maximum background color intensity
SATURATION               = 0.9                                                                          # word hilighting: default saturation level
LIGHTNESS                = 0.5                                                                          # word hilighting: default  lightness level


################ USER CONFIGURATION FOR COSMETICS: ################
DEFAULT_ROWS_ADDED_TO_OUTPUT = 7                                                                        # SUGGESTED: 7. Number of rows to subtract from screen height as desired maximum output height before adding columns. May not currently do anything.
content_ansi                 =  "\033[0m"
divider_ansi                 =  "\033[38;2;187;187;0m"
BOT_OFF                      =  "\033#0"
#content_ansi                =  "\033[42m\033[31m"
divider                      = f"  {divider_ansi}" + "│" + f"  {content_ansi}"                          # Divider with #BBBB00 color and additional padding
divider_visible_length       = 5                                                                        # basically the same as len(stripe_ansi(divider))
DEFAULT_WRAPPING             = False                                                                    # do we default to enabling the wrapping of long lines


################ USER CONFIGURATION FOR DEBUGGING: ################
DEBUG_STRIPE_GENERATION      = False
DEBUG_VERBOSE_COLUMNS        = False






##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
##### CONSTANTS:
##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


################ CONSTANTS FOR ANSI CODE: ################
ANSI_RESET          = "\033[39m\033[49m\033[0m"
ANSI_EOL            = "\033[0K"
ANSI_BIG_OFF        = "\033#0"
ANSI_FG_BLACK       = "\033[30m"
ANSI_BLINK_ON       = "\033[6m"
ANSI_BLINK_OFF      = "\033[25m"
ANSI_COLOR_GREY     = "\033[90m"
ANSI_FAINT_ON       = "\033[2m"
ANSI_FAINT_OFF      = "\033[22m"
REGEX_TO_MATCH_ANSI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07|P[^\\]*\\)')


################ CONSTANTS FOR MANUAL UNICODE NORMALIZATION: ################                           # to help stripe-segment-color consistency for letters that SEEM to be the same letter but aren’t
char_map = {                                                                                            # we simply convert an identical-looking not-normal-letter to the normal-letter it appears to be!
    # Cyrillic to Latin (Visually Identical)
    'е': 'e', 'Е': 'E',      # Cyrillic e and E to Latin e and E
    'а': 'a', 'А': 'A',      # Cyrillic a and A to Latin a and A
    'о': 'o', 'О': 'O',      # Cyrillic o and O to Latin o and O
    'с': 'c', 'С': 'C',      # Cyrillic c and C to Latin c and C
    'т': 't', 'Т': 'T',      # Cyrillic t and T to Latin t and T
    'р': 'p', 'Р': 'P',      # Cyrillic p and P to Latin p and P
    'у': 'y', 'У': 'Y',      # Cyrillic y and Y to Latin y and Y
    'в': 'b', 'В': 'B',      # Cyrillic b and B to Latin b and B
    'н': 'h', 'Н': 'H',      # Cyrillic n and N to Latin n and N
    'к': 'k', 'К': 'K',      # Cyrillic k and K to Latin k and K
    'м': 'm', 'М': 'M',      # Cyrillic m and M to Latin m and M
    'л': 'l', 'Л': 'L',      # Cyrillic l and L to Latin l and L

    # Greek to Latin (Visually Identical)
    'α': 'a', 'Α': 'A',      # Greek   alpha to Latin a
    'β': 'b', 'Β': 'B',      # Greek    beta to Latin b
    'ε': 'e', 'Ε': 'E',      # Greek epsilon to Latin e
    'ο': 'o', 'Ο': 'O',      # Greek omicron to Latin o
    'ρ': 'p', 'Ρ': 'P',      # Greek     rho to Latin p
    'σ': 's', 'Σ': 'S',      # Greek   sigma to Latin s
    'ι': 'i', 'Ι': 'I',      # Greek    iota to Latin i
    'κ': 'k', 'Κ': 'K',      # Greek   kappa to Latin k
    'λ': 'l', 'Λ': 'L',      # Greek  lambda to Latin l
    'μ': 'm', 'Μ': 'M',      # Greek      mu to Latin m
    'ν': 'n', 'Ν': 'N',      # Greek      nu to Latin n
    'τ': 't', 'Τ': 'T',      # Greek     tau to Latin t

    # Other common similar letters
    'ı': 'i',               # Generic Dotless i to Latin i
    'İ': 'I',               # Generic Dotted  I to Latin I
    'ı': 'i',               # Turkish dotless i to Latin i
}






##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
##### GLOBAL VARIABLES:
##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
WRAPPING                     = DEFAULT_WRAPPING
STRIPE                       = False
VERBOSE                      = False
WORD_HIGHLIGHTING            = False
FORCE_COLUMNS                = False
IGNORE_NUMSIGNLINES          = False
TEXT_ALSO                    = False
args                         = None
parser                       = None
avg_line_width               = None
console_width                = None
console_height               = None
FORCED_CONSOLE_WIDTH         = 0
columns                      = 0
INTERNAL_LOG                 = ""
record_working_column_length = 0










##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#####                  SUBROUTINES:
##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


from wcwidth import wcswidth as _orig_wcswidth
def wcswidth(s):                                                # override wcwidth function to never return -1
    #w = _orig_wcswidth(           s )                          # wrong way: not accurate unless ANSI is stripped first!
    w  = _orig_wcswidth(strip_ansi(s))                          # right way: not accurate unless ANSI is stripped first!

    #print (f"---- w={w} for “{s}” -----")                      #debug

    #if s in ['⸎❶❷']: return 2

    return 0 if w < 0 else w                                    # never return -1, which the original library returns in situations


def parse_arguments():
    """
    Parse command-line arguments.
    """

    global STRIPE, WRAPPING, VERBOSE, FORCE_COLUMNS, FORCED_CONSOLE_WIDTH, IGNORE_NUMSIGNLINES, args, console_width, console_height, WORD_HIGHLIGHTING, TEXT_ALSO, DEFAULT_ROWS_ADDED_TO_OUTPUT

    DRTS=DEFAULT_ROWS_ADDED_TO_OUTPUT # shorthand


    #parser = argparse.ArgumentParser(description="****** Displays a file or STDIN in a compact, multi-column format, to reduce scrolling. Optionally highlight longer words and/or generate a visual stripe that summarizes the file in a single deterministic line ******")
    parser = argparse.ArgumentParser(
        description=(
            "✨✨✨ 🇵 🇷 🇮 🇳 🇹   🇼 🇮 🇹 🇭   🇨 🇴 🇱 🇺 🇲 🇳 🇸 ✨✨✨\n\n"
            "⛧ Displays a file (or STDIN) in a multi-column layout to reduce scrolling ⛧\n"
            "⛧ Optionally word hilighting and visual stripe summarizing file contents! ⛧\n"
        ),
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('optional_filename'                          , type   = str, nargs = '?', help=f"Optional filename to process. If not provided, input must be piped from STDIN.")
    parser.add_argument('-cw'  , '--console_width'                   , type   = int,              help=f"↔  Override detected console width [which is currently “{console_width}”]")
    parser.add_argument('-wh'  , '--word_highlighting'               , action = 'store_true',     help=f"🦓 STRIPES:🦓  Enable word highlighting")
    parser.add_argument('-st'  , '--stripe'                          , action = 'store_true',     help=f"🦓 STRIPES:🦓  Show visual stripe summary")
    parser.add_argument('-also', '--text_also'                       , action = 'store_true',     help=f"🦓 STRIPES:🦓  display the text AND stripe; not *just* the stripe")
    parser.add_argument('-ins' , '--ignore_numsign_lines_for_stripes', action = 'store_true',     help=f"🦓 STRIPES:🦓  Ignore lines starting with “#” when creating stripe")
    parser.add_argument('-stu' , '--upper-stripe',dest='upper_stripe', action = 'store_true',     help=f"🦓 STRIPES:🦓  ↗ For use with the --also parameter:  Show visual stripe summery ABOVE the content")
    parser.add_argument('-stl' , '--lower-stripe',dest='lower_stripe', action = 'store_true',     help=f"🦓 STRIPES:🦓  ↘ For use with the --also parameter:  Show visual stripe summery BELOW the content")
    parser.add_argument('-stb' , '--both-stripes',dest='both_stripes', action = 'store_true',     help=f"🦓 STRIPES:🦓  ↕ For use with the --also parameter:  Show visual stripe summery above AND below the content")
    parser.add_argument( '-w'  , '--width'                           , type   = int,              help=f"RARE: ↔  Override output width, in case you don’t want to fill up the whole screen width")
    parser.add_argument( '-c'  , '--columns'                         , type   = int,              help=f"RARE: 🏁 Override number of columns used in displaying the text")
    parser.add_argument( '-p'  , '--row_padding'                     , type   = int, default=DRTS,help=f"RARE: 🏁 Override the number of rows to subtract from screen height when calculating tallest output [default: {DRTS}]")
    parser.add_argument('-wr'  , '--wrap'                            , action = 'store_true',     help=f"DEPRECATED:  Enable line wrapping for long lines")
    parser.add_argument('-nw'  , '--no_wrap'                         , action = 'store_true',     help=f"DEPRECATED: Disable line wrapping for long lines")
    parser.add_argument('-ll'  , '--max_line_length_before_wrapping' , type   = int, default=999, help=f"DEPRECATED: Maximum line length before wrapping [default: 999]")     #was 80 for like 6 months but changed to 999 2025/03/03
    parser.add_argument( '-v'  , '--verbose'                         , action = 'store_true',     help=f"Verbose mode—display debug info and internal logs")


    IGNORE_NUMSIGNLINES  = False                              # unnecessary
    args                 = parser.parse_args()
    ROW_PADDING          = args.row_padding
    VERBOSE              = args.verbose
    WORD_HIGHLIGHTING    = args.word_highlighting
    FORCE_COLUMNS        = args.columns
    FORCED_CONSOLE_WIDTH = args.console_width
    STRIPE               = args.stripe
    TEXT_ALSO            = args.text_also
    IGNORE_NUMSIGNLINES  = args.ignore_numsign_lines_for_stripes
    if STRIPE: WORD_HIGHLIGHTING = True                         #stripe is really an abbreviated form of word_highlighting mode

    #print(f"word_highlighting is {WORD_HIGHLIGHTING}")

    return parser.parse_args()



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def strip_ansi(text):
    """
    Strip ANSI escape codes

    Requires global var REGEX_TO_MATCH_ANSI as the compiled regex to remove all codes
    Suggested value: REGEX_TO_MATCH_ANSI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07|P[^\\]*\\)')

    """
    global REGEX_TO_MATCH_ANSI
    return REGEX_TO_MATCH_ANSI.sub('', text)
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###



ansi_escape = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
def visible_width(s):
    stripped = ansi_escape.sub('', s)
    return len(stripped)




# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def wcsarraywidth(strings, mode="total", division_mode="integer"):
    """
    Calculate the width of an array of strings based on display widths, for accurate text placement with emoji/double-width characters

    Parameters:
        strings (list of str): Array of strings to measure.
        mode (str):
            "total"   - Sum the widths of all strings.
            "max"     - Return the width of the widest string.
            "average" - Return the average width of all strings.

    Returns:
        int: The calculated width based on the mode.
    """
    if not all(isinstance(s, str) for s in strings): raise ValueError("All elements in 'strings' must be strings.")

    if 1 == 2:
        print("=== DEBUG: line widths (aggregated per line) ===")
        for idx, s in enumerate(strings, start=1):
            # if strings is already a line, this prints one per line;
            # if it's characters, join() reconstructs the visible string
            # line_text = ''.join(s) if isinstance(s, (list, tuple)) else str(s)
            #line_text = ''.join(s) if isinstance(s, (list, tuple)) else str(s)
            line_text = ''.join(s)
            width = wcswidth(line_text)
            print(f"{idx:03}: width={width:<4} len={len(line_text):<4} text={repr(line_text)}")
        print("=== END DEBUG ===")

    widths = [wcswidth(s) for s in strings]

    retval = None
    if   mode == "total": return sum(widths)
    elif mode ==   "max": return max(widths)
    elif mode == "average" or mode == "avg":
        if division_mode == "integer": retval = sum(widths) // len(widths)  # Use integer division to get a  whole  number
        else                         : retval = sum(widths) /  len(widths)  # Use float   division to get a decimal number
    else:
        raise ValueError("Invalid mode. Use 'total', 'max', or 'average'/'avg'.")
    if VERBOSE: print(f"🔰 wcsarraywidth returning retval={retval} for line={strings} ... sum={sum(widths)},max={max(widths)}, len(widths)={len(widths)}, sum(widths) // len(widths)={sum(widths) // len(widths)}")
    return retval
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###




# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def calculate_aspect_ratio(total_width, total_rows):
    """
        Function to calculate the aspect ratio of our rendered text
        Since characters are twice as high as they are wide, we internally multiply rows by 2
    """
    return total_width / (2 * total_rows) if total_rows != 0 else float('inf')
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###





# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def determine_optimal_columns(lines, console_width, divider_length, desired_max_height, verbose=False):
    global avg_line_width, columns, INTERNAL_LOG
    """
    Determine the optimal number of columns based on console width and desired max height.
    Starts with the maximum possible columns and decreases until a fit is found.
    """

    DEBUG_DETERMINE_OPTIMAL_COLUMNS = False

    #default to 1 col if no lines
    if not lines:
        print(f"⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠ No lines❓❓❓ ⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠")
        return 1

    #ensure global var has been calculated
    if avg_line_width == 0: avg_line_width = 1
    if not avg_line_width  and  avg_line_width != 0: print(f"⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠ Why is avg_line_width == '{avg_line_width}' ???? ⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠")
    elif VERBOSE or DEBUG_DETERMINE_OPTIMAL_COLUMNS: print(f"💦Avg line width: {avg_line_width}")

    #get max line length
    max_line_length = max(wcsarraywidth(line) for line in lines)
    if verbose or DEBUG_DETERMINE_OPTIMAL_COLUMNS: print(f"💥Max line length: {max_line_length}, console_width={console_width}")

    #get max possible columns, then triple it to be sure
    max_possible_columns = console_width // avg_line_width                           # Start with the maximum possible columns based on the average line

    # what if we removed this line... max_possible_columns = max_possible_columns * 3
    # and replaced it with: #GOATGOAT
    max_possible_columns = max_possible_columns + 2

    #make sure max possible columns has been set
    if max_possible_columns == 0: max_possible_columns = 1
    if verbose or DEBUG_DETERMINE_OPTIMAL_COLUMNS: INTERNAL_LOG = INTERNAL_LOG + f"💌Initial max possible columns: {max_possible_columns}"

    #determine max possible columns
    for cols in range(max_possible_columns, 0, -1):
        rows = ceil(len(lines) / cols)
        required_width = cols * max_line_length + (cols -1) * divider_length
        if required_width <= console_width and rows <= desired_max_height:
            if verbose or DEBUG_DETERMINE_OPTIMAL_COLUMNS: print(f"🔍 ??? Optimal columns determined: {cols} with {rows} rows per column")
            #eturn cols #chatgpt20250302
            return max_possible_columns

    #eturn cols #chatgpt20250302
    if verbose or DEBUG_DETERMINE_OPTIMAL_COLUMNS: print(f"‼️‼️‼️‼️‼️‼️ ??? max_possible_columns ===═==══{max_possible_columns}")
    return max_possible_columns
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###




# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def read_input(wrapping, max_width):
    """
    Read input lines from STDIN and optionally wrap them.
    """
    #input_lines = sys.stdin.read().strip().splitlines()

    input_lines=[]


    # Check if an optional filename is provided and exists
    if args.optional_filename:
        if os.path.exists(args.optional_filename):
            with open(args.optional_filename, 'r', encoding='utf-8', errors='replace') as file:
                input_lines.extend(file.readlines())  # Read lines from the file
        else:
            print(f"❗❗❗❗❗❗ Error: The file “{args.optional_filename}” does not exist. ❗❗❗❗❗❗❗")
            sys.exit(1)  # Exit with error code if file does not exist
    else:
        # Read from stdin if no filename is provided
        for line in sys.stdin:
            input_lines.append(line)

    if not input_lines:
        sys.exit(" 💥 No file 💥 ")

    if wrapping:
        wrapped_lines = []
        for line in input_lines:
            wrapped = textwrap.wrap(line, width=max_width) or ['']
            wrapped_lines.extend(wrapped)
        return wrapped_lines
    else:
        return [line.rstrip() for line in input_lines]
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###






# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# Function to format text into columns
def format_columns(lines, columns, column_widths, divider):
    global INTERNAL_LOG
    output = []
    #um_lines = len     (lines)
    num_lines = wcswidth(lines)
    rows_per_col = ceil(num_lines / columns) if columns > 0 else 1
    column_lines = [lines[i * rows_per_col:(i + 1) * rows_per_col] for i in range(columns)]

    number_of_columns_currently = len(column_widths)

    for row in range(rows_per_col):
        line_parts = []
        for col_index in range(columns):
            #f col_index >= wcswidth(column_widths):                # Defensive check to prevent IndexError
            if col_index >= number_of_columns_currently:            # Defensive check to prevent IndexError
                text = ""
            #lif row < wcswidth(column_lines[col_index]):
            elif row < number_of_columns_currently:
                text = column_lines[col_index][row]
            else:
                text = ""                                           # Handle empty cells
            #f col_index < wcswidth(column_widths):                 # Ensure column_widths[col_index] exists
            if col_index < number_of_columns_currently:             # Ensure column_widths[col_index] exists
                line_parts.append(text.ljust(column_widths[col_index]))
            else:
                line_parts.append(text)                             # If somehow missing, append without padding

        line = divider.join(line_parts)
        INTERNAL_LOG = INTERNAL_LOG + f"🌿🌿🌿🌿🌿 Processed row #️⃣{row_num}:\n\t{line_parts}\n🌿🌿🌿🌿🌿 Into: \n{line}\t🌿🌿🌿is_too_wide={is_too_wide}"

        #NTERNAL_LOG = INTERNAL_LOG + f"line_parts={line_parts}\n"
        #dummy__is_to_wide__dummy, internal_log_fragment = log_line_parts_and_process_them_too([line], row, column_widths, "")
        output.append(line)

    return output
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def distribute_lines_into_columns_PRODTIL202510(lines, columns, rows_per_col):
    global VERBOSE
    """
    Distribute lines into the specified number of columns.
    """
    columns_data = []
    for col in range(columns):
        start_index = col         * rows_per_col
        end_index   = start_index + rows_per_col
        column      = lines[start_index:end_index]
        columns_data.append(column)

    if VERBOSE:
        print(f"✍ distributed lines into {columns} columns")
        print(f"💥columns_data={columns_data}")

    return columns_data
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def distribute_lines_into_columns(lines, columns, rows_per_col):
    global VERBOSE
    """
    Distribute lines into the specified number of columns.
    Keeps ANSI formatting for display but calculates widths correctly.
    """

    # Prepare empty columns
    columns_data = [[] for _ in range(columns)]

    for col in range(columns):
        start_index = col * rows_per_col
        end_index   = start_index + rows_per_col
        column_lines = lines[start_index:end_index]

        # Store original lines for display
        columns_data[col] = column_lines

        # Optional: calculate widths using stripped lines if you need max column widths
        max_width = max((len(strip_ansi(line)) for line in column_lines), default=0)
        if VERBOSE:
            print(f"📏 Column {col} max width (visible chars): {max_width}")

    if VERBOSE:
        print(f"✍ distributed lines into {columns} columns")
        print(f"💥columns_data={columns_data}")

    return columns_data
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def calculate_column_widths_PRODTIL202510(columns_data):
    """
    Calculate the maximum width for each column.
    """
    column_widths = []
    for col in columns_data:
        if col:
            #ax_width = max(len     (line) for line in col)
            max_width = max(wcswidth(line) for line in col)
        else:
            max_width = 0
        column_widths.append(max_width)
    return column_widths
def calculate_column_widths(columns_data):
    """
    Given a list of columns (each a list of lines), return the max visible width per column.
    ANSI codes are ignored for width calculation.
    """
    column_widths = []
    for col_idx, column_lines in enumerate(columns_data):
        # Max width of any line in this column, ignoring ANSI
        max_width = max((len(strip_ansi(line)) for line in column_lines), default=0)
        column_widths.append(max_width)
    return column_widths
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def log_line_parts_and_process_them_too(line_parts, row_num, column_widths, rendered_row):
    global INTERNAL_LOG, record_working_column_length, console_width, console_height
    INTERNAL_LOG_LOCAL = ""
    """
    Logs the details of each element in line_parts with their lengths and positions.

    Args:
        line_parts (list): List of strings representing parts of a line.
        row_num (int): The current row number.
        column_widths (list): List of column widths.
        rendered_row: the actual fully rendered version of the row, so we can double-check that we are within proper width parameters
    Returns:
        str: Updated INTERNAL_LOG_LOCAL with the new entries.
    """
    too_wide = False
    max_row_width = 0
    for col_num, (part, width) in enumerate(zip(line_parts, column_widths), start=1):
        part_width   = wcswidth(part)
        col_width    = column_widths[col_num-1]
        stripped_row = strip_ansi(rendered_row)
        #en2         =        len(stripped_row)
        len2         =   wcswidth(stripped_row)
        if col_num == 1:
            tmpstr = f"\n🪓 Row {row_num}:      Length={len2:3} / length2={len2:3} / con width={console_width}\n{rendered_row}\n"
            INTERNAL_LOG_LOCAL = INTERNAL_LOG_LOCAL + tmpstr
        INTERNAL_LOG_LOCAL     = INTERNAL_LOG_LOCAL + f"        ❕ Column {col_num} width={col_width:2} ... part width={part_width:2} \n"
        #GOAT should this be ≥ and not >?
        if len2 > console_width:
            too_wide = True
            if VERBOSE: print(f"🪓{columns} columns causes overflow on row {row_num} because len2:{len2} > col_width={console_width}!\n{stripped_row}\n{rendered_row}")
        if too_wide and not FORCE_COLUMNS: break
    if not too_wide:
            if VERBOSE: print(f"💥   checking if columns={columns} > record_working_column_length={record_working_column_length}")
            if columns > record_working_column_length:
                record_working_column_length = columns
                if VERBOSE: print(f"💥   record_working_column_length is now {record_working_column_length}")
    if VERBOSE: print(f"🪓   ...Returning: log_line_parts_and_process_them_too return {too_wide}, INTERNAL_LOG_LOCAL\n")
    return too_wide, INTERNAL_LOG_LOCAL
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###












##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#####                  SUBROUTINES:
##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════





# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def render_columns(columns_data, column_widths, divider):
    """
    Render the columns with proper alignment and fixed-width dividers.

    Args:
        columns_data  (list of lists): Distributed lines per column.
        column_widths (list):          Maximum width for each column.
        divider       (str):           The string used to separate columns.

    Returns:
        list of strings: Each string represents a formatted row.
    """
    global VERBOSE, WORD_HIGHLIGHTING

    #print(f"word_highlighting is {WORD_HIGHLIGHTING}")

    if columns_data: rows_per_col = max(len(col) for col in columns_data)
    else:            rows_per_col = 1
    if VERBOSE: print(f"😷😷😷😷😷 Recalculated rows per column as: {rows_per_col}")

    stripe=""
    rendered_rows = []
    for row in range(rows_per_col):
        row_parts = []
        for current_column_index, current_column in enumerate(columns_data):
            current_column_width = column_widths[current_column_index]
            if VERBOSE: print(f"😷 Rendering rows: row {row}, col {current_column_index} is: {current_column}")
            if row < len(current_column): part = current_column[row]
            else:
                part = ""
                if VERBOSE: print(f'⚠🚫 assigned "" to part ')

            # pad "part" into "padded_part"
            current_content_width   = wcswidth(part)
            #print(              f"[[[wcswidth(part)={current_content_width},part={part}]]]")
            num_spaces_to_add       = current_column_width - current_content_width
            spacer                  = num_spaces_to_add * " "
            if WORD_HIGHLIGHTING:
                part_to_use, stripe = consistent_word_highlight(part)
                #print(f"APPLYING HIGHLIGHTING TO: {part}")
            else:
                part_to_use         = part
            padded_part             = part_to_use + spacer

            # append "padded part" to our row:
            row_parts.append(padded_part)

        # Join the rows together with the divider
        rendered_row = divider.join(row_parts)
        rendered_rows.append(rendered_row)
        #print (f"🍎 hey stripe is {stripe}")
    return rendered_rows, stripe
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###






# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def debug_info(columns, width, desired_max_height, console_width, console_height, input_lines, formatted_output):
    """
        Debug function to display layout information
    """
    longest_length=9999999999999
    if formatted_output:
        try:
            longest_line = max(formatted_output, key=len)                                             # Use key=len to find the longest line based on length
            longest_length = wcswidth(longest_line)                                                   # how wide is the longest line? [len() won't cut it here due to double-wide chars]
            longest_lines = [line for line in formatted_output if wcswidth(line) == longest_length]   # Find all lines that share the maximum length
        except ValueError:
            longest_line = ''             # This block of code is precautionary;
            longest_length = 0            # it shouldn't be reached, since we've
            longest_lines = []            # checked if formatted_output is not empty

    total_width = longest_length                                                                 #old formula was: total_width = sum(column_widths) + (divider_visible_length * (columns - 1))    #rows_per_col = ceil(wcswidth(input_lines) / columns) if columns > 0 else 1    #if rows_per_col < 1: rows_per_col=1
    aspect_ratio = calculate_aspect_ratio(total_width, rows_per_col) if rows_per_col > 0 else float('inf')
    aspect_diff = abs(aspect_ratio - 1.0)
    divider = "🌟🌟🌟🌟🌟🌟🌟🌟"
    print(f"\n\033[38;2;187;0;0m{divider}DEBUG INFO:{divider}\033[0m" + INTERNAL_LOG)
    print(f"Rows original: {wcswidth(input_lines)}")
    print(f"Rows after:    {wcswidth(formatted_output)}")
    print(f"Columns used:  {columns}")
    #rint(f"Width of each column: {column_widths}")
    print(f"Total width:   {total_width}   (console_width:{console_width}, height:{console_height})")
    #rint(f"Rows per column: {rows_per_col}")
    print(f"Aspect Ratio (Width/Height): {aspect_ratio:.2f}")
    print(f"Aspect Ratio diff from 1.00: {aspect_diff :.2f}")
    print(f"Detected screen  width: {console_width}")
    print(f"Detected screen height: {console_height}")
    print(f"Desired     max height: {desired_max_height}")
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###



# ═════════════════════════════════════════════════════════════════════════════════
def remove_trailing_blank_line(output):
    # Split into lines, remove trailing empty lines, and rejoin
    lines = output.splitlines()
    while lines and lines[-1] == "":
        lines.pop()
    retval = "\n".join(lines) + "\n"  # Add back a single newline at the end
    print(f"return value is:\n[[[[[{retval}]]]]]")
    return retval
# ═════════════════════════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════════════════════════
def remove_trailing_blank_lines(output):
    # Normalize line endings for consistent processing
    normalized_output = output.replace("\r\n", "\n")
    # Split into lines
    lines = normalized_output.splitlines()
    # Remove all trailing blank lines
    while lines and lines[-1].strip() == "":
        lines.pop()
    # Join lines back with original Windows-style line endings
    return "\r\n".join(lines) + "\r\n" if lines else ""
# ═════════════════════════════════════════════════════════════════════════════════



# ════════════════════════════════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════════ WORD HILIGHTING: BEGIN:
# ════════════════════════════════════════════════════════════════════════════════════════════════════════
def string_to_color(word):
    """
    Convert a string to a deterministic RGB color.
    """
    global NUMBER_OF_CHARACTERS_TO_CONSIDER_FOR_STRIPE_COLOR
    #print(f"called string_to_color({word})\t",end="")

    word = word[:NUMBER_OF_CHARACTERS_TO_CONSIDER_FOR_STRIPE_COLOR]

    #prep our word
    word_clean = unicodedata.normalize('NFC', word.upper())
    word_clean = word_clean.upper().replace("'","").replace("’","").replace("`","").replace("-","").replace(".","").replace('е', 'e')  # that last one is replacing Cyrillic 'е' with Latin 'e'
    #print([ord(c) for c in word_clean])  # Check the code points

    wordfg  =     word_clean    .encode('utf-8')    # strip out characters that we don’t want to modify the color of a word, if it’s in one set and not another. For example, “can’t” and “cant” should be same color:
    wordbg = f"bg{word_clean}bg".encode('utf-8')                                                                                  # make bg color different by modifying the string a bit

    #print(f"wordclean: {word_clean} // wordfg: {wordfg}\twordbg: {wordbg}")


    #hash our word
    hash_value1 = int(hashlib.sha256(wordfg).hexdigest(), 16)  # Hash the word to get a consistent integer for foreground ... don’t consider apostrophes/periods/etc so that the word is colored the same apostrophe or not
    hash_value2 = int(hashlib.sha256(wordbg).hexdigest(), 16)  # Hash the word to get a consistent integer for background ... don’t consider apostrophes/periods/etc so that the word is colored the same apostrophe or not
    #print(f"hv1={hash_value1} //",end="")

    # calculate colors
    hue1        = hash_value1 %     360                                             # Map the hash value to a foreground hue (0-360 degrees)
    hue2        = hash_value2 % int(360*MAX_BACKGROUND_INTENSITY)                   # Map the hash value to a background hue (0-[360*max_bg_intensity] degrees)
    hue2        = hash_value2 %     360                                             # Map the hash value to a background hue (0-[360*max_bg_intensity] degrees)
    lightness   = LIGHTNESS                                                         # Saturation and lightness are kept constant for distinct colors
    saturation  = SATURATION                                                        # Saturation and lightness are kept constant for distinct colors

    # convert colors
    r , g , b   = hsl_to_rgb(hue1, saturation, lightness)                           # Convert HSL to RGB: foreground
    rb, gb, bb  = hsl_to_rgb(hue2, saturation, MAX_BACKGROUND_INTENSITY)            # Convert HSL to RGB: background

    # set background color
    background  = apply_background_color(gb, bb, rb)                                # Apply a subtle background color: scramble it up a bit by changing rgb=>gbr

    #print(f"c returned r={r:3},g={g:3},b={b:3},background={background}")
    return r, g, b, background                                                      # Return our values
# ═════════════════════════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════════════════════════
def hsl_to_rgb(h, s, l):
    """
    Convert HSL color to RGB.
    """
    c =     (1 - abs(       2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l -                 c / 2
    if     0 <= h <  60: r, g, b = c, x, 0
    elif  60 <= h < 120: r, g, b = x, c, 0
    elif 120 <= h < 180: r, g, b = 0, c, x
    elif 180 <= h < 240: r, g, b = 0, x, c
    elif 240 <= h < 300: r, g, b = x, 0, c
    else:                r, g, b = c, 0, x
    r = (r + m) * 255
    g = (g + m) * 255
    b = (b + m) * 255
    return int(r), int(g), int(b)
# ═════════════════════════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════════════════════════
def apply_background_color(r, g, b):
    """
    Apply a subtle background color to the text.
    """
    luminance            = 0.2126 * r + 0.7152 * g + 0.0722 * b                                                           # Calculate the luminance of the text color
    background_intensity =      MAX_BACKGROUND_INTENSITY * (1 - luminance / 255)                                          # Determine the background color intensity based on luminance
    background           = (int(r * background_intensity), int(g * background_intensity), int(b * background_intensity))  # Apply the background color
    return background
# ═════════════════════════════════════════════════════════════════════════════════






# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def normalize_for_highlight(word):
    word = re.split(r"[-–—━]", word, 1)[0]  # truncate at first hyphen-like character
    if word == "’round"  or word == "around": word = "around"                        # ❶ different ways to express the same word should be drawn  the same color so it doesn’t appear like a mismatch①①
    if word == "versus"  or word ==   "v.s.": word = "vs"                            # ❶ different ways to express the same word should be drawn  the same color so it doesn’t appear like a mismatch
    word = word.replace("’ve", "").replace("'ve", "").replace("´ve", "")             # ❷ makes word-variants like “should’ve”  and  “should have” the same color so it doesn’t appear like a mismatch
    word = word.replace("’s" ,"s").replace("'s" ,"s").replace("´s" ,"s")             # ❷ makes word-variants like  “there’s”   and    “there is”  the same color so it doesn’t appear like a mismatch
    word = word.replace("’"  , "").replace("'"  , "").replace("´"  , "")             # ❸ variations in which apostrophe we use should all be made the same color so it doesn’t appear like a mismatch
    if word.endswith("ing"): word = word[:-3] + "in"                                 # ❹ makes word-variants like “coping” vs “copin’” vs “copin” the same color so it doesn’t appear like a mismatch

    word = unicodedata.normalize('NFC', word)
    for cyrillic_char, latin_char in char_map.items():
            word = word.replace(cyrillic_char, latin_char)

    #print (f"word={word}")
    return word
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


# ═════════════════════════════════════════════════════════════════════════════════
words_used=""
striped_text = []
def consistent_word_highlight(text):
    global words_used, striped_text, WORD_HIGHLIGHT_LEN_MIN
    """
    Highlight words in the text that are longer than WORD_HIGHLIGHT_LEN_MIN.
    """
    highlighted_text = []
    #striped_text    = []  # reset every time
    word             = ''
    in_highlight     = False                                                            # Track whether we're currently inside a highlighted word

    # cosmetic buff:
    text2use = text.replace('--','——');                                                 # double-hyphens are really meant to be em-dashes (“—”), however, windows terminal displays em-dashes as a single character in width, so we have to make two of them to not potentially upset the width (NOT length) of the string.

    for char in text2use:
        #f char.isalnum() or char in {"’", "'", "´", "-", "–", "—"}:                    # Building a word: punctuation that we still want to consider part of the word
        if char.isalnum() or char in {"’", "'", "´", "-", "–"     }:                    # Building a word: punctuation that we still want to consider part of the word —— maybe en-dash should NOT be on the list afterall?
            if               char in {"’", "'", "´"}: char = "’"                        # Building a word: replace dumb apostrophes with smart apostrophes
            word += char
        else:
            normalized_word = normalize_for_highlight(word)


            # To keep stripe alignment more consistent, we exclude words that start with -/–/— because they are hyphenated word segments:
            if normalized_word.startswith('-') or normalized_word.startswith('–') or normalized_word.startswith('—'):
                highlighted_text.append(word)
                highlighted_text.append(char)
                word = ''
                continue



            #f len(           word) >= WORD_HIGHLIGHT_LEN_MIN:                          # Word is long enough for highlighting  ... this change would cause ’cause to highlight when it really shouldn’t .. I forget why this was the best change to make at one point
            if len(normalized_word) >= WORD_HIGHLIGHT_LEN_MIN:                          # Word is long enough for highlighting

                if not in_highlight:                                                    # Start highlighting
                    #normalized_word = normalize_for_highlight(word)                    #moved above so we can check length AFTER normalizatoin process
                    r, g, b, background = string_to_color(normalized_word)
                    payload    = f"\033[38;2;{r};{g};{b}m\033[48;2;{background[0]};{background[1]};{background[2]}m"
                    stripeload = f"\033[38;2;{background[0]};{background[1]};{background[2]}m\033[48;2;{r};{g};{b}m"
                    highlighted_text.append(payload)
                    striped_text.    append(payload)
                    #print(f"adding payload to striped text: “{payload}”")
                    in_highlight = True
                if not words_used: words_used =                    word
                else:              words_used = words_used + " " + word
                payload = word + "\033[0m"
                highlighted_text.append(payload)                                        # Reset formatting after the word
                #print(f"adding payload to striped text: “{payload}”")
                striped_text.    append(payload)
                in_highlight = False
            else:
                highlighted_text.append(word)                                           # Just append the word without highlighting
            highlighted_text.append(char)                                               # Append the non-word character (punctuation, space, etc.)
            word = ''


    if word:
        normalized_word = normalize_for_highlight(word)
        if len(normalized_word) >= WORD_HIGHLIGHT_LEN_MIN:
            r, g, b, background = string_to_color(normalized_word)
            ansi = f"\033[38;2;{r};{g};{b}m\033[48;2;{background[0]};{background[1]};{background[2]}m"
            payload = word + "\033[0m"                                                  # todo maybe try this with normalized_word if the stripe doesn’t match for some reason
            striped_text    .append(ansi)
            striped_text    .append(payload)
            highlighted_text.append(ansi + payload)
        else:
            words_used = words_used + " " + word                                        # ?
            highlighted_text.append(word)                                               # todo maybe try this with normalized_word if the stripe doesn’t match for some reason


    #print (f"🍏 hey striped_text is {striped_text}")
    return ''.join(highlighted_text), striped_text
# ═════════════════════════════════════════════════════════════════════════════════



# ═════════════════════════════════════════════════════════════════════════════════
import re

def convert_stretched_stripe(stripe, columns, console_width):
    result = ''
    words = []

    for i in range(0, len(stripe), 2):
        if i + 1 < len(stripe):
            word = stripe[i + 1].split('\x1b')[0]
        else:
            word = stripe[i].split('m', 1)[-1].split('\x1b')[0]
        words.append(word)

    num_words = len(words)
    min_per_word_width = 2
    #if num_words * min_per_word_width > console_width:
    #    return "(stripe too wide)"

    max_letters = 2
    while max_letters * num_words > console_width and max_letters > 1:
        max_letters -= 1

    total_chars = max_letters * num_words
    total_padding = console_width - total_chars
    if num_words:   base_pad = total_padding // num_words
    else:           base_pad = total_padding
    if num_words:  extra_pad = total_padding  % num_words
    else:          extra_pad = total_padding

    for i in range(0, len(stripe), 2):
        ansi_raw = stripe[i]
        word = stripe[i + 1].split('\x1b')[0] if i + 1 < len(stripe) else ""

        # Parse 38 = bg, 48 = fg (because of the flip done in stripeload)
        bg_match = re.search(r'38;2;(\d+);(\d+);(\d+)', ansi_raw)  # actual bg
        fg_match = re.search(r'48;2;(\d+);(\d+);(\d+)', ansi_raw)  # actual text color

        if not (fg_match and bg_match):
            continue

        r_bg, g_bg, b_bg = map(int, bg_match.groups())  # ← visual background
        r_fg, g_fg, b_fg = map(int, fg_match.groups())  # ← current text color

        # Check if background is too blue or dark
        luminance = 0.2126 * r_bg + 0.7152 * g_bg + 0.0722 * b_bg
        is_blueish = b_bg > max(r_bg, g_bg) and b_bg > 100
        is_dark = luminance < 80

        if is_blueish or is_dark:
            r_fg, g_fg, b_fg = 255, 255, 255  # use white text

        # Build the ANSI stripe block: foreground (text) then background (box)
        ansi = f"\033[38;2;{r_fg};{g_fg};{b_fg}m\033[48;2;{r_bg};{g_bg};{b_bg}m"

        if len(word) >= 2 and max_letters >= 2:
            letters = word[0].upper() + word[1].lower()
        else:
            letters = word[:1].upper()

        pad = base_pad + (1 if extra_pad > 0 else 0)
        if extra_pad > 0:
            extra_pad -= 1

        left = pad // 2
        right = pad - left
        right_segment = f"{' ' * right}"
        #f right_segment and right_segment[-1] == ' ': right_segment = right_segment[:-1]                 +  '▕'
        if right_segment and right_segment[-1] == ' ': right_segment = right_segment[:-1] + ANSI_FG_BLACK +  '▕'
        result += f"{ansi}{' ' * left}{letters}{right_segment}\033[0m"

    return result
# ═════════════════════════════════════════════════════════════════════════════════


# ═════════════════════════════════════════════════════════════════════════════════
def convert_stretched_stripe_yay(stripe, columns, console_width):
    result = ''
    words = []

    # Step 1: Extract the words from the stripe array
    for i in range(0, len(stripe), 2):
        if i + 1 < len(stripe):
            word = stripe[i + 1].split('\x1b')[0]  # Extract the word before the ANSI reset sequence
            words.append(word)
        else:
            split_code_word = stripe[i].split('m', 1)
            word_with_reset = split_code_word[1] if len(split_code_word) > 1 else ''
            last_word = word_with_reset.split('\x1b')[0]
            words.append(last_word)

    # Step 2: Calculate how many characters need to be added
    total_characters = len(words)
    total_length = sum(1 for word in words if word)  # One letter from each word

    extra_spaces = console_width - total_length

    # Step 3: Calculate equal padding for each letter
    if total_characters > 0:
        base_padding = extra_spaces // total_characters  # Even padding for each letter
        remaining_padding = extra_spaces % total_characters  # Remainder padding

    # Step 4: Add padding to the result
    for i in range(0, len(stripe), 2):
        if i + 1 < len(stripe):
            ansi_code = stripe[i].replace("38", "temp").replace("48", "38").replace("temp", "48")
            word      = stripe[i + 1].split('\x1b')[0].upper()  # Extract the word

            #1ˢᵗ one did not center/caps the letter
            #esult +=                             f'{ansi_code}{word[0]}' + ' ' *  base_padding                       # Add base padding
            #result += f'{ansi_code} ' * (base_padding // 2) + f'{ansi_code}{word[0]}' + ' ' * (base_padding - base_padding // 2)  # Center the letter

            # Determine stripe width per word segment
            segment_width = base_padding + 1  # 1 char minimum from word + its padding

            # Choose 2-letter output only if wide enough
            if segment_width >= 4 and len(word) >= 2:
                letters = word[0].upper() + word[1].lower()
            else:
                letters = word[0].upper()

            # Center letters in the segment
            pad_total = base_padding
            pad_left  = pad_total // 2
            pad_right = pad_total - pad_left
            result += f'{ansi_code}{" " * pad_left}{letters}{" " * pad_right}\x1b[0m'



            # Step 5: Distribute extra spaces (remaining_padding) based on word length
            if remaining_padding   > 0:
                result            += ' '  # Add an extra space to the longest words
                remaining_padding -= 1

            result += '\x1b[0m'  # Reset ANSI codes
        else:
            split_code_word = stripe[i].split('m', 1)
            ansi_code       = split_code_word[0] + 'm'
            word_with_reset = split_code_word[1] if len(split_code_word) > 1 else ''
            last_word       = word_with_reset.split('\x1b')[0]
            if last_word:
                result += f'{ansi_code}{last_word[0]}' + ' ' * base_padding

                # Distribute remaining padding for last word
                if remaining_padding   > 0:
                    result            += ' '
                    remaining_padding -= 1

                result += '\x1b[0m'  # Reset ANSI codes
    return result
# ═════════════════════════════════════════════════════════════════════════════════


# ═════════════════════════════════════════════════════════════════════════════════
def convert_stripe(stripe, columns):
    result = ''
    for i in range(0, len(stripe), 2):
        if i + 1 < len(stripe):                                         # Swap foreground and background colors
            ansi_code = stripe[i].replace("38", "temp").replace("48", "38").replace("temp", "48")
            word      = stripe[i + 1].split('\x1b')[0]                  # Extract the word before the ANSI reset sequence
            result   += f'{ansi_code}{word[0]}\x1b[0m'                  # Add only the first letter
        else:                                                           # Handle the last element, which includes ANSI code and word together
            split_code_word = stripe[i].split('m', 1)                   # Split only once at the first 'm'
            ansi_code       = split_code_word[0] + 'm'                        # Get the ANSI code part
            word_with_reset = split_code_word[1] if len(split_code_word) > 1 else ''  # Get the word if it exists
            # Remove the ANSI reset sequence and extract the first letter of the word:
            last_word = word_with_reset.split('\x1b')[0]                # Extract the word before the reset sequence
            if last_word:                                               # Safely add the first character of the word to the result if the word exists
                result += f'{ansi_code}{last_word[0]}\x1b[0m'           # Add only the first letter
    return result
# ═════════════════════════════════════════════════════════════════════════════════

# ═════════════════════════════════════════════════════════════════════════════════
# ═════════════════════════════════════════════════════════════════════════════════ WORD HIGHLIGHTING: END






def try_generate_stripe(joined_input_data, max_len=6):
    global WORD_HIGHLIGHT_LEN_MIN, striped_text, DEBUG_STRIPE_GENERATION
    MIN_STRIPE_WIDTH = 4

    for threshold in range(max_len, 0, -1):
        WORD_HIGHLIGHT_LEN_MIN = threshold
        striped_text = []
        #_, _ = render_columns([[joined_input_data]], [len(joined_input_data)], divider)
        _, _ = render_columns([[line] for line in joined_input_data.split(BOT_OFF)], [len(line) for line in joined_input_data.split(BOT_OFF)], divider)

        stripe_rendered = convert_stretched_stripe(striped_text, 1, console_width - 1)
        stripe_width = wcswidth(strip_ansi(stripe_rendered))

        if stripe_width >= MIN_STRIPE_WIDTH:
            return stripe_rendered

        if DEBUG_STRIPE_GENERATION: print(f"⚠️ stripe was empty or too narrow with WORD_HIGHLIGHT_LEN_MIN={threshold} (width={stripe_width})")

    if DEBUG_STRIPE_GENERATION: print("‼️ Unable to generate stripe. Falling back to default test data.")
    return convert_stretched_stripe([
        '\x1b[38;2;255;255;255m\x1b[48;2;0;0;255m',   'NULL\x1b[0m',
        '\x1b[38;2;0;0;0m\x1b[48;2;255;255;0m'    , 'STRIPE\x1b[0m',
        ], 1, console_width - 1)





def get_max_stripped_line_width(text):
    """Return the width of the longest line in `text`, after stripping ANSI escapes."""
    return max((len(strip_ansi(line)) for line in text.splitlines()), default=0)



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###

def main():
    global INTERNAL_LOG, VERBOSE, WRAPPING, STRIPE, FORCE_COLUMNS, FORCED_CONSOLE_WIDTH, console_width, console_height, columns, avg_line_width, record_working_column_length, ROW_PADDING, DEBUG_VERBOSE_COLUMNS, WORD_HIGHLIGHT_LEN_MIN
    our_args = parse_arguments()
    INTERNAL_LOG=""
    stripester=""

    # Try to detect terminal width and height, otherwise use default values
    try:
        console_width, console_height = shutil.get_terminal_size()
    except Exception:
        console_width, console_height = 666, 69
        INTERNAL_LOG = INTERNAL_LOG + "Unable to detect console size. Using default width=666 and height=69."
    if VERBOSE:
        INTERNAL_LOG = INTERNAL_LOG + f" —— Detected console  width of {console_width } ——\n"
        INTERNAL_LOG = INTERNAL_LOG + f" —— Detected console height of {console_height} ——\n"


    # Process our command line parameters:
    WRAPPING = DEFAULT_WRAPPING
    IGNORE_NUMSIGNLINES = False
    width    = args.width or console_width
    if our_args.row_padding:                      ROW_PADDING = our_args.row_padding
    else:                                         ROW_PADDING = DEFAULT_ROWS_ADDED_TO_OUTPUT
    if our_args.wrap:                             WRAPPING = True
    if our_args.no_wrap:                          WRAPPING = False
    if our_args.ignore_numsign_lines_for_stripes: IGNORE_NUMSIGNLINES = True
    if FORCED_CONSOLE_WIDTH:
        if FORCED_CONSOLE_WIDTH > 0 and our_args.console_width: console_width=our_args.console_width


    # read our input data:
    input_data = read_input(WRAPPING, args.max_line_length_before_wrapping)     # Read and process input lines
    tmp_stripped_input_data = [strip_ansi(line) for line in input_data]

    # Calculate avg line width
    avg_line_width  = wcsarraywidth(             input_data, mode="average")    #0
    avg_line_width2 = wcsarraywidth(tmp_stripped_input_data, mode="average")    #17

    if args.verbose: print(f"Avg line width1: {avg_line_width }") # goat
    if args.verbose: print(f"Avg line width2: {avg_line_width2}") # goat


    # Determine the number of columns
    desired_max_height = console_height - ROW_PADDING                           # total height of output before we *must* attempt wrapping columns [which currently always happens anyway]
    if our_args.columns:
        if our_args.columns < 1:
            print("Error: Number of columns must be at least 1.")
            sys.exit(1)

        columns           = our_args.columns
        joined_input_data = "\n".join(input_data)
        rows_per_col      = ceil(len(joined_input_data) / columns)                  # NOT a situation for wcswidth

        if our_args.verbose or VERBOSE: print(f"Using user-specified columns: {columns}\nRows per column: {rows_per_col}")
    else:
        #olumns      = determine_optimal_columns(             input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
        columns      = determine_optimal_columns(tmp_stripped_input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
        rows_per_col = ceil(len(input_data) / columns)                        # NOT a situation for wcswidth


    #Generate Stripe one-line representation
    if STRIPE:
        if IGNORE_NUMSIGNLINES: joined_input_data = (BOT_OFF + " ").join(line for line in input_data if not line.lstrip().startswith("#"))
        else:                   joined_input_data = (BOT_OFF + " ").join(input_data)                                                              #print(f"joined_input_data is {joined_input_data}")
        columns_data      = [[joined_input_data]]                                                                                     #print(f"columns_data is {columns_data}")
        column_widths     = calculate_column_widths(columns_data)                                                                     #print(f"column_widths is {column_widths}")
        striped_text      = []  # 🔧 Reset this so next render_columns() call refills it
        meh, stripeamabob = render_columns(columns_data, column_widths, divider)                                                      #print(f"stripeamabob is {stripeamabob}")     #        striperooni       = convert_stripe(stripeamabob,1)                        #print(f"\nstriperooni is:\n{striperooni}\nand looks like this:"); print(striperooni)       #tripester = format_colored_array(striperooni,console_width-1)
        stripester        = try_generate_stripe(joined_input_data)
        print(stripester)




    #start preliminarily generating output, which we will determine post-generation whether it's too wide or not:
    output            = ""
    keep_looping      = True
    force_num_columns = False
    joined_input_data = "\n".join(input_data)
    while keep_looping:
        is_too_wide = False
        output      = ""

        #calculate # of columns unless we are forcing it:
        if not force_num_columns and not FORCE_COLUMNS:
            #olumns = determine_optimal_columns(             input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
            columns = determine_optimal_columns(tmp_stripped_input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
        if columns == 0: columns = 1

        #rows per column
        rows_per_col = ceil(len(input_data) / columns)                          #NOT a situation for wcswidth
        if VERBOSE: INTERNAL_LOG = INTERNAL_LOG + (f"🚣‍♀️ rows_per_col={rows_per_col}")

        #distribute data into columns & calculate the widths of the columns
        #olumns_data  = distribute_lines_into_columns(tmp_stripped_input_data, columns, rows_per_col)   #loses final formatting
        columns_data  = distribute_lines_into_columns(             input_data, columns, rows_per_col)
        column_widths = calculate_column_widths(columns_data)
        if VERBOSE: print(f"🔧 🔧 🔧 columns_data is {columns_data}\n☀☀ column widths [re]calculated to: {column_widths}")

        #test-render the rows
        rendered_rows, throwaway_stripe = render_columns(columns_data, column_widths, divider)
        if not rendered_rows:
            print("⚠⚠⚠ Warning: rendered_rows is empty. Check the rendering function. ⚠⚠⚠")
        elif VERBOSE:
            print(f"💯💯 rendered_rows length = {len(rendered_rows)}, column_widths={column_widths}")

        if args.verbose: print(f"Column  widths: {    column_widths}")

        #if STRIPE: break

        #render the rows repeatedly, decreasing until they fit within the propr width
        loopybob = enumerate(rendered_rows, start=1)
        for row_num, rendered_row in loopybob:
            if VERBOSE: print(f"🏹🏹🏹🏹🏹🍎🍎🍎 processing row_num {row_num}")
            INTERNAL_LOG_FRAGMENT=""
            line_parts = rendered_row.split(divider)                      # Split the rendered row back into parts based on the divider
            line_parts = [part.strip() for part in line_parts]            # Trim any extra spaces

            #figure out if this line is too long or not, and create important processing info to log *IF* we keep this rendering:
            is_too_wide, INTERNAL_LOG_FRAGMENT = log_line_parts_and_process_them_too(line_parts, row_num, column_widths, rendered_row)

            #if it's too wide, stop bothering to process (unless we are forcing columns):
            if VERBOSE: print(f"🐾🐾 row_num {row_num}... is_too_wide={is_too_wide}")

            #goat chatgpt nuked this and it helped me?!?!!!!!
            #if is_too_wide and not FORCE_COLUMNS and (not STRIPE or TEXT_ALSO):
            #    if VERBOSE: print(f"🐾🐾 breaking")
            #    break

            #we kept this rendering, so add the important processing info to the log
            INTERNAL_LOG = INTERNAL_LOG + INTERNAL_LOG_FRAGMENT

            #add our rendered row to our output:
            output += rendered_row.replace("Æ","’") + ANSI_EOL + "\n"              # the mis-encoded apostrophe fix is not a very tenable fix, but the ANSI_EOL is *VERY IMPORTANT*!!
            #output += f"RENDERED ROW: {repr(rendered_row)}"
            #🐱🐱🐱 if VERBOSE: print(f"🤬🤬 row_num {row_num}... is_too_wide={is_too_wide}\n⚙ ⚙ ⚙ OUTPUT SO FAR:\n{ANSI_BLINK_ON}{ANSI_COLOR_GREY}{output}{ANSI_BLINK_OFF}{ANSI_RESET}⚙ ⚙ ⚙ That's it!")

            #print("loopybob")
            if STRIPE and not TEXT_ALSO:
                #print("breaking")
                break

        if not STRIPE:
            widest_output_line = get_max_stripped_line_width(output)
            if VERBOSE: INTERNAL_LOG = INTERNAL_LOG + f"🥒 ❷ widest_output_line for columns={columns} is “{widest_output_line}” ...  console_width={console_width} 🥒"
            if widest_output_line > console_width: is_too_wide = True

        #now that we have rendered our row, figure out if we are done or not:
        keep_looping = False                                                       # only keep looking if things required a redo
        force_num_columns = False                                                  # keep track of forced-column mode
        if is_too_wide and not FORCE_COLUMNS:                                      # ignore the error of things being too wide if we are in forced-columns mode
            keep_looping = True                                                    # keep looping, but with a lower number of coumns
            columns = columns - 1                                                  # next time, try with 1 fewer columns
            force_num_columns = True                                               # internally, we are now forcing the number of columns to be the 1 fewer that we set in the previous line
            #bad logic: if columns == 1: keep_looping = False                     if we are down to 1 column, there's no more to check, so stop
            if columns == 0:                                                       # if we are down to 0 columns, go back to 1 and quit
                columns = 1
                keep_looping = False
            if VERBOSE: INTERNAL_LOG = INTERNAL_LOG + f"🤬🤬 ACTING ON IT ——> columns is now {columns}"
        if STRIPE and not TEXT_ALSO:  keep_looping = False
        if VERBOSE: INTERNAL_LOG = INTERNAL_LOG + f"🤬🤬🤬🤬 FINAL_COLUMNS ——> columns is now {columns}"   #debug
        #print(F"keep_looping is {keep_looping}")

    # Optionally, print the internal log
    if VERBOSE:
        print("\nInternal Log:")
        print(INTERNAL_LOG)
    if VERBOSE or DEBUG_VERBOSE_COLUMNS:
        print(f"🥒 num_columns={columns} ... column_widths={column_widths} 🥒")
        print(f"🥒 ❶ widest_output_line={widest_output_line} ...  🥒")

    if VERBOSE:
        #print(f"🥒  output=🥒 {output}\n")
        #print(f'💔input_data=' + "\n".join(input_data) + '\n')
        pass
    if VERBOSE or DEBUG_VERBOSE_COLUMNS:
        print(f"🥒 console_width=🥒 {console_width}...")
        print(f"💿 record_working_column_length={record_working_column_length}")
    if VERBOSE:
        print(f"💿 stripe={STRIPE}")
        print(f"💿 WORD_HIGHLIGHTING={WORD_HIGHLIGHTING}")
        print(f"💿 words_used={words_used}")
        print(f"💿 stripester={stripester}")



    #══════════════════════════════════════════════════════════════════════#
    # 🎉🎉🎉 ⭐⭐⭐⭐ THE FILE IS GONNA BE PRINTED RIGHT HERE ⭐⭐⭐⭐ 🎉🎉🎉 #
    # output="" at the end of each line:                                   #
    if (output==""):                                                       #
        print("\n".join(input_data))                                       #
        if VERBOSE: print("❕‼ OUTPUT EMPTY. Joined input_data manually ❕‼")#
    #══════════════════════════════════════════════════════════════════════#
    # 🎉🎉🎉 ⭐⭐⭐⭐⭐ FILE IS ACTUALLY PRINTED RIGHT HERE: ⭐⭐⭐⭐⭐ 🎉🎉🎉 #
    else:                                                                  #
        if not STRIPE or TEXT_ALSO:                                        #
            trimmed_output = remove_trailing_blank_lines(output)           #
            if WORD_HIGHLIGHTING:                                          #
                highlighted_output = trimmed_output                        #
                print(highlighted_output, end="")                          #
            else:                                                          #
                print(    trimmed_output, end="")                          #
    #══════════════════════════════════════════════════════════════════════#


    #print(f"word_highlighting is {WORD_HIGHLIGHTING}")


# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###

if __name__ == "__main__":
    main()



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═════════════════════════════════════════════════  O L D   N O T E S  ═════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###

#NOTES for when I was trying to make the output a square: font coefficient = 1.4! that's what i got! #lhecker@github: Generally speaking, you can assume that fonts have roughly an aspect ratio of 2:1. It seems you measured the actual size of the glyph though which is slightly different from the cell height/width.


