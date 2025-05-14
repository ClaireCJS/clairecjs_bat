#TODO: bg color is same as fg bug-ish??

DEBUG_VERBOSE_COLUMNS = False

#### USER CONFIGURATION:
NUMBER_OF_CHARACTERS_TO_CONSIDER_FOR_STRIPE_COLOR = 19                            # we don’t need to look very far into words to get unique colors. Wider than 25 we start to get into subtitle-split-word territory where words >25chars get split into 2 lines and become a differently-colored stripe segment even though they were technically the same word.
DEFAULT_ROW_PADDING                               = 7                             # SUGGESTED: 7. Number of rows to subtract from screen height as desired maximum output height before adding columns. May not currently do anything.
content_ansi                                      =  "\033[0m"
divider_ansi                                      =  "\033[38;2;187;187;0m"
#content_ansi                                     =  "\033[42m\033[31m"
divider                                           = f"  {divider_ansi}" + "│" + f"  {content_ansi}"  # Divider with #BBBB00 color and additional padding

#TODO: deal with situation of lines that are sooo long that we'd really have to wrap them to fit? or is this fine?
#TODO: maybe make each column a slightly different color

#font coefficient = 1.4! that's what i got!
#lhecker@github: Generally speaking, you can assume that fonts have roughly an aspect ratio of 2:1. It seems you measured the actual size of the glyph though which is slightly different from the cell height/width.

#define some ANSI codes we plan to use
BLINK_ON   = "\033[6m"
BLINK_OFF  = "\033[25m"
FAINT_ON   = "\033[2m"
FAINT_OFF  = "\033[22m"
COLOR_GREY = "\033[90m"
ANSI_RESET = "\033[39m\033[49m\033[0m"





##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
##### INIT LIBRARIES:
import sys
import argparse
from   math         import ceil
import re
import textwrap
import shutil
from   rich.console import Console                                        #shutil *and* os do *NOT* get the right console dimensions under Windows Terminal
import colorama
from   colorama     import Fore, Style
from   wcwidth      import wcswidth
sys.stdin .reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
colorama.init()
#print(Fore.RED + "This text should be red." + Style.RESET_ALL)




##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
##### GLOBAL VARIABLES:
divider_visible_length       = 5
DEFAULT_WRAPPING             = False                                            #do we default to enabling the wrapping of long lines
WRAPPING                     = DEFAULT_WRAPPING
STRIPE                       = False
VERBOSE                      = False
WORD_HIGHLIGHTING            = False
FORCE_COLUMNS                = False
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

