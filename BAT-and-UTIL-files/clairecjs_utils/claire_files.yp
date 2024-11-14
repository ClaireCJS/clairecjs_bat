#TO USE: import clairecjs_utils as claire
import os
import re
import shutil
from colorama import Fore, init
init()



DEBUG_RENAME = False





def rename(filename, new_filename):
    """
    A renamer that will never overwrite an existing file, instead adding "-1", "-2", "-3", etc, to the filename until it is unique

    Returns the new name as a return value

    filename_we_actually_renamed_it_to = rename(before_rename_filename, intended_after_rename_filename)

    """
    global DEBUG_RENAME
    if DEBUG_RENAME: print(f"* called: rename({filename},{new_filename})")
    if not os.path.exists(filename): raise FileNotFoundError(f"{filename} does not exist")

    return_value = ""

    base_dir, base_filename      = os.path.split   (new_filename)
    new_filename_root, extension = os.path.splitext(base_filename)

    counter = 1                                                                                                             # Handle duplicate filenames
    while os.path.exists(new_filename):
        new_filename = f"{new_filename_root}-{counter}{extension}"
        new_filename = os.path.join(base_dir, new_filename)
        return_value = new_filename
        counter      += 1

    if DEBUG_RENAME: print(f"{Fore.GREEN}- About to try to rename {filename} to {new_filename}...")

    #ry:                    os.rename(filename, new_filename)
    try:                    shutil.move(filename, new_filename)
    except FileExistsError: print(f"{Fore.RED}Failed to rename file. Destination file already exists: {new_filename}") ; return ""
    except OSError as e:    print(f"{Fore.RED}Failed to rename file: {e}")                                             ; return ""
    return return_value



def strip_ansi_from_file(filename):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    with open(filename, 'r') as file:
        log_content          = file.read()
        log_content_stripped = ansi_escape.sub('', log_content)
    with open(filename, 'w') as file: file.write(log_content_stripped)

