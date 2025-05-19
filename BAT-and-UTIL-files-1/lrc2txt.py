import unittest
"""

    LRC to TXT converter

    lrc2txt.py {lrc_input_file)  ———  creates input_file.txt

    Uses thresholds to add blank lines during longer vocal silence periods, as well as to merge lines that are very close together

"""

##### CONFIGURATION: THRESHOLDS:
MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE      = 0.65                             # (various experiments)->0.15->1.50->1.00->0.75->0.65
ADD_A_BLANK_LINE_IF_MORE_THAN_THESE_MANY_SECONDS_PAST_LAST_LINE = 4.75                             # (various experiments)->4.75

#### CONFIGURATION: OUTPUT FILE:
EXTENSION_TO_PRODUCE          = '.txt'

#### CONFIGURATION: DEBUG:
DEBUG_CHAR_HANDLING           = False
DEBUG_ENCOUNTERED_LINES       = False
DEBUG_INSERT_TIME_DIFFERENCES = False
DEBUG_TIME                    = False


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


class TestSmartQuotes(unittest.TestCase):
    def test_smart_quotes(self):
        test_cases = [                              # Test data: (input, expected_output)
            # Single quote
            ('"',
             '“'),
            ('This "is a test sentence with 1 quote, an opening quote, but no closer.',
             'This “is a test sentence with 1 quote, an opening quote, but no closer.'),
            ('This  is a test sentence with 1 quote, a  closing quote, but no" opener.',
             'This  is a test sentence with 1 quote, a  closing quote, but no” opener.'),
            # Two quotes
            ('""',
             '“”'),
            (' " " ',
             ' ” “ '),  #changed our mind and decided it makes more sense for these to be parts of 2 quotes that have no punctuation between them, than a single-space quoted. Might be a bad choice if this was processing code instead of lyrics....
            ('"This is a test sentence with two opening quotes "and no closers.',
             '“This is a test sentence with two opening quotes “and no closers.'),
            ('This is a test sentence with properly "paired" quotes.',
             'This is a test sentence with properly “paired” quotes.'),
            ('This is a test sentence with a closing quote first" and an "opening quote after that *****.',
             'This is a test sentence with a closing quote first” and an “opening quote after that *****.'),
            ('This is a test sentence 👽 with two closing quotes" like Arizona."',
             'This is a test sentence 👽 with two closing quotes” like Arizona.”'),

            # Three quotes (9 combinations)
            ('This is a test sentence with "three "opening "quotes.',
             'This is a test sentence with “three “opening “quotes.'),
            ('This is a test sentence with three" closing" quotes".',
             'This is a test sentence with three” closing” quotes”.'),
            ('"three "opening "quotes',
             '“three “opening “quotes'),
            ('three" closing" quotes"',
             'three” closing” quotes”'),

            ('"This is test sentence 1 with 3 quotes, a single opener next to a "proper pair".',
             '“This is test sentence 1 with 3 quotes, a single opener next to a “proper pair”.'),
            ('This "is test sentence 2 with 3 quotes, a single opener next to a "proper pair"',
             'This “is test sentence 2 with 3 quotes, a single opener next to a “proper pair”'),

            #('"This is a test sentence" with mismatched "quotes.',
            # '“This is a test sentence” with mismatched “quotes.'),
            #('"This is a test sentence" with two closing quotes."',
            # '“This is a test sentence” with two closing quotes.”'),
            #('This" is "a test sentence "with mismatched quotes.',
            # 'This” is “a test sentence “with mismatched quotes.'),
            #('This" is "a test sentence" with mixed quotes.',
            # 'This” is “a test sentence” with mixed quotes.'),
            #('This" is a test sentence" with mismatched "quotes.',
            # 'This” is a test sentence” with mismatched “quotes.'),
            #('This" is a test sentence" with three closing quotes."',
            # 'This” is a test sentence” with three closing quotes.”'),

            # Four quotes (16 combinations)
            #('"This is "a test sentence "with "four opening quotes.',
            # '“This is “a test sentence “with “four opening quotes.'),
            #('"This is "a test sentence "with mixed "quotes."',
            # '“This is “a test sentence “with mixed “quotes.”'),
            #('"This is "a test sentence" with "varied quotes.',
            # '“This is “a test sentence” with “varied quotes.'),
            #('"This is "a test sentence" with properly "paired quotes."',
            # '“This is “a test sentence” with properly “paired quotes.”'),
            #('"This is a test sentence" with "some mismatched "quotes.',
            # '“This is a test sentence” with “some mismatched “quotes.'),
            #('"This is a test sentence" with "properly matched "quotes."',
            # '“This is a test sentence” with “properly matched “quotes.”'),
            #('"This is a test sentence" with mismatched "quotes" like this.',
            # '“This is a test sentence” with mismatched “quotes” like this.'),
            #('"This is a test sentence" with mixed "quotes" and a closer."',
            # '“This is a test sentence” with mixed “quotes” and a closer.”'),
            #('This" is "a test sentence "with "varied quotes.',
            # 'This” is “a test sentence “with “varied quotes.'),
            #('This" is "a test sentence "with proper "pairing."',
            # 'This” is “a test sentence “with proper “pairing.”'),
            #('This" is "a test sentence" with mixed "quotes.',
            # 'This” is “a test sentence” with mixed “quotes.'),
            #('This" is "a test sentence" with paired "quotes."',
            # 'This” is “a test sentence” with paired “quotes.”'),
            #('This" is a test sentence" with mismatched "quotes "like this.',
            # 'This” is a test sentence” with mismatched “quotes “like this.'),
            #('This" is a test sentence" with mixed "quotes "properly."',
            # 'This” is a test sentence” with mixed “quotes “properly.”'),
            #('This" is a test sentence" with mismatched "quotes."',
            # 'This” is a test sentence” with mismatched “quotes.”'),
            ('This is a test sentence "with "four "opening "quotes.',
             'This is a test sentence “with “four “opening “quotes.'),
            ('This is a test sentence with" four" closing" quotes".',
             'This is a test sentence with” four” closing” quotes”.'),
            ('"with "four "opening "quotes.',
             '“with “four “opening “quotes.'),
            ('with" four" closing" quotes"',
             'with” four” closing” quotes”'),
            ('lone quote " to be opening or closing? we say opening',
             'lone quote “ to be opening or closing? we say opening'),

            # No quotes
            ("This is a test sentence without any quotes.",
             "This is a test sentence without any quotes."),

            #More lone quotes
            #('',
            #''),
            ('a lone quote, " what he said ".',
             'a lone quote, “ what he said ”.'),
            ('a lone quote, " what he said "',
             'a lone quote, “ what he said ”'),
            ('"a lone quote, what he said.',
             '“a lone quote, what he said.'),
            ('a " " z',
             'a ” “ z'),        #wouldn’t make sense to have “ ” with nothing in between them, this must be part of a larger set of 2 quotes improperly punctuated between
        ]
        print(f"There are {len(test_cases)} test cases")

        i = 0
        success = 0
        failures = 0
        for input_text, expected_output in test_cases:
            i = i + 1                                                                                                           #print(f"Test #" + {i:2} + f": Original: " + input_text + "      " + "  "  + f"  Expected: " + expected_output)
            with self.subTest(input_text=input_text):
                print(f"\nTest #{i:2}: " + "  in: " + input_text)
                print(   "          "    + "want: " + expected_output)
                print(   "          "    + " got: " + replace_smart_quotes(input_text))
                if replace_smart_quotes(input_text) == expected_output:
                    print( "            "    + "✅")
                    success = success + 1
                else:
                    print( "            "    + "🧨")
                    failures = failures + 1
                self.assertEqual(replace_smart_quotes(input_text), expected_output )

        print(f"\n🎂 {success} out of {i} tests successful!")
        if failures: print(f"🛑 {failures} failures 😢")

