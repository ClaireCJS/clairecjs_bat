#TODO: deal with situation of lines that are sooo long that we'd really have to wrap them to fit
#TODO: maybe make each column a slightly different color

#font coefficient = 1.4! that's what i got!
#lhecker@github: Generally speaking, you can assume that fonts have roughly an aspect ratio of 2:1. It seems you measured the actual size of the glyph though which is slightly different from the cell height/width.



import sys
import argparse
from math import ceil
import re
import textwrap
from rich.console import Console                                    #shutil *and* os do *NOT* get the right console dimensions under Windows Terminal
import colorama
from colorama import Fore, Style
colorama.init()
#print(Fore.RED + "This text should be red." + Style.RESET_ALL)
import sys
sys.stdin .reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# Define default ROW_PADDING
DEFAULT_ROW_PADDING = 7  # Number of rows to subtract from screen height as desired maximum

# Define the divider and its visible length
content_ansi           =  "\033[0m"
divider_ansi           =  "\033[38;2;187;187;0m"
#content_ansi          =  "\033[42m\033[31m" #
divider                = f"  {divider_ansi}" + "│" + f"  {content_ansi}"  # Divider with #BBBB00 color and additional padding
divider_visible_length = 5
DEFAULT_WRAPPING       = False                                            #do we default to enabling the wrapping of long lines

# Internal log
INTERNAL_LOG = ""
WRAPPING = DEFAULT_WRAPPING
VERBOSE = False
FORCE_COLUMNS = False
args = None
parser = None

console_width=None
console_height=None
columns=0

def parse_arguments():
    global WRAPPING, VERBOSE, FORCE_COLUMNS, args, console_width, console_height
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Display STDIN in a compact, multi-column format.")
    parser.add_argument('-w', '--width', type=int, help="Override console width")
    parser.add_argument('-c', '--columns', type=int, help="Number of columns (overrides automatic calculation)")
    parser.add_argument('-p', '--row_padding', type=int, default=7, help="Number of rows to subtract from screen height as desired maximum")
    parser.add_argument('-v', '--verbose', action='store_true', help="Verbose mode—display debug info and internal logs")
    parser.add_argument('--wrap', action='store_true', help="Enable line wrapping for long lines")
    parser.add_argument('--no_wrap', action='store_true', help="Disable line wrapping for long lines")
    parser.add_argument('--max-line-length-before-wrapping', type=int, default=80, help="Maximum line length before wrapping")
    args = parser.parse_args()
    ROW_PADDING   = args.row_padding
    VERBOSE       = args.verbose
    FORCE_COLUMNS = args.columns
    return parser.parse_args()


    # Set up the argument parser
    #parser = argparse.ArgumentParser(description="Display STDIN in a compact, multi-column format.")
    #parser.add_argument('-w', '--width'                    , type=int,                              help="Override console width")
    #parser.add_argument('-c', '--columns'                  , type=int,                              help="Number of columns (overrides automatic calculation)")
    #parser.add_argument('-p', '--row_padding'              , type=int, default=DEFAULT_ROW_PADDING, help="Number of rows to subtract from screen height as desired maximum")
    #parser.add_argument('-v', '--verbose'                  , action='store_true',                   help="Verbose mode——display debug info")
    #parser.add_argument('--wrap'                           , action='store_true',                   help="Enable line wrapping for long lines") #makes args.wrap true
    #parser.add_argument('--no_wrap'                        , action='store_true',                   help="Disable line wrapping for long lines") #makes args.wrap false
    #parser.add_argument('--max-line-length-before-wrapping', type=int, default=80,                  help="Maximum line length before wrapping")
    #args = parser.parse_args()

# Read input from STDIN
# input_lines = sys.stdin.read().strip().splitlines()
#
#if not input_lines:
#    sys.exit("No input data provided.")

