###🤔IDEA: a maximum threshold where if it's less than that, the next line is considered part of the previous line.
#Basically, make the resultant TXT file not be limited to the width of the SRT file, which is often 20-25 chars.

#mport sys                                                                                         # Import sys        module for system-specific parameters
import re                                                                                          # Import re         module for regular expressions, the heart of the actual file conversion
import os                                                                                          # Import os         module for operating system dependent functionality
import datetime                                                                                    # Import datetime   module for handling date and time
import glob                                                                                        # Import glob       module for pathname pattern expansion
import argparse                                                                                    # Import argparse   module for parsing command-line options
import chardet                                                                                     # Import chardet    module for sampling files to determine their character encoding, so that they can be properly opened and read
import string                                                                                      # Import string     module
from colorama import Fore, Back, Style, init                                                       # Import ANSI color module for creating output in color
init()                                                                                             # Enable ANSI output

EXTENSION = '.txt'                                          # Hardcoded extension for output files
MAX_TIME_BETWEEN_SUBTITLES_TO_JOIN_TOGETHER       = 0.3     #if one subtitle begins less than this much time after the last ends, consider it the same line of text in the output file
MAX_TIME_BETWEEN_SUBTITLES_TO_JOIN_TOGETHER       = 0.05    #if one subtitle begins less than this much time after the last ends, consider it the same line of text in the output file
MIN_TIME_BETWEEN_SUBTITLES_TO_GENERATE_BLANK_LINE = 1.5     #if one subtitle begins MORE than this much time after the last subtitle, insert a fully blank line  into  the output file
MIN_TIME_BETWEEN_SUBTITLES_TO_GENERATE_BLANK_LINE = 1.25    #if one subtitle begins MORE than this much time after the last subtitle, insert a fully blank line  into  the output file

DEBUG_ENCOUNTERED_LINES = False
DEBUG_SMART_QUOTES      = False
DEBUG_SHOW_INPUT_FILES  = False



def is_punctuation(c):
    return c in string.punctuation
   
def is_punctuation_except_quotes(c):
    if c in string.punctuation:
        if c == '"': return False
        else       : return True
    return False

