"""


TASK: error out on any keywords that aren't in our last

TASK: synonyms must be converted to what they are a synonym of before processing


This script scans a directory for script files. If a script file contains a :PUBLISH: line,
it is considered a candidate for publishing. The script then extracts additional metadata from
the file based on certain keywords. The data is written to an output file. The script can work on the
current directory with a single argument of "." or "/c". For recursive scanning, use "/s".
"""

import os
import argparse
import logging
import sys
try:
    import clairecjs_utils as claire
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path: sys.path.insert(0, script_dir)
    try:
        import clairecjs_utils as claire
    except ImportError:
        raise ImportError("Cannot find 'clairecjs_utils' module in site-packages or the local directory.")
from colorama import Fore, Back, Style, init
init()

## Set up the logger: pre-unicode
#LOGGER = logging.getLogger(__name__)
#LOGGER.setLevel(logging.DEBUG)

## Set up the logger: supporting different encodings
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
handler.encoding = 'utf-8'
logging.basicConfig(level=logging.WARNING, handlers=[handler])
LOGGER = logging.getLogger(__name__)

# Set up file handler for logger
FILE_HANDLER = logging.FileHandler(os.path.splitext(sys.argv[0])[0] + '.log', mode='w')  # dynamic log filename
FILE_HANDLER.setLevel(logging.DEBUG)
LOGGER.addHandler(FILE_HANDLER)

# Keywords we are looking for - #TODO perhaps come up with default values of these
KEYWORDS = ["DESCRIPTION"  ,    #description of script
            "USAGE"        ,    #invocation - may be more than one given
            "EXAMPLE"      ,    #example calls - may be more than one given
            "EXAMPLES"     ,        #snyonym

            "REQUIRES"     ,    #comma-separated verbal description of what is required, such as "windows 10".
                                    #may also include filenames (followed by comments in parens) but those are really DEPENDENCIES
            "REQUIRE"      ,        #synonym
            "DEPENDENCIES" ,    #comma-separated list of files (followed by comments in parens) required to run this

            "USED-BY"      ,    #comma-separated list of files (followed by comments in parens) which use this
            "USED BY"      ,        #synonym
            "RELATED"      ,    #comma-separated list of files (followed by comments in parens) related to this

            "TESTING"      ,    #descriptions on how to test the script

            "COMPLICATIONS",    #more like a dev log, just comments about complications possibly encountered
            "ASSUMPTIONS"  ,    #assumptions
            "ASSUME"       ,        #synonym

            "REPLACES"     ,    #if this replaces a different or built-in utility

            "VERSION"      ,    #version
            "AUTHOR"       ,    #pointless because it's always going to be me
            "CREATED"      ,    #not usually included or known
            "UPDATED"      ,    #not usually included or known
            "RUNTIME"      ,    #estimate of how long it will take to run. Could be in description but this categorizes it better.

            "EFFECTS"      ,    #main effects caused by this script           \
            "EFFECT"       ,        #synonym                                   \____ effectively the same thing, but not quite
            "SIDE-EFFECTS" ,    #side-effects caused by this script            /
            "SIDE EFFECTS" ,        #synonym                                  /
            ]
DELIMITERS = [":", "#", ";"]    #delimiters around our keyword - we need to accomodate various languages' formats for comments

examples = """
:DESCRIPTION:    This script creates pies out of thin air
:USAGE:          make-me-a-pie {number of pies you want}
:REQUIRES:       latest TCC (preferably v10)
:DEPENDENCIES:   pie.bat (where the actual pie gets made), cook-food.bat (called by pie.bat)
:USED-BY:        restaurant.bat (when pies are ordered by a customer)
:RELATED:        hotdog.bat (not directly related but uses similar structure)
:REPLACES:       make-me-a-pie-right-now.bat (an older version that we renamed)
:VERSION:        1.2.3.4
:AUTHOR:         Claire with Carolyn's help
:CREATED:        1995
:UPDATED:        2023
:RUNTIME:        about 15 minutes, 10 minutes if %OVEN_PREHEATED% == 1
:EFFECTS:        makes a pie, but also uses 0.3kWh of electricity
:SIDE-EFFECTS:   increases temperature of kitchen by 1 degree
"""




#def read_file_content(filename):
#    """
#    Try to read the file with two different encodings.
#    :param filename: The path of the file to process.
#    :return: File content lines.
#    """
#    for encoding in [None, "utf-8", "ISO-8859-1"]:
#        try:
#            with open(filename, "r", encoding=encoding) as file:
#                return file.readlines()
#        except UnicodeDecodeError:
#            continue
#    return []



import chardet
import codecs
def handle_encoding_error(exception):
    #eturn (''.join(f'{ GOAT:{hex(ord(ch))}'   for ch in exception.object[exception.start:exception.end]), exception.end)
    #eturn (''.join(f'{{GOAT:{hex(ord(ch))}}}' for ch in exception.object[exception.start:exception.end]), exception.end)
    return (''.join(f'{{GOAT:{hex(    ch)}}}'  for ch in exception.object[exception.start:exception.end]), exception.end)

codecs.register_error('error_goat_er', handle_encoding_error)
def read_file_content(filename):
    """
    Try to read the file with the correct encoding.
    :param filename: The path of the file to process.
    :return: File content lines.
    """
    # Detect the encoding of the file
    with open(filename, 'rb') as file:
        rawdata = file.read()
        result = chardet.detect(rawdata)
        charenc = result['encoding']

    # Now open the file with the detected encoding
    with open(filename, "r", encoding=charenc, errors='error_goat_er') as file:
        return file.readlines()