## Implement line wrapping if enabled
#if WRAPPING:
#    wrapped_lines = []
#    for line in input_lines:
#        # Wrap lines longer than max_line_length
#        wrapped = textwrap.wrap(line.rstrip(), width=args.max_line_length) or ['']
#        wrapped_lines.extend(wrapped)
#    input_data = wrapped_lines
#else:
#    input_data = [line.rstrip() for line in input_lines]
#
## Update max_line_length after wrapping
#max_line_length = max(len(line) for line in input_data) if input_data else 0
#INTERNAL_LOG += f"Initial Max_line_length is {max_line_length}\n"

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~]|\][^\x07]*\x07|P[^\\]*\\)')
def strip_ansi(text):
    global ANSI_ESCAPE
    return ANSI_ESCAPE.sub('', text)


# Function to calculate the adjusted aspect ratio
def calculate_aspect_ratio(total_width, total_rows):
    # Since characters are twice as high as they are wide, multiply rows by 2
    return total_width / (2 * total_rows) if total_rows != 0 else float('inf')


def determine_optimal_columns(lines, console_width, divider_length, desired_max_height, verbose=False):
    """
    Determine the optimal number of columns based on console width and desired max height.
    Starts with the maximum possible columns and decreases until a fit is found.
    """
    if not lines:
        print(f"No lines?!?!?!?!?!?!?!?!??!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!?!??!!?")
        return 1  # Default to 1 column if no lines

    max_line_length = max(len(line) for line in lines)
    # Start with the maximum possible columns based on the longest line
    max_possible_columns = console_width // (max_line_length + divider_length)
    if max_possible_columns == 0:
        max_possible_columns = 1

    if verbose:
        print(f"Max line length: {max_line_length}")
        print(f"Initial max possible columns: {max_possible_columns}")

    for cols in range(max_possible_columns, 0, -1):
        rows = ceil(len(lines) / cols)
        required_width = cols * max_line_length + (cols -1) * divider_length
        if required_width <= console_width and rows <= desired_max_height:
            if verbose:
                print(f"Optimal columns determined: {cols} with {rows} rows per column")
            return cols
    #eturn 1  # Fallback to 1 column
    return 2  # Fallback to 2 columns



