"""

todo: need to make this skip processing files that say 5.1 or 7.1 mix

1) This looks for files that don't have ReplayGain tags, or which are set to read-only, and generates a script to add them.

2) It also generates into this same script❟ fixes for any files erroneously set to read-only [which may be an issue if that’s what you WANT, but we prefer to be able to edit our metadata on the fly!]

3) It also calls out 0-byte audio files, which really shoudln’t exist❟ with a fix for those as well (relying on our “rn.bat”)

Just run it in the base of any folder tree that has audio files.

"""

# CONFIGURATION:
forbidden_chars            = [';',  '%',   '^']                                              # Characters to not allow in filenames! [Sorry❟ caret is a command separator for me❗!❕!❗!❗]
forbidden_chars_alternates = ['；',  '％',  'ˆ']                                               # Characters to use instead —— typically unicode equivalents with no speical use
AUDIT_ONLY_MONO_AND_STEREO = True                                                            # to our experience❟ our tool workflow only works correctly with 1–2-channel audio
VERBOSE_CHANNEL_SKIPPING   = False                                                           # set to True if you want to “see” every time it skips a file for having an incorrect number of audio channels
supported_extensions       = ('.mp3', '.flac')                                               # the only 2 extensions that support ReplayGain tags which I want to audit
                                                                                           
import os                                                                                    # library: file processing
import glob                                                                                  # library: filename wildcards
import time                                                                                  # library: timers
from mutagen.flac       import FLAC                                                          # library: examine FLAC to get # of channels
#mport wave                                                                                  # library: examine WAV  to get # of channels except WAV doesn’t support ReplayGain so let’s not and say we did
from mutagen.mp3        import MP3, HeaderNotFoundError                                      # library: examine MP3  to get # of channels + mp3 error: header not found: mp3
from mutagen.id3        import ID3NoHeaderError                                              # library: ————————-━-——-—-—-—--—━-—-━—━—————> mp3 error: header not found: id3 tag
from mutagen            import File                                                          # library: mutagen stuffs
from pathlib            import Path                                                          # library: filename paths
from itertools          import count                                                         # library: incrementing number used safe file backups
from concurrent.futures import ThreadPoolExecutor, as_completed                              # library: multi-threading
from colorama           import Fore, Style, init                                             # library: ANSI color
from tqdm               import tqdm                                                          # library: status bar 


clairecjs_util_loaded = False                                                                # Optional enhancements if clairecjs library is accessible 
try:                                                                                         # get them via: git clone http://www.github.com/clairecjs/clairecjs_utils
    import clairecjs_utils as claire                                                         # drop them in subfolder named “clairecjs_utils”
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
                                                                                                                                       