def parse_arguments():
    global STRIPE, WRAPPING, VERBOSE, FORCE_COLUMNS, FORCED_CONSOLE_WIDTH, args, console_width, console_height, WORD_HIGHLIGHTING

    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Display STDIN in a compact, multi-column format.")

    # Optional positional argument for the filename
    parser.add_argument('optional_filename'                        , nargs='?', type=str,  help="Optional filename to process. If not provided, input is from STDIN.")
    parser.add_argument( '-w', '--width'                           , type=int,             help="Override output width to something other than console width")
    parser.add_argument('-cw', '--console_width'                   , type=int,             help="Override detected console width")
    parser.add_argument( '-c', '--columns'                         , type=int,             help="Override number of columns calculation")
    parser.add_argument( '-p', '--row_padding'                     , type=int, default=7,  help="Number of rows to subtract from screen height as desired maximum")
    parser.add_argument( '-v', '--verbose'                         , action='store_true',  help="Verbose mode—display debug info and internal logs")
    parser.add_argument('-wh', '--word_highlighting'               , action='store_true',  help="Word Highlighting")
    parser.add_argument('-st', '--stripe'                          , action='store_true',  help="generate a visual stripe summary instead")
    parser.add_argument('-wr', '--wrap'                            , action='store_true',  help="Enable line wrapping for long lines")
    parser.add_argument('-nw', '--no_wrap'                         , action='store_true',  help="Disable line wrapping for long lines")
    parser.add_argument('-ll', '--max_line_length_before_wrapping' , type=int, default=999, help="Maximum line length before wrapping")     #was 80 for like 6 months but changed to 999 2025/03/03
    args = parser.parse_args()
    ROW_PADDING          = args.row_padding
    VERBOSE              = args.verbose
    WORD_HIGHLIGHTING    = args.word_highlighting
    FORCE_COLUMNS        = args.columns
    FORCED_CONSOLE_WIDTH = args.console_width
    STRIPE               = args.stripe
    if STRIPE: WORD_HIGHLIGHTING = True                         #stripe is really an abbreviated form of word_highlighting mode
    return parser.parse_args()



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07|P[^\\]*\\)')
def strip_ansi(text):
    """
    Strip ANSI escape codes

    Requires global var ANSI_ESCAPE as the compiled regex to remove all codes
    Suggested value: ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07|P[^\\]*\\)')

    """
    global ANSI_ESCAPE
    return ANSI_ESCAPE.sub('', text)
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###







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

    widths = [wcswidth(s) for s in strings]

    retval = None
    if   mode == "total": return sum(widths)
    elif mode ==   "max": return max(widths)
    elif mode == "average" or mode == "avg":
        if division_mode == "integer": retval = sum(widths) // len(widths)  # Use integer division to get a whole number
        else                         : retval = sum(widths) /  len(widths)  # Use float   division to get a whole number
    else:
        raise ValueError("Invalid mode. Use 'total', 'max', or 'average'/'avg'.")
    if VERBOSE: print(f"🔰 wcsarraywidth returning retval={retval}")
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

    #default to 1 col if no lines
    if not lines:
        print(f"⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠ No lines❓❓❓ ⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠")
        return 1

    #ensure global var has been calculated
    if avg_line_width == 0: avg_line_width = 1
    if not avg_line_width and avg_line_width !=  0: print(f"⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠ Why is avg_line_width == '{avg_line_width}' ???? ⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠")
    elif   VERBOSE                                : print(f"Avg line width: {avg_line_width}")

    #get max line length
    max_line_length = max(wcsarraywidth(line) for line in lines)
    if verbose: print(f"Max line length: {max_line_length}")

    #get max possible columns, then triple it to be sure
    max_possible_columns = console_width // avg_line_width                           # Start with the maximum possible columns based on the average line
    max_possible_columns = max_possible_columns * 3

    #make sure max possible columns has been set
    if max_possible_columns == 0: max_possible_columns = 1
    if verbose: INTERNAL_LOG = INTERNAL_LOG + f"Initial max possible columns: {max_possible_columns}"

    #determine max possible columns
    for cols in range(max_possible_columns, 0, -1):
        rows = ceil(len(lines) / cols)
        required_width = cols * max_line_length + (cols -1) * divider_length
        if required_width <= console_width and rows <= desired_max_height:
            if verbose: print(f"🔍 ??? Optimal columns determined: {cols} with {rows} rows per column")
            #eturn cols #chatgpt20250302
            return max_possible_columns

    #eturn cols #chatgpt20250302
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
        import os
        if os.path.exists(args.optional_filename):
            with open(args.optional_filename, 'r', encoding='utf-8') as file:
                input_lines.extend(file.readlines())  # Read lines from the file
        else:
            print(f"❗❗❗❗❗❗ Error: The file “{args.optional_filename}” does not exist. ❗❗❗❗❗❗❗")
            sys.exit(1)  # Exit with error code if file does not exist
    else:
        # Read from stdin if no filename is provided
        for line in sys.stdin:
            input_lines.append(line)

    if not input_lines:
        sys.exit("No input data provided.")

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
def distribute_lines_into_columns(lines, columns, rows_per_col):
    global VERBOSE
    """
    Distribute lines into the specified number of columns.
    """
    columns_data = []
    for col in range(columns):
        start_index = col * rows_per_col
        end_index = start_index + rows_per_col
        column = lines[start_index:end_index]
        columns_data.append(column)

    if VERBOSE:
        print(f"✍ distributed lines into {columns} columns")
        print(f"💥columns_data={columns_data}")

    return columns_data
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def calculate_column_widths(columns_data):
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
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###



# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def log_line_parts_and_process_them_too(line_parts, row_num, column_widths, rendered_row):
    global INTERNAL_LOG, record_working_column_length
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
            #print(f"INTERNAL_LOG_LOCAL = {INTERNAL_LOG_LOCAL}")
            tmpstr = f"\n🪓 Row {row_num}:      Length={len2:3} / length2={len2:3} / con width={console_width}\n{rendered_row}\n"
            #tmpstr = tmpstr + f"{stripped_row}\n"
            INTERNAL_LOG_LOCAL = INTERNAL_LOG_LOCAL + tmpstr
        #NTERNAL_LOG_LOCAL     = INTERNAL_LOG_LOCAL + f"\tColumn {col_num}={col_width} {len     (part):2}  Length: {part.ljust(width)} \n"
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
            current_content_width   = wcswidth(part)                                                        #print(f"[[[part={part}]]]")
            num_spaces_to_add       = current_column_width - current_content_width
            spacer                  = num_spaces_to_add * " "
            if WORD_HIGHLIGHTING:
                part_to_use, stripe = consistent_word_highlight(part)
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
import hashlib