# Function to determine the optimal number of columns
def OLD___determine_optimal_columns(lines, console_width, divider_len, desired_max_height, initial_cols=1, strict=False):
    global INTERNAL_LOG

    if not lines: return 1  # Default to 1 column if no lines

    num_lines = len(lines)
    max_line_length = max(len(line) for line in lines) if lines else 0
    #print(f"Max line length: {max_line_length}")

    max_possible_columns = console_width // (max_line_length + divider_len)
    if max_possible_columns == 0:
        max_possible_columns = 1
        
    #print(f"Initial max possible columns: {max_possible_columns}")
    INTERNAL_LOG = INTERNAL_LOG + f"determine_optimal_columns({len(lines)} lines, width={console_width}, div-len={divider_len}, desired_rows={desired_max_height}, strict={strict})\n"
    INTERNAL_LOG = INTERNAL_LOG + f"\tmax_line_length is {max_line_length}\n"



    for cols in range(max_possible_columns, 0, -1):
        rows = ceil(len(lines) / cols)
        required_width = cols * max_line_length + (cols -1) * divider_len
        if required_width <= console_width and rows <= desired_max_height:
            if VERBOSE:
                print(f"Optimal columns determined: {cols} with {rows} rows per column")
            FirstReturnValue = cols
            
    #tentative_column_lines  = [lines[i * tentative_rows_per_col:(i + 1) * tentative_rows_per_col] for i in range(tentative_cols)]
    #column_widths = [max(len(line) for line in col) if col else 0 for col in lines]            
    #tentative_column_widths = [max(len(line) for line in col) if col else 0 for col in tentative_column_lines]

    FirstReturnValue = 1
    return FirstReturnValue
    #eturn FirstReturnValue, column_widths  # Fallback to 1 column

    ### UNREACHABLE OLD CODE: 
    #### STRICT IS ABANDONED
    if strict:                      # Enforce the specified number of columns without adjustment (🐮untested)
        optimal_cols = initial_cols
        rows_per_col = ceil(num_lines / optimal_cols)
        column_lines = [lines[i * rows_per_col:(i + 1) * rows_per_col] for i in range(optimal_cols)]
        column_widths = [max(len(line) for line in col) if col else 0 for col in column_lines]
        total_width = sum(column_widths) + divider_len * (optimal_cols - 1)

        INTERNAL_LOG += f"\tStrict mode: columns={optimal_cols}, total_width={total_width}\n"

        # Check if total_width exceeds console_width
        if total_width > console_width:
            print(f"Warning: Specified number of columns ({optimal_cols}) may exceed console width ({console_width}).")
            print(f"Total required width: {total_width}. Some lines may wrap or be truncated.")

        if optimal_cols <= 0: optimal_cols = 1        
        INTERNAL_LOG += f"* phase 2:RETURNING: returning optimal_cols={optimal_cols} & widths of {column_widths}\n"
        return optimal_cols, column_widths



    # Phase 2: Optimize aspect ratio by adding more columns if possible
    optimal_cols = 1
    optimal_widths = []
    record_low_aspect_ratio_difference = float('inf')
    tentative_cols = 1
    keep_going = True
    while keep_going:
        tentative_rows_per_col  = ceil(num_lines / tentative_cols)
        tentative_column_lines  = [lines[i * tentative_rows_per_col:(i + 1) * tentative_rows_per_col] for i in range(tentative_cols)]
        tentative_column_widths = [max(len(line) for line in col) if col else 0 for col in tentative_column_lines]
        tentative_total_width   = sum(tentative_column_widths) + divider_len * (tentative_cols - 1)
        aspect_ratio = calculate_aspect_ratio(tentative_total_width, tentative_rows_per_col)
        aspect_diff = abs(aspect_ratio - 1.0)
        INTERNAL_LOG += f"* If # columns={tentative_cols}, then:\t... width?={tentative_total_width} \tconsole={console_width}x{console_height}, num_lines(orig)={num_lines}, AR={aspect_ratio},AR_diff={aspect_diff}\n"

        if aspect_diff < record_low_aspect_ratio_difference:                   # Accept the additional column for better aspect ratio
            record_low_aspect_ratio_difference = aspect_diff
            pass    #todo
            
        #print(f"if tentative_total_width:{tentative_total_width} > console_width:{console_width}: keep_going = False")
        if tentative_total_width > console_width: 
            keep_going = False
        else:                                   
            tentative_cols += 1
        
    optimal_cols  = tentative_cols-1        
    column_widths = tentative_column_widths
    total_width   = tentative_total_width
    if optimal_cols <= 0: optimal_cols = 1

    INTERNAL_LOG += f"* phase 2:RETURNING: returning optimal_cols={optimal_cols} & widths of {column_widths}\n"
    return optimal_cols, column_widths
    
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
    


#def CRUFT():
#    # Determine the optimal number of columns
#    if parser.columns:
#        # Enforce the specified number of columns
#        columns = determine_optimal_columns(
#            input_data,
#            width,
#            divider_visible_length,
#            desired_max_height,
#            #initial_cols=args.columns,
#            #strict=True
#        )
#    else:
#        # Allow dynamic calculation of columns
#        initial_columns = 1  # Starting point
#        columns = determine_optimal_columns(
#            input_data,
#            width,
#            divider_visible_length,
#            desired_max_height,
#            #initial_cols=initial_columns,
#            #strict=False
#        )
#
#    # Inform the user if the specified column count was adjusted (only applicable when -c is not used)
#    if args.columns:
#        # Since we are enforcing strict=True, no adjustment should occur
#        pass
#    else:
#        # If dynamic columns were adjusted, inform the user
#        INTERNAL_LOG = INTERNAL_LOG + f"Determined number of columns: {columns}"
#
#    # short-circuit if columns is 1 —— we're just printing it normally if there's just 1 column!
#    if columns == 1:
#        for line in input_data: print (line)
#        exit(1)





