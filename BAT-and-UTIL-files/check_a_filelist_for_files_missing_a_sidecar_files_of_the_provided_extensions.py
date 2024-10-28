#
########################### FILELIST SIDECAR AUDITOR ###########################
########################### FILELIST SIDECAR AUDITOR ###########################
########################### FILELIST SIDECAR AUDITOR ###########################
########################### FILELIST SIDECAR AUDITOR ###########################
########################### FILELIST SIDECAR AUDITOR ###########################
########################### FILELIST SIDECAR AUDITOR ###########################
########################### FILELIST SIDECAR AUDITOR ###########################
#
# Example use case:
#
#       1) You have a playlist, PLAYLIST.m3u
#
#       2) Some songs in the playlist have a karaoke file, which has the same filename, but with an extension of either LRC or SRT
#
#       3) We want to know which songs in the playlist **DO NOT** have these sidecar files.
#
#       The invocation would be:
#
#             this_script.py playlist.m3u *.lrc;*.srt
#
#                      (For reference, the reason the extensions are "*.lrc;*.srt" format instead of "lrc,srt" format)
#                      (is because of compatibility with some environment variables I create in my personal life.    )
#
#      And as a side effect, it would create a file called: PLAYLIST-without lrc srt.m3u that contains these files
#
#
#

import os
import sys
import glob
from termcolor import colored

def main(input_filename, extensions):
    # Check if the input file exists
    if not os.path.exists(input_filename):
        print(f"Error: The file '{input_filename}' does not exist.")
        sys.exit(1)

    # Parse the extensions
    extensions_list = extensions.split(';')
    extensions_list = [ext.strip() for ext in extensions_list if ext.strip().startswith('*.')]
    if not extensions_list:
        print("Error: No valid extensions provided.")
        sys.exit(1)

    # Create a set to keep track of files without sidecars (unique entries)
    files_without_sidecars = set()

    # Open and read the input filename (list of files)
    with open(input_filename, 'r') as file:
        files = [line.strip() for line in file.readlines() if line.strip()]

    # Check for sidecar files
    for file in files:
        base_filename, _ = os.path.splitext(file)
        has_sidecar = any(glob.glob(f"{base_filename}{ext[1:]}") for ext in extensions_list)

        if not has_sidecar:
            files_without_sidecars.add(file)
            print(file)

    # Write the output file
    if files_without_sidecars:
        input_file_ext = os.path.splitext(input_filename)[1]
        output_filename = f"{os.path.splitext(input_filename)[0]}-without {' '.join(ext[2:] for ext in extensions_list)}{input_file_ext}"
        print(colored(f"Writing output file: {output_filename}", 'green', attrs=['bold']))
        with open(output_filename, 'w') as output_file:
            for missing_file in sorted(files_without_sidecars):
                output_file.write(f"{missing_file}\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_filename> <extensions>")
        sys.exit(1)

    input_filename = sys.argv[1]
    extensions = sys.argv[2]
    main(input_filename, extensions)