def replace_smart_quotes(text):
    """
    Replace straight quotes with curly quotes based on context.
    """
    
    if DEBUG_SMART_QUOTES: print(f"all-but-last char of text is [" + text[:-1] + "]")

    if   text == ''  : return ""
    if   text == '"' : return "“"
    elif text == '""': return "“”"
    else:
        if text[-1] == '"': text = text[:-1] + '”'             # Replace closing quote
        if text[ 0] == '"': text =             '“' + text[1:]  # Replace opening quote

    result = []
    in_quotes = False
    last_non_space_char = ""
    prev_prev_char = ""
    prev_char = ""
    next_char = ""
    for i, char in enumerate(text):
        if DEBUG_SMART_QUOTES: print(f"🐐 Handling char: {Fore.YELLOW}{char}{Fore.WHITE} ... " , end="")

        if char == '“': in_quotes = True
        if char == '”': in_quotes = False       
        if char == '"':
            prev_char      = text[i-1] if i > 0           else ''
            prev_prev_char = text[i-2] if i > 1           else ''
            next_char      = text[i+1] if i < len(text)-1 else ''
            next_next_char = text[i+2] if i < len(text)-2 else ''
                       
            # Rule 1: 
            if prev_char in [" ",""] and next_char in [" ",""]:
                if DEBUG_SMART_QUOTES: print(f"got here 🌵 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")# ... last_non_space_char.isalpha()={last_non_space_char.isalpha()},next_next_char.isalpha()={next_next_char.isalpha()})")
                
                if last_non_space_char == "”":
                    result.append("“")
                    char_used =   '“'
                    in_quotes=True
                elif last_non_space_char == "“":
                    result.append('”')
                    char_used =   '”'
                    in_quotes=True
                
                elif (is_punctuation(last_non_space_char) and last_non_space_char not in ['“'] and next_next_char.isalpha()) \
                   or             (last_non_space_char.isalpha()                             and next_next_char.isalpha()):
                    if DEBUG_SMART_QUOTES: print(f"got here 🍒 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")                
                    result.append('“')
                    char_used =   '“'
                    in_quotes = True
                else:                   
                    result.append('”')
                    char_used =   '”'
                    in_quotes = True
                
            # Rule 2: 
            elif prev_char == " " and next_char.isalpha() and last_non_space_char != ".":
                if DEBUG_SMART_QUOTES: print(f"got here 🦋 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")                
                result.append('“')
                char_used =   '“'
                in_quotes = True
            
            # Rule 3: Quotes at the end of words, after punctuation, or at the end of sentences
            elif  (is_punctuation_except_quotes(prev_char) or prev_char.isalpha()):
                if DEBUG_SMART_QUOTES: print(f"got here 🍌 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")                
                result.append('”')
                char_used =   '”'
                in_quotes = False
                
            # Rule 4: Quotes at the beginning of words or after punctuation
            elif (prev_char == '' or is_punctuation_except_quotes(prev_char)) and last_non_space_char !=  "“":
                if DEBUG_SMART_QUOTES: print(f"got here ⚠  with char [{Fore.YELLOW}{char}{Fore.WHITE}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")
                result.append('“')
                char_used =   '“'
                in_quotes = True
                
            # Rule 5: parse leftovers ones as if they are pairs?                
            else:
                if DEBUG_SMART_QUOTES: print(f"got here 🎯 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")
                # Handling odd/even quotes when there are spaces around
                if not in_quotes:
                        result.append('“')
                        char_used =   '”'
                        in_quotes = True
                else:
                        result.append('”')
                        char_used =   '”'
                        in_quotes = False

        # Most characters will fall into the “else” part here:
        else:
            if DEBUG_SMART_QUOTES: print(f"got here 👻 with char [{char}] ... prev_char=[{prev_char:1}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}], next_char=[{next_char}]")
            result.append(char)
            char_used =   char
            
        # store last non-space char
        if char !=  " ": 
            if char_used == "“" or char_used == "”": last_non_space_char = char_used
            else                                   : last_non_space_char = char

    return ''.join(result)



def parse_timecode(time_str):                                                                           # Define function to parse timecode strings
    """
    Parse a timecode string 'HH:MM:SS,mmm' and return the time in seconds as a float.
    """
    try:
        hours, minutes, seconds_millis = time_str.split(':')                                            # Split time_str into hours, minutes, and seconds_millis
        seconds, millis = seconds_millis.split(',')                                                     # Split seconds_millis into seconds and milliseconds
        total_seconds = (int(hours) * 3600) + (int(minutes) * 60) + int(seconds) + (int(millis) / 1000) # Calculate total seconds as a float
        return total_seconds                                                                            # Return total seconds
    except ValueError:
        return None                                                                                     # Return None if parsing fails

                                                                                                       
