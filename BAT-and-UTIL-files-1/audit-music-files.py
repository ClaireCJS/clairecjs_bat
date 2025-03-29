
"""

1) This looks for audio files that don't have ReplayGain tags, and generates a script to add them.

2) It also generates into this same script❟ fixes for any audio files erroneously set to read-only [which may be an issue if that’s what you WANT, but we prefer to be able to edit our metadata on the fly!]

3) It also calls out 0-byte audio/subtitle/artwork files, which really shoudln’t exist

4) Finally, it renames any audio/subtitle/artwork files according to a configurable list of file-renaming mappings, for example “(instrumental)” in the filename is changed into “[instrumental]”, etc

...and it does in in parallel, processing >150 files per second, which for me means 161,713 files audited in 17.3 minutes


"""

# CONFIGURATION:
forbidden_chars                       = [';',  '%',   '^']                                                   # Characters to not allow in filenames! [Sorry❟ caret is a command separator for me❗!❕!❗!❗]
forbidden_chars_alternates            = ['；',  '％',  'ˆ']                                                   # Characters to use instead —— typically unicode equivalents with no speical use
AUDIT_ONLY_MONO_AND_STEREO            = True                                                                 # to our experience❟ our tool workflow only works correctly with 1–2-channel audio
VERBOSE_CHANNEL_SKIPPING              = False                                                                # set to True if you want to “see” every time it skips a file for having an incorrect number of audio channels
supported_extensions_description      = "audio"                                                              # the only 2 extensions that support ReplayGain tags which I want to audit — description of
supported_extensions                  = ('.mp3', '.flac')                                                    # the only 2 extensions that support ReplayGain tags which I want to audit — the list
extra_renaming_extensions             = ('.srt', '.lrc', '.txt', '.json', '.jpg', '.gif', '.png', '.webp', '.log')   # other extensions that we want to apply our rename_mappings renamings to  — the list
extra_renaming_extensions_description = "subtitle/lyric/art"                                                 # other extensions that we want to apply our rename_mappings renamings to  — description of
rename_mappings  = {
         "(instrumental)"  :      "[instrumental]",
    "(semi-instrumental)"  : "[semi-instrumental]",
    "(semi-music)"         : "[semi-music]"       ,
     "(non-music)"         :  "[non-music]"       ,
      "(nonmusic)"         :  "[non-music]"       ,
      "[nonmusic]"         :  "[non-music]"       ,
}

                                                                                           

# LIBRARIES:
import os                                                               # library: file processing
import glob                                                             # library: filename wildcards
import time                                                             # library: timers
from mutagen.flac       import FLAC                                     # library: examine FLAC to get # of channels
#mport wave                                                             # library: examine WAV  to get # of channels except WAV doesn’t support ReplayGain so let’s not and say we did
from mutagen.mp3        import MP3, HeaderNotFoundError                 # library: examine MP3  to get # of channels + mp3 error: header not found: mp3
from mutagen.id3        import ID3NoHeaderError                         # library: ————————-━-——-—-—-—--—━-—-━—━—————> mp3 error: header not found: id3 tag
from mutagen            import File                                     # library: mutagen stuffs
from pathlib            import Path                                     # library: filename paths
from itertools          import count                                    # library: incrementing number used safe file backups
from concurrent.futures import ThreadPoolExecutor, as_completed         # library: multi-threading
from colorama           import Fore, Style, init                        # library: ANSI color
from tqdm               import tqdm                                     # library: status bar 


clairecjs_util_loaded = False                                           # Optional enhancements if clairecjs library is accessible 
try:                                                                    # get them via: git clone http://www.github.com/clairecjs/clairecjs_utils
    import clairecjs_utils as claire                                    # drop them in subfolder named “clairecjs_utils”
    clairecjs_util_loaded = True