def test_suite():
    print(f"This is the test suite. Let us test some quotes.")
    unittest.main(argv=[''], exit=False)
    exit()



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

    if DEBUG_CHAR_HANDLING: print(f"all-but-last char of text is [" + text[:-1] + "]")

    if   text == ""  : return ""
    elif text == '"' : return "“"
    elif text == '""': return "“”"                             # the one exception to our rule that 2 quotes should be considered opening, then closing, and not vice versa, absent other contextual clues
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
        if DEBUG_CHAR_HANDLING: print(f"🐐 Handling char: {Fore.YELLOW}{char}{Fore.WHITE} ... " , end="")

        if char == '“': in_quotes = True
        if char == '”': in_quotes = False
        if char == '"':
            prev_char      = text[i-1] if i > 0           else ''
            prev_prev_char = text[i-2] if i > 1           else ''
            next_char      = text[i+1] if i < len(text)-1 else ''
            next_next_char = text[i+2] if i < len(text)-2 else ''

            # ✅ Rule 0: if directly after opening punctuation, always opening quote                                # [chatgpt:2025/05/19]
            if prev_char in ['[', '(', '{', '<', '¡', '¿', '“']:                                                    # [chatgpt:2025/05/19]
                if DEBUG_CHAR_HANDLING: print(f"got here 🧩 (Rule 0) ... after open punct [{prev_char}]")           # [chatgpt:2025/05/19]
                result.append('“')                                                                                  # [chatgpt:2025/05/19]
                char_used = '“'                                                                                     # [chatgpt:2025/05/19]
                in_quotes = True                                                                                    # [chatgpt:2025/05/19]

            # Rule 1:
            if prev_char in [" ",""] and next_char in [" ",""]:
                if DEBUG_CHAR_HANDLING: print(f"got here 🌵 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")# ... last_non_space_char.isalpha()={last_non_space_char.isalpha()},next_next_char.isalpha()={next_next_char.isalpha()})")

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
                    if DEBUG_CHAR_HANDLING: print(f"got here 🍒 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")
                    result.append('“')
                    char_used =   '“'
                    in_quotes = True
                else:
                    result.append('”')
                    char_used =   '”'
                    in_quotes = True

            # Rule 2:
            elif prev_char == " " and next_char.isalpha() and last_non_space_char != ".":
                if DEBUG_CHAR_HANDLING: print(f"got here 🦋 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")
                result.append('“')
                char_used =   '“'
                in_quotes = True

            # Rule 3: Quotes at the end of words, after punctuation, or at the end of sentences
            elif  (is_punctuation_except_quotes(prev_char) or prev_char.isalpha()):
                if DEBUG_CHAR_HANDLING: print(f"got here 🍌 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")
                result.append('”')
                char_used =   '”'
                in_quotes = False

            # Rule 4: Quotes at the beginning of words or after punctuation
            elif (prev_char == '' or is_punctuation_except_quotes(prev_char)) and last_non_space_char !=  "“":
                if DEBUG_CHAR_HANDLING: print(f"got here ⚠  with char [{Fore.YELLOW}{char}{Fore.WHITE}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")
                result.append('“')
                char_used =   '“'
                in_quotes = True

            # Rule 5: parse leftovers ones as if they are pairs?
            else:
                if DEBUG_CHAR_HANDLING: print(f"got here 🎯 with char [{char}] ... prev_char=[{prev_char}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}]")
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
            if DEBUG_CHAR_HANDLING: print(f"got here 👻 with char [{char}] ... prev_char=[{prev_char:1}], last_non_space_char=[{Fore.CYAN}{last_non_space_char}{Fore.WHITE}], next_char=[{next_char}]")
            result.append(char)
            char_used =   char

        # store last non-space char
        if char !=  " ":
            if char_used == "“" or char_used == "”": last_non_space_char = char_used
            else                                   : last_non_space_char = char

    return ''.join(result)








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
        timestamps =                             re.findall(r'\[(\d+:\d+\.\d+)\]', line)        # Find all timestamps
        if not timestamps:                      #re.findall(r'\[(\d+:\d+\.\d+)\]', line)        # This was not sufficient in the wild, because we ran into malformed LRCs that only went to the second-precision instead of to the centisecond-precision, i.e. “[00:14]” instead of “[00:14.01]”
            timestamps =                         re.findall(r'\[(\d+:\d+)\]'     , line)        # Find all malformed “seconds-only–precision” timestamps
            timestamps = [ts if re.search(r'\.\d{2}$', ts) else ts + ".00" for ts in timestamps]

        # Extract the lyric (everything after the last timestamp)
        lyric = re.split(r'\[\d+:\d+\.?\d*\]', line)[-1].strip()
        if DEBUG_ENCOUNTERED_LINES: print(f"--?--> lyric=“{lyric}” ... timestamps=“{timestamps}”")

        if not lyric:  # Only process if there are lyrics
            if DEBUG_ENCOUNTERED_LINES: print(f"⚠ ⚠ ⚠  No lyrics for line [{line}]")
        else:
            for timestamp in timestamps:
                # Convert timestamp to seconds for sorting
                minutes, seconds = map(float, timestamp.split(":"))
                total_seconds = minutes * 60 + seconds
                if DEBUG_ENCOUNTERED_LINES: print(f"\t\ttimestamp=“{timestamp}” minutes=“{minutes}” seconds=“{seconds}” total_s={total_seconds}")

                # Add the converted line to the output:
                expanded_lines.append((total_seconds, lyric))

    # Sort by timestamps
    retval = sorted(expanded_lines, key=lambda x: x[0])
    if DEBUG_ENCOUNTERED_LINES: print(f"---> sorted lines=🍠🍠🍠🍠“{retval}”🍠🍠🍠🍠")
    return retval





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

    if partial_match:
        minutes, seconds, centiseconds = partial_match.groups()
        _, _, _, text                  =         match.groups()
        total_seconds = int(minutes) * 60 + int(seconds) + int(centiseconds) / 100
        return total_seconds, text.strip()
    return None, line