def srt_to_txt(input_file, output_file):                                                                # Define the main function
    if os.path.exists(output_file):                                                                     # Check if output file already exists
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')                                    # Get current timestamp in yyyymmddHHMMSS format
        backup_filename = f"{output_file}.bak.{timestamp}.bak"                                          # Construct backup filename
        os.rename(output_file, backup_filename)                                                         # Rename existing output file to backup filename
                                                                                                       
    # open file *safely*
    with open(input_file, 'rb') as raw_file:                                                            # fix for real-world files that have varied encoding
        result = chardet.detect(raw_file.read(1000))    # Detect encoding based on a sample             # fix for real-world files that have varied encoding
        encoding = result['encoding']                                                                   # fix for real-world files that have varied encoding
    with open(input_file, 'r', encoding=encoding, errors='replace') as f_in:                            # Open the input file with UTF-8 encoding
        lines = f_in.readlines()                                                                        # Read all lines from the input file
                                                                                                      
    subtitles = []                                                                                      # Initialize a list to store subtitles
    subtitle = []                                                                                       # Initialize a list to store lines of the current subtitle
                                                                                                      
    previous_line = None                                                                              
    for line in lines:                                                                                  # Iterate over each line
        line = line.rstrip('\n')                                                                        # Remove trailing newline character
        if line.strip() == '':                                                                          # If the line is empty
            if subtitle:                                                                                # If there is a current subtitle
                subtitles.append(subtitle)                                                              # Add the current subtitle to subtitles list
                subtitle = []                                                                           # Reset subtitle for the next one
        else:                                                                                        
            subtitle.append(line)                                                                       # Add line to the current subtitle
                                                                                                     
    if subtitle:                                                                                        # Add any remaining subtitle
        subtitles.append(subtitle)                                                                   
                                                                                                     
    text_lines = []                                                                                     # Initialize a list to store subtitle text lines
    last_non_blank_end_time = None                                                                      # Initialize end time of last non-blank subtitle
                                                                                                     
    for subtitle in subtitles:                                                                          # Iterate over each subtitle
        if len(subtitle) >= 2:                                                                       
            index_line = subtitle[0]                                                                    # First line is the index number
            timecode_line = subtitle[1]                                                                 # Second line is the timecode line
            content_lines = subtitle[2:] if len(subtitle) > 2 else []                                   # Remaining lines are content lines
        else:                                                                                        
            continue                                                                                    # Skip malformed subtitles

        # Parse timecodes
        match = re.match(r'^(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', timecode_line)
        if match:
            start_time_str, end_time_str = match.groups()                                               # Extract start and end time strings
            start_time = parse_timecode(start_time_str)                                                 # Parse start time
            end_time   = parse_timecode(  end_time_str)                                                 # Parse end time
        else:                                                                                       
            continue                                                                                    # Skip malformed timecodes
                                                                                                    
        # Remove any blank lines in content                                                         
        content = [line for line in content_lines if line.strip() != '']                                # Filter out empty lines in content
                                                                                                    
        if content:                                                                                 
            # Non-blank subtitle                                                                    
            if last_non_blank_end_time is not None:                                                 
                time_diff = start_time - last_non_blank_end_time                                        # Calculate time difference from last non-blank subtitle
                if time_diff > MIN_TIME_BETWEEN_SUBTITLES_TO_GENERATE_BLANK_LINE:                   
                    text_lines.append('')                                                               # Insert extra blank line
                elif time_diff < MAX_TIME_BETWEEN_SUBTITLES_TO_JOIN_TOGETHER:
                    if text_lines and text_lines[-1]:                                                   # If there's existing text, append the current subtitle's content
                        text_lines[-1] += ' ' + ' '.join(content)                                       # Join lines by adding a space
                        content=""
                    else:
                        text_lines.append(' '.join(content))                                            # If no previous line, just add this one as is
            text_lines.extend(content)                                                                  # Append content lines to text_lines
            last_non_blank_end_time = end_time                                                          # Update last non-blank end time
        else:                                                                                           # else it’s an Empty subtitle                                                                           
            text_lines.append('')                                                                       # Append a blank line - Do not update last_non_blank_end_time                                                    
                                                                                                      
    with open(output_file, 'w', encoding='utf-8') as f_out:                                             # Open the output file for writing with UTF-8 encoding
        for line in text_lines:                                                                         # Iterate over the collected text lines
            if DEBUG_ENCOUNTERED_LINES: print(f"Encountered line: [{line}]")                            # DEBUG: print out each encountered line
            line = replace_smart_quotes(line)                                                           # change " to “ and ”
            line = line.replace("'","’")                                                                # change ' to ’
            f_out.write(line.lstrip() + '\n')                                                           # Write each line followed by a newline character
                                                                                                      
