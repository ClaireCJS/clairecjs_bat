"""

    LRC to TXT converter

    lrc2txt.py {lrc_input_file)  ———  creates input_file.txt
    
    Uses thresholds to add blank lines during longer vocal silence periods, as well as to merge lines that are very close together

"""


#### CONFIGURATION: DEBUG:
DEBUG_TIME                    = False   
DEBUG_INSERT_TIME_DIFFERENCES = True
DEBUG_INSERT_TIME_DIFFERENCES = False

##### CONFIGURATION: THRESHOLDS:
MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE      = 0.65                             # (various experiments)->0.15->1.50->1.00->0.75->0.65
ADD_A_BLANK_LINE_IF_MORE_THAN_THESE_MANY_SECONDS_PAST_LAST_LINE = 4.75                             # (various experiments)->4.75

#### CONFIGURATION: OUTPUT FILE:
EXTENSION_TO_PRODUCE          = '.txt'



import sys                                                                                         # Import sys        module for system-specific parameters
import re                                                                                          # Import re         module for regular expressions
import os                                                                                          # Import os         module for operating system dependent functionality
import datetime                                                                                    # Import datetime   module for handling date and time
import glob                                                                                        # Import glob       module for pathname pattern expansion
import argparse                                                                                    # Import argparse   module for parsing command-line options
import chardet                                                                                     # Import chardet    module for sampling text files to determine their encoding so they can be opened without throwing errors
import string                                                                                      # Import string     module for checking for punctuation marks
from colorama import Fore, Back, Style, init                                                       # Import ANSI color module for ANSI coloration`
init()                                                                                             # Enable ANSI output


import re

def expand_and_sort_timestamps(lines):
    """
    Expands timestamps for lyrics, ensuring each timestamp is linked correctly to its lyrics.
    
    Args:
        lines (list of str): Lines with timestamps and lyrics.
    
    Returns:
        list of tuple: Sorted list of (timestamp, lyric).
    """
    expanded_lines = []

    for line in lines:
        # Find all timestamps
        timestamps = re.findall(r'\[(\d+:\d+\.\d+)\]', line)
        # Extract the lyric (everything after the last timestamp)
        lyric = re.split(r'\[\d+:\d+\.\d+\]', line)[-1].strip()
        
        if lyric:  # Only process if there are lyrics
            for timestamp in timestamps:
                # Convert timestamp to seconds for sorting
                minutes, seconds = map(float, timestamp.split(":"))
                total_seconds = minutes * 60 + seconds
                expanded_lines.append((total_seconds, lyric))
    
    # Sort by timestamps
    return sorted(expanded_lines, key=lambda x: x[0])





def expand_and_sort_timestamps_v2(lines):
    expanded_lines = []

    for line in lines:                                                  # Find all timestamps in the line
        timestamps = re.findall(r'\[(\d+):(\d+)\.(\d+)\]', line)        # Extract all timestamps
        text_match = re.search (r'\](.*)'                , line)        # Extract the text after the last timestamp
        if timestamps and text_match:
            text = text_match.group(1).strip()
            seen = set()  # Track unique timestamps
            for minutes, seconds, centiseconds in timestamps:
                total_seconds = int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
                #expanded_lines.append((total_seconds, text))                                
                if total_seconds not in seen:                           # Skip duplicate timestamps
                    seen.add(total_seconds)
                    expanded_lines.append((total_seconds, text))

    expanded_lines.sort(key=lambda x: x[0])                             # Sort by time
    return expanded_lines