# Function to format text into columns
def format_columns(lines, columns, column_widths, divider):
    global INTERNAL_LOG
    output = []
    num_lines = len(lines)
    rows_per_col = ceil(num_lines / columns) if columns > 0 else 0
    column_lines = [lines[i * rows_per_col:(i + 1) * rows_per_col] for i in range(columns)]

    for row in range(rows_per_col):
        line_parts = []
        for col_index in range(columns):
            if col_index >= len(column_widths):                     # Defensive check to prevent IndexError
                text = ""
            elif row < len(column_lines[col_index]):
                text = column_lines[col_index][row]
            else:
                text = ""                                           # Handle empty cells
            if col_index < len(column_widths):                      # Ensure column_widths[col_index] exists
                line_parts.append(text.ljust(column_widths[col_index]))
            else:
                line_parts.append(text)                             # If somehow missing, append without padding
                
        line = divider.join(line_parts)

        #NTERNAL_LOG = INTERNAL_LOG + f"line_parts={line_parts}\n"
        #dummy__is_to_wide__dummy, internal_log_fragment = log_line_parts_and_process_them_too([line], row, column_widths, "")
        output.append(line)
    return output



def distribute_lines_into_columns(lines, columns, rows_per_col):
    """
    Distribute lines into the specified number of columns.
    """
    columns_data = []
    for col in range(columns):
        start_index = col * rows_per_col
        end_index = start_index + rows_per_col
        column = lines[start_index:end_index]
        columns_data.append(column)
    return columns_data

def calculate_column_widths(columns_data):
    """
    Calculate the maximum width for each column.
    """
    column_widths = []
    for col in columns_data:
        if col:
            max_width = max(len(line) for line in col)
        else:
            max_width = 0
        column_widths.append(max_width)
    return column_widths

def log_line_parts_and_process_them_too(line_parts, row_num, column_widths, rendered_row):
    global INTERNAL_LOG
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
        col_width    = column_widths[col_num-1]
        stripped_row = strip_ansi(rendered_row)
        len2         =        len(stripped_row)
        len2
        if col_num == 1:
            #print(f"INTERNAL_LOG_LOCAL = {INTERNAL_LOG_LOCAL}")
            tmpstr = f"\nRow {row_num}: Length={len2:3}: length2={len2:3}  (cols:{console_width}):" + f"\n{rendered_row}\n{stripped_row}\n"            
            INTERNAL_LOG_LOCAL = INTERNAL_LOG_LOCAL + tmpstr
        INTERNAL_LOG_LOCAL     = INTERNAL_LOG_LOCAL + f"\tColumn {col_num}={col_width} {len(part):2}=Length: {part.ljust(width)} \n"
        #GOAT should this be ≥ and not >?
        if len2 > console_width: 
            too_wide = True
            if VERBOSE: print(f"{columns} columns causes overflow on row {row_num} because len2:{len2} > col_width={console_width}!\n{stripped_row}\n{rendered_row}")
        if too_wide: break        
    if VERBOSE: print(f" ------> log_line_parts_and_process_them_too return {too_wide}, INTERNAL_LOG_LOCAL")
    return too_wide, INTERNAL_LOG_LOCAL
    
    
# Generate the formatted output
#formatted_output = format_columns(input_data, columns, column_widths, divider)
#formatted_output=""

def render_columns(columns_data, column_widths, divider):
    """
    Render the columns with proper alignment and fixed-width dividers.

    Args:
        columns_data (list of lists): Distributed lines per column.
        column_widths (list): Maximum width for each column.
        divider (str): The string used to separate columns.
    
    Returns:
        list of strings: Each string represents a formatted row.
    """
    rows_per_col = max(len(col) for col in columns_data)
    rendered_rows = []
    for row in range(rows_per_col):
        row_parts = []
        for col_idx, column in enumerate(columns_data):
            if row < len(column):
                part = column[row]
            else:
                part = ""
            # Ensure the part does not exceed the column width
            if len(part) > column_widths[col_idx]:
                part = part[:column_widths[col_idx]]
            # Pad the part to match the column width
            padded_part = f"{part.ljust(column_widths[col_idx])}"
            row_parts.append(padded_part)
        # Join the parts with the divider
        rendered_row = divider.join(row_parts)
        rendered_rows.append(rendered_row)
    return rendered_rows