except ImportError:
    clairecjs_util_loaded = False
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path: sys.path.insert(0, script_dir)
    try:
        import clairecjs_utils as claire
        clairecjs_util_loaded = True
    except ImportError:
        clairecjs_util_loaded = False
        if os.getenv('USERNAME') == 'claire':                                                # if env var USERNAME=“claire”❟ then it’s me❟ and i want to know if my own utilities didn’t load! For everyone else❟ it’s not as important...
            raise ImportError("Cannot find 'clairecjs_utils' module in site-packages or the local directory.")


# Constants:
rg_fix_bat             = "RG_fix.bat"                                                        # filename for our script to fix things
rg_yes_file            = "RG_yes.dat"                                                        # filename for our results bucket #1
rg_no_file             = "RG_no.dat"                                                         # filename for our results bucket #2
blink_on               = "\033[6m"                                                           # ANSI code to: turn on  blinking 
blink_off              = "\033[25m"                                                          # ANSI code to: turn off blinking 
underline_on           = "\033[4m"                                                           # ANSI code to: turn on  underline 
underline_off          = "\033[24m"                                                          # ANSI code to: turn off underline
move_up_one_row        = "\033M"                                                             # ANSI code to: move up one row
special_message_prefix = "\033M\033[0G\033[0K"                                               # ANSI code to: move to the 1ˢᵗ column of the line❟ and then to erase to to EOL
                                                                                          
# result buckets:                                                                            # Result buckets:
rg_yes = []                                                                                  #   𝟙) “rg_yes” == “replay gain: yes” == Files that *DO*  have ReplayGain tags
rg_no  = []                                                                                  #   𝟚) “rg_no”  == “replay gain: no”  == Files that DON’T have ReplayGain tags and will need corrective action

# counters:
total_num_files_processed = 0
  
# flags:                                                                                  
bat_header_printed = False                                                                   # stores whether we’ve printed the header to our script or not
                                                                                                
def backup_existing_file(file_path):                                                         # safe backup by incrementing a number until the filename is unique
    if os.path.exists(file_path):                                                         
        for i in count(0):                                                                
            backup_path = f"{file_path}.bak.{i:03d}"
            if not os.path.exists(backup_path):
                os.rename(file_path, backup_path)
                break
                
def maybe_print_bat_header(f):                                                               # prints the header to our bat file❟ but only if we haven’t already 
    global bat_header_printed                                                                # stores whether we’ve printed the header to our script or not
    if not bat_header_printed:                                                               # if we HAVEN’T printed the header do this stuff:
        f.write('@loadbtm on\n')                                                             # load the full batfile to memory for faster execution & no spoooky errors if it’s edited while executing
        f.write('@Echo OFF\n')                                                               # that bat file should only echo what we want
        f.write('on break cancel\n\n')                                                       # ctrl-break should work well while running it
        f.write('call validate-in-path add-ReplayGain-tags pushd rn.bat\n\n'   )             # it should check that its tools exist prior to trying to use them
        f.write('rem Use this script to fix files with missing replaygain tags❟')             # it should inform the user why we’re here
        f.write(' then when done, run “audit-music-files.py” again...\n\n'     )             # and what to do after we’re done
        bat_header_printed = True                                                            # stores that we’ve now printed the header 

# Function to replace forbidden characters with alternates
char_map = dict(zip(forbidden_chars, forbidden_chars_alternates))
def substitute_forbidden_chars(file_path):
    global char_map
    new_file_path = file_path
    for forbidden, alternate in char_map.items():
        new_file_path = new_file_path.replace(forbidden, alternate)
    return new_file_path                                                                                                               

                                                                                                                                          


