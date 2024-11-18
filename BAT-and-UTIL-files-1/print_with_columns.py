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

import sys
sys.stdin .reconfigure(encoding='utf-8', errors='replace')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# Define default ROW_PADDING
DEFAULT_ROW_PADDING = 7  # Number of rows to subtract from screen height as desired maximum

# Define the divider and its visible length
content_ansi           =  "\033[0m"
divider_ansi           =  "\033[38;2;187;187;0m"
divider                = f"  {divider_ansi}" + "│" + f"  {content_ansi}"  # Divider with #BBBB00 color and additional padding
divider_visible_length = 5
DEFAULT_WRAPPING       = False                                            #do we default to enabling the wrapping of long lines

# Internal log
INTERNAL_LOG = ""

# Set up the argument parser
parser = argparse.ArgumentParser(description="Display STDIN in a compact, multi-column format.")
parser.add_argument('-w', '--width'                    , type=int,                              help="Override console width")
parser.add_argument('-c', '--columns'                  , type=int,                              help="Number of columns (overrides automatic calculation)")
parser.add_argument('-p', '--row_padding'              , type=int, default=DEFAULT_ROW_PADDING, help="Number of rows to subtract from screen height as desired maximum")
parser.add_argument('-v', '--verbose'                  , action='store_true',                   help="Verbose mode——display debug info")
parser.add_argument('--wrap'                           , action='store_true',                   help="Enable line wrapping for long lines") #makes args.wrap true
parser.add_argument('--no_wrap'                        , action='store_true',                   help="Disable line wrapping for long lines") #makes args.wrap false
parser.add_argument('--max-line-length-before-wrapping', type=int, default=80,                  help="Maximum line length before wrapping")
args = parser.parse_args()

# Override ROW_PADDING if specified
ROW_PADDING = args.row_padding
VERBOSE     = args.verbose

WRAPPING = DEFAULT_WRAPPING
if args   .wrap: WRAPPING = True
if args.no_wrap: WRAPPING = False

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

INTERNAL_LOG = INTERNAL_LOG + f" —— Detected console  width of {console_width } ——\n"
INTERNAL_LOG = INTERNAL_LOG + f" —— Detected console height of {console_height} ——\n"

# Override with user-provided width if specified
width = args.width or console_width
desired_max_height = console_height - ROW_PADDING  # Adjust height by subtracting ROW_PADDING

# Read input from STDIN
input_lines = sys.stdin.read().strip().splitlines()

if not input_lines:
    sys.exit("No input data provided.")

# Implement line wrapping if enabled
if WRAPPING:
    wrapped_lines = []
    for line in input_lines:
        # Wrap lines longer than max_line_length
        wrapped = textwrap.wrap(line.rstrip(), width=args.max_line_length) or ['']
        wrapped_lines.extend(wrapped)
    input_data = wrapped_lines
else:
    input_data = [line.rstrip() for line in input_lines]

# Update max_line_length after wrapping
max_line_length = max(len(line) for line in input_data) if input_data else 0

INTERNAL_LOG += f"Initial Max_line_length is {max_line_length}\n"

# Function to calculate the adjusted aspect ratio
def calculate_aspect_ratio(total_width, total_rows):
    # Since characters are twice as high as they are wide, multiply rows by 2
    return total_width / (2 * total_rows) if total_rows != 0 else float('inf')

# Function to determine the optimal number of columns
def determine_optimal_columns(lines, console_width, divider_len, desired_max_height, initial_cols=1, strict=False):
    global INTERNAL_LOG
    num_lines = len(lines)
    max_line_length = max(len(line) for line in lines) if lines else 0

    INTERNAL_LOG += f"determine_optimal_columns({len(lines)} lines, width={console_width}, div-len={divider_len}, desired_rows={desired_max_height}, strict={strict})\n"
    INTERNAL_LOG += f"\tmax_line_length is {max_line_length}\n"

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
        INTERNAL_LOG += f"* If # columns={tentative_cols}, then:\t... width?={tentative_total_width} ... console={console_width}x{console_height}, num_lines(orig)={num_lines}, AR={aspect_ratio},AR_diff={aspect_diff}\n"

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

