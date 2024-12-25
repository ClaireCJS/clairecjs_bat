DEBUG_DETECT_ENCODING = False
DEBUG_SIDECAR_SEARCH  = False
import io
import sys
import chardet
import os
import glob
from termcolor import colored
import random
from colorama import init
init(autoreset=False)



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


# compensate for utf-8 files                                                            #print(f"Before reconfigure: sys.stdout.encoding = {sys.stdout.encoding}")
sys.stdout.reconfigure(encoding='utf-8')                                                #print(f"After reconfigure: sys.stdout.encoding = {sys.stdout.encoding}")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')                      #print(f"After reconfigure: sys.stdout.encoding = {sys.stdout.encoding}")

# These leftover files eventually get found and deleted in free-harddrive-space.bat which is called from maintenance.bat which is called upon reboot:
SCRIPT_NAME_FOR_LYRIC_RETRIEVAL  = "get-the-missing-lyrics-here-temp.bat"           #don't change without changing in accompanying BAT files
SCRIPT_NAME_FOR_KARAOKE_CREATION = "create-the-missing-karaokes-here-temp.bat"      #don't change without changing in accompanying BAT files

without_sidecar_count = 0
total_file_count      = 0

def detect_encoding(filename):
    with open(filename, 'rb') as file:
        raw_data = file.read(1024)  # Read a portion of the file for analysis
    return chardet.detect(raw_data)['encoding']