def process_file(file_path, primary_processing=True):                                                                                          # process one file. primary_processing refers to our ReplayGain processing and other fixes that only make sense for those types of files and not for our extra_renaming_extensions files
    global forbidden_chars, forbidden_chars_alternates, rename_mappings, total_num_files_processed                                             # use our character lists defined at the top of the file
    total_num_files_processed = total_num_files_processed + 1
    abs_file_path = os.path.abspath(file_path)                                                                                                
    try:                                                                                                                                      
        audio = File(file_path)                                                                                                               
                                                                                                                                              
        if any(char in file_path for char in forbidden_chars):                                                                                 # Check if the file path contains forbidden characters
            with open(rg_fix_bat, "a", encoding="utf-8") as f:                                                                                 # for any that contain forbidden characters❟ add a fix to our fix script
                maybe_print_bat_header(f)                                                                                                     
                f.write(f"\n\n\n\nrem ━━━━━━━━━━━━━━━━━━━━━ BAD FILENAME ENCOUNTERED: BEGIN ━━━━━━━━━━━━━━━━━━━━━━\n")                         # look pretty in our BAT file output
                f.write(f"    echo.\n")                                                                                                        # insert blank line in our STDOUT output
                #.write(f"    setdos /x-3 \n")                                                                                                 # turn off all variable expansion so we can use perent signs to rename files with percent signs
                f.write(f"    setdos /x-35\n")                                                                                                 # turn off all variable expansion so we can use perent signs to rename files with percent signs
                f.write(f"    echo %ansi_color_warning%This file path contains forbidden characters:%ansi_color_normal% “{abs_file_path}”\n")  # let user know
                # NO!  (f"    setdos /c%@CHAR[1]\n")                                                                                           # switch to nonsense command separator during rename process❟ just as extra protection
                f.write(f"    echo Forbidden characters in name: “{abs_file_path}”\n")                                                         # let user know
                new_file_path  =  substitute_forbidden_chars(     abs_file_path)                                                               # subtitute new❟ valid characters in❟ for invalid characters
                f.write(f"    echo Trying to rename to new name: “{new_file_path}”\n")                                                         # let user know
                f.write(f"    ren \"{abs_file_path}\" \"{new_file_path}\"\n")                                                                  # Rename command 
                f.write(f"    setdos /x-3\n")                                                                                                  # turn off command separator processing
                if "default_command_separator_character" in os.environ: f.write(f"    setdos /c%default_command_separator_character%\n")       # what I   try  to use
                elif os.getenv('USERNAME') == 'claire':                 f.write(f"    setdos /c^\n")                                           # what I  actually use
                else:                                                   f.write(f"    setdos /c&\n")                                           # what most people use
                f.write(f"    setdos /x0\n")                                                                                                   # turn everything we turned off back on
                f.write(f"rem ━━━━━━━━━━━━━━━━━━━━━ BAD FILENAME ENCOUNTERED: END ━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n\n\n")                         # look pretty in our BAT file output
            # Optionally, you can also print the message to console for feedback:
            print(f"\n\n{Fore.RED}ERROR: {abs_file_path} contains one of the forbidden characters ({forbidden_chars}). The “RG_fix.bat” that this script produces will TRY to fix it❟ but it may not be able to handle these characters. You may need to rename the file yourself. Suggested to use these alternative characters: {forbidden_chars_alternates}{Fore.GREEN}\n\n")
            return                                                                                                                             # return nothing because this isn’t a ReplayGain-related error
            return False, abs_file_path                                                                                                        # quit out for this file if this happens
                                                                                                                                             
        #print(f"size: {os.path.getsize(file_path)} for {file_path}")                                                                          # debug that we are correctly probing our file sizes
        if os.path.getsize(file_path) == 0:                                                                                                    # take action if the file is 0 bytes
            with open(rg_fix_bat, "a", encoding="utf-8") as f:                                                                                 # add to our output script
                f.write(f"echo.\necho.\necho.\necho.\necho.\n")                                                                                # cosmetic spacer
                f.write(f"echo %@RandFG_soft[]*** This file is 0 bytes, how do you want to deal with it?:\n")                                  # warn user
                f.write(f"echo    “{abs_file_path}”\n")                                                                                        # show filename
                #.write(f'call rn "{abs_file_path}"\n')                                                                                        #  'rn' command to rename the file
                f.write(f'*del /p "{abs_file_path}"\n')                                                                                        # 'del' command to delete the file
            print("\r\033[K",end="")                                                                                                           # Optionally, you can also print the....
            print(f"\n\n{Fore.RED}ERROR: {abs_file_path} is 0 bytes. “RG_fix.bat” will address this.{Fore.GREEN}")                             # ...message to the console for feedback
            return None, None                                                                                                                  # return nothing because this isn’t a ReplayGain-related error
            return                                                                                                                             # return nothing because this isn’t a ReplayGain-related error
            #eturn False, abs_file_path                                                                                                        # quit out for this file if this happens
                                                                                                                                           




        # ━━━━━━━━━━━━━━━━━━━━━ Rename (instrumental) → [instrumental] and other similar renamings ━━━━━━━━━━━━━━━━━━━━━ BEGIN:
        for old, new in rename_mappings.items():                                                                                               # for each configured (at top of file) renaming
            if old.lower() in file_path.lower():                                                                                               # if the pattern we want to replace is in the old filename
                new_file_path = file_path.replace(old, new).replace(old.lower(), new)                                                          # then replace it with the new pattern for our new filename
                with open(rg_fix_bat, "a", encoding="utf-8") as f:                                                                             # and open up our output script
                    maybe_print_bat_header(f)                                                                                                  # print the header if it isn’t printed already
                    entity_for_bat_file_header_comment = old.replace("(", "").replace(")", "").upper()                                         # make some cosmetic adjustments to our header text
                    f.write(f"\n\nrem ━━━━━━━━━━━━━━━━━━━━━ INCORRECTLY-MARKED ")                                                              # leave a comment in our output script explaining this [1/2]
                    f.write(f"{entity_for_bat_file_header_comment}: ━━━━━━━━━━━━━━━━━━━━━━\n")                                                 # leave a comment in our output script explaining this [2/2]
                    f.write(f'ren "{file_path}" "{new_file_path}"\n\n\n')                                                                      # rename the old filename to the new filename
        # ━━━━━━━━━━━━━━━━━━━━━ Rename (instrumental) → [instrumental] and other similar renamings ━━━━━━━━━━━━━━━━━━━━━ ^END                  




    
        if not primary_processing: return






        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Disallow non-2-channel audio from being audited ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # at this point❟ there are no “forbidden” characters left in the files❟ and they aren’t 0-byte files either
        # so the next thing is to check if it’s 1–2 channels —— we don’t know how to audit music that has a different # of channels
        if primary_processing == True and AUDIT_ONLY_MONO_AND_STEREO == True:
            try:
                if "5.1 " in file_path.lower() or "7.1 " in file_path.lower():
                    print(f"\n{Fore.YELLOW}Skipping {file_path}: Filename suggests not a 1–2-channel file.{Fore.WHITE}\n")
                    return

                channels = 2
                audio    = None
                if   file_path.lower().endswith(".flac"): audio = FLAC(file_path)
                elif file_path.lower().endswith(".mp3" ): audio =  MP3(file_path)
                #lif file_path.lower().endswith(".wav" ):                                               #this library won’t read WAVs
                #    with wave.open(file_path, 'rb')   as  audio: channels = audio.getnchannels()       #this library won’t read WAVs
                if audio and audio.info and audio.info.channels: channels = audio.info.channels
                if channels != 2 and channels != 1:
                    if VERBOSE_CHANNEL_SKIPPING:
                        print("\r\033[K",end="") 
                        print(f"\n{Fore.YELLOW}Skipping {file_path}: Not a 1–2-channel file (Channels: {channels}){Fore.WHITE}\n")
                    return            
            except:
                pass
        
        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Fix read-only attribute if file is incorrectly read-only: BEGIN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if not os.access(file_path, os.W_OK and primary_processing):                                                   # automatically fix things if file is erroneously read-only but only on the same types of files we do replaygain processing on
            with open(rg_fix_bat, "a", encoding="utf-8") as f: f.write(f"attrib -r \"{abs_file_path}\"\n")
        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Fix read-only attribute if file is incorrectly read-only: END ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━



        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Check for presence of missing ReplayGainTags: BEGIN: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if primary_processing:
            # initialize landing-pad variables
            rg_track_gain = None
            rg_track_peak = None
            rg_album_gain = None
            rg_album_peak = None

            # postentially grab a value for each one of these landing-pad variables — primary method
            for key, value in audio.items():
                if   key.lower() == "TXXX:replaygain_track_gain".lower(): rg_track_gain = value
                elif key.lower() == "TXXX:replaygain_track_peak".lower(): rg_track_peak = value
                elif key.lower() == "TXXX:replaygain_album_gain".lower(): rg_album_gain = value
                elif key.lower() == "TXXX:replaygain_album_peak".lower(): rg_album_peak = value

            # postentially grab a value for each one of these landing-pad variables — backup method
            if not (rg_track_gain): rg_track_gain = audio.get("REPLAYGAIN_TRACK_GAIN")
            if not (rg_track_peak): rg_track_peak = audio.get("REPLAYGAIN_TRACK_PEAK")
            if not (rg_album_gain): rg_album_gain = audio.get("REPLAYGAIN_ALBUM_GAIN")
            if not (rg_album_peak): rg_album_peak = audio.get("REPLAYGAIN_ALBUM_PEAK")

            # if any of these values exist, package them and return them
            if rg_track_gain or rg_track_peak or rg_album_gain or rg_album_peak:
                rg_data = [
                    f"replaygain_track_gain={rg_track_gain[0]}" if rg_track_gain else "",
                    f"replaygain_track_peak={rg_track_peak[0]}" if rg_track_peak else "",
                    f"replaygain_album_gain={rg_album_gain[0]}" if rg_album_gain else "",
                    f"replaygain_album_peak={rg_album_peak[0]}" if rg_album_peak else ""
                ]
                return (True, f"{abs_file_path} : {', '.join(rg_data)}")

            # otherwise return “False” and the path so that we will fix that folder in our fix-script
            else:                                                                                                                              
                print("\r\033[K",end="")                                                                                                       # erase current line
                print(f"\n{Fore.BRIGHT_RED}ERROR: Missing ReplayGain tags: {file_path}{Fore.WHITE}\n")                                         # let the user nkow
                return (False, abs_file_path)                                                                                                  # return fact no replaygain tags are there
        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Check for presence of missing ReplayGainTags: END ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━





    # check for corrupt id3 headers
    except HeaderNotFoundError as e:
        if primary_processing:
            print("\r\033[K",end="")                                                            #ansi code to erase current line
            print(f"\n\n{Fore.RED}*** Error processing file: {Fore.YELLOW}{abs_file_path}")
            print(f"\t{Fore.RED}Exception: {str(e)}")
            print(f"\t{Fore.RED}File might be corrupt/malformed. Skipping.{Fore.WHITE}\n")
            return(False, abs_file_path)

    # check for missing id3 header
    except (ID3NoHeaderError, Exception) as e:
        if primary_processing:
            print("\r\033[K",end="") 
            rg_no.append(abs_file_path)
            print(f"\n{Fore.RED}Error processing file: {Fore.YELLOW}{abs_file_path}\n{Fore.RED}Exception: {str(e)}" + Fore.WHITE + "\n")
            return(False, abs_file_path)