## Print the formatted output
#print (content_ansi, end="");
#for line in formatted_output:
#    print(line)
#print(f"🙀 formatted output is '{formatted_output}'\n")

# Debug function to display layout information
#ef debug_info(columns, column_widths, width, desired_max_height, console_width, console_height, input_lines, formatted_output):
def debug_info(columns,                width, desired_max_height, console_width, console_height, input_lines, formatted_output):
    longest_length=9999999999999
    if formatted_output:
        try:
            # Use key=len to find the longest line based on length
            longest_line = max(formatted_output, key=len)
            longest_length = len(longest_line)
            # Find all lines that share the maximum length
            longest_lines = [line for line in formatted_output if len(line) == longest_length]
        except ValueError:
            # This block is precautionary; it shouldn't be reached since we've checked if formatted_output is not empty
            longest_line = ''
            longest_length = 0
            longest_lines = []

    #total_width = sum(column_widths) + (divider_visible_length * (columns - 1))
    total_width = longest_length
    rows_per_col = ceil(len(input_lines) / columns) if columns > 0 else 0
    aspect_ratio = calculate_aspect_ratio(total_width, rows_per_col) if rows_per_col > 0 else float('inf')
    aspect_diff = abs(aspect_ratio - 1.0)
    divider = "🌟🌟🌟🌟🌟🌟🌟🌟"
    print(f"\n\033[38;2;187;0;0m{divider}DEBUG INFO:{divider}\033[0m")
    print(f"{INTERNAL_LOG}", end="")
    print(f"\nRows original: {len(input_lines)}")
    print(f"Rows after:    {len(formatted_output)}")
    print(f"Columns used:  {columns}")
    #print(f"Width of each column: {column_widths}")
    print(f"Total width: {total_width} (console_width:{console_width}, height:{console_height})")
    print(f"Rows per column: {rows_per_col}")
    print(f"Aspect Ratio (Width/Height): {aspect_ratio:.2f}")
    print(f"Aspect Ratio Difference from 1.0: {aspect_diff:.2f}")
    print(f"Detected screen width: {console_width}")
    print(f"Detected screen height: {console_height}")
    print(f"Desired maximum rows per column: {desired_max_height}")

# Run the debug function
#f VERBOSE: debug_info(columns, column_widths, width, desired_max_height, console_width, console_height, input_data, formatted_output)
#f VERBOSE: debug_info(columns, width, desired_max_height, console_width, console_height, input_data, formatted_output)
#f VERBOSE: debug_info(columns, width, desired_max_height, console_width, console_height, input_data)