def main_guts(input_filename, extensions, options, extra_args):
    #DEBUG: print(f"main got extra args of '{extra_args}'")

    global without_sidecar_count
    global total_file_count


    # Detect encoding of the input file
    encoding = detect_encoding(input_filename)
    if not encoding:
        print(f"Error: Unable to detect encoding for file '{input_filename}'.")
        sys.exit(1)
    else:
        if DEBUG_DETECT_ENCODING: print(f"Detected encoding for {input_filename} of {encoding}")

    # Check if the input file exists
    if not os.path.exists(input_filename):
        print(f"Error: The file '{input_filename}' does not exist." )
        sys.exit(1)

    # Parse the extensions
    extensions_list1 = extensions.split(';')
    extensions_list2 = [ext.strip()[2:] for ext in extensions_list1 if ext.startswith('*.')]        #DEBUG: print(f"extensions_list1='{extensions_list1}'\nextensions_list2='{extensions_list2}'")
    extensions_list=extensions_list2;
    if not extensions_list:
        print("Error: No valid extensions provided.")
        sys.exit(1)

    # Create a set to keep track of files without sidecars (unique entries)
    files_without_sidecars = set()

    # Open and read the input filename (list of files)
    #ith open(input_filename, 'r')                   as file:
    #with open(input_filename, 'r', encoding='utf-8') as file:
    #    files = [line.strip() for line in file.readlines() if line.strip()]
    try:
        with open(input_filename, 'r', encoding=encoding) as file:
            files = [line.strip() for line in file.readlines() if line.strip()]
    except UnicodeDecodeError:
        try:
            if DEBUG_DETECT_ENCODING: print(f"Warning: failed to read file '{input_filename}' with detected encoding of '{encoding}'... trying UTF-8")
            with open(input_filename, 'r', encoding='UTF-8') as file:
                files = [line.strip() for line in file.readlines() if line.strip()]
        except UnicodeDecodeError:
            print(f"Error: Unable to read file '{input_filename}' with detected encoding '{encoding}'.")
            sys.exit(1)
    


    # Check each file for sidecar files
    for file in            files:
        total_file_count = total_file_count + 1
        
        # Skip files containing "(instrumental)" or "[instrumental]"
        if "(instrumental)" in file.lower() or "[instrumental]" in file.lower(): continue
                
        file_path = os.path.abspath(file)  # Get absolute path for consistency
        directory = os.path.dirname(file_path)
        base_filename, _ = os.path.splitext(file)
        base_filename, _ = os.path.splitext(os.path.basename(file))
        #if DEBUG_SIDECAR_SEARCH: print(f"found file {file_path} ... base_filename={base_filename} ... for file={file}")
        
        #use glob.escape so it works with filenames that have brakcets in them too:
        #works for these.m3u but not all.m3u: has_sidecar = any(glob.glob(                                     f"{glob.escape(base_filename)}{ext[1:]}")  for ext in extensions_list)
        #failed fix: has_sidecar = any(glob.glob(os.path.join(glob.escape(directory), f"{glob.escape(base_filename)}{ext[1:]}")) for ext in extensions_list)
        #Let’s just expand it to a more traditional loop:
        # Check for sidecar files explicitly with a debug-friendly loop
        has_sidecar = False  # Assume no sidecar file initially
        for ext in extensions_list:
            potential_sidecar = os.path.join(directory, f"{base_filename}.{ext}")
            if DEBUG_SIDECAR_SEARCH: print(f"DEBUG: Looking for sidecar file: {potential_sidecar}")
            if os.path.exists(potential_sidecar):
                if DEBUG_SIDECAR_SEARCH: print(f"DEBUG: Found sidecar file: {potential_sidecar}")
                has_sidecar = True
        
        if DEBUG_SIDECAR_SEARCH: print(f"has_sidecar is {has_sidecar} for file {file}\n")

        if not has_sidecar:
            without_sidecar_count = without_sidecar_count + 1
            files_without_sidecars.add(file)
            #TODO need an option to display the missing ones i think! I like them displayed in folder mode, but not in playlist mode?            
            #print(file)

    # Write the output file
    if files_without_sidecars:
        input_file_ext = os.path.splitext(input_filename)[1]
        output_filename = f"{os.path.splitext(input_filename)[0]}-without {' '.join(ext[2:] for ext in extensions_list)}{input_file_ext}"
        if options.lower() == "getlyricsfilewrite": output_filename = SCRIPT_NAME_FOR_LYRIC_RETRIEVAL
        if options.lower() == "createsrtfilewrite": output_filename = SCRIPT_NAME_FOR_KARAOKE_CREATION
        if options.lower() !=        "NoFileWrite":
            #print          (colored(f"✏✏✏  Writing output file: {output_filename} ✏✏✏"  , 'green', attrs=['bold']))
            #print          (colored(f"✏✏✏  Writing output file: {output_filename} ✏✏✏"  , 'green', attrs=['bold']), file=sys.stderr)
            #ys.stderr.write(colored(f"✏ ✏ ✏  Writing output file ✏ ✏ ✏\n", 'green', attrs=['bold']))
            #ys.stderr.write(colored(f"       Files processed:  {total_file_count} \n"     , 'green', attrs=['bold']))
            #ys.stderr.write(colored(f"       Without sidecar:  {without_sidecar_count} \n", 'green', attrs=['bold']))
            #ys.stderr.write(colored(f"       To fix, run:      {output_filename} \n", 'green', attrs=['bold']))
            sys.stderr.write(        f"✏ ✏ ✏  Writing output file ✏ ✏ ✏\n")
            sys.stderr.write(        f"       Files processed:  {total_file_count} \n")
            sys.stderr.write(        f"       Without sidecar:  {without_sidecar_count} \n")
            sys.stderr.write(        f"       To fix, run:      {output_filename} \n")
            #DEBUG: if extra_args: print(f"Using extra arguments of: {extra_args}")


            if extra_args == "/s": extra_args=""

            # run any special postprocessing we've created, usually to create scripts to deal with files that are missing sidecar files
            #ith open(output_filename, 'w') as output_file:
            with open(output_filename, 'w', encoding='utf-8') as output_file:
                output_file.write(f"@on break cancel\n")

                # Convert set to list
                files_without_sidecars_list = list(files_without_sidecars)

                # Shuffle the list
                random.shuffle(files_without_sidecars_list)

                #or missing_file in sorted(files_without_sidecars)    :
                for missing_file in        files_without_sidecars_list:
                    if os.path.exists(missing_file):
                        if options.lower() == "getlyricsfilewrite": output_file.write(f"@repeat 13 echo. %+ @call get-lyrics \"{missing_file}\" {extra_args} %+ @call divider\n %+ rem from check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py")
                        if options.lower() == "createsrtfilewrite": output_file.write(f"@repeat 13 echo. %+ @call create-srt \"{missing_file}\" {extra_args} %+ @call divider\n %+ rem from check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extensions.py")
                        else                                      : output_file.write(f"{missing_file}\n")
                if options.lower()         == "getlyricsfilewrite": output_file.write("@call divider\n@call celebration \"ALL DONE WITH LYRIC RETRIEVAL!!!!\" silent\n") #@echo yra | *del %0 >&>nul\n") Self-deleting like this doesn't work, so these leftover files eventually get found and deleted in free-harddrive-space.bat which is called from maintenance.bat which is called upon reboot
                if options.lower()         == "createsrtfilewrite": output_file.write("@call divider\n@call celebration \"ALL DONE WITH KARAOKE CREATION!!!\" silent\n") #@echo yra | *del %0 >&>nul\n") Self-deleting like this doesn't work, so these leftover files eventually get found and deleted in free-harddrive-space.bat which is called from maintenance.bat which is called upon reboot

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python check_a_filelist_for_files_missing_sidecar_files_of_the_provided_extension.py <input_filename> <extensions> <postprocessor> {parameters to pass to created script}\n")
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

    #print(f"- DEBUG: Extra args are: '{extra_args_str}'") #
    #print(f"- DEBUG: Extensions are: '{extensions    }'") #

    main_guts(input_filename, extensions, options, extra_args_str)