def maincolor():                                                # sets color based on which modules are loaded
    if clairecjs_util_loaded: print(Fore.WHITE,end="")
    else:                     print(Fore.GREEN,end="")




def process_renaming_only_files():                                                                      # for processing the files in “extra_renaming_extensions”
    r1, r2 = process_music_files(extra_renaming_extensions, extra_renaming_extensions_description)
    return r1, r2

def process_music_files(extensions_to_use=supported_extensions, processing_filetypes_of=supported_extensions_description):
    global special_message_prefix, extra_renaming_extensions

    print (special_message_prefix + "⭐ Enumerating files of extensions {extensions_to_use}...", end="")
    #file_paths = [path for ext in supported_extensions for path in glob.glob(f"**/*{ext}", recursive=True)]
    #for ext in tqdm(supported_extensions, desc="🔍 Enumerating files", unit="ext"): file_paths.extend(glob.glob(f"**/*{ext}", recursive=True))
    #total_files = len(file_paths)
    

    # processing rules: in our case, we want to process replaygain only for our “supported_extensions” list up top, and not for our “extra_renaming_extensions” list up top, which are for renaming only
    primary_processing = True
    if extensions_to_use == extra_renaming_extensions: 
        primary_processing = False


    file_paths  = []
    root_dir    = "."
    print (move_up_one_row)
    print (move_up_one_row)
    print (move_up_one_row)
    total_files = sum(len(files) for _, _, files in os.walk(root_dir))                                      # Count all files to estimate total progress
    with tqdm(total=total_files, desc="🔍 Enumerating files", unit="file") as pbar:                         # Initialize the progress bar
        for dirpath, _, filenames in os.walk(root_dir):                                                     # for each dir found
            for file in filenames:                                                                          # for each file found
                if clairecjs_util_loaded: claire.tick()                                                     # realtime color-cycling through the visible spectrum
                else:                     maincolor()                                                       # a flat color
                pbar.update(1)                                                                              # Update the progress bar for each file               
                if os.path.splitext(file)[1].lower() in extensions_to_use:                                  # Check file extension and add to file_paths if supported
                    file_paths.append(os.path.join(dirpath, file))                                        
                                                                                                          
    file_count  = 0                                                                                       
                                                                                                          
    print (special_message_prefix + move_up_one_row)                                                      
    #ith ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:                                        # This didn’t work out...
    with ThreadPoolExecutor(                          ) as executor:                                        # ........but this did :)
        maincolor()                                                                              
        with tqdm(total=len(file_paths), desc=f"👀 Auditing {processing_filetypes_of} files") as pbar:
            future_to_file = {executor.submit(process_file, file_path, primary_processing): file_path for file_path in file_paths}
            maincolor()
            for future in as_completed(future_to_file):
                maincolor()
                file_count += 1                                                                             # old progress code from before we started using tqdm status bars:                #if file_count % 20 == 0 or file_count == total_files:                                               #    percentage     = "{:.2f}".format((file_count / total_files) * 100)                #    if percentage == "100.00": blink = blink_off                #    else                     : blink = blink_on                #    #🐐print(f"\r{Fore.WHITE}⚙️ {blink}Auditing audio files:{blink_off} {Style.NORMAL}{Fore.WHITE}{Style.BRIGHT}{percentage}{Style.NORMAL}%", end='', flush=True)
                    
                result = future.result()
                if result is not None:                                                                      # if we have any results:
                    has_rg, data = result                                                                   #   examine our results
                    if has_rg: rg_yes.append(data)                                                          #   add files **with**  ReplayGain tags to result bucket 1
                    else:      rg_no .append(data)                                                          #   add files *without* ReplayGain tags to result bucket 2
                                                                                                           
                if clairecjs_util_loaded: claire.tick()                                                     # realtime color-cycling through the visible spectrum
                else:                     maincolor()                                                       # a flat color
                pbar.update(1)                                                                              # update progress bar               
                                                                                                          
    if clairecjs_util_loaded:                                                                               # if the Claire::Console library is loaded:
        claire.tock()                                                                                       #    reset the custom color definitions used in the color-cycling
        print(Fore.GREEN)                                                                                   #    and bring us back to our “success color”
    else:                                                                                                   # if the Claire::Console library is NOT loaded:
        maincolor()                                                                                         #    reset to our default color
    return rg_yes, rg_no                                                                                    # return our result buckets
                                                                                                          
                                                                                                          
                                                                                                          
