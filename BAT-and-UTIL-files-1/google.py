import sys
import urllib.parse
import webbrowser
import ctypes

def main():
    # Use ctypes to get the raw command line with quotes preserved
    GetCommandLineW = ctypes.windll.kernel32.GetCommandLineW
    GetCommandLineW.restype = ctypes.c_wchar_p
    raw_cmd = GetCommandLineW()

    # Get the script name from sys.argv[0]
    script_name = sys.argv[0]

    # Find the position where the arguments start
    script_name_in_cmd = script_name
    if ' ' in script_name:
        # If the script name contains spaces, it will be quoted in the command line
        script_name_in_cmd = f'"{script_name}"'

    args_start       = raw_cmd.find(script_name_in_cmd) + len(script_name_in_cmd)
    args_with_quotes = raw_cmd[args_start:].strip()

    if not args_with_quotes:
        print("Please provide a search query.")
        sys.exit(1)

    # URL-encode the query, preserving quotes
    encoded_query = urllib.parse.quote(args_with_quotes)

    # Construct the full Google search URL
    url = 'http://www.google.com/search?q=' + encoded_query

    # Open the URL in the default web browser
    webbrowser.open(url)

if __name__ == '__main__':
    main()