def main():
    global INTERNAL_LOG, VERBOSE, WRAPPING, FORCE_COLUMNS, console_width, console_height, columns
    our_args = parse_arguments()
    INTERNAL_LOG=""


    # Override ROW_PADDING if specified
    ROW_PADDING = our_args.row_padding
    VERBOSE     = our_args.verbose

    WRAPPING = DEFAULT_WRAPPING
    if our_args   .wrap: WRAPPING = True
    if our_args.no_wrap: WRAPPING = False
       

    # Try to detect terminal width and height, otherwise use default values
    try:
        import shutil
        console_width, console_height = shutil.get_terminal_size()
        #import os
        #console_width, console_height = os.get_terminal_size().lines, os.get_terminal_size().columns
        #x = os.get_terminal_size().lines
        #y = os.get_terminal_size().columns
        #console_width, console_height = x, y
        #from rich.console import Console
        #console = Console(stderr=True, legacy_windows=False)
        #print(console.size, file=sys.stderr)
        #console_width, console_height = console.size.width, console.size.height
    except Exception:
        console_width, console_height = 80, 25
        print("Unable to detect console size. Using default width=80 and height=25.")

    ## Override with user-provided width if specified
    width = args.width or console_width
    desired_max_height = console_height - ROW_PADDING  # Adjust height by subtracting ROW_PADDING


    # Try to detect terminal width and height, otherwise use default values
    try:
        import shutil
        console_width, console_height = shutil.get_terminal_size()
    except Exception:
        console_width, console_height = 80, 25
        print("Unable to detect console size. Using default width=80 and height=25.")
    if VERBOSE: print(f" —— Detected console  width of {console_width } ——\n —— Detected console height of {console_height} ——\n")

    width = args.width or console_width                                         # Override with user-provided width if specified
    desired_max_height = console_height - args.row_padding                      # Adjust height by subtracting ROW_PADDING

    input_data = read_input(WRAPPING, args.max_line_length_before_wrapping)     # Read and process input lines

    # Determine the number of columns
    if our_args.columns:
        if our_args.columns < 1:
            print("Error: Number of columns must be at least 1.")
            sys.exit(1)
        columns = our_args.columns
        rows_per_col = ceil(len(input_data) / columns)  #redundant
        if our_args.verbose or VERBOSE or True:
            print(f"Using user-specified columns: {columns}")
            print(f"Rows per column: {rows_per_col}")
    else:
        columns = determine_optimal_columns(input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
        rows_per_col = ceil(len(input_data) / columns)  #redundant


    INTERNAL_LOG = ""
    output = ""
    keep_looping = True
    force_num_columns = False
    while keep_looping:
        is_too_wide = False
        output = ""
        
        if not force_num_columns and not FORCE_COLUMNS:
                columns = determine_optimal_columns(input_data, width, divider_length=3, desired_max_height=desired_max_height, verbose=args.verbose)
        if columns == 0: rows_per_col  = 1
        else:            rows_per_col  = ceil(len(input_data) / columns)        
        columns_data  = distribute_lines_into_columns(input_data, columns, rows_per_col)      
        column_widths = calculate_column_widths(columns_data)
        rendered_rows = render_columns(columns_data, column_widths, divider)
        if args.verbose: print(f"Column widths: {column_widths}")
        
        #DEBUG: print(f"🦈 in the end, columns were {columns}")
        
        for row_num, rendered_row in enumerate(rendered_rows, start=1):
            INTERNAL_LOG_FRAGMENT=""
            line_parts = rendered_row.split(divider)                      # Split the rendered row back into parts based on the divider
            line_parts = [part.strip() for part in line_parts]            # Trim any extra spaces
            is_too_wide, INTERNAL_LOG_FRAGMENT = log_line_parts_and_process_them_too(line_parts, row_num, column_widths, rendered_row)
            if VERBOSE: print(f"🐾🐾 row_num {row_num}... is_too_wide={is_too_wide}")
            if is_too_wide: 
                if VERBOSE: print(f"🐾🐾 breaking")
                break
            INTERNAL_LOG = INTERNAL_LOG + INTERNAL_LOG_FRAGMENT
            output += rendered_row + "\n"
        if VERBOSE: print(f"🤬🤬 row_num {row_num}... is_too_wide={is_too_wide}")
        keep_looping = False                                             #only keep looking if things required a redo
        force_num_columns = False               
        if is_too_wide and not FORCE_COLUMNS: 
            if VERBOSE: print(f"🤬🤬 ACTING ON IT")
            keep_looping = True                                          #keep looping, but with a lower number of coumns
            columns = columns - 1
            force_num_columns = True
            if columns == 1: keep_looping = False
        
    #DEBUG: print(f"🦈 in the end, columns were {columns}")
    print(output)
    
    # Optionally, print the internal log
    if args.verbose:
        print("\nInternal Log:")
        print(INTERNAL_LOG)

if __name__ == "__main__":
    main()