def process_file(file_path):                                                                                                              # process one file
    global forbidden_chars, forbidden_chars_alternates                                                                                    # use our character lists defined at the top of the file
    abs_file_path = os.path.abspath(file_path)                                                                                         
    try:                                                                                                                               
        audio = File(file_path)                                                                                                        
                                                                                                                                       
        if any(char in file_path for char in forbidden_chars):                                                                            # Check if the file path contains forbidden characters
            with open(rg_fix_bat, "a", encoding="utf-8") as f:                                                                            # for any that contain forbidden characters❟ add a fix to our fix script
                maybe_print_bat_header(f)
                f.write(f"\n\n\n\nrem ━━━━━━━━━━━━━━━━━━━━━ BAD FILENAME ENCOUNTERED: BEGIN ━━━━━━━━━━━━━━━━━━━━━━\n")                    # look pretty in our BAT file output
                f.write(f"    echo.\n")                                                                                                   # insert blank line in our STDOUT output
                #.write(f"    setdos /x-3 \n")                                                                                            # turn off all variable expansion so we can use perent signs to rename files with percent signs
                f.write(f"    setdos /x-35\n")                                                                                            # turn off all variable expansion so we can use perent signs to rename files with percent signs
                f.write(f"    echo This file path contains forbidden characters: “{abs_file_path}”\n")                                    # let user know
                # NO!  (f"    setdos /c%@CHAR[1]\n")                                                                                      # switch to nonsense command separator during rename process❟ just as extra protection
                f.write(f"    echo Forbidden characters in name: “{abs_file_path}”\n")                                                    # let user know
                new_file_path  =  substitute_forbidden_chars(     abs_file_path)                                                          # subtitute new❟ valid characters in❟ for invalid characters
                f.write(f"    echo Trying to rename to new name: “{new_file_path}”\n")                                                    # let user know
                f.write(f"    ren \"{abs_file_path}\" \"{new_file_path}\"\n")                                                             # Rename command 
                f.write(f"    setdos /x-3\n")                                                                                             # turn off command separator processing
                if "default_command_separator_character" in os.environ: f.write(f"    setdos /c%default_command_separator_character%\n")  # what I   try  to use
                elif os.getenv('USERNAME') == 'claire':                 f.write(f"    setdos /c^\n")                                      # what I  actually use
                else:                                                   f.write(f"    setdos /c&\n")                                      # what most people use
                f.write(f"    setdos /x0\n")                                                                                              # turn everything we turned off back on
                f.write(f"rem ━━━━━━━━━━━━━━━━━━━━━ BAD FILENAME ENCOUNTERED: END ━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n\n\n")                    # look pretty in our BAT file output
            # Optionally, you can also print the message to console for feedback:
            print(f"\n\n{Fore.RED}ERROR: {abs_file_path} contains one of the forbidden characters ({forbidden_chars}). The “RG_fix.bat” that this script produces will TRY to fix it❟ but it may not be able to handle these characters. You may need to rename the file yourself. Suggested to use these alternative characters: {forbidden_chars_alternates}{Fore.GREEN}\n\n")

        elif os.path.getsize(file_path) == 0:                                                                                             # take action if the file is 0 bytes
            with open(rg_fix_bat, "a", encoding="utf-8") as f:
                f.write(f"echo.\n")
                f.write(f"echo.\n")
                f.write(f"echo This file is 0 bytes, how do you want to rename it: {abs_file_path}\n")
                f.write(f"call rn {abs_file_path}\n")  # 'rn' command to rename the file
            # Optionally, you can also print the message to console for feedback:
            print("\r\033[K",end="") 
            print(f"\n\n{Fore.RED}ERROR: {abs_file_path} is 0 bytes. “RG_fix.bat” will address this.{Fore.GREEN}")
            return False, abs_file_path        

        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Disallow non-2-channel audio from being audited ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # at this point❟ there are no “forbidden” characters left in the files❟ and they aren’t 0-byte files either
        # so the next thing is to check if it’s 1–2 channels —— we don’t know how to audit music that has a different # of channels
        if AUDIT_ONLY_MONO_AND_STEREO == True:
            try:
                channels = 2
                audio    = None
                if   file_path.lower().endswith(".flac"): audio = FLAC(file_path)
                elif file_path.lower().endswith(".mp3" ): audio =  MP3(file_path)
                #elif file_path.lower().endswith(".wav" ): 
                #    with wave.open(file_path, 'rb')   as  audio: channels = audio.getnchannels()
                if audio and audio.info and audio.info.channels: channels = audio.info.channels
                if channels != 2 and channels != 1:
                    if VERBOSE_CHANNEL_SKIPPING:
                        print("\r\033[K",end="") 
                        print(f"\n{Fore.YELLOW}Skipping {file_path}: Not a 1–2-channel file (Channels: {channels}){Fore.WHITE}\n")
                    return            
            except:
                pass
        
        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Fix read-only attribute if file is incorrectly read-only: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if not os.access(file_path, os.W_OK):                                                   # automatically fix things if file is erroneously read-only
            with open(rg_fix_bat, "a", encoding="utf-8") as f: f.write(f"attrib -r \"{abs_file_path}\"\n")

        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Check for presence of missing ReplayGainTags: BEGIN: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        rg_track_gain = None
        rg_track_peak = None
        rg_album_gain = None
        rg_album_peak = None
        for key, value in audio.items():
            if   key.lower() == "TXXX:replaygain_track_gain".lower(): rg_track_gain = value
            elif key.lower() == "TXXX:replaygain_track_peak".lower(): rg_track_peak = value
            elif key.lower() == "TXXX:replaygain_album_gain".lower(): rg_album_gain = value
            elif key.lower() == "TXXX:replaygain_album_peak".lower(): rg_album_peak = value

        if not (rg_track_gain): rg_track_gain = audio.get("REPLAYGAIN_TRACK_GAIN")
        if not (rg_track_peak): rg_track_peak = audio.get("REPLAYGAIN_TRACK_PEAK")
        if not (rg_album_gain): rg_album_gain = audio.get("REPLAYGAIN_ALBUM_GAIN")
        if not (rg_album_peak): rg_album_peak = audio.get("REPLAYGAIN_ALBUM_PEAK")

        if rg_track_gain or rg_track_peak or rg_album_gain or rg_album_peak:
            rg_data = [
                f"replaygain_track_gain={rg_track_gain[0]}" if rg_track_gain else "",
                f"replaygain_track_peak={rg_track_peak[0]}" if rg_track_peak else "",
                f"replaygain_album_gain={rg_album_gain[0]}" if rg_album_gain else "",
                f"replaygain_album_peak={rg_album_peak[0]}" if rg_album_peak else ""
            ]
            return (True, f"{abs_file_path} : {', '.join(rg_data)}")
        else:
            return (False, abs_file_path)
        #━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ Check for presence of missing ReplayGainTags: END ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
    except HeaderNotFoundError as e:
        print("\r\033[K",end="")    #ansi code to erase current line
        print(f"\n\n{Fore.RED}*** Error processing file: {Fore.YELLOW}{abs_file_path}")
        #rint(f"\t{Fore.RED}Exception in {Fore.YELLOW}{abs_file_path}{Fore.RED}: {str(e)}")
        print(f"\t{Fore.RED}Exception: {str(e)}")
        #rint(f"\t{Fore.RED}File might be corrupt/malformed. Skipping: {Fore.YELLOW}" + abs_file_path + Fore.WHITE + "\n")
        print(f"\t{Fore.RED}File might be corrupt/malformed. Skipping.{Fore.WHITE}\n")
        return(False, abs_file_path)
    except (ID3NoHeaderError, Exception) as e:
        print("\r\033[K",end="") 
        rg_no.append(abs_file_path)
        print(f"\n{Fore.RED}Error processing file: {Fore.YELLOW}{abs_file_path}\n{Fore.RED}Exception: {str(e)}" + Fore.WHITE + "\n")
        return(False, abs_file_path)


