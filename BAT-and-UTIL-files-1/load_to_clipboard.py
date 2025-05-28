"""

    Loads STDIN/file to clipboard

    To make up for TCC’s inability to handle modern clipboard characters

"""

import sys, os
try: import pyperclip
except ImportError: sys.exit("Error: Install pyperclip with `pip install pyperclip`")

ITALICS_ON  = "\033[3m"
ITALICS_OFF = "\033[23m"

what = "Piped text"

def get_input_meh():
    global what
    if not sys.stdin.isatty():
        retval = sys.stdin.read().rstrip('\n')
        what   = retval
        return   retval
    if len(sys.argv) > 1:
        path = sys.argv[1]
        what = ITALICS_ON + path + ITALICS_OFF
        if not os.path.exists(path):
            #sys.exit(f"Error: File not found: {what}")
            pass
        else:
            with open(path, encoding='utf-8') as f: return f.read()
    sys.exit("Error: No input detected. Provide a filename or pipe text into the program.\n\nUsage:\n  copyclip.py <filename>\n  echo text | copyclip.py")

def get_input():
    global what
    if not sys.stdin.isatty():
        retval = sys.stdin.read().rstrip('\n')
        what   = retval
        return retval
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.exists(path):
            what = ITALICS_ON + path + ITALICS_OFF
            with open(path, encoding='utf-8') as f:
                return f.read()
        else:
            # Treat all args as literal text to copy
            text = " ".join(sys.argv[1:])
            what = text
            return text
    sys.exit("Error: No input detected. Provide a filename, a string of text, or pipe text into the program.\n\nUsage:\n  load_to_clipboard.py <filename>\n  echo text | load_to_clipboard.py\n  load_to_clipboard.py your text here")


#If input needs to be cleaned of unicode, that could be done like this:
    #import unicodedata
    #def clean_text(s): return ''.join(c for c in s if not unicodedata.category(c).startswith('C'))
    #pyperclip.copy(clean_text(get_input()))

pyperclip.copy(get_input())
print(f"✅ Copied to clipboard: {what}")