def main():                                                                                               
    global bat_header_printed, total_num_files_processed                                                           # stores whether we’ve printed the header to our script or not, and total files processed
    start_time = time.monotonic()                                                                                  # timer on
                                                                                                                  
    # backup existing files                                                                                       
    print("\n⭐ Backing up files...")                                                                               # Back up relavant files:
    backup_existing_file(rg_yes_file)                                                                              # back up previous result bucket 1 file
    backup_existing_file(rg_no_file)                                                                               # back up previous result bucket 2 file
    backup_existing_file(rg_fix_bat)                                                                               # back up previously-generated fix script
                                                                                                                  
    # the main brunt of the work is done here:                                                                     # the main brunt of the work is done here:
    zzzzzz, xxxxx = process_renaming_only_files()                                                                  # do the secondary work 1ˢᵗ because it’s quicker
    rg_yes, rg_no = process_music_files()                                                                          # do the   primary work 2ⁿᵈ because it’s  slower
    rg_no  = [file for file in rg_no  if file is not None]
    rg_yes = [file for file in rg_yes if file is not None]
    if rg_yes:                                                                                                    
        #ith open(rg_yes_file, 'w', encoding='utf-8') as f: f.write('\n'.join(                      rg_yes))       # result bucket 1 to file
        with open(rg_yes_file, 'w', encoding='utf-8') as f: f.write('\n'.join(filter(None, map(str, rg_yes))))
    if rg_no:  
        #ith open(rg_no_file , 'w', encoding='utf-8') as f: f.write('\n'.join(                      rg_no ))       # result bucket 2 to file
        with open(rg_no_file , 'w', encoding='utf-8') as f: f.write('\n'.join(filter(None, map(str, rg_no))))
                                                                                                          
    # create script to fix all that is wrong:                                                                      # (though “add-RelayGain-tags.bat” must exist for it to be effective)
    if rg_no:                                                                                                      # if result bucket 2 has contents (filenames)
        rg_no_folders = set(os.path.dirname(file) for file in rg_no)                                               # discover all the unique dir names for all those files
        with open(rg_fix_bat, 'a', encoding='utf-8') as f:                                                         # open up a bat file to run the commands to fix it all
            maybe_print_bat_header(f)                                                                              # print the BAT file header❟ but only if we havent’ already
            for folder in rg_no_folders:                                                                           # then it should go through each unique folder we discovered
                f.write(f'cd    "{folder}"\n')                                                                     # change into the folder in case the pushd command doesn’t work
                f.write(f'pushd "{folder}"\n')                                                                     # store the folder into the directory stack so we can return from whence we came
                f.write(f'call add-ReplayGain-tags\n')                                                             # call whatever our script to add ReplayGain tags to all files in a folder is
                f.write('popd\n')                                                                                  # return from whence we came
        #print(f"Created {rg_fix_bat} to fix problems.")                                                           # Let them know about the fixer script
                                                                                                                  
    # final report:                                                                                                # final report:
    end_time = time.monotonic()                                                                                    # timer off
    elapsed_time = end_time - start_time                                                                           # how long did it take?
    #ps = round((len(rg_yes) + len(rg_no)) / elapsed_time)                                                         # how many files per second did we process?
    fps = round(total_num_files_processed  / elapsed_time)                                                         # how many files per second did we process?
                                                                                                                  
    minutes = elapsed_time / 60                                                                                    # convert to minutes❟ then report:
    #rint(f"✔️ {Fore.GREEN}{Style.BRIGHT}{underline_on}{len(rg_yes)  + len(rg_no)}{underline_off}", end="")        # report
    print(f"✔️ {Fore.GREEN}{Style.BRIGHT}{underline_on}{total_num_files_processed}{underline_off}", end="")        # report
    print(f"{Style.NORMAL} files audited in {Style.BRIGHT}{underline_on}{elapsed_time:.2f}"      , end="")         # report
    print(f"{underline_off}{Style.NORMAL} seconds ({minutes:.1f} minutes) ({fps} files/sec)"             )         # report
                                                                                                                  
if __name__ == "__main__":                                                                                        
    main()                                                                                                        
