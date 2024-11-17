
#TODO: use this package instead: https://github.com/jianfch/stable-ts

#TODO: mention LRC was created
#TODO: process a playlist (may need to update single file mode to not just assume "." is the path?)
#TODO: what if text file already present? We could actually use it to engineer the prompt to make fewer mistakes
#TODO: better LRC quality (comments in writer function)
            #request to improve line length for shorter lines https://github.com/openai/whisper/discussions/314
            #thread on splitting srt files: https://gist.github.com/rBrenick/fcb8d07ecaa55856ecd9745ecfd29341
            #word-level timestamp request on github: https://github.com/openai/whisper/pull/869

MODEL_TO_USE = "large"                                                        # tiny/base/small/medium/large-v1/large-v2/large[large should point to latest large version]

from colorama import Fore, Back, Style, init
init()
import os
import sys
import glob
import clairecjs_utils as claire

print(f"{Fore.RED}Importing openlrc...",end="")
from openlrc import LRCer
print(f"{Fore.BLUE}done!")

lrcer = None
#print(f"{Fore.RED}Starting LRCer engine...",end="")
lrcer = LRCer()
#print(f"{Fore.BLUE}...done!")


audio_extensions = [".mp3", ".wav", ".flac", ".ogg", ".m4a"]                  # List of valid audio extensions
output_extensions = [".srt", ".txt", ".lrc"]                                  # List of output extensions

def old_process_files(path, is_dry_run=True):
    global audio_extensions
    for subdir, dirs, files in os.walk(path):                                 # Traverse directory with all its subdirectories and files
        for filename in files:
            process_file (filename, subdir, is_dry_run=is_dry_run)
        postprocess_files(subdir          , is_dry_run=is_dry_run)            # for reasons of impatience, do post-processing in each folder so that we can examine our results sooner, at the expense of the final post-processing being completely redundant

def warning(msg):
    print(f"{Fore.RED}{Style.BRIGHT}{msg}{Style.RESET_ALL}")



def process_file_into_lrc(filename, subdir, is_dry_run=False):
    global lrcer

    ## lazy loading of our modules
    #global MODEL_TO_USE
    #print(f"Importing whisper...")
    #import whisper
    ##print("Importing whisper writer...")
    #from whisper.utils import get_writer
    #print("Loading whisper model...")
    #model = whisper.load_model(MODEL_TO_USE)                                  # tiny/base/small/medium/large-v1/large-v2/large[large should point to latest large version]

    audio_file_name = subdir + os.sep + filename

    if os.path.splitext(filename)[1] not in audio_extensions: return          # Check if the file has a valid audio extension
    base_name, ext = os.path.splitext(audio_file_name)                        # get base filename to figure out companion filenames
    transcript_txt_name = f"{base_name}.txt"                                  #     companion filename
    transcript_lrc_name = f"{base_name}.lrc"                                  #     companion filename

    if os.path.isfile(transcript_txt_name):
        warning(f"{transcript_txt_name} text file already exists; skipping")
        return
    if os.path.isfile(transcript_lrc_name):
        warning(f"{transcript_lrc_name} LRC file already exists; skipping")
        return

    print(f'\n{Fore.CYAN}{Style.BRIGHT}**** ', end="")
    if is_dry_run: print(f'{Fore.CYAN}{Style.BRIGHT}Would ',end="")
    print(f'{Fore.CYAN}{Style.BRIGHT}Transcribe {audio_file_name} to {transcript_lrc_name}{Style.NORMAL}')

    if lrcer is None:
        print(f"{Fore.RED}Starting LRCer engine...",end="")
        lrcer = LRCer()
        print(f"{Fore.BLUE}...done!")

    # the new way which uses lrcer
    lrcer.run(audio_file_name,skip_trans=True,target_lang="en")

    # the old way which used the default openai
    # if False:
    #     result = model.transcribe(audio_file_name, verbose=True, language="en")
    #     transcript = result["text"]
    #     #no longer need this with verbose=True: print(f"{Fore.WHITE}Raw Transcript: {Fore.LIGHTBLACK_EX}{transcript}")
    #     print (f"{Fore.MAGENTA}results are: {result}{Fore.BLUE}")
    #     if not is_dry_run:
    #         #without line breaks: with open(transcript_txt_name, "w", encoding="utf-8") as f: f.write(transcript)
    #         #with line breaks:
    #         my_writer = get_writer("txt", subdir)
    #         my_writer(result, audio_file_name)
    #         my_writer = get_writer("srt", subdir)
    #         my_writer(result, audio_file_name)
    #         #my_writer = get_writer("lrc", subdir)      #used modded whisper\utils.py
    #         #my_writer(result, audio_file_name)         #used modded whisper\utils.py
    #         write_lrc (result, base_name)

def write_lrc(result: dict, base_name):
    lrc = f"{base_name}.lrc"
    with open(lrc, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], start=1):
            f.write(f"[{format_timestamp(segment['start'], always_include_hours=False, decimal_marker='.')}]{segment['text'].strip().replace('🎵', '')}\n")
            #TODO we may want to only close it out like this if the next segment's timestamp is a threshold later [or we're the last timestamp]
            #     and may want to only close it out a second later
            # and may want to not close it out if the end timestamp is the same as the begin for the next segment
            f.write(f"[{format_timestamp(segment['end'  ], always_include_hours=False, decimal_marker='.')}]\n")



