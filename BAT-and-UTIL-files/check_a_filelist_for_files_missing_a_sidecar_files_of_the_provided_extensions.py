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
#      And as a side effect, it would create a file called: PLAYLIST-without lrc srt.m3u that contains these files ——
#                       —— unless you add a NoFileWrite option at the end then it doesn't
#                       —— unless you add a GetLyricsFileWrite then it writes a bat file to retrieve lyrics
#                       —— unless you add a CreateSRTFileWrite thne it writes a bat file to create karaokes
#
#

import os
import sys
import glob
from termcolor import colored


SCRIPT_NAME_FOR_LYRIC_RETRIEVAL  = "get-the-missing-lyrics-here.bat"
SCRIPT_NAME_FOR_KARAOKE_CREATION = "create-the-missing-karaokes-here.bat"


def main(input_filename, extensions, options):
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
        if options.lower() == "getlyricsfilewrite": output_filename = SCRIPT_NAME_FOR_LYRIC_RETRIEVAL
        if options.lower() == "createsrtfilewrite": output_filename = SCRIPT_NAME_FOR_KARAOKE_CREATION
        if options.lower() !=        "NoFileWrite":
            print(colored(f"Writing output file: {output_filename}", 'green', attrs=['bold']))
            with open(output_filename, 'w') as output_file:
                for missing_file in sorted(files_without_sidecars):
                    if options.lower() == "getlyricsfilewrite": output_file.write(f"@call get-lyrics \"{missing_file}\"\n")
                    if options.lower() == "createsrtfilewrite": output_file.write(f"@call create-srt \"{missing_file}\"\n")
                    else                                      : output_file.write(f"{missing_file}\n")
                if options.lower() == "getlyricsfilewrite"    : output_file.write("@echo *** ALL DONE WITH LYRIC RETRIEVAL!!!! ***\n@echo yra | *del %0 >&>nul\n")
                if options.lower() == "createsrtfilewrite"    : output_file.write("@echo *** ALL DONE WITH KARAOKE CREATION!!! ***\n@echo yra | *del %0 >&>nul\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_filename> <extensions>")
        sys.exit(1)

    options=""
    if len(sys.argv)>0:
        input_filename = sys.argv[1]
        extensions = sys.argv[2]
    if len(sys.argv) >= 4:
        options = sys.argv[3]
    main(input_filename, extensions, options)