'''
        USAGE:
            set FILEMASK_AUDIO=*.mp3;*.flac <etc>               {if you don't set this, a default set of extensoins will be used}
            generate_thesem3u_and_allm3u_playlists_in_folder.py <folder we want to generate playlists in>

        DESCRIPTION:
            * Walks a given folder tree looking for audio files in all folders and subfolders
            1) Generates these.m3u playlists in every folder that has audio files.               Filenames, no path.
            2) Generates   all.m3u playlists in every folder that has audio files in subfolders. Full paths for each entry.

        EXTEND:
            This program could be warped to other objectives. For example:
                    set FILEMASK_AUDIO=*.gif;*.jpg;*.webp
            ...and you could generate lists of images.
'''
import os
import sys
import fnmatch
import colorama
import random
import stat
import threading
import time
try:
    import clairecjs_utils as claire
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path: sys.path.insert(0, script_dir)
    try:
        import clairecjs_utils as claire
    except ImportError:
        raise ImportError("Cannot find 'clairecjs_utils' module in site-packages or the local directory.")
from colorama import Fore, Style

DEBUG = False



def warn_playlist_problem(action, playlist, error):                                                # Warn about one bad playlist without aborting the whole tree
    print(f"\n{Fore.YELLOW}WARNING: Could not {action} {playlist}: {error}{Style.RESET_ALL}")



def remove_playlist_if_possible(playlist):                                                         # Delete one playlist, tolerating read-only or locked files
    if not os.path.exists(playlist): return True

    try:
        os.remove(playlist)
        return True
    except PermissionError:
        try:
            os.chmod(playlist, stat.S_IWRITE)
            os.remove(playlist)
            return True
        except OSError as error:
            warn_playlist_problem("delete", playlist, error)
            return False
    except OSError as error:
        warn_playlist_problem("delete", playlist, error)
        return False



def write_playlist_if_possible(playlist, filenames, use_absolute_paths=False):                      # Write one playlist, but keep going if Windows blocks it
    try:
        with open(playlist, 'w', encoding='utf-8') as f:
            for filename in filenames:
                if use_absolute_paths: f.write(os.path.abspath(filename) + '\n')
                else:                  f.write(filename + '\n')
        return True
    except PermissionError:
        try:
            if os.path.exists(playlist): os.chmod(playlist, stat.S_IWRITE)
            with open(playlist, 'w', encoding='utf-8') as f:
                for filename in filenames:
                    if use_absolute_paths: f.write(os.path.abspath(filename) + '\n')
                    else:                  f.write(filename + '\n')
            return True
        except OSError as error:
            warn_playlist_problem("write", playlist, error)
            return False
    except OSError as error:
        warn_playlist_problem("write", playlist, error)
        return False



def delete_existing_playlists(folder):                                                              # Function to delete existing playlist files
    these_playlist = os.path.join(folder, 'these.m3u')                                              # playlist for the files in current folder
    all_playlist   = os.path.join(folder, 'all.m3u'  )                                              # playlist for all files in all subfolders

    if os.path.exists(these_playlist):                                                              # playlist for the files in current folder
        if remove_playlist_if_possible(these_playlist):                                             #     (delete it before we make a new one)
            if DEBUG: print(f"{Fore.YELLOW}Deleted existing these.m3u in {folder}{Style.RESET_ALL}")#             (debug info)

    if os.path.exists(all_playlist):                                                                # playlist for all files in all subfolders
        if remove_playlist_if_possible(all_playlist):                                               #     (delete it before we make a new one)
            if DEBUG: print(f"{Fore.YELLOW}Deleted existing all.m3u in {folder}{Style.RESET_ALL}")  #             (debug info)



def create_playlists(folder, audio_extensions):                                                     # Function to create playlist files
    these_playlist = os.path.join(folder, 'these.m3u')                                              # playlist for the files in current folder
    all_playlist   = os.path.join(folder, 'all.m3u'  )                                              # playlist for all files in all subfolders

    these_files = []                                                                                # playlist for the files in current folder
    all_files   = []                                                                                # playlist for all files in all subfolders

    for root, dirs, files in os.walk(folder):                                                       # walk through all the folders in the folder the user has selected
        for file in files:                                                                          # find all the files in all those folders
            if any(fnmatch.fnmatch(file.lower(), pattern) for pattern in audio_extensions):         # see which ones are audio files
                if root == folder: these_files.append(                   file )                     # files in current folders go in the playlist for the files in current folder
                else:                all_files.append(os.path.join(root, file))                     # flies in      subfolders go in the playlist for all flies in all subfolders

    if these_files:                                                                                 # write these.m3u
        if write_playlist_if_possible(these_playlist, these_files):                                 # in utf-8 format
            if DEBUG: print(f"{Fore.GREEN}Created these.m3u in {folder}{Style.RESET_ALL}")          # with debug nfo

    if all_files:                                                                                   # write these.m3u
        if write_playlist_if_possible(all_playlist, all_files, use_absolute_paths=True):             # in utf-8 format
            if DEBUG: print(f"{Fore.GREEN}Created all.m3u in {folder}{Style.RESET_ALL}")            # with debug nfo


# Parallel thread for color-cycling during long beginning pause——to assuage program-hang-anxiety
tick_running = True                                                                                 # Global flag to control the tick thread
def tick_thread():
    while tick_running:
        claire.tick()
        time.sleep(0.05)                                                                            # Adjust sleep time for desired color cycle rate



def main():
    colorama.init()

    filemask_audio = os.getenv('FILEMASK_AUDIO')                                                    # Get audio extensions from environment variable or use default
    if filemask_audio: audio_extensions = filemask_audio.split(';')
    else:              audio_extensions = ["*.mp3", "*.wav",  "*.rm", "*.voc",   "*.au", "*.mid", "*.stm",  "*.mod", "*.vqf",
                                           "*.ogg", "*.mpc", "*.wma", "*.mp4", "*.flac", "*.snd", "*.aac", "*.opus", "*.ac3"]

    if len(sys.argv) != 2:                                                                          # Get folder path from command line argument
        print("Usage: generate_thesem3u_and_allm3u_playlists_in_folder.py <base folder name>")
        sys.exit(1)
    folder_path = sys.argv[1]

    if not os.path.exists(folder_path):                                                              # Check if folder exists
        print(f"Folder '{folder_path}' does not exist.")
        sys.exit(1)

    # Start a thread for color cycling with claire.tick()
    claire_thread = threading.Thread(target=tick_thread)
    claire_thread.start()

    # Iterate over the folder and its entire tree
    i = 1
    print(f"\n🔧🔧🔧 Generating all.m3u and these.m3u playlists in '{folder_path}'... 🔧🔧🔧")
    for root, dirs, files in os.walk(folder_path):
        if DEBUG: print(f"{Fore.CYAN}Processing folder: {root}{Style.RESET_ALL}")
        i += 1
        if (i % 5 == 0): print(random.choice([Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]) + "." + Style.RESET_ALL, end="")          #random-colored '.' every 5 folders
        delete_existing_playlists(root)
        create_playlists(root, audio_extensions)
    print(f"\n{Style.BRIGHT}{Fore.GREEN}🎂🎂🎂 all.m3u and these.m3u playlists generated! 🎂🎂🎂")


    global tick_running                                 # stop the color cycling
    tick_running = False                                # stop the color cycling
    claire_thread.join()                                # stop the color cycling and wait for the last tick() function to finish
    colorama.deinit()                                   #deinitialize ANSI color library

if __name__ == "__main__":
    main()
