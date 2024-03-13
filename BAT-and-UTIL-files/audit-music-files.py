import os
import glob
import time
from mutagen import File
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import HeaderNotFoundError
from pathlib import Path
from itertools import count
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init


## This looks for files that don't have ReplayGain tags, or which are set to read-only, and generates a fix script.

supported_extensions = ('.mp3', '.flac')                                                                    #the only 2 extensions that support ReplayGain tags which I use
rg_fix_bat           = "RG_fix.bat"
rg_yes_file          = "RG_yes.dat"
rg_no_file           = "RG_no.dat"
rg_yes               = []
rg_no                = []
blink_on             = "\033[6m"
blink_off            = "\033[25m"
underline_on         = "\033[4m"
underline_off        = "\033[24m"

def backup_existing_file(file_path):
    if os.path.exists(file_path):
        for i in count(0):
            backup_path = f"{file_path}.bak.{i:03d}"
            if not os.path.exists(backup_path):
                os.rename(file_path, backup_path)
                break

def process_file(file_path):
    abs_file_path = os.path.abspath(file_path)
    try:
        audio = File(file_path)

        # Check if file is erroneously read-only
        if not os.access(file_path, os.W_OK):
            with open(rg_fix_bat, "a") as f: f.write(f"attrib -r \"{abs_file_path}\"\n")

        # Check for presence of missing ReplayGainTags
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
    except HeaderNotFoundError as e:
        print(f"*** Error processing file: {abs_file_path}\n")
        print(f"\nException in {abs_file_path}: {str(e)}")
        print("File might be corrupt/malformed. Skipping: " + abs_file_path)
        return(False, abs_file_path)
    except (ID3NoHeaderError, Exception) as e:
        rg_no.append(abs_file_path)
        print(f"Error processing file: {abs_file_path}\nException: {str(e)}")
        return(False, abs_file_path)

def process_music_files():
    file_paths = [path for ext in supported_extensions for path in glob.glob(f"**/*{ext}", recursive=True)]

    total_files = len(file_paths)
    file_count = 0


    #with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(process_file, file_path): file_path for file_path in file_paths}
        for future in as_completed(future_to_file):
            file_count += 1
            if file_count % 20 == 0 or file_count == total_files:
                percentage = "{:.2f}".format((file_count / total_files) * 100)
                if percentage == "100.00": blink = blink_off
                else                     : blink = blink_on
                print(f"\r{Fore.GREEN}⚙️ {blink}Auditing audio files:{blink_off} {Style.NORMAL}{Fore.GREEN}{Style.BRIGHT}{percentage}{Style.NORMAL}%", end='', flush=True)
            result = future.result()
            if result is not None:
                has_rg, data = result
                if has_rg: rg_yes.append(data)
                else:      rg_no .append(data)

    return rg_yes, rg_no



def main():
    backup_existing_file(rg_yes_file)
    backup_existing_file(rg_no_file)
    backup_existing_file(rg_fix_bat)

    start_time = time.monotonic()
    rg_yes, rg_no = process_music_files()
    end_time = time.monotonic()

    with open(rg_yes_file, 'w', encoding='utf-8') as f: f.write('\n'.join(rg_yes))
    with open(rg_no_file , 'w', encoding='utf-8') as f: f.write('\n'.join(rg_no ))

    #make bat file to fix it with our argt [add-replaygain-tags] script
    if rg_no:
        rg_no_folders = set(os.path.dirname(file) for file in rg_no)
        with open(rg_fix_bat, 'w', encoding='utf-8') as f:
            f.write('rem Use this script to fix files with missing replaygain tags\n\n')
            for folder in rg_no_folders:
                f.write(f'pushd "{folder}"\n')
                f.write(f'call add-replay-gain-tags\n')
                f.write('popd\n')
        #print(f"Created {rg_fix_bat} with backup rules.")

    elapsed_time = end_time - start_time
    print(f"\n✔️ {Style.BRIGHT}{underline_on}{len(rg_yes) + len(rg_no)}{underline_off}{Style.NORMAL} files audited in {Style.BRIGHT}{underline_on}{elapsed_time:.2f}{underline_off}{Style.NORMAL} seconds")

if __name__ == "__main__":
    main()