if __name__ == "__main__":                                                                              # Entry point of the script
    parser = argparse.ArgumentParser(description='Converts SRT files to TXT files.')                    # Create ArgumentParser object with description
    parser.add_argument('input_files', nargs='+', help='Input SRT files [supports wildcards]')          # Add positional argument for input files
    parser.add_argument('-o', '--output', help='Output file name [only valid with single input file]')  # Add optional argument for output file
    args = parser.parse_args()                                                                          # Parse the command-line arguments

    input_files = []                                                                                    # Initialize list to hold all input files
    if args.input_files == ['all']:                                                                     # to operate on all the SRT files at once
        input_files = glob.glob("*.srt")                                                                # Get all .srt files in the current directory 
        if DEBUG_SHOW_INPUT_FILES: print(f"input files are {input_files}")                              # DEBUG: list out our input files
        if not input_files:                                                                             # If there are no SRT files in the whole folder...
            print("No .srt files found in the current directory.")                                      # Display error message
            import sys                                                                                  # Load sys module to be able to exit program with sys.exit(1)
            sys.exit(1)                                                                                 # Exit with error code 1
    else:                                                                                               # if we gave an argument other than “all”
        for pattern in args.input_files:                                                                # Iterate over input file patterns
            escaped_pattern = glob.escape(        pattern)                                              # wow, glob is stupid... Let us use parens and brackets without complication, we don’t always want regex! geeze.
            matched_files   = glob.  glob(escaped_pattern)                                              # Expand wildcards and get matching files
            if not matched_files:                                                                       # If no files matched the pattern
                print(f"No files matched pattern: {pattern}")                                           # Display a warning message
            input_files.extend(matched_files)                                                           # Add matched files to input_files list
                                                                                                      
    if not input_files:                                                                                 # If no input files were found
        print("No input files to process.")                                                             # Display error message
        import sys                                                                                      # Load sys module to be able to exit program with sys.exit(1)
        sys.exit(1)                                                                                     # Exit with error code 1
                                                                                                      
    if args.output and len(input_files) > 1:                                                            # If output file is specified with multiple input files
        print("Error: Cannot specify an output file when multiple input files are provided.")           # Display error message
        import sys                                                                                      # Load sys module to be able to exit program with sys.exit(1)
        sys.exit(1)                                                                                     # Exit with error code 1
                     
    if DEBUG_SHOW_INPUT_FILES: print(f"input files are {input_files}")                     
                                                                                                      
    for input_file in input_files:                                                                      # Iterate over each input file
        #if args.output:                                                                                # If output filename is specified
        #    output_file = args.output                                                                  # Use the specified output filename
        #else:                                                                                          # If no output filename is provided
        #    output_file = re.sub(r'\.[^.]+$', EXTENSION, input_file)                                   # Replace input file's extension with EXTENSION
        output_file = args.output if args.output else re.sub(r'\.[^.]+$', ".txt", input_file)           # use specified output filename, or replace input filename extension with txt
        #base_name = os.path.splitext(input_file)[0]                                                    # get the base filename without the extension
        #txt_file = f"{base_name}.txt"                                                                  # create the filename of the txt file that would be our output file
        #if os.path.exists(txt_file):                                                                   # If the text file exists already
        if os.path.exists(output_file):                                                                 # If the text file exists already
            print(f"❌ Not converting: {input_file} because TXT file exists already")                   # then don’t convert it
        else:                                                                                           # but if the txt file DOESN’T exist already
            print(f"Converting: {input_file}")                                                          # convert it
            srt_to_txt(input_file, output_file)                                                         # Call the main function with input and output files
            #rint(f"✔  Generated: {output_file} generated")                                            # Display success message
            print(f'✔  Karaoke conversion success: “{output_file}”')                                   # Display success message
            #rint(f'✔  Converted  SRT file to TXT: “{output_file}” successfully!')                     # Display success message                                       