# Determine the optimal number of columns
if args.columns:
    # Enforce the specified number of columns
    columns, column_widths = determine_optimal_columns(
        input_data,
        width,
        divider_visible_length,
        desired_max_height,
        initial_cols=args.columns,
        strict=True
    )
else:
    # Allow dynamic calculation of columns
    initial_columns = 1  # Starting point
    columns, column_widths = determine_optimal_columns(
        input_data,
        width,
        divider_visible_length,
        desired_max_height,
        initial_cols=initial_columns,
        strict=False
    )

# Inform the user if the specified column count was adjusted (only applicable when -c is not used)
if args.columns:
    # Since we are enforcing strict=True, no adjustment should occur
    pass
else:
    # If dynamic columns were adjusted, inform the user
    INTERNAL_LOG = INTERNAL_LOG + f"Determined number of columns: {columns}"

# short-circuit if columns is 1 —— we're just printing it normally if there's just 1 column!
if columns == 1:
    for line in input_data: print (line)
    exit(1)


# Function to format text into columns
def format_columns(lines, columns, column_widths, divider):
    output = []
    num_lines = len(lines)
    rows_per_col = ceil(num_lines / columns) if columns > 0 else 0
    column_lines = [lines[i * rows_per_col:(i + 1) * rows_per_col] for i in range(columns)]

    for row in range(rows_per_col):
        line_parts = []
        for col_index in range(columns):
            if col_index >= len(column_widths):
                # Defensive check to prevent IndexError
                text = ""
            elif row < len(column_lines[col_index]):
                text = column_lines[col_index][row]
            else:
                text = ""  # Handle empty cells
            # Ensure column_widths[col_index] exists
            if col_index < len(column_widths):
                line_parts.append(text.ljust(column_widths[col_index]))
            else:
                line_parts.append(text)  # If somehow missing, append without padding
        line = divider.join(line_parts)
        output.append(line)
    return output

# Generate the formatted output
formatted_output = format_columns(input_data, columns, column_widths, divider)


# Print the formatted output
print (content_ansi, end="");
for line in formatted_output:
    print(line)

# Debug function to display layout information
def debug_info(columns, column_widths, width, desired_max_height, console_width, console_height, input_lines, formatted_output):
    total_width = sum(column_widths) + (divider_visible_length * (columns - 1))
    rows_per_col = ceil(len(input_lines) / columns) if columns > 0 else 0
    aspect_ratio = calculate_aspect_ratio(total_width, rows_per_col) if rows_per_col > 0 else float('inf')
    aspect_diff = abs(aspect_ratio - 1.0)
    divider = "🌟🌟🌟🌟🌟🌟🌟🌟"
    print(f"\n\033[38;2;187;0;0m{divider}DEBUG INFO:{divider}\033[0m")
    print(f"{INTERNAL_LOG}", end="")
    print(f"\nRows original: {len(input_lines)}")
    print(f"Rows after:    {len(formatted_output)}")
    print(f"Columns used:  {columns}")
    print(f"Width of each column: {column_widths}")
    print(f"Total width: {total_width} (console_width:{console_width}, height:{console_height})")
    print(f"Rows per column: {rows_per_col}")
    print(f"Aspect Ratio (Width/Height): {aspect_ratio:.2f}")
    print(f"Aspect Ratio Difference from 1.0: {aspect_diff:.2f}")
    print(f"Detected screen width: {console_width}")
    print(f"Detected screen height: {console_height}")
    print(f"Desired maximum rows per column: {desired_max_height}")

# Run the debug function
if VERBOSE: debug_info(columns, column_widths, width, desired_max_height, console_width, console_height, input_data, formatted_output)