def maincolor():
    if clairecjs_util_loaded: print(Fore.WHITE,end="")
    else:                     print(Fore.GREEN,end="")


def process_music_files():
    global special_message_prefix
    print (special_message_prefix + "⭐ Enumerating files...", end="")
    #file_paths = [path for ext in supported_extensions for path in glob.glob(f"**/*{ext}", recursive=True)]
    #for ext in tqdm(supported_extensions, desc="🔍 Enumerating files", unit="ext"): file_paths.extend(glob.glob(f"**/*{ext}", recursive=True))
    #total_files = len(file_paths)
    file_paths  = []
    root_dir    = "."
    print (move_up_one_row)
    print (move_up_one_row)
    print (move_up_one_row)
    total_files = sum(len(files) for _, _, files in os.walk(root_dir))                              # Count all files to estimate total progress
    with tqdm(total=total_files, desc="🔍 Enumerating files", unit="file") as pbar:                 # Initialize the progress bar
        for dirpath, _, filenames in os.walk(root_dir):                                             # for each dir found
            for file in filenames:                                                                  # for each file found
                if clairecjs_util_loaded: claire.tick()                                             # realtime color-cycling through the visible spectrum
                else:                     maincolor()                                               # a flat color
                pbar.update(1)                                                                      # Update the progress bar for each file               
                if os.path.splitext(file)[1].lower() in supported_extensions:                       # Check file extension and add to file_paths if supported
                    file_paths.append(os.path.join(dirpath, file))    
    
    file_count  = 0

    print (special_message_prefix + move_up_one_row)
    #ith ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:                                # This didn’t work out...
    with ThreadPoolExecutor(                          ) as executor:                                # ........but this did :)
        maincolor()                                                                              
        with tqdm(total=len(file_paths), desc="👀 Auditing audio files") as pbar:
            future_to_file = {executor.submit(process_file, file_path): file_path for file_path in file_paths}
            maincolor()
            for future in as_completed(future_to_file):
                maincolor()
                file_count += 1                
                
                # old progress code from before we started using tqdm status bars:
                #if file_count % 20 == 0 or file_count == total_files:                               
                #    percentage     = "{:.2f}".format((file_count / total_files) * 100)
                #    if percentage == "100.00": blink = blink_off
                #    else                     : blink = blink_on
                #    #🐐print(f"\r{Fore.WHITE}⚙️ {blink}Auditing audio files:{blink_off} {Style.NORMAL}{Fore.WHITE}{Style.BRIGHT}{percentage}{Style.NORMAL}%", end='', flush=True)
                    
                result = future.result()
                if result is not None:                                                              # if we have any results:
                    has_rg, data = result                                                           #   examine our results
                    if has_rg: rg_yes.append(data)                                                  #   add files **with**  ReplayGain tags to result bucket 1
                    else:      rg_no .append(data)                                                  #   add files *without* ReplayGain tags to result bucket 2
                    
                if clairecjs_util_loaded: claire.tick()                                             # realtime color-cycling through the visible spectrum
                else:                     maincolor()                                               # a flat color
                pbar.update(1)                                                                      # update progress bar               
                                                                                                  
    if clairecjs_util_loaded:                                                                       # if the Claire::Console library is loaded:
        claire.tock()                                                                               #    reset the custom color definitions used in the color-cycling
        print(Fore.GREEN)                                                                           #    and bring us back to our “success color”
    else:                                                                                           # if the Claire::Console library is NOT loaded:
        maincolor()                                                                                 #    reset to our default color
    return rg_yes, rg_no                                                                            # return our result buckets