def lrc_to_txt(input_file, output_file):
    """
    Performs the actual LRC->TXT conversion
    """

    # backup original file
    if os.path.exists(output_file):                                                                     # check if output file exists
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')                                    # generate string for this moment in time
        backup_filename = f"{output_file}.bak.{timestamp}.bak"                                          # generate unique backup filename
        os.rename(output_file, backup_filename)                                                         # rename the old file to our newly-generated backup filename

    # open file *safely*
    with open(input_file, 'rb') as raw_file:                                                            #fix for real-world files that have varied encoding
        result = chardet.detect(raw_file.read(1000))    # Detect encoding based on a sample             #fix for real-world files that have varied encoding
        encoding = result['encoding']                                                                   #fix for real-world files that have varied encoding
    with open(input_file, encoding=encoding, errors='replace') as file_in:                              #fix for real-world files that have varied encoding
        lines = file_in.readlines()

    # Preprocess lines to convert/expand lines-with-multiple-timestamps into single-timpestamp lines, and to then sort them:
    original_lines = lines
    lines          = expand_and_sort_timestamps(lines)

    if DEBUG_ENCOUNTERED_LINES: print(f"\n\n\n\noriginal lines  was: :\n“““““{original_lines}”””””\n\n\nexpanded lines is now:\n“““““{         lines}”””””\n\n\n\n")

    merged_output_lines        = []
    cleaned_output_lines       = []
    last_line                  = "N/A"
    last_text                  = ""
    last_time                  = 0
    time_difference            = 0
    inserted                   = 0
    current_output_line        = ""
    for line in lines:
        time, text = line                                                # separate out timestamps from text:                       #if DEBUG_TIME: print(f"\n* looping: time={time},text==>'{text.strip()}'",end="\n")
        if time is None: continue                                        # skip lines without timestampes
        text = text if text else "\n"                                    # massage text
        time_difference = time - last_time if last_time else -666        # get time difference

        # **DO** merge lines if they *ARE* close enough ***************************************************************************************************************************
        if 0 < time_difference < MERGE_LINES_LESS_THAN_THESE_MANY_SECONDS_APART_INTO_1_LINE and inserted > 0:
            if DEBUG_INSERT_TIME_DIFFERENCES: text = f"🍌 {time_difference:5.1f} 🍌 " + text.strip()
            text = text.strip()
            if current_output_line and current_output_line[-1] not in string.punctuation: joined_line_divider = ", "
            else:                                                                         joined_line_divider = " "
            current_output_line += joined_line_divider + text.lstrip()
            inserted = inserted + 1

        # DON’T merge lines if they aren’t close enough ***************************************************************************************************************************
        else:
            inserted = 0

            if current_output_line:                                                                     # Finalizing merged content
                merged_output_lines.append(current_output_line)
                current_output_line=""

            if time_difference > ADD_A_BLANK_LINE_IF_MORE_THAN_THESE_MANY_SECONDS_PAST_LAST_LINE:       # Append a blank line for large gaps
                merged_output_lines.append("")

            if DEBUG_INSERT_TIME_DIFFERENCES: text = f"⏱ {time_difference:5.1f} ⏱ " + text.strip()
            text = text.strip()                                                                         # Append the current text
            current_output_line = text

        last_time = time
    #end for line in lines

    if current_output_line: merged_output_lines.append(current_output_line)

    # clean successive blank lines
    last_line=""
    for line in merged_output_lines:
        line = line.strip()
        if line != "" or last_line != "": cleaned_output_lines.append(line)
        last_line=line

    # output our finialized file with final massage of values
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for line in cleaned_output_lines:
            line = replace_smart_quotes(line)      # change " to “ and ”
            line = line.replace("'","’")           # change ' to ’
            f_out.write(line.lstrip() + "\n")      # output the cleaned line

