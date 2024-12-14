import sys                                                                                         # Import sys module for system-specific parameters
import re                                                                                          # Import re module for regular expressions
import os                                                                                          # Import os module for operating system dependent functionality
import datetime                                                                                    # Import datetime module for handling date and time
import glob                                                                                        # Import glob module for pathname pattern expansion
import argparse                                                                                    # Import argparse module for parsing command-line options
import chardet                                                                                     # Import chardet module for sampling text files to determine their encoding so they can be opened without throwing errors
from colorama import Fore, Back, Style, init                                                       # Import ANSI color module
init()                                                                                             # Enable ANSI output

#ERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE    = 2.5                                # lines ended up being too long on average
MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE    = 1.5

EXTENSION_TO_PRODUCE = '.txt'

def expand_and_sort_timestamps(lines):
    """
    Expands lines with multiple timestamps into separate lines, 
    sorts them in chronological order.
    
    For example:
               
        line #1: [00:49.74]Create Fictitious Enemy
        line #2: [00:54.35]Outlaw Of Expression
        line #3: [00:58.95]Forget Past Wars We Have Fought
        line #4: [01:04.06][02:32.47]Watchers Of Morality        //notice how this line has 2 timestamps?
        line #5: [01:05.67][02:33.97]Told By The Hierarchy       //notice how this line has 2 timestamps?
        line #6: [01:07.79][02:36.21]Machine To Society          //notice how this line has 2 timestamps?
        line #7: [01:09.90]Falling To Conformity

    would be turned into: 
        
        line  #1: [00:49.74]Create Fictitious Enemy
        line  #2: [00:54.35]Outlaw Of Expression
        line  #3: [00:58.95]Forget Past Wars We Have Fought
        line  #4: [01:04.06]Watchers Of Morality                 //this line was split off of the original line #4 above
        line  #5: [01:05.67]Told By The Hierarchy                //this line was split off of the original line #5 above
        line  #6: [01:07.79]Machine To Society                   //this line was split off of the original line #6 above
        line  #7: [01:09.90]Falling To Conformity
        line  #8: [02:32.47]Watchers Of Morality                 //this line was split off of the original line #4 above
        line  #9: [02:33.97]Told By The Hierarchy                //this line was split off of the original line #5 above
        line #10: [02:36.21]Machine To Society                   //this line was split off of the original line #6 above
    """
    expanded_lines = []

    for line in lines:                                                  # Find all timestamps in the line
        timestamps = re.findall(r'\[(\d+):(\d+)\.(\d+)\]', line)
        text_match = re.search (r'\](.*)'                , line)
        if timestamps and text_match:
            text = text_match.group(1).strip()
            for minutes, seconds, centiseconds in timestamps:
                total_seconds = int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
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
    partial_match = re.match(r'\[(\d+):(\d+)\.(\d+)\]'       , line)                                     # DEBUG: print(f"\n* parse_timecode_lrc({line.strip()})")
    match         = re.match(r'\[(\d+):(\d+)\.(\d+)\]\s*(.*)', line)
    #f         match:  #no! this doesn’t match blank lines
    if partial_match:                                                                                    # DEBUG: print(f"partial match for {line} !")
        #try:
        minutes, seconds, centiseconds = partial_match.groups()
        _, _, _, text                  =         match.groups()
        total_seconds = int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
        return total_seconds, text.strip()
        #except ValueError: return None, line                                                            # Return None if parsing fails
    return None, line

def lrc_to_txt(input_file, output_file):
    if os.path.exists(output_file):
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        backup_filename = f"{output_file}.bak.{timestamp}.bak"
        os.rename(output_file, backup_filename)

    # open file *safely*
    with open(input_file, 'rb') as raw_file:                                                         #fix for real-world files that have varied encoding
        result = chardet.detect(raw_file.read(1000))    # Detect encoding based on a sample          #fix for real-world files that have varied encoding
        encoding = result['encoding']                                                                #fix for real-world files that have varied encoding
    with open(input_file, encoding=encoding) as file_in:                                             #fix for real-world files that have varied encoding
        lines = file_in.readlines()

    # Preprocess lines to convert/expand lines-with-multiple-timestamps into single-timpestamp lines, and to then sort them:
    original_lines = lines
    lines = expand_and_sort_timestamps(lines)

    # process our new expanded file that is guaranteed to only have 1 timestamp per line
    current_text  = []
    merged_lines  = []
    last_time     = None
    previous_line = None
    DEBUG_TIME    = False           
    for line in lines:
        time, text = parse_timecode_lrc(line)
        #print(f"looping: time={time},text==>'{text.strip()}'",end="\n")
        if time is None:
            if DEBUG_TIME: print(f"TIME IS NONE FOR TEXT OF --> '{text.strip()}'\n")
            #Do not append lines that look like these, as they tend to be non-lyric lines like 
            #“[id: ms_aasdfasdf]” or “[ar:Metallica]” and are not what we’d want in a TXT file:
            #current_text.append('\n')
        else:            
            if text is None:
                current_text.append("\n")
            else:                
                # spicy take: merge lines together if the timing is really really close:
                if last_time is not None:
                    time_difference = time - last_time
                    if time_difference > MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE:
                        if DEBUG_TIME: merged_lines.append(f"\n{time_difference:.2f} seconds (thresh={MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE}): {text}")  # Add time difference
                        merged_lines.append(' '.join(current_text))
                        current_text = []
                else:
                    if DEBUG_TIME: merged_lines.append(f"\n0.00 seconds (thresh={MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE}): {text}")  # No difference for the first line

                # regardless of whether we merged multiple lines together (about 10 lines earlier in this file),
                # we need to append our results to “current_text”:
                current_text.append(text)
                last_time = time
            

    if current_text:
            merged_lines.append(' '.join(current_text))

    with open(output_file, 'w', encoding='utf-8') as f_out:
        for line in merged_lines:
            f_out.write(line + '\n')
                                                                                                                                                                              
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
        print(f'✔  Lyric generation success: "{output_file}"')                                               # Display success message                                       

    #—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————                                                                                                                                                                              

