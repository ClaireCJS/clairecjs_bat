import os
import sys
import fnmatch
import colorama
import random
import threading
import time
import clairecjs_utils as claire
from colorama import Fore, Style

DEBUG = False

# Function to delete existing playlist files
def delete_existing_playlists(folder):
    these_playlist = os.path.join(folder, 'these.m3u')
    all_playlist = os.path.join(folder, 'all.m3u')

    if os.path.exists(these_playlist):
        os.remove(these_playlist)
        if DEBUG:
            print(f"{Fore.YELLOW}Deleted existing these.m3u in {folder}{Style.RESET_ALL}")

    if os.path.exists(all_playlist):
        os.remove(all_playlist)
        if DEBUG:
            print(f"{Fore.YELLOW}Deleted existing all.m3u in {folder}{Style.RESET_ALL}")

# Function to create playlist files
def create_playlists(folder, audio_extensions):
    these_playlist = os.path.join(folder, 'these.m3u')
    all_playlist = os.path.join(folder, 'all.m3u')

    these_files = []
    all_files = []

    for root, dirs, files in os.walk(folder):
        for file in files:
            if any(fnmatch.fnmatch(file.lower(), pattern) for pattern in audio_extensions):
                if root == folder:
                    these_files.append(file)
                else:
                    all_files.append(os.path.join(root, file))

    if these_files:
        with open(these_playlist, 'w', encoding='utf-8') as f:
            for filename in these_files:
                f.write(filename + '\n')
        if DEBUG:
            print(f"{Fore.GREEN}Created these.m3u in {folder}{Style.RESET_ALL}")

    if all_files:
        with open(all_playlist, 'w', encoding='utf-8') as f:
            for filename in all_files:
                f.write(os.path.abspath(filename) + '\n')
        if DEBUG:
            print(f"{Fore.GREEN}Created all.m3u in {folder}{Style.RESET_ALL}")


# Let's add some color-cycling during the long pause at the beginning
tick_running = True                                                                             # Global flag to control the tick thread
def tick_thread():
    while tick_running:
        claire.tick()
        time.sleep(0.05)  # Adjust sleep time for desired tick rate



# Main function
def main():
    colorama.init()

    # Get audio extensions from environment variable or use default
    filemask_audio = os.getenv('FILEMASK_AUDIO')
    if filemask_audio:
        audio_extensions = filemask_audio.split(';')
    else:
        audio_extensions = ["*.mp3", "*.wav", "*.rm", "*.voc", "*.au", "*.mid", "*.stm", "*.mod", "*.vqf",
                            "*.ogg", "*.mpc", "*.wma", "*.mp4", "*.flac", "*.snd", "*.aac", "*.opus", "*.ac3"]

    # Get folder path from command line argument
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder>")
        sys.exit(1)

    folder_path = sys.argv[1]

    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        sys.exit(1)


    # Start a thread for claire.tick()
    claire_thread = threading.Thread(target=tick_thread)
    claire_thread.start()

    # Iterate over the folder and its entire tree
    i = 1
    #print(f"\n{Style.BRIGHT}{Fore.CYAN}🛠🛠🛠 Generating all.m3u and these.m3u playlists! 🛠🛠🛠")
    print(f"\n🔧🔧🔧 Generating all.m3u and these.m3u playlists in '{folder_path}'! 🔧🔧🔧")
    for root, dirs, files in os.walk(folder_path):
        if DEBUG: print(f"{Fore.CYAN}Processing folder: {root}{Style.RESET_ALL}")
        i += 1
        if (i % 5 == 0): print(random.choice([Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN]) + "." + Style.RESET_ALL, end="")
        delete_existing_playlists(root)
        create_playlists(root, audio_extensions)

    # stop color cycling
    global tick_running
    tick_running = False
    claire_thread.join()  # Wait for the tic

    print(f"\n{Style.BRIGHT}{Fore.GREEN}🎂🎂🎂 all.m3u and these.m3u playlists generated! 🎂🎂🎂")

    colorama.deinit()


if __name__ == "__main__":
    main()
