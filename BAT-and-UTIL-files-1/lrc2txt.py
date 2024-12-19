##### CONFIGURATION:
MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE = .15 #🐐
MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE = 1.5
ADD_A_BLANK_LINE_IF_MORE_THAN_THESE_MANY_SECONDS_PAST_LAST_LINE = 4.75
EXTENSION_TO_PRODUCE = '.txt'


import sys                                                                                         # Import sys module for system-specific parameters
import re                                                                                          # Import re module for regular expressions
import os                                                                                          # Import os module for operating system dependent functionality
import datetime                                                                                    # Import datetime module for handling date and time
import glob                                                                                        # Import glob module for pathname pattern expansion
import argparse                                                                                    # Import argparse module for parsing command-line options
from colorama import Fore, Back, Style, init                                                       # Import ANSI color module
init()                                                                                             # Enable ANSI output


def parse_timecode_lrc(line):
    """
    Parse an LRC line '[MM:SS.xx] <text>' and return the timestamp in seconds and the text.
    """
    #print(f"\n* parse_timecode_lrc({line.strip()})")
    partial_match = re.match(r'\[(\d+):(\d+)\.(\d+)\]'       , line)
    match         = re.match(r'\[(\d+):(\d+)\.(\d+)\]\s*(.*)', line)
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




def lrc_to_txt(input_file, output_file):
    
    if os.path.exists(output_file):
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f"{output_file}.bak.{timestamp}.bak"
        os.rename(output_file, backup_filename)

    with open(input_file, 'r', encoding='utf-8') as f_in:
        lines = f_in.readlines()

    merged_output_lines        = []
    cleaned_output_lines       = []
    last_time                  = 0
    last_line                  = "N/A"
    last_text                  = ""
    previous_line              = ""
    time_difference            = 0
    DEBUG_TIME                 = False   
    current_output_line        = ""
    for line in lines:       
        time, text = parse_timecode_lrc(line)                                                   #if DEBUG_TIME: print(f"\n* looping: time={time},text==>'{text.strip()}'",end="\n")       
        if time is None: 
            text=""
            continue
        if last_time: time_difference = time - last_time
        else        : time_difference = 0       
        if "" == text: text="\n"
            
        if time_difference > MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE:
            merged_output_lines.append(current_output_line + " " + text) 
            current_output_line = ""
            if time_difference > ADD_A_BLANK_LINE_IF_MORE_THAN_THESE_MANY_SECONDS_PAST_LAST_LINE: merged_output_lines.append("")
            last_time = time        
            continue
        else:            
            if "" == current_output_line: current_output_line =                             text.lstrip()
            else:                         current_output_line = current_output_line + " " + text.lstrip()
        last_time = time                           
    if text != "":
            merged_output_lines.append(current_output_line)


    # clean successive blank lines
    last_line=""
    for line in merged_output_lines:
        line = line.strip()
        if line != "" or last_line != "": cleaned_output_lines.append(line)
        last_line=line


    with open(output_file, 'w', encoding='utf-8') as f_out:
        for line in cleaned_output_lines:
            f_out.write(line.lstrip() + "\n")
                                                                                                                                                                              
#—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————                                                                                                                                                                              
if __name__ == "__main__":                                                                                    # Entry point of the script                                                                                                                                                                                                                                                                 
    parser = argparse.ArgumentParser(description='Converts LRC files to TXT files.')                          # Create ArgumentParser object with description                 
    parser.add_argument('input_files', nargs='+', help='Input LRC files [supports wildcards]')                # Add positional argument for input files    
    parser.add_argument('-o', '--output', help='Output file name [only valid with single input file]')        # Add   optional argument for output file                         
    args = parser.parse_args()                                                                                # Parse the command-line arguments                              
                                                                                                                                                                              
    input_files = []                                                                                          # Initialize list to hold all input files                       
    for pattern in args.input_files:                                                                          # Iterate over input file patterns                              
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
        print(f'✔  Karaoke conversion success: "{output_file}"')                                               # Display success message                                       

    #—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————                                                                                                                                                                              

