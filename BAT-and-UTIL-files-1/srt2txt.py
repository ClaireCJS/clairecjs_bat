###🤔IDEA: a maximum threshold where if it's less than that, the next line is considered part of the previous line.
#Basically, make the resultant TXT file not be limited to the width of the SRT file, which is often 20-25 chars.

import sys                                                                                         # Import sys module for system-specific parameters
import re                                                                                          # Import re module for regular expressions
import os                                                                                          # Import os module for operating system dependent functionality
import datetime                                                                                    # Import datetime module for handling date and time
import glob                                                                                        # Import glob module for pathname pattern expansion
import argparse                                                                                    # Import argparse module for parsing command-line options
from colorama import Fore, Back, Style, init                                                       # Import ANSI color module
init()                                                                                             # Enable ANSI output

EXTENSION = '.txt'                                                                                 # Hardcoded extension for output files
MAX_TIME_BETWEEN_SUBTITLES_TO_JOIN_TOGETHER       = 0.3     #if one subtitle begins less than this much time after the last ends, consider it the same line of text in the output file
MIN_TIME_BETWEEN_SUBTITLES_TO_GENERATE_BLANK_LINE = 1.5     #if one subtitle begins MORE than this much time after the last subtitle, insert a fully blank line  into  the output file

def parse_timecode(time_str):                                                                      # Define function to parse timecode strings
    """
    Parse a timecode string 'HH:MM:SS,mmm' and return the time in seconds as a float.
    """
    try:
        hours, minutes, seconds_millis = time_str.split(':')                                       # Split time_str into hours, minutes, and seconds_millis
        seconds, millis = seconds_millis.split(',')                                                # Split seconds_millis into seconds and milliseconds
        total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + int(seconds) + (int(millis) / 1000)  # Calculate total seconds as a float
        return total_seconds                                                                        # Return total seconds
    except ValueError:
        return None                                                                                # Return None if parsing fails

def srt_to_txt(input_file, output_file):                                                           # Define the main function
    if os.path.exists(output_file):                                                                # Check if output file already exists
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')                               # Get current timestamp in yyyymmddHHMMSS format
        backup_filename = f"{output_file}.bak.{timestamp}.bak"                                     # Construct backup filename
        os.rename(output_file, backup_filename)                                                    # Rename existing output file to backup filename

    with open(input_file, 'r', encoding='utf-8') as f_in:                                          # Open the input file with UTF-8 encoding
        lines = f_in.readlines()                                                                   # Read all lines from the input file

    subtitles = []                                                                                 # Initialize a list to store subtitles
    subtitle = []                                                                                  # Initialize a list to store lines of the current subtitle

    previous_line = None
    for line in lines:                                                                             # Iterate over each line
        line = line.rstrip('\n')                                                                   # Remove trailing newline character
        if line.strip() == '':                                                                     # If the line is empty
            if subtitle:                                                                           # If there is a current subtitle
                subtitles.append(subtitle)                                                         # Add the current subtitle to subtitles list
                subtitle = []                                                                      # Reset subtitle for the next one
        else:
            subtitle.append(line)                                                                  # Add line to the current subtitle

    if subtitle:                                                                                   # Add any remaining subtitle
        subtitles.append(subtitle)

    text_lines = []                                                                                # Initialize a list to store subtitle text lines
    last_non_blank_end_time = None                                                                 # Initialize end time of last non-blank subtitle

    for subtitle in subtitles:                                                                     # Iterate over each subtitle
        if len(subtitle) >= 2:
            index_line = subtitle[0]                                                               # First line is the index number
            timecode_line = subtitle[1]                                                            # Second line is the timecode line
            content_lines = subtitle[2:] if len(subtitle) > 2 else []                              # Remaining lines are content lines
        else:
            continue                                                                               # Skip malformed subtitles

        # Parse timecodes
        match = re.match(r'^(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timecode_line)
        if match:
            start_time_str, end_time_str = match.groups()                                          # Extract start and end time strings
            start_time = parse_timecode(start_time_str)                                            # Parse start time
            end_time   = parse_timecode(  end_time_str)                                            # Parse end time
        else:
            continue                                                                               # Skip malformed timecodes

        # Remove any blank lines in content
        content = [line for line in content_lines if line.strip() != '']                           # Filter out empty lines in content
        
        if content:
            # Non-blank subtitle
            if last_non_blank_end_time is not None:
                time_diff = start_time - last_non_blank_end_time                                   # Calculate time difference from last non-blank subtitle
                if time_diff > MIN_TIME_BETWEEN_SUBTITLES_TO_GENERATE_BLANK_LINE:
                    text_lines.append('')                                                          # Insert extra blank line
                elif time_diff < MAX_TIME_BETWEEN_SUBTITLES_TO_JOIN_TOGETHER:
                    if text_lines and text_lines[-1]:  # If there's existing text, append the current subtitle's content
                        text_lines[-1] += ' ' + ' '.join(content)  # Join lines by adding a space
                        content=""
                    else:
                        text_lines.append(' '.join(content))  # If no previous line, just add this one as is
            text_lines.extend(content)                                                             # Append content lines to text_lines
            last_non_blank_end_time = end_time                                                     # Update last non-blank end time
        else:
            # Empty subtitle
            text_lines.append('')                                                                  # Append a blank line
            # Do not update last_non_blank_end_time

    with open(output_file, 'w', encoding='utf-8') as f_out:                                        # Open the output file for writing with UTF-8 encoding
        for line in text_lines:                                                                    # Iterate over the collected text lines
            f_out.write(line.lstrip() + '\n')                                                      # Write each line followed by a newline character

if __name__ == "__main__":                                                                         # Entry point of the script
    parser = argparse.ArgumentParser(description='Converts SRT files to TXT files.')               # Create ArgumentParser object with description
    parser.add_argument('input_files', nargs='+', help='Input SRT files [supports wildcards]')     # Add positional argument for input files
    parser.add_argument('-o', '--output', help='Output file name [only valid with single input file]')  # Add optional argument for output file
    args = parser.parse_args()                                                                     # Parse the command-line arguments

    input_files = []                                                                               # Initialize list to hold all input files
    for pattern in args.input_files:                                                               # Iterate over input file patterns
        escaped_pattern = glob.escape(pattern)                                                     # wow, glob is stupid... Let us use parens and brackets without complication, we don’t always want regex! geeze.
        matched_files   = glob.glob(escaped_pattern)                                               # Expand wildcards and get matching files
        if not matched_files:                                                                      # If no files matched the pattern
            print(f"No files matched pattern: {pattern}")                                          # Display a warning message
        input_files.extend(matched_files)                                                          # Add matched files to input_files list

    if not input_files:                                                                            # If no input files were found
        print("No input files to process.")                                                        # Display error message
        sys.exit(1)                                                                                # Exit with error code 1

    if args.output and len(input_files) > 1:                                                       # If output file is specified with multiple input files
        print("Error: Cannot specify an output file when multiple input files are provided.")      # Display error message
        sys.exit(1)                                                                                # Exit with error code 1

    for input_file in input_files:                                                                 # Iterate over each input file
        if args.output:                                                                            # If output filename is specified
            output_file = args.output                                                              # Use the specified output filename
        else:                                                                                      # If no output filename is provided
            output_file = re.sub(r'\.[^.]+$', EXTENSION, input_file)                               # Replace input file's extension with EXTENSION

        srt_to_txt(input_file, output_file)                                                        # Call the main function with input and output files
        #rint(f"✔  Generated: {output_file} generated")                                           # Display success message
        print(f'✔  Converted  SRT file to TXT: ‘{output_file}’ successfully!')                    # Display success message                                       
