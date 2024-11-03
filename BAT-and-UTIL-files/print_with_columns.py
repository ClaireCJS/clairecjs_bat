import sys
import shutil
import argparse
from math import ceil
import re

# Define the divider and its visible length
divider = "  \033[38;2;187;187;0m│\033[0m  "  # Divider with #BBBB00 color and additional padding

def get_visible_length(s):
    # Remove ANSI escape codes
    return len(re.sub(r'\x1b\[[0-9;]*m', '', s))

divider_visible_length = get_visible_length(divider)  # 5 characters

# Define ROW_PADDING
ROW_PADDING = 5  # Number of rows to subtract from screen height as a desired maximum

# Set up the argument parser
parser = argparse.ArgumentParser(description="Display STDIN in a compact, multi-column format.")
parser.add_argument('-w', '--width', type=int, help="Override console width")
parser.add_argument('-c', '--columns', type=int, help="Number of columns")

# Parse arguments
args = parser.parse_args()

# Try to detect terminal width and height, otherwise prompt for manual input
try:
    console_width, console_height = shutil.get_terminal_size((80, 25))
except Exception:
    console_width, console_height = 80, 25
    print("Unable to detect console size. Please specify -w (width) manually.")

# Override with user-provided width if specified
width = args.width or console_width
height = console_height - ROW_PADDING  # Adjust height by subtracting ROW_PADDING

# Read input from STDIN
input_data = [line.rstrip() for line in sys.stdin.read().strip().splitlines()]

# Determine the optimal number of columns if not specified
def determine_columns(lines, width, divider_len, desired_max_height):
    if not lines:
        return 1, [0]  # Return 1 column with width 0 if no lines

    max_line_length = max(len(line) for line in lines)
    num_lines = len(lines)

    # Start with the maximum possible columns and decrease until it fits
    for cols in range(len(lines), 0, -1):
        rows = ceil(num_lines / cols)
        if cols > rows:
            continue  # Ensure columns do not exceed rows

        column_width = (width - (divider_len * (cols - 1))) // cols
        if column_width < max_line_length:
            continue  # Column width too small for the longest line

        # Calculate total width based on column widths
        column_lines = [lines[i * ceil(num_lines / cols):(i + 1) * ceil(num_lines / cols)] for i in range(cols)]
        column_widths = [max(len(line) for line in col) if col else 0 for col in column_lines]
        total_width = sum(column_widths) + divider_len * (cols - 1)

        if total_width > desired_max_height:
            continue  # Total width exceeds desired maximum height

        return cols, column_widths

    return 1, [max(len(line) for line in lines)]  # Fallback to 1 column

# Set columns automatically if not provided
desired_max_height = height
columns, column_widths = (args.columns, [])  # Initialize

if args.columns:
    # If user specified columns, calculate column widths
    rows_per_column = ceil(len(input_data) / args.columns)
    column_lines = [input_data[i * rows_per_column:(i + 1) * rows_per_column] for i in range(args.columns)]
    column_widths = [max(len(line) for line in col) if col else 0 for col in column_lines]
else:
    # Determine columns based on available width and desired max height
    columns, column_widths = determine_columns(input_data, width, divider_visible_length, desired_max_height)

# If columns were determined automatically, check the "too wide" condition
def adjust_columns_if_too_wide(lines, width, divider_len, desired_max_height):
    cols, col_widths = determine_columns(lines, width, divider_len, desired_max_height)
    while True:
        total_width = sum(col_widths) + divider_len * (cols - 1)
        if total_width <= desired_max_height:
            break  # Width is within desired maximum height
        if cols <= 1:
            break  # Cannot reduce columns further
        cols -= 1
        cols, col_widths = determine_columns(lines, width, divider_len, desired_max_height)
    return cols, col_widths

if not args.columns:
    columns, column_widths = adjust_columns_if_too_wide(input_data, width, divider_visible_length, desired_max_height)

# Format text into a balanced "newspaper" style layout
def format_column(lines, height, columns, divider, column_widths):
    output = []
    rows_per_column = ceil(len(lines) / columns)  # Calculate number of rows per column
    column_lines = [lines[i * rows_per_column:(i + 1) * rows_per_column] for i in range(columns)]

    for row in range(rows_per_column):
        line_parts = []
        for col_index in range(columns):
            if row < len(column_lines[col_index]):
                text = column_lines[col_index][row]
            else:
                text = ""
            line_parts.append(text.ljust(column_widths[col_index]))
        line = divider.join(line_parts)
        output.append(line)
    return output

# Generate and print the newspaper-style output
output = format_column(input_data, height, columns, divider, column_widths)
for line in output:
    print(line)

# Debug function
def debug_info(columns, column_widths, width, height, console_width, console_height):
    total_width = sum(column_widths) + divider_visible_length * (columns - 1)
    total_rows = ceil(len(input_data) / columns)
    print("\n\033[38;2;187;0;0mDEBUG INFO:\033[0m")
    print(f"Columns used: {columns}")
    print(f"Width of each column: {column_widths}")
    print(f"Total width: {total_width}")
    print(f"Total rows: {total_rows}")
    print(f"Detected screen width: {console_width}")
    print(f"Detected screen height: {console_height}")

# Run the debug function
debug_info(columns, column_widths, width, height, console_width, console_height)