def postprocess_files(path, is_dry_run=False):
    global audio_extensions
    global output_extensions

    for subdir, dirs, files in os.walk(path):                                                   # Traverse directory with all its subdirectories and files
        for filename in files:
            file_base, file_ext = os.path.splitext(filename)

            if file_ext not in output_extensions: continue                                      # Skip if not an output file

            # Check if filename contains a double extension with an audio file type
            second_base, second_ext = os.path.splitext(file_base)
            if second_ext not in audio_extensions: continue                                     # Skip if not a double extension with an audio file type

            new_filename = f"{second_base}{file_ext}"
            new_filepath = os.path.join(subdir, new_filename)

            # Check if a file with the new name already exists
            if os.path.isfile(new_filepath):
                #print(f'{Fore.YELLOW}{Style.BRIGHT}Cannot rename {filename} to {new_filename} because a file with the new name already exists.{Style.NORMAL}')
                continue

            old_filepath = os.path.join(subdir, filename)

            if is_dry_run:
                print(f'{Fore.CYAN}{Style.BRIGHT}Would rename {old_filepath} to {new_filepath}{Style.NORMAL}')
            else:
                print(f'{Fore.GREEN}{Style.BRIGHT}Renaming {old_filepath} to {new_filepath}{Style.NORMAL}')
                os.rename(old_filepath, new_filepath)


def format_timestamp(sec: float, always_include_hours: bool = False, decimal_marker: str = '.'):
    assert sec >= 0, "sorry, but we expected a timestamp that wasn't negative"
    ms = round(sec * 1000.0)
    hrs = ms // 3_600_000 ; ms -= hrs * 3_600_000
    min = ms //    60_000 ; ms -= min *    60_000
    sec = ms //     1_000 ; ms -= sec *     1_000
    hrs_marker = f"{hrs:02d}:" if always_include_hours or hrs > 0 else ""
    return f"{hrs_marker}{min:02d}:{sec:02d}{decimal_marker}{ms:03d}"




def main():
    if True:
        path = './'                                                         # Get the path from the command-line argument # default path to current directory
        #f len(sys.argv) > 1 and sys.argv[1] in ["do_it","doit","force","go"]:
        #if len(sys.argv) > 1 and sys.argv[1] not in ["dry_run","dry-run","dryrun","test","testing"]:
        if len(sys.argv) == 1:
            print(f"{Fore.GREEN}>Running in production mode.{Fore.BLUE}")
            process_files(path, is_dry_run=False)
            postprocess_files(path, is_dry_run=False)
        elif len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
            print(f"{Fore.GREEN}>Running on a single file{Fore.BLUE}")
            process_file_into_lrc(sys.argv[1], path, is_dry_run=False)
            postprocess_files    (             path, is_dry_run=False)
        elif len(sys.argv) > 1 and sys.argv[1] in ["postprocess","post_process","post-process","fixnames","fix_names","fix-names","fix-filenames","fix_filenames","fixfilenames"]:
            print(f"{Fore.GREEN}{Style.BRIGHT}>Postprocessing files...{Style.NORMAL}")
            postprocess_files(path, is_dry_run=False)
        else:
            print(f"{Fore.YELLOW}{Style.BRIGHT}>Running in dry-run mode. To run in production mode, re-run with the 'do_it' argument.{Fore.RED}")
            process_files(path, is_dry_run=True)
            print(f"{Fore.YELLOW}{Style.BRIGHT}>No post-proccesing was performed. Do it manually with the 'postprocess' argument.")

    claire.tock()








### Requires modifying whisper\utils.py to add this class:
###
### class WriteLRC(ResultWriter):
###     extension: str = 'lrc'
###
###     def write_result(self, result: dict, file: TextIO):
###         for i, segment in enumerate(result['segments'], start=1):
###             # write srt lines
###             print(
###                 f'[{format_timestamp(segment['start'], always_include_hours=False, decimal_marker='.')}]'
###                 f'{segment['text'].strip().replace('-->', '').replace('🎵','')}\n'
###                 f'[{format_timestamp(segment['end'  ], always_include_hours=False, decimal_marker='.')}]\n',
###                 file=file,
###                 flush=True,
###             )
###
###
### As well as adding:
###
###         'lrc': WriteLRC,
###
### to the writers list found in get_writer near the end of the utils.py file:
###
###     writers = {
###         'txt': WriteTXT,
###         'vtt': WriteVTT,
###         'srt': WriteSRT,
###         'tsv': WriteTSV,
###         'json': WriteJSON,
###         'lrc': WriteLRC,            # add this line
###     }
###
###
###
### Thought we were going to use this approach, but the whisper large model so far seems fine without splitting vocal tracks off. At least for Destroy Boys.
### Let's see if we think the same with more metaly stuff like Slayer though
### ### print('Importing spleeter separator...')
### from spleeter.separator import Separator
### print('Importing tempfile...')
### import tempfile
### def separated_vocals(filename):
###     # Use spleeter to separate into files in a temporary directory, and return a reference to the directory
###     separator = Separator('spleeter:2stems')
###     temp_dir = tempfile.TemporaryDirectory()
###     separator.separate_to_file(filename, temp_dir.name)
###     return temp_dir


if __name__ == "__main__":
    main()
