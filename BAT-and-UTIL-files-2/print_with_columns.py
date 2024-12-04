#### USER CONFIGURATION:
    
    
    
DEFAULT_ROW_PADDING = 7                             # SUGGESTED: 7. Number of rows to subtract from screen height as desired maximum output height before adding columns. May not currently do anything.
content_ansi        =  "\033[0m"
divider_ansi        =  "\033[38;2;187;187;0m"
#content_ansi       =  "\033[42m\033[31m" #
divider             = f"  {divider_ansi}" + "│" + f"  {content_ansi}"  # Divider with #BBBB00 color and additional padding


#TODO: deal with situation of lines that are sooo long that we'd really have to wrap them to fit? or is this fine?
#TODO: maybe make each column a slightly different color

#font coefficient = 1.4! that's what i got!
#lhecker@github: Generally speaking, you can assume that fonts have roughly an aspect ratio of 2:1. It seems you measured the actual size of the glyph though which is slightly different from the cell height/width.


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
colorama.init()
#print(Fore.RED + "This text should be red." + Style.RESET_ALL)
sys.stdin .reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')




##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
##### GLOBAL VARIABLES:
divider_visible_length = 5
DEFAULT_WRAPPING       = False                                            #do we default to enabling the wrapping of long lines
WRAPPING               = DEFAULT_WRAPPING
VERBOSE                = False
FORCE_COLUMNS          = False
args                   = None
parser                 = None
avg_line_width         = None
console_width          = None
console_height         = None
FORCED_CONSOLE_WIDTH   = 0
columns                = 0
INTERNAL_LOG           = ""
record_working_column_length = 0










##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
#####                  SUBROUTINES:
##### ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

def parse_arguments():
    global WRAPPING, VERBOSE, FORCE_COLUMNS, FORCED_CONSOLE_WIDTH, args, console_width, console_height
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Display STDIN in a compact, multi-column format.")
    parser.add_argument('-w', '--width', type=int, help="Override output width to something other than console width")
    parser.add_argument('-cw', '--console_width', type=int, help="Override detected console width")
    parser.add_argument('-c', '--columns', type=int, help="Override number of columns calculation")
    parser.add_argument('-p', '--row_padding', type=int, default=7, help="Number of rows to subtract from screen height as desired maximum")
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose mode—display debug info and internal logs")
    parser.add_argument('--wrap', action='store_true', help="Enable line wrapping for long lines")
    parser.add_argument('--no_wrap', action='store_true', help="Disable line wrapping for long lines")
    parser.add_argument('--max_line_length_before_wrapping', type=int, default=80, help="Maximum line length before wrapping")
    args = parser.parse_args()
    ROW_PADDING   = args.row_padding
    VERBOSE       = args.verbose
    FORCE_COLUMNS = args.columns
    FORCED_CONSOLE_WIDTH = args.console_width
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
    global avg_line_width, columns
    """
    Determine the optimal number of columns based on console width and desired max height.
    Starts with the maximum possible columns and decreases until a fit is found.
    """
    
    #default to 1 col if no lines
    if not lines:                                                                   
        print(f"⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠ No lines❓❓❓ ⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠")
        return 1  

    #ensure global var has been calculaed
    if not avg_line_width: print(f"⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠ Why is avg_line_width == '{avg_line_width}' ???? ⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠⚠")
    elif   VERBOSE       : print(f"Avg line width: {avg_line_width}")                                   

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
            return max_possible_columns

    return max_possible_columns
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###



    
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def read_input(wrapping, max_width):
    """
    Read input lines from STDIN and optionally wrap them.
    """
    input_lines = sys.stdin.read().strip().splitlines()
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
    
    rows_per_col = max(len(col) for col in columns_data)   
    if VERBOSE: print(f"😷😷😷😷😷 Recalculated rows per column as: {rows_per_col}")
     
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
            current_content_width = wcswidth(part)
            num_spaces_to_add     = current_column_width - current_content_width
            spacer                = num_spaces_to_add * " "
            padded_part           = part + spacer
            
            # append "padded part" to our row:
            row_parts.append(padded_part)
            
        # Join the rows together with the divider
        rendered_row = divider.join(row_parts)
        rendered_rows.append(rendered_row)
    return rendered_rows
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







# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
def main():
    global INTERNAL_LOG, VERBOSE, WRAPPING, FORCE_COLUMNS, FORCED_CONSOLE_WIDTH, console_width, console_height, columns, avg_line_width, record_working_column_length, ROW_PADDING
    our_args = parse_arguments()
    INTERNAL_LOG=""

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
    VERBOSE     = our_args.verbose
    WRAPPING    = DEFAULT_WRAPPING
    ROW_PADDING = DEFAULT_ROW_PADDING   
    width = args.width or console_width
    if our_args.row_padding: ROW_PADDING = our_args.row_padding
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
            
        columns = our_args.columns
        joined_input_data = "\n".join(input_data)
        rows_per_col = ceil(len(joined_input_data) / columns)           #NOT a situation for wcswidth

        if our_args.verbose or VERBOSE: print(f"Using user-specified columns: {columns}\nRows per column: {rows_per_col}")
    else:
        columns = determine_optimal_columns(input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
        rows_per_col = ceil(len(input_data) / columns)                  #NOT a situation for wcswidth

    #define some ANSI codes we plan to use
    BLINK_ON   = "\033[6m"
    BLINK_OFF  = "\033[25m"
    FAINT_ON   = "\033[2m"
    FAINT_OFF  = "\033[22m"
    COLOR_GREY = "\033[90m"
    ANSI_RESET = "\033[39m\033[49m\033[0m"

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
        rendered_rows = render_columns(columns_data, column_widths, divider)
        if not rendered_rows:   
            print("⚠⚠⚠ Warning: rendered_rows is empty. Check the rendering function. ⚠⚠⚠")
        elif VERBOSE:            
            print(f"💯💯 rendered_rows length = {len(rendered_rows)}, column_widths={column_widths}")

        if args.verbose: print(f"Column  widths: {    column_widths}")

        #render the rows repeatedly, decreasing until they fit within the propr width 
        for row_num, rendered_row in enumerate(rendered_rows, start=1):
            if VERBOSE: print(f"🏹🏹🏹🏹🏹🍎🍎🍎 processing row_num {row_num}")
            INTERNAL_LOG_FRAGMENT=""
            line_parts = rendered_row.split(divider)                      # Split the rendered row back into parts based on the divider
            line_parts = [part.strip() for part in line_parts]            # Trim any extra spaces
            
            #figure out if this line is too long or not, and create important processing info to log *IF* we keep this rendering:
            is_too_wide, INTERNAL_LOG_FRAGMENT = log_line_parts_and_process_them_too(line_parts, row_num, column_widths, rendered_row)
            
            #if it's too wide, stop bothering to process (unless we are forcing columns):
            if VERBOSE: print(f"🐾🐾 row_num {row_num}... is_too_wide={is_too_wide}")
            if is_too_wide and not FORCE_COLUMNS: 
                if VERBOSE: print(f"🐾🐾 breaking")
                break

            #we kept this rendering, so add the important processing info to the log                                                    
            INTERNAL_LOG = INTERNAL_LOG + INTERNAL_LOG_FRAGMENT
            
            #add our rendered row to our output:
            output += rendered_row + "\n"
            #🐱🐱🐱 if VERBOSE: print(f"🤬🤬 row_num {row_num}... is_too_wide={is_too_wide}\n⚙ ⚙ ⚙ OUTPUT SO FAR:\n{BLINK_ON}{COLOR_GREY}{output}{BLINK_OFF}{ANSI_RESET}⚙ ⚙ ⚙ That's it!")
            
        #now that we have rendered our row, figure out if we are done or not:
        keep_looping = False                                                       #only keep looking if things required a redo
        force_num_columns = False                                                  #keep track of forced-column mode
        if is_too_wide and not FORCE_COLUMNS:                                      #ignore the error of things being too wide if we are in forced-columns mode
            keep_looping = True                                                    #keep looping, but with a lower number of coumns
            columns = columns - 1                                                  #next time, try with 1 fewer columns
            force_num_columns = True                                               #internally, we are now forcing the number of columns to be the 1 fewer that we set in the previous line
            if columns == 1: keep_looping = False                                  #if we are down to 1 column, there's no more to check, so stop
            if VERBOSE: print(f"🤬🤬 ACTING ON IT ——> columns is now {columns}")   #debug
        
    # kludge to fix bug, really shouldn't happen anymore:
    if (output==""): 
        print("\n".join(input_data))
        if VERBOSE: print("❕‼ OUTPUT WAS EMPTY, so we joined input_data manually ❕‼")
    else: 
        print(output)
    
    # Optionally, print the internal log
    if VERBOSE:
        print(f"🦈 in the end, columns were {columns}")
        print("\nInternal Log:")
        print(INTERNAL_LOG)
        print(f"🥒 columns=🥒 {columns}...")
        #print(f"🥒  output=🥒 {output}\n")
        #print(f'💔input_data=' + "\n".join(input_data) + '\n')
        print(f"🥒 console_width=🥒 {console_width}...")
        print(f"💿 record_working_column_length={record_working_column_length}")

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════###

if __name__ == "__main__": 
    main()