def get_raw_command_tail():
    import ctypes
    GetCommandLineW              = ctypes.windll.kernel32.GetCommandLineW
    GetCommandLineW.restype      = ctypes.c_wchar_p
    raw_cmd                      = GetCommandLineW()
    script_name                  = sys.argv[0]                                                  # Get the script name from sys.argv[0]
    script_name_in_cmd           = script_name                                                  # Find the position where the arguments start
    if ' ' in script_name:         script_name_in_cmd = f'"{script_name}"'                      # If the script name contains spaces, it will be quoted in the command line
    args_start                   = raw_cmd.find(script_name_in_cmd) + len(script_name_in_cmd)
    args_that_may_contain_quotes = raw_cmd[args_start:]                                         # construct our verbatim original command line
    return args_that_may_contain_quotes


def test_string():
    s = get_raw_command_tail()                                      # get raw command tail, which requirse ctypes
    if s.startswith(' -s '): s = s[4:]                              # remove “-s ” from the beginning, which was used to get here
    q = replace_smart_quotes(s)
    print(f"⭐ Original: {Fore.RED}[{Fore.WHITE}" + s + f"{Fore.RED}]{Fore.WHITE}")
    print(f"⭐ Replaced: {Fore.RED}[{Fore.WHITE}" + q + f"{Fore.RED}]{Fore.WHITE}")
    exit()