WORD_HIGHLIGHT_LEN_MIN   = 7     # Minimum length of a word to highlight
WORD_HIGHLIGHT_LEN_MIN   = 6     # Minimum length of a word to highlight
MAX_BACKGROUND_INTENSITY = 0.37  # Maximum background color intensity
MAX_BACKGROUND_INTENSITY = 0.25  # Maximum background color intensity
MAX_BACKGROUND_INTENSITY = 0.22  # Maximum background color intensity
SATURATION               = 0.9
LIGHTNESS                = 0.5

# ═════════════════════════════════════════════════════════════════════════════════
import unicodedata
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





char_map = {
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
    'α': 'a', 'Α': 'A',      # Greek alpha to Latin a
    'β': 'b', 'Β': 'B',      # Greek beta to Latin b
    'ε': 'e', 'Ε': 'E',      # Greek epsilon to Latin e
    'ο': 'o', 'Ο': 'O',      # Greek omicron to Latin o
    'ρ': 'p', 'Ρ': 'P',      # Greek rho to Latin p
    'σ': 's', 'Σ': 'S',      # Greek sigma to Latin s
    'ι': 'i', 'Ι': 'I',      # Greek iota to Latin i
    'κ': 'k', 'Κ': 'K',      # Greek kappa to Latin k
    'λ': 'l', 'Λ': 'L',      # Greek lambda to Latin l
    'μ': 'm', 'Μ': 'M',      # Greek mu to Latin m
    'ν': 'n', 'Ν': 'N',      # Greek nu to Latin n
    'τ': 't', 'Τ': 'T',      # Greek tau to Latin t

    # Other common similar letters
    'ı': 'i',               # Dotless i to i
    'İ': 'I',               # Dotted I to I
    'ı': 'i',               # Turkish dotless i to Latin i
}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def normalize_for_highlight(word):
    if word == "versus" or word == "v.s.": word = "vs"                               #different ways to express the same word should be drawn  the same color
    word = word.replace("’ve", "").replace("'ve", "").replace("´ve", "")             #makes word-variants like “should’ve”  and  “should have” the same color
    word = word.replace("’s" , "").replace("'s" , "").replace("´s" , "")             #makes word-variants like  “there’s”   and    “there is”  the same color
    word = word.replace("’"  , "").replace("'"  , "").replace("´"  , "")             #variations in which apostrophe we use should all be made the same color
    if word.endswith("ing"): word = word[:-3] + "in"                                 #makes word-variants like “coping” vs “copin’” vs “copin” the same color

    word = unicodedata.normalize('NFC', word)
    for cyrillic_char, latin_char in char_map.items():
            word = word.replace(cyrillic_char, latin_char)

    #print (f"word={word}")
    return word
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


