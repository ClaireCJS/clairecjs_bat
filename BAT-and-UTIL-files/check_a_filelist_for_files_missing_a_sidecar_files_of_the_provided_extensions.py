import io
import sys
print(f"Before reconfigure: sys.stdout.encoding = {sys.stdout.encoding}")
sys.stdout.reconfigure(encoding='utf-8')
print(f"After reconfigure: sys.stdout.encoding = {sys.stdout.encoding}")

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
print(f"After reconfigure: sys.stdout.encoding = {sys.stdout.encoding}")


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
#             this_script.py playlist.m3u *.lrc;*.srt {extra arguments}
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

# These leftover files eventually get found and deleted in free-harddrive-space.bat which is called from maintenance.bat which is called upon reboot:
SCRIPT_NAME_FOR_LYRIC_RETRIEVAL  = "get-the-missing-lyrics-here-temp.bat"
SCRIPT_NAME_FOR_KARAOKE_CREATION = "create-the-missing-karaokes-here-temp.bat"


def main(input_filename, extensions, options, extra_args):

    #DEBUG: print(f"main got extra args of '{extra_args}'")

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
    #ith open(input_filename, 'r')                   as file:
    with open(input_filename, 'r', encoding='utf-8') as file:
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
            if extra_args: print(f"Using extra arguments of: {extra_args}")

            # run any special postprocessing we've created, usually to create scripts to deal with files that are missing sidecar files
            # 🐐 don't we need to open it in utf-8?
            #ith open(output_filename, 'w') as output_file:
            with open(output_filename, 'w', encoding='utf-8') as output_file:
                output_file.write(f"@on break cancel\n")
                for missing_file in sorted(files_without_sidecars):
                    if os.path.exists(missing_file):
                        if options.lower() == "getlyricsfilewrite": output_file.write(f"@call get-lyrics \"{missing_file}\" {extra_args}\n")
                        if options.lower() == "createsrtfilewrite": output_file.write(f"@call create-srt \"{missing_file}\" {extra_args}\n")
                        else                                      : output_file.write(f"{missing_file}\n")
                if options.lower()         == "getlyricsfilewrite": output_file.write("@echo *** ALL DONE WITH LYRIC RETRIEVAL!!!! ***\n") #@echo yra | *del %0 >&>nul\n") Self-deleting like this doesn't work, so these leftover files eventually get found and deleted in free-harddrive-space.bat which is called from maintenance.bat which is called upon reboot
                if options.lower()         == "createsrtfilewrite": output_file.write("@echo *** ALL DONE WITH KARAOKE CREATION!!! ***\n") #@echo yra | *del %0 >&>nul\n") Self-deleting like this doesn't work, so tThese leftover files eventually get found and deleted in free-harddrive-space.bat which is called from maintenance.bat which is called upon reboot

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python check_a_filelist_for_files_missing_a_sidecar_files_of_the_provided_extension.py <input_filename> <extensions> <postprocessor> {parameters to pass to created script}\n")
        print("Postprocessors can be GetLyricsFileWrite, CreateSrtFileWrite, and they cretae scripts based on missing sidecar files\n")
        sys.exit(1)


    options=""
    extra_args_str=""
    if len(sys.argv)>0:
        input_filename = sys.argv[1]
        extensions = sys.argv[2]
    if len(sys.argv) >= 4:
        options = sys.argv[3]
    if len(sys.argv) >= 5:
        extra_args = sys.argv[4:]
        extra_args_str=  ' '.join(extra_args)

    #print(f"- DEBUG: Extra args are: '{extra_args_str}'")

    main(input_filename, extensions, options, extra_args_str)