#—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

if __name__ == "__main__":                                                                                             # Entry point of the script
    parser = argparse.ArgumentParser(description='Converts LRC files to TXT files.')                                   # Create ArgumentParser object with description
    #arser.add_argument('input_files', nargs='+', help='Input LRC files [supports wildcards]')                         # Add positional argument for input files
    parser.add_argument('input_files', nargs='*', help='Input LRC files [supports wildcards]')                         # Positional argument for input files (optional for initial parsing because not applicable when using -t for tests)
    parser.add_argument('-o', '--output', help='Output file name [only valid with single input file]')                 # Add   optional argument for output file
    parser.add_argument('-t', action='store_true', help='Run tests')                                                   # Add   optional argument for testing
    parser.add_argument('-s', nargs=argparse.REMAINDER, help='Test on a string [the remainder of the command line]')   # Optional argument for capturing a single string with quotes preserved
    args = parser.parse_args()                                                                                         # Parse the command-line arguments with the argparse library
    if not args.input_files and not args.s and not args.t: parser.error("No input files provided")                     # Enforce semi-mandatory args that are mandatory if we aren’t using one of the testing (-s, -t) args
    if args.t: test_suite()                                                                                            # “-t” runs test suite
    if args.s: test_string()                                                                                           # “-s” to test a string that is whatever is after the “-s”

    input_files = []                                                                                                   # Initialize list to hold all input files
    for pattern in args.input_files:                                                                                   # Iterate over input file patterns
        escaped_pattern = glob.escape(        pattern)                                                                 # wow, glob is stupid... Let us use parens and brackets without complication, we don’t always want regex! geeze.
        matched_files   = glob.  glob(escaped_pattern)                                                                 # Expand wildcards and get matching files
        if not matched_files:                                                                                          # If no files matched the pattern
            print(f"?! No files matched pattern: {pattern}")                                                              # Display a warning message
        input_files.extend(matched_files)                                                                              # Add matched files to input_files list

    if not input_files:                                                                                                # If no input files were found
        print("No input files to process.")                                                                            # Display error message
        sys.exit(1)                                                                                                    # Exit with error code 1

    if args.output and len(input_files) > 1:                                                                           # If output file is specified with multiple input files
        print("Error: Cannot specify an output file when multiple input files are provided.")                          # Display error message
        sys.exit(1)                                                                                                    # Exit with error code 1

    #—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

    for input_file in input_files:                                                                                     # Iterate over each input file
        if args.output: output_file = args.output                                                                      # If output filename is specified, use the specified output filename
        else:           output_file = re.sub(r'\.[^.]+$', EXTENSION_TO_PRODUCE, input_file)                            # If no output filename is provided, replace input file's extension with EXTENSION
        lrc_to_txt(input_file, output_file)                                                                            # Call the main function with input and output files
        print(f'✔  Karaoke conversion success: “{output_file}”')                                                      # Display success message

    #—————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