def parse_timecode_lrc(line):
    """
    Parse an LRC line '[MM:SS.xx] <text>' and return the timestamp in seconds and the text.

    Does not work for lines with multiple timestamps:
        parse_timecode_lrc() assumes that lines with multiple timestamps have been 
        preprocessed into separate lines with function expand_and_sort_timestamps() 
    """
    print(f"\n* parse_timecode_lrc(line={line})")
    
    if line:
        partial_match = re.match(r'\[(\d+):(\d+)\.(\d+)\]'       , line)
        match         = re.match(r'\[(\d+):(\d+)\.(\d+)\]\s*(.*)', line)
        pass
        
    #f         match:                              #no! this doesn’t match blank lines
    if partial_match:
        #print(f"partial match for {line} !")
        #try:
        minutes, seconds, centiseconds = partial_match.groups()
        _, _, _, text                  =         match.groups()
        total_seconds = int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
        return total_seconds, text.strip()
        #except ValueError:
        #    return None, line                                                                           # Return None if parsing fails
    return None, line


import re

def replace_smart_quotes(line):
    """
    Define patterns for identifying opening and closing quotes
    
    Example usage:
        text = '''"Hello," he said. "Is this your book?"'''
        result = replace_smart_quotes(text)
        print(result)

    """
    
    ### Replace the first occurrence of " with a left quote (opening quote)
    #ine = re.sub(r'(^|[\s\(\[\{.,!?;])"', r'\1“', line, count=1)
    line = re.sub(r'(^|[\s\(\[\{,!?;])"' , r'\1“', line, count=1)
    
    ### Replace the last occurrence of " with a right quote (closing quote)
    #ine = re.sub(r'"([\s.,!?;:\)\]\}])', r'”\1', line[::-1], count=1)[::-1]
    line = re.sub(r'"([\s.,!?;:\)\.\]\}])', r'”\1', line[::-1], count=1)[::-1]

    return line


def lrc_to_txt(input_file, output_file):
    """
    Performs the actual LRC->TXT conversion
    """
        
    # backup original file
    if os.path.exists(output_file):                                                                     # check if output file exists
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')                                    # generate string for this moment in time
        backup_filename = f"{output_file}.bak.{timestamp}.bak"                                          # generate unique backup filename
        os.rename(output_file, backup_filename)                                                         # rename the old file to our newly-generated backup filename

    #with open(input_file, 'r', encoding='utf-8') as f_in:
    #   lines = f_in.readlines()

    # open file *safely*
    with open(input_file, 'rb') as raw_file:                                                            #fix for real-world files that have varied encoding
        result = chardet.detect(raw_file.read(1000))    # Detect encoding based on a sample             #fix for real-world files that have varied encoding
        encoding = result['encoding']                                                                   #fix for real-world files that have varied encoding
    with open(input_file, encoding=encoding, errors='replace') as file_in:                              #fix for real-world files that have varied encoding
        lines = file_in.readlines()

    # Preprocess lines to convert/expand lines-with-multiple-timestamps into single-timpestamp lines, and to then sort them:
    original_lines = lines
    lines          = expand_and_sort_timestamps(lines)
    
    #print(f"\n\n\n\nexpanded lines is now:\n{lines}\n\n\n\n")

    merged_output_lines        = []
    cleaned_output_lines       = []
    last_line                  = "N/A"
    last_text                  = ""
    last_time                  = 0
    time_difference            = 0
    current_output_line        = ""
    for line in lines:       
        # separate out timestamps from text:
        #ime, text = parse_timecode_lrc(line)                                                   #if DEBUG_TIME: print(f"\n* looping: time={time},text==>'{text.strip()}'",end="\n")       
        time, text = line                                                                       #if DEBUG_TIME: print(f"\n* looping: time={time},text==>'{text.strip()}'",end="\n")       
        
        if time is None: continue                                        # skip lines without timestampes
        text = text if text else "\n"                                    # massage text
        time_difference = time - last_time if last_time else -666        # get time difference

        # **DO** merge lines if they *ARE* close enough ***************************************************************************************************************************
        if 0 < time_difference < MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE:
            if DEBUG_INSERT_TIME_DIFFERENCES: text = f"🍌 {time_difference:5.1f} 🍌 " + text.strip()
            text = text.strip()
            if current_output_line and current_output_line[-1] not in string.punctuation: joined_line_divider = ", " 
            else:                                                                         joined_line_divider = " "
            current_output_line += joined_line_divider + text.lstrip()

        # DON’T merge lines if they aren’t close enough ***************************************************************************************************************************
        else:
            # Finalizing merged content:
            if current_output_line:
                merged_output_lines.append(current_output_line)
                current_output_line=""
                
            # Append a blank line for large gaps
            if time_difference > ADD_A_BLANK_LINE_IF_MORE_THAN_THESE_MANY_SECONDS_PAST_LAST_LINE:
                #merged_output_lines.append("🐐")
                merged_output_lines.append("")
            
            # Append the current text
            if DEBUG_INSERT_TIME_DIFFERENCES: text = f"⏱ {time_difference:5.1f} ⏱ " + text.strip()
            text = text.strip()
            #merged_output_lines.append(text)
            #current_output_line = ""            
            current_output_line = text
            
        last_time = time                           
    #end for line in lines
        
    #if text != "":
    if current_output_line:
            merged_output_lines.append(current_output_line)

    # clean successive blank lines
    last_line=""
    for line in merged_output_lines:
        line = line.strip()
        if line != "" or last_line != "": cleaned_output_lines.append(line)
        last_line=line

    # output our finialized file with final massage of values
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for line in cleaned_output_lines:
            line = replace_smart_quotes(line)                                                                 # change " to “ and ”
            line = line.replace("'","’")                                                                      # change ' to ’
            f_out.write(line.lstrip() + "\n")
                                                                                                                                                                              
#—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————                                                                                                                                                                              

if __name__ == "__main__":                                                                                    # Entry point of the script                                                                                                                                                                                                                                                                 
    parser = argparse.ArgumentParser(description='Converts LRC files to TXT files.')                          # Create ArgumentParser object with description                 
    parser.add_argument('input_files', nargs='+', help='Input LRC files [supports wildcards]')                # Add positional argument for input files    
    parser.add_argument('-o', '--output', help='Output file name [only valid with single input file]')        # Add   optional argument for output file                         
    args = parser.parse_args()                                                                                # Parse the command-line arguments                              
                                                                                                                                                                              
    input_files = []                                                                                          # Initialize list to hold all input files                       
    for pattern in args.input_files:                                                                          # Iterate over input file patterns                              
        escaped_pattern = glob.escape(pattern)                                                                # wow, glob is stupid... Let us use parens and brackets without complication, we don’t always want regex! geeze.
        matched_files = glob.glob(pattern)                                                                    # Expand wildcards and get matching files                       
        if not matched_files:                                                                                 # If no files matched the pattern                               
            print(f"No files matched pattern: {pattern}")                                                     # Display a warning message                                     
        input_files.extend(matched_files)                                                                     # Add matched files to input_files list                         
                                                                                                                                                                              
    if not input_files:                                                                                       # If no input files were found                                  
        print("No input files to process.")                                                                   # Display error message                                         
        sys.exit(1)                                                                                           # Exit with error code 1                                        
                                                                                                                                                                              
    if args.output and len(input_files) > 1:                                                                  # If output file is specified with multiple input files         
        print("Error: Cannot specify an output file when multiple input files are provided.")                 # Display error message                                         
        sys.exit(1)                                                                                           # Exit with error code 1                                                                                        
        
    #—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————                                                                                                                                                                              
    
    for input_file in input_files:                                                                            # Iterate over each input file                                  
        if args.output: output_file = args.output                                                             # If output filename is specified, use the specified output filename                                                                                                                 
        else:           output_file = re.sub(r'\.[^.]+$', EXTENSION_TO_PRODUCE, input_file)                   # If no output filename is provided, replace input file's extension with EXTENSION                                                                                                                                                                                               
        lrc_to_txt(input_file, output_file)                                                                   # Call the main function with input and output files            
        #rint(f'✔  Generated lyrics: "{output_file}"')                                                       # Display success message                                       
        print(f'✔  Karaoke conversion success: “{output_file}”')                                             # Display success message
        #rint(f'✔  Converted  LRC file to TXT: “{output_file}” successfully!')                               # Display success message 🐐

    #—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————                                                                                                                                                                              