#timer tests: tick=False: 11.686ish
#timer tests: tick=True:  9999999999   9 minutes before aborting - even after optimizations
#timer tests: tick=True:   44.72       but i was checking time throttling in an inner loop thanks to chatgpt dumbness

#timer tests: tick=True:  104.62       more optimizations, with 0.1 minimum time
#timer tests: tick=True:  11.54        0.01 second delay and more optimizations
#timer tests: tick=True:  .
#timer tests: tick=True:  .
#timer tests: tick=True:  .
#timer tests: tick=True:  .
#timer tests: tick=True:  .
#timer tests: tick=True:  .
#timer tests: tick=True:  .
#timer tests: tick=True:  .




def process_file(filename,tick=False):

    """
    Process a single file, looking for keywords.
    :param filename: The path of the file to process.
    :return: A dictionary with the found keywords and their corresponding values.
    """
    metadata = {}
    lines = read_file_content(filename)
    for line in lines:
        LOGGER.debug(f"Processing line: {filename}:{line}")  # Logging the line
        if tick: claire.tick()
        for delimiter in DELIMITERS:
            publish_search_for = delimiter + "PUBLISH" + delimiter
            LOGGER.debug(f"Looking for {publish_search_for} in file: {filename}")  # Logging the filename
            #if delimiter + "PUBLISH" + delimiter in line:
            if line.lstrip().startswith(publish_search_for):
                LOGGER.debug(f"{Fore.LIGHTGREEN_EX}  !! Found: {filename}:{line}{Fore.WHITE}")  # Logging the line
                metadata["PUBLISH"] = True  # Set a "PUBLISH" key in the metadata dictionary
                for keyword in KEYWORDS:
                    for delimiter in DELIMITERS:
                        #if delimiter + keyword + delimiter in line:
                        if line.lstrip().startswith(delimiter + keyword + delimiter):
                            metadata[keyword] = line.split(delimiter + keyword + delimiter)[-1].strip()
                break
    return metadata if "PUBLISH" in metadata else None  # Check if "PUBLISH" key exists in metadata dictionary


def scan_directory(directory, recursive, tick=False):
    """
    Scan a directory for script files and process each one.
    :param directory: The path of the directory to scan.
    :param recursive: Boolean value indicating if the scan should be recursive.
    :return: A list of tuples, each containing a filename and its corresponding metadata.
    """
    extensions_to_check=['.bat', '.btm' , '.cmd', '.ps1' , '.sh' , '.js', '.py' , '.pl' , '.pm' , '.conf', '.ahk' ,
                         '.doc', '.htm', '.html', '.ini', '.java', '.php', '.rc', '.sql', '.vbs' , '.yaml']         #decided against TXT files due to potentially large files and slow processing and referable as dependencies anyway
    result = []
    for root, _, files in os.walk(directory):
        for file in files:
            _, ext = os.path.splitext(file)

            #print(f"Checking file: {file}")
            LOGGER.debug(f"Checking file: {file}")
            #for ext in extensions_to_check:
            if   ext in extensions_to_check:
                LOGGER.debug(f"Checking file {file} against extension {ext}")
                #f file.endswith(ext):
                #f any(file.endswith(ext) for ext in extensions_to_check):
                if not file.endswith(' __') and not file.startswith('__ ') and not file.startswith('delme'):
                    filename = os.path.join(root, file)
                    metadata = process_file(filename,tick=tick)
                    if metadata:  # If we found a :PUBLISH: line
                        result.append((filename, metadata))
        if not recursive:
            break

    return result


def maine(directory, recursive, tick):
    """
    Main function, processes files and writes output.
    :param directory: The path of the directory to process.
    :param recursive: Boolean value indicating if the scan should be recursive.
    """
    LOGGER.info(f"Scanning directory {directory}")
    scan_directory_results = scan_directory(directory, recursive, tick=tick)
    for filename, metadata in scan_directory_results:
        filename = os.path.basename(filename)
        print(f"{filename}", end=" ")

    LOGGER.info(f"Found {len(scan_directory_results)} script files to publish")
    with open(os.path.splitext(sys.argv[0])[0] + '.dat', 'w') as output_file:
        LOGGER.info(f"data file opened")
        for filename, metadata in scan_directory_results:
            filename = os.path.basename(filename)
            metadata_string = ",".join(f"{key}={value}" for key, value in metadata.items())
            output_file.write(f"{filename}:{metadata_string}\n")
            LOGGER.info(f"Wrote metadata for {filename} to output file")



if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description="Processes scripts to see which ones are published, and to collect their publishing info")
    #print(args.filename, args.count, args.verbose)
    PARSER.add_argument("directory", nargs='?', default=".", help="The directory to scan. Use '.' for the current directory and '/c' for recursive scanning.")
    PARSER.add_argument("-s", "--recursive", action="store_true", help="Scan directories recursively.")
    PARSER.add_argument("-t", "--tick", action="store_true", help="Use tick function to cycle color while waiting")
    ARGS = PARSER.parse_args()

    # If no arguments are passed, print the help message and exit.
    if len(sys.argv)==1:
        PARSER.print_help(sys.stderr)
        sys.exit(1)

    maine(ARGS.directory, ARGS.recursive, ARGS.tick)