# ═════════════════════════════════════════════════════════════════════════════════
words_used=""
striped_text = []
def consistent_word_highlight(text):
    global words_used, striped_text
    """
    Highlight words in the text that are longer than WORD_HIGHLIGHT_LEN_MIN.
    """
    highlighted_text = []
    word             = ''
    in_highlight     = False                                                            # Track whether we're currently inside a highlighted word

    text2use = text.replace('--','—');

    for char in text2use:
        #f char.isalnum() or char ==  "’" or char == "'" or char == "´":                # Building a word: punctuation that we still want to consider part of the word
        #f char.isalnum() or char in {"’", "'", "´", "-", "–", "—"}:                    # Building a word: punctuation that we still want to consider part of the word
        if char.isalnum() or char in {"’", "'", "´", "-", "–"     }:                    # Building a word: punctuation that we still want to consider part of the word —— maybe en-dash should NOT be on the list afterall?
            if               char in {"’", "'", "´"}: char = "’"                        # Building a word: replace dumb apostrophes with smart apostrophes
            word += char
        else:
            normalized_word = normalize_for_highlight(word)
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
def convert_stretched_stripe(stripe, columns, console_width):
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
            result += f'{ansi_code} ' * (base_padding // 2) + f'{ansi_code}{word[0]}' + ' ' * (base_padding - base_padding // 2)  # Center the letter

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









# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###

def main():
    global INTERNAL_LOG, VERBOSE, WRAPPING, STRIPE, FORCE_COLUMNS, FORCED_CONSOLE_WIDTH, console_width, console_height, columns, avg_line_width, record_working_column_length, ROW_PADDING, DEBUG_VERBOSE_COLUMNS
    our_args = parse_arguments()
    INTERNAL_LOG=""
    stripester=""

    # Try to detect terminal width and height, otherwise use default values
    try:
        import shutil
        console_width, console_height = shutil.get_terminal_size()
    except Exception:
        console_width, console_height = 666, 69
        INTERNAL_LOG = INTERNAL_LOG + "Unable to detect console size. Using default width=666 and height=69."
    if VERBOSE:
        INTERNAL_LOG = INTERNAL_LOG + f" —— Detected console  width of {console_width } ——\n"
        INTERNAL_LOG = INTERNAL_LOG + f" —— Detected console height of {console_height} ——\n"


    # Process our command line parameters:
    WRAPPING    = DEFAULT_WRAPPING
    width = args.width or console_width
    if our_args.row_padding: ROW_PADDING = our_args.row_padding
    else:                    ROW_PADDING = DEFAULT_ROW_PADDING
    if our_args   .wrap:     WRAPPING = True
    if our_args.no_wrap:     WRAPPING = False
    if FORCED_CONSOLE_WIDTH: console_width=our_args.console_width


    # read our input data:
    input_data = read_input(WRAPPING, args.max_line_length_before_wrapping)     # Read and process input lines

    # Calculate avg line width
    avg_line_width = wcsarraywidth(input_data, mode="average")
    if args.verbose: print(f"Avg line width: {avg_line_width}")

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
        columns      = determine_optimal_columns(input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
        rows_per_col = ceil(len(input_data) / columns)                        # NOT a situation for wcswidth


    #Generate Stripe one-line representation
    if STRIPE:
        joined_input_data = " ".join(input_data)                                         #print(f"joined_input_data is {joined_input_data}")
        columns_data      = [[joined_input_data]]                                        #print(f"columns_data is {columns_data}")
        column_widths     = calculate_column_widths(columns_data)                        #print(f"column_widths is {column_widths}")
        meh, stripeamabob = render_columns(columns_data, column_widths, divider)         #print(f"stripeamabob is {stripeamabob}")     #        striperooni       = convert_stripe(stripeamabob,1)                        #print(f"\nstriperooni is:\n{striperooni}\nand looks like this:"); print(striperooni)       #tripester = format_colored_array(striperooni,console_width-1)
        #stripeamabob is ['\x1b[38;2;150;242;12m\x1b[48;2;15;12;0m', 'Definition\x1b[0m', '\x1b[38;2;12;119;242m\x1b[48;2;20;0;12m', 'secretly\x1b[0m', '\x1b[38;2;242;12;31m\x1b[48;2;13;0;21m', 'smiling\x1b[0m', '\x1b[38;2;150;242;12m\x1b[48;2;15;12;0m', 'Definition\x1b[0m', '\x1b[38;2;12;234;242m\x1b[48;2;19;5;0m', 'Conversations\x1b[0m', '\x1b[38;2;12;226;242m\x1b[48;2;20;0;19m', 'Russian\x1b[0m', '\x1b[38;2;242;47;12m\x1b[48;2;2;16;0m', 'accent\x1b[0m', '\x1b[38;2;242;89;12m\x1b[48;2;19;0;20m', "that's\x1b[0m", '\x1b[38;2;242;12;242m\x1b[48;2;11;0;21m', 'colored\x1b[0m', '\x1b[38;2;112;12;242m\x1b[48;2;17;9;0m', 'Blanket\x1b[0m', '\x1b[38;2;242;12;24m\x1b[48;2;20;0;18m', 'dinner\x1b[0m', '\x1b[38;2;12;242;108m\x1b[48;2;15;13;0m', 'President\x1b[0m', '\x1b[38;2;73;242;12m\x1b[48;2;4;15;0m', 'Cardboard\x1b[0m', '\x1b[38;2;127;12;242m\x1b[48;2;20;0;16m', 'appliance\x1b[0m', '\x1b[38;2;150;242;12m\x1b[48;2;15;12;0m', 'Definition\x1b[0m', '\x1b[38;2;12;188;242m\x1b[48;2;1;1;22m', 'flamingos\x1b[0m', '\x1b[38;2;142;12;242m\x1b[48;2;18;8;0m', 'engaging\x1b[0m', '\x1b[38;2;150;242;12m\x1b[48;2;15;12;0m', 'Definition\x1b[0m', '\x1b[38;2;12;192;242m\x1b[48;2;0;16;6m', 'Listening\x1b[0m', '\x1b[38;2;12;242;12m\x1b[48;2;9;15;0m', 'Captain\x1b[0m', '\x1b[38;2;242;158;12m\x1b[48;2;20;0;15m', 'Beefheart\x1b[0m', '\x1b[38;2;66;242;12m\x1b[48;2;0;14;16m', 'Everyone\x1b[0m', '\x1b[38;2;242;12;35m\x1b[48;2;4;1;21m', 'Mixing\x1b[0m', '\x1b[38;2;12;242;223m\x1b[48;2;0;15;7m', 'pieces\x1b[0m', '\x1b[38;2;12;238;242m\x1b[48;2;0;15;11m', 'different\x1b[0m', '\x1b[38;2;242;135;12m\x1b[48;2;20;3;0m', 'Sleeping\x1b[0m', '\x1b[38;2;89;12;242m\x1b[48;2;13;14;0m', 'bathtub\x1b[0m', '\x1b[38;2;242;89;12m\x1b[48;2;19;0;20m', "that's\x1b[0m", '\x1b[38;2;123;242;12m\x1b[48;2;0;15;6m', 'stored\x1b[0m', '\x1b[38;2;20;242;12m\x1b[48;2;0;15;14m', 'larger\x1b[0m', '\x1b[38;2;242;43;12m\x1b[48;2;20;0;13m', 'version\x1b[0m', '\x1b[38;2;12;192;242m\x1b[48;2;12;14;0m', 'itself\x1b[0m', '\x1b[38;2;150;242;12m\x1b[48;2;15;12;0m', 'Definition\x1b[0m', '\x1b[38;2;12;104;242m\x1b[48;2;17;9;0m', 'Unbelievably\x1b[0m', '\x1b[38;2;127;242;12m\x1b[48;2;19;0;20m', 'shadow\x1b[0m', '\x1b[38;2;12;204;242m\x1b[48;2;7;1;21m', 'puppets\x1b[0m', '\x1b[38;2;12;242;131m\x1b[48;2;20;0;4m', 'Masterminding\x1b[0m', '\x1b[38;2;242;116;12m\x1b[48;2;5;15;0m', 'scheme\x1b[0m', '\x1b[38;2;242;12;200m\x1b[48;2;0;16;3m', 'stretches\x1b[0m', '\x1b[38;2;242;12;77m\x1b[48;2;7;15;0m', 'around\x1b[0m', '\x1b[38;2;150;242;12m\x1b[48;2;15;12;0m', 'Definition\x1b[0m', '\x1b[38;2;181;12;242m\x1b[48;2;0;9;19m', 'Understanding\x1b[0m', '\x1b[38;2;242;12;200m\x1b[48;2;0;8;19m', 'complicated\x1b[0m', '\x1b[38;2;242;39;12m\x1b[48;2;8;1;21m', 'puzzle\x1b[0m', '\x1b[38;2;234;12;242m\x1b[48;2;0;16;4m', 'Laughing\x1b[0m', '\x1b[38;2;12;242;39m\x1b[48;2;20;0;20m', 'Looking\x1b[0m', '\x1b[38;2;66;12;242m\x1b[48;2;0;16;4m', 'Knowing\x1b[0m', '\x1b[38;2;16;12;242m\x1b[48;2;1;1;22m', 'everything\x1b[0m', '\x1b[38;2;0;16;3m\x1b[48;2;242;150;12m', 'thinking\x1b[0m']
        stripester        = convert_stretched_stripe(stripeamabob,1,console_width-1)     #print(f"\nstripester is:\n{stripester}")
        if stripester == "": stripester = convert_stretched_stripe(
            ['\x1b[38;2;4;1;21m\x1b[48;25;25;240;12m', 'NNNNNN\x1b[0m',
             '\x1b[38;2;4;1;21m\x1b[48;26;250;240;12m', 'UUUUUU\x1b[0m',
             '\x1b[38;2;4;1;21m\x1b[48;27;25;240;12m', 'LLLLLL\x1b[0m',
             '\x1b[38;2;4;1;21m\x1b[48;28;25;240;12m', 'LLLLLL\x1b[0m',],1,console_width-1)
        print(stripester)


    #start preliminarily generating output, which we will determine post-generation whether it's too wide or not:
    output = ""
    keep_looping = True
    force_num_columns = False
    joined_input_data = "\n".join(input_data)
    while keep_looping:
        is_too_wide = False
        output = ""

        #calculate # of columns unless we are forcing it:
        if not force_num_columns and not FORCE_COLUMNS:
            columns = determine_optimal_columns(input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
        if columns == 0: columns = 1

        #rows per column
        rows_per_col = ceil(len(input_data) / columns)                          #NOT a situation for wcswidth
        if VERBOSE: INTERNAL_LOG = INTERNAL_LOG + (f"🚣‍♀️ rows_per_col={rows_per_col}")

        #distribute data into columns & calculate the widths of the columns
        columns_data  = distribute_lines_into_columns(input_data, columns, rows_per_col)
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
            if is_too_wide and not FORCE_COLUMNS and not STRIPE:
                if VERBOSE: print(f"🐾🐾 breaking")
                break

            #we kept this rendering, so add the important processing info to the log
            INTERNAL_LOG = INTERNAL_LOG + INTERNAL_LOG_FRAGMENT

            #add our rendered row to our output:
            output += rendered_row.replace("Æ","’") + "\n"                         #mis-encoded apostrpohe fox ... This is very untenable
            #🐱🐱🐱 if VERBOSE: print(f"🤬🤬 row_num {row_num}... is_too_wide={is_too_wide}\n⚙ ⚙ ⚙ OUTPUT SO FAR:\n{BLINK_ON}{COLOR_GREY}{output}{BLINK_OFF}{ANSI_RESET}⚙ ⚙ ⚙ That's it!")

            #print("loopybob")
            if STRIPE:
                #print("breaking")
                break

        #now that we have rendered our row, figure out if we are done or not:
        keep_looping = False                                                       #only keep looking if things required a redo
        force_num_columns = False                                                  #keep track of forced-column mode
        if is_too_wide and not FORCE_COLUMNS:                                      #ignore the error of things being too wide if we are in forced-columns mode
            keep_looping = True                                                    #keep looping, but with a lower number of coumns
            columns = columns - 1                                                  #next time, try with 1 fewer columns
            force_num_columns = True                                               #internally, we are now forcing the number of columns to be the 1 fewer that we set in the previous line
            if columns == 1: keep_looping = False                                  #if we are down to 1 column, there's no more to check, so stop
            if columns == 0:                                                       #if we are down to 0 columns, go back to 1 and quit
                columns = 1
                keep_looping = False
            if VERBOSE: INTERNAL_LOG = INTERNAL_LOG + f"🤬🤬 ACTING ON IT ——> columns is now {columns}"
        if STRIPE:  keep_looping = False
        if VERBOSE: INTERNAL_LOG = INTERNAL_LOG + f"🤬🤬🤬🤬 FINAL_COLUMNS ——> columns is now {columns}"   #debug
        #print(F"keep_looping is {keep_looping}")

    # Optionally, print the internal log
    if VERBOSE:
        print("\nInternal Log:")
        print(INTERNAL_LOG)
    if VERBOSE or DEBUG_VERBOSE_COLUMNS:
        print(f"🥒 num_columns={columns} ... column_widths={column_widths} 🥒")
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
    # 🎉🎉🎉 ⭐⭐⭐⭐⭐ THE FILE IS GONNA BE PRINTED RIGHT HERE: ⭐⭐⭐⭐⭐ 🎉🎉🎉 #
    # output="" at the end of each line:                                   #
    if (output==""):                                                       #
        print("\n".join(input_data))                                       #
        if VERBOSE: print("❕‼ OUTPUT EMPTY. Joined input_data manually ❕‼")#
    #══════════════════════════════════════════════════════════════════════#
    # 🎉🎉🎉 ⭐⭐⭐⭐⭐ THE FILE IS ACTUALLY PRINTED RIGHT HERE: ⭐⭐⭐⭐⭐ 🎉🎉🎉 #
    else:                                                                  #
        if not STRIPE:                                                     #
            trimmed_output = remove_trailing_blank_lines(output)           #
            if WORD_HIGHLIGHTING:                                          #
                highlighted_output = trimmed_output                        #
                print(highlighted_output, end="")                          #
            else:                                                          #
                print(    trimmed_output, end="")                          #
    #══════════════════════════════════════════════════════════════════════#




# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###

if __name__ == "__main__":
    main()
