import random
import os
import sys
import shutil


##### This goes through an m3u playlist file and, if it finds duplicate entries, ensures those entires are not next to each other.
##### The algorithm is VERY basic and inefficient, so we simply go through it a maximum of 50 times before quitting.


global VERBOSITY, FOLDER_NAMES_TO_IGNORE, SHUFFLE, LAST_COMMON, MAX_ATTEMPTS

SHUFFLE = True                                                                                                          # randomize the entire playlist first? True=Yes

MAX_ATTEMPTS = 50                                                                                                       # how many times to keep going through the file before giving up... It generally will be done after 2-3 no mat#####                     er what, anyway

FOLDER_NAMES_TO_IGNORE = ['', 'music', 'mp3', 'tv & movies & games']                                                    # don't swap entries simply from encountering *these* in the folder tree [must include '']
                        #'misc' may or may not be a good addition here. Currently thinking no.

           #0 no output
VERBOSITY = 1                                                                                                           # default verbosity level if not specified as 2nd command-line argument
           #1 file saving
           #2 basic output only, 'hunting' message
           #3 backup & are we shuffling?
           #4 file loading
           #5 swaps performed & consecutives-still-exist message
           #6 each common substring check


LAST_COMMON = set()





def load_m3u(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        lines = [line.strip() for line in file if line.strip() and not line.startswith('#')]                            # ignore comment lines
    if VERBOSITY >= 4: print(f"🟢 Loaded {len(lines)} lines from {filename}")
    return lines


def save_m3u(filename, lines):
    with open(filename, 'w', encoding='utf-8') as file:
        for line in lines: file.write(line + '\n')
    if VERBOSITY >= 1: print(f"🟢 Saved {len(lines)} lines to {filename}")


def get_folder(file):
    return os.path.dirname(file)


def get_common_substring(path1, path2):
    # Extract parts of the paths and find common substrings
    global LAST_COMMON
    folder_names_to_ignore = FOLDER_NAMES_TO_IGNORE
    #arts1 = path1.lower().split(os.sep); parts2 = path2.lower().split(os.sep)
    parts1 = [part for part in path1.lower().split(os.sep) if part not in folder_names_to_ignore]
    parts2 = [part for part in path2.lower().split(os.sep) if part not in folder_names_to_ignore]
    common_parts = set(parts1) & set(parts2)
    LAST_COMMON = common_parts
    return_value = False
    #eturn_value = any(part for part in common_parts if part.isalnum())
    if len(common_parts) > 0: return_value = True
    if VERBOSITY >= 6: print(f"\t\t🔧 get_common_substring()\n\t\t\tp1={path1}\n\t\t\tp2={path2}\n\t\t\t\tcommon={common_parts}      \t['set()' means none]\n\t\t\t\tretval={return_value}")
    return return_value


def reorder_playlist(lines):
    global SHUFFLE, MAX_ATTEMPTS, LAST_COMMON

    if SHUFFLE:
        if VERBOSITY >= 3: print("🟢 Shuffling playlist...", end="")
        random.shuffle(lines)
        if VERBOSITY >= 3: print("done!")
    else:
        if VERBOSITY >= 3: print("🔴 NOT shuffling playlist...")
    n = len(lines)

    #ax_attempts = n * 2  # Set a limit on the number of attempts to reorder
    max_attempts = MAX_ATTEMPTS
    attempts = 0

    if VERBOSITY >= 2: print("🟡 Hunting consecutive entries from same folder...")
    remaining_count = max_attempts
    while attempts  < max_attempts:
        if VERBOSITY >= 2: print(f"\t🔰 maximum {remaining_count} passes left")
        success = True
        for i in range(1, n):
            if get_common_substring(lines[i - 1], lines[i]):
                success = False
                if VERBOSITY >= 5: print(f"\t🧧Consecutive-duplicates still exist with:\n\t\t{lines[i-1]}\n\t\t{lines[i]}\n\t\t{LAST_COMMON}")
                break
        if success:
            if VERBOSITY >= 2: print(f"\t🟢 maximum 0 passes left 🎈[finished up early]🎈")
            return lines

        # Try to swap the problematic entry with a non-adjacent one
        for i in range(1, n):
            if get_common_substring(lines[i - 1], lines[i]):
                for j in range(i + 1,      n):
                #or j in range(i + (n/2), 2n???): want to do something like this, swap it halfway ... but would go over total.... so..... subtract length if over the total length? ... and run until ... 2n??! #TODO GOATGOAT 🐐
                    #f not get_common_substring(lines[i], lines[j]) and not get_common_substring(lines[i - 1], lines[j]):
                    if not get_common_substring(lines[i], lines[j]):
                        if VERBOSITY >= 5:
                            print(f"\t\t🔴Swapping entries 1 & 2:\n\t\t\t0: {lines[i-1]}\n\t\t\t1: {lines[i]}\n\t\t\t2: {lines[j]}\n\t\t\t",end="")
                            print(list(LAST_COMMON))
                        lines[i], lines[j] = lines[j], lines[i]
                        break
        attempts        += 1
        remaining_count -= 1
    return lines


def main(input_file):
    global VERBOSITY
    if len(sys.argv) > 2:
        VERBOSITY = int(sys.argv[2])
        if VERBOSITY > 0: print(f"🟡 Set verbosity level to {VERBOSITY}")
    backup_file = input_file + '.bak'                                                                                   # Backup the original file
    shutil.copyfile(input_file, backup_file)
    if VERBOSITY >= 3: print(f"🟢 Backup created: {backup_file}")

    lines = load_m3u(input_file)                                                                                        # Load, reorder, and save the playlist
    reordered_lines = reorder_playlist(lines)

    if len(reordered_lines) != len(lines):                                                                              # Ensure the reordered list has the same length as the original
        print("🛑🛑🛑🛑🛑🛑🛑 Error: The reordered playlist length does not match the original length. 🛑🛑🛑🛑🛑🛑🛑")
        return

    save_m3u(input_file, reordered_lines)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("🌟 Usage: python reorder_playlist.py <input_file> [optional verbosity level 0-6]\n")
        print("🌟 Will reorder playlist/filelist to try to prevent consecutive songs/files from the same album/folder\n")
        print("🌟 Playlst/filelist original will be renamed to .bak")
    else:
        input_file = sys.argv[1]
        main(input_file)