def main():
    global bat_header_printed                                                                       # stores whether we’ve printed the header to our script or not
    start_time = time.monotonic()                                                                   # timer on
    print("\n⭐ Backing up files...")                                                                # Back up relavant files:
    backup_existing_file(rg_yes_file)                                                               # back up previous result bucket 1 file
    backup_existing_file(rg_no_file)                                                                # back up previous result bucket 2 file
    backup_existing_file(rg_fix_bat)                                                                # back up previously-generated fix script

    # the main brunt of the work is done here:                                                      # the main brunt of the work is done here:
    rg_yes, rg_no = process_music_files()                                                           # do the work
    with open(rg_yes_file, 'w', encoding='utf-8') as f: f.write('\n'.join(rg_yes))                  # result bucket 1 to file
    with open(rg_no_file , 'w', encoding='utf-8') as f: f.write('\n'.join(rg_no ))                  # result bucket 2 to file

    # create script to fix all that is wrong:                                                       # (though “add-RelayGain-tags.bat” must exist for it to be effective)
    if rg_no:                                                                                       # if result bucket 2 has contents (filenames)
        rg_no_folders = set(os.path.dirname(file) for file in rg_no)                                # discover all the unique dir names for all those files
        with open(rg_fix_bat, 'w', encoding='utf-8') as f:                                          # open up a bat file to run the commands to fix it all
            maybe_print_bat_header(f)                                                               # print the BAT file header❟ but only if we havent’ already
            for folder in rg_no_folders:                                                            # then it should go through each unique folder we discovered
                f.write(f'cd    "{folder}"\n')                                                      # change into the folder in case the pushd command doesn’t work
                f.write(f'pushd "{folder}"\n')                                                      # store the folder into the directory stack so we can return from whence we came
                f.write(f'call add-ReplayGain-tags\n')                                              # call whatever our script to add ReplayGain tags to all files in a folder is
                f.write('popd\n')                                                                   # return from whence we came
        #print(f"Created {rg_fix_bat} to fix problems.")                                            # Let them know about the fixer script

    # final report:                                                                                 # final report:
    end_time = time.monotonic()                                                                     # timer off
    elapsed_time = end_time - start_time                                                            # how long did it take?
    fps = round((len(rg_yes) + len(rg_no)) / elapsed_time)                                          # how many files per second did we process?
    minutes = elapsed_time / 60                                                                     # convert to minutes❟ then report:
    print(f"✔️ {Fore.GREEN}{Style.BRIGHT}{underline_on}{len(rg_yes) + len(rg_no)}{underline_off}")  # report
    print(f"{Style.NORMAL} files audited in {Style.BRIGHT}{underline_on}{elapsed_time:.2f}"      )  # report
    print(f"{underline_off}{Style.NORMAL} seconds ({minutes:.1f} minutes) ({fps} files/sec)"     )  # report

if __name__ == "__main__":
    main()
