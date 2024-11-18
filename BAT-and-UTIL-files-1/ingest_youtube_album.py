"""
    Ingest downloaded youtube album
    tag it, move it, rename it
    assume info.json + mp3s present

    if it does rename any file, it will cleanse any emoji and unicode and invalid filename characters in it using my fix_unicode_filenames library
"""
import os
import re
import sys
import json
import time
import shutil
import msvcrt
import eyed3
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PromptStyle
from eyed3.id3.frames import TextFrame
from eyed3.id3.frames import UserUrlFrame
from colorama import Fore, Back, Style, init
import fix_unicode_filenames
#pylint: disable=C0305















DEBUG_SANITIZE_TEXT                    = False
DEBUG_COMMENT_NEWLINES                 = False
DEBUG_FILENAME_SPLITTING               = False
DEBUG_FILE_RENAMING                    = False
DEBUG_VIEW_TAG_VALUES_BEFORE_INSERTION = False
DEBUG_TAGGING_CRASHES                  = False























LOG_FILE = "_ingest.log"
COMPANION_FILES = ["info.json", "README.txt", LOG_FILE]














def log_print(text,end="\n"):
    print(text,end=end)
    with open(LOG_FILE, 'a', encoding="utf-8") as file:
        file.write(text + '\n')

def debug_char(description_new):
    log_print(f"\t{Fore.CYAN}newline in description_new?", end="")
    log_print("\\n" in description_new)                                  # Check if \n exists in the original string
    for char in description_new: log_print(f'\t"{char}": {ord(char)}')   # Print ASCII value of each character




def fix_filename_case(filename):
    """
    This version of the function capitalizes the first character of each word, while leaving the rest of each word in its original case.
    """
    text = ' '.join(word[0].upper() + word[1:] if word else '' for word in filename.split())
    return text


def preprocess_filenames(directory):
    log_print(f'{Fore.RED}{Style.BRIGHT}*** Pre-processing filenames...{Style.NORMAL}')

    mp3_file_count = 0
    guessed_orig_artist = ""
    for filename in os.listdir(directory):
        if filename.endswith('.mp3'):
            mp3_file_count += 1
            temp_orig_artist = get_artist_from_filename(filename)
            if temp_orig_artist and not guessed_orig_artist: guessed_orig_artist = temp_orig_artist

    if mp3_file_count == 1:
        pass                #don't rename files if there's just one
    else:
        for filename in os.listdir(directory):
            new_filename = filename                                                                                                    #initial placeholder value
            if filename.endswith('.mp3'):
                log_print(f'{Fore.YELLOW}{Style.BRIGHT}  * Pre-process: {Style.NORMAL}' + filename, end='')

                match = re.match(r'(.*\d{3} )\d{1,3}-?(.*.mp3)', filename)                                                             # Match the filename pattern using a regular expression
                if match:
                    new_filename = match.group(1) + match.group(2)

                if new_filename != filename:                                                                                           # If the filename has changed, rename the file
                    log_print(f'\n\t- {Fore.WHITE              }Old name: {Fore.LIGHTBLACK_EX}{    filename}')
                    log_print(  f'\t- {Fore.GREEN}{Style.BRIGHT}New name: {Style.NORMAL      }{new_filename}')
                    os.rename(os.path.join(directory, filename), os.path.join(directory,       new_filename))
                else:
                    log_print(f'{Fore.GREEN}...Name unchanged.')

    return mp3_file_count, guessed_orig_artist


def show_audio_files_in_rainbow(directory):
    log_print(f"{Fore.CYAN}{Style.BRIGHT}Here are our filenames:{Style.NORMAL}\n")
    color_list = [Fore.LIGHTRED_EX, Fore.RED, Fore.YELLOW, Fore.LIGHTYELLOW_EX, Fore.LIGHTGREEN_EX, Fore.GREEN, Fore.CYAN, Fore.LIGHTBLUE_EX, Fore.BLUE, Fore.MAGENTA, Fore.LIGHTMAGENTA_EX]
    files = os.listdir(directory)
    mp3_files = [f for f in files if f.endswith('.mp3')]
    num_files = len(mp3_files)
    num_colors = len(color_list)
    if num_files: color_step = num_colors / num_files
    else:         color_step = 1
    for i, file in enumerate(mp3_files):
        color_index = int(i * color_step)                                                                    #changed int to round and afraid of ArrayOutOfBound exceptions
        if color_index >= len(color_list): color_index=len(color_list)-1
        color = color_list[color_index]
        log_print(f"{color}{file}")
    log_print(f"{Fore.YELLOW}{Style.BRIGHT}")



def load_json_file(file):
    with open(file, 'r', encoding='utf-8') as our_json:
        data = json.load(our_json)
    return data



def load_json_data(our_json_file):
    if not os.path.isfile(our_json_file):
        json_files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.json')]              # List all JSON files in the current directory
        if not json_files:
            raise FileNotFoundError(f"Error: No JSON file found. Looking for: {our_json_file}")
            #sys.exit(1)

        if len(json_files) > 1:                                                                             # If multiple JSON files are found, load the most recently modified one - mismatch is still possible, but less likely, and not super consequential
            latest_file = max(json_files, key=os.path.getmtime)
            print(f"Multiple JSON files found. Loading the most recent file: {latest_file}")
            our_json_file = latest_file
        elif len(json_files) == 1:
            our_json_file = json_files[0]

    data = load_json_file(our_json_file)                                                                    # Load the JSON file
    return data





def get_artist_from_filename(filename):
    orig_artist = ""
    match = re.match(r"(.*?)'s", filename)
    if match: orig_artist = match.group(1)
    else:
        match = re.match(r"(.*?) - .* \[.*\]", filename)
        if match: orig_artist = match.group(1)
        else:     orig_artist = ""
    return orig_artist




def rename_tag_move_incoming_youtube_album(directory, our_json_file):
    global DEBUG_COMMENT_NEWLINES, DEBUG_VIEW_TAG_VALUES_BEFORE_INSERTION
    log_print(f"{Fore.GREEN}{Style.BRIGHT}Processing directory: {directory}{Style.NORMAL}\n\n{Fore.YELLOW}{Style.BRIGHT} ")
    num_mp3s, guessed_orig_artist = preprocess_filenames(directory)                                                          # fix filenames first
    data = load_json_data(our_json_file)                                                                                     # get values
    show_audio_files_in_rainbow(directory)                                                                                   # show files to user
    artist      = data.get('album_artist') or data.get('artist' ) or data.get('creator') or data.get('uploader'   )
    year        = data.get('release_year') or data.get('release') or data.get('date'   ) or data.get('upload_date')
    album_name  = data.get('title'  )    # it also could be a song name                                                      # there is no album-specific field it seems
    publisher   = data.get('uploader'    )
    description = data.get('description' )
    url         = data.get('webpage_url' )

    # input/scrub values manually
    #DEBUG: print(f"year is {year}")
    if isinstance(year,int): year=str(year)
    if year: year = year[:4]
    album_name_filename = ""
    genre               = fix_and_edit_value("genre"                      , "Chiptunes"                  )
    orig_artist         = fix_and_edit_value("original artist"            , guessed_orig_artist          ,fix_default_value_for_filenames=True)
    album_name          = strip_artist_from_album_or_filename(album_name  , orig_artist,num_mp3s=num_mp3s)                                                                                               #remove "Metallica's " from "Metallica's Master Of Puppets"
    album_name          = fix_and_edit_value("album title in our tag"     , fix_filename_case(album_name),fix_default_value_for_filenames=True)
    artist              = fix_and_edit_value("artist name in our tag"     , fix_filename_case(  artist  ),fix_default_value_for_filenames=True)
    album_name_filename = fix_and_edit_value("album title in our filename", album_name                   ,fix_default_value_for_filenames=True, mode="file", prompt_only_if_unicode_was_changed=True)    #we still do album even if it's a single song, so don't bother checking of mp3_count>1
    artistname_filename = fix_and_edit_value("artist name in our filename", artist                       ,fix_default_value_for_filenames=True, mode="file", prompt_only_if_unicode_was_changed=True)

    # output scrubbed values
    log_print(f"{Fore.GREEN}{Style.NORMAL}", end="")
    log_print(f"{Fore.GREEN}{Style.NORMAL}Artist Name 1: {Style.BRIGHT}{artist}")
    log_print(f"{Fore.GREEN}{Style.NORMAL}Artist Name 2: {Style.BRIGHT}{artistname_filename}\n")
    log_print(f"{Fore.GREEN}{Style.NORMAL} Album Name 1: {Style.BRIGHT}{album_name}")
    log_print(f"{Fore.GREEN}{Style.NORMAL} Album Name 2: {Style.BRIGHT}{album_name_filename}")
    log_print(f"{Fore.GREEN}{Style.NORMAL}\nYear: {Style.BRIGHT}{year}")

    # make our new folder
    our_new_folder = os.path.join(artistname_filename, f"{year} - {album_name_filename}")
    if num_mp3s > 1: os.makedirs(our_new_folder, exist_ok=True)

    # tag and move our songs
    process_files(directory,artist=artist,year=year,album_name=album_name,publisher=publisher,genre=genre,description=description,url=url,orig_artist=orig_artist,our_new_folder=our_new_folder,num_mp3s=num_mp3s)

    # do all the other cleanup/post stuff
    if num_mp3s > 1:
        create_bat_file(our_new_folder)
        remove_leading_zeroes(our_new_folder)
        move_companion_files(directory, our_new_folder)
        log_print(f"\n{Fore.GREEN}{Style.NORMAL}* Successfully tagged downloaded album.")
        log_print(  f"{Fore.GREEN}{Style.NORMAL}* Successfully  moved downloaded album to: {our_new_folder}\n\n")
    if num_mp3s == 1:
        log_print(f"\n{Fore.GREEN}{Style.NORMAL}* Successfully tagged & processed song." +                "\n\n")

    return our_new_folder








def fix_and_edit_value(key, value, mode="tag", prompt_only_if_unicode_was_changed=None, fix_default_value_for_filenames=False):                #pylint: disable=C0103
    original_value = value
    log_print("")

    custom_style = PromptStyle([
        (   'prompt'  , 'fg:ansibrightyellow'),
        (    'text'   , 'fg:ansibrightyellow'),
        ('user_input' , 'fg:ansibrightcyan'  ),
    ])
    session = PromptSession(style=custom_style)

    if mode == "file": default_value = fix_unicode_filenames.convert_a_filename(value,silent_if_unchanged=True)
    else:              default_value = value

    do_prompt = True
    if prompt_only_if_unicode_was_changed is True:
        do_prompt = bool(default_value != original_value)

    if do_prompt:
        clear_keyboard_buffer()
        if fix_default_value_for_filenames: default = fix_unicode_filenames.convert_a_filename(default_value,silent=True)
        else:                               default =                                        default_value

        user_input = session.prompt([('class:prompt', f'>>Please enter new value for {key}:\n'),
                                     ('class:user_input', '')], default=default)
        return user_input if user_input else default_value

    return default_value


def clear_keyboard_buffer():
    while msvcrt.kbhit(): msvcrt.getch()



def rename_with_companion_rename(filename_old, filename_new, directory="."):
    filename_old, ext_old = os.path.splitext(os.path.basename(filename_old))                              # pylint: disable=W0612
    filename_new, ext_new = os.path.splitext(os.path.basename(filename_new))                              # pylint: disable=W0612
    for filename in os.listdir(directory):
        basename_file, ext_file = os.path.splitext(filename)                                              # pylint: disable=W0612
        if basename_file.startswith(filename_old):
            old_filepath = os.path.join(directory, filename)
            new_filepath = os.path.join(directory, filename.replace(filename_old, filename_new, 1))
            os.rename(old_filepath, new_filepath)
            dim = '\033[2m'
            log_print(f"{dim}                 Renamed companion: {old_filepath}")                              # Print the old and new filepaths
            log_print(f"{dim}                                To: {new_filepath}{Fore.RESET}")                  # Print the old and new filepaths


def process_files(directory,artist="",year="",album_name="",publisher="",genre="",description="",url="",orig_artist="",our_new_folder="",num_mp3s=123456):                   #pylint: disable=R0913,R0912,R0915
    global DEBUG_VIEW_TAG_VALUES_BEFORE_INSERTION, DEBUG_FILENAME_SPLITTING, DEBUG_FILE_RENAMING, DEBUG_TAGGING_CRASHES

    our_new_folder=our_new_folder.strip()
    for file in os.listdir(directory):
        if not file.endswith('.mp3'): continue
        log_print(f"\n{Fore.CYAN}{Style.BRIGHT}* Processing file: {file}{Style.NORMAL}")

        ##### GET VALUES:

        # split values from filename - a mess because it was founded on chatgpt code that wasn't great and just keeps getting fixed as new filenames break it
        already_processed = False
        parts = re.split(r' - (?=\d)', file, maxsplit=1)                                      # New method 20230711
        if len(parts) != 2:
            if re.match(r'^\d+_', file):                                                      # Processed file format: XX_Name
                already_processed = True
                #parts = [album_name, file[3:]]
                parts = file.rsplit( '_' , 1)
            else:                                                                             # Original file format: Album - XX Name
                already_processed = False
                parts = file.rsplit(' - ', 1)
        if len(parts) != 2:                                                                   # got backed into a corner here, some of this part was poorly written by chatgpt
            parts = ["", file]
        if DEBUG_FILENAME_SPLITTING: log_print(f"\n{Fore.YELLOW}{Style.BRIGHT}* parts(b12)==== {Fore.CYAN}{Style.NORMAL}{parts}")
        if len(parts) != 2:
            log_print(f"{Fore.RED}Warning: Skipping file due to not being able to split correctly: {file} [parts={parts}]")
            time.sleep(5)
            continue
        if DEBUG_FILENAME_SPLITTING: log_print(f"\n{Fore.YELLOW}{Style.BRIGHT}* parts(c23)==== {Fore.CYAN}{Style.NORMAL}{parts}")

        youtube_video_title_string = parts[0]                                                 # unused
        #f num_mp3s > 1: chapter_id_title = "0" + parts[1]                                    # Adding back the "0"
        #lse:            chapter_id_title =       parts[1]                                    # ...(or not)
        chapter_id_title = parts[1]
        if DEBUG_VIEW_TAG_VALUES_BEFORE_INSERTION: log_print(f"\t{Fore.MAGENTA}chapter_id_title[55]={chapter_id_title},already_processed={already_processed}")                                                                                              #chapter_id_title[55]=Where is My Mind but with the SM64 Soundfont [ePL44jEEOCQ].mp3,already_processed=False
        chapter_num="1"
        if not already_processed:                                                             # Now, we split chapter_id_title into chapter_num, title and youtube_id
            if num_mp3s == 1:
                rest = chapter_id_title
                if DEBUG_FILENAME_SPLITTING: log_print(f"\n\t{Fore.RED}{Back.BLUE}{Style.BRIGHT}* chap,rest[YY]={Fore.CYAN}{Back.BLACK}{Style.NORMAL}chapter_num={chapter_num},rest={rest}")
                #title, youtube_id = rest.rsplit(" [", 1)                                     #* chap,rest[YY]=chapter_num=Where,rest=is My Mind but with the SM64 Soundfont [ePL44jEEOCQ].mp3
                #youtube_id  = youtube_id.rstrip(']')
            else:
                if " " in chapter_id_title: chapter_num, rest = chapter_id_title.split(" ", 1)
                if DEBUG_FILENAME_SPLITTING: log_print(f"\n\t{Fore.YELLOW}{Style.BRIGHT}* chap,rest[YY]= {Fore.CYAN}{Style.NORMAL}chapter_num={chapter_num},rest={rest}")
            if "[" in rest and "]" in rest:
                title, youtube_id = rest.rsplit(" [", 1)
                youtube_id = youtube_id.rstrip(']')
            else:
                title = rest.strip(' ')
                youtube_id = ""
        if num_mp3s == 1:     chapter_num = "1"
        if already_processed: chapter_num, title = parts[0], parts[1]


        print(f"{Fore.CYAN}  - Chapter #{chapter_num}: {chapter_id_title} [already_processed={already_processed}]")

        ##### INSERT TAGS :
        if DEBUG_VIEW_TAG_VALUES_BEFORE_INSERTION: log_print(f"\t{Fore.MAGENTA}year={year},#={Style.BRIGHT}{chapter_num}{Style.NORMAL},title[xx]={title},youtube_video_title_string={youtube_video_title_string},chapter_id_title={chapter_id_title},youtube_id={youtube_id},orig_artist={orig_artist}")

        #og_print(f"{Fore.RED}{Style.BRIGHT}  ************ Updating Tags!!! (file={file}) ************{Fore.BLACK}{Style.NORMAL}")
        log_print(f"{Fore.CYAN}{Style.NORMAL}               ...Updating Tags!{Fore.BLACK}{Style.NORMAL}")
        audiofile = eyed3.load(file)
        if DEBUG_TAGGING_CRASHES: log_print(f"{Fore.RED}{Style.BRIGHT}      * audiofile loaded * {Fore.BLACK}{Style.NORMAL}")

        if not audiofile.tag: audiofile.initTag()
        if DEBUG_TAGGING_CRASHES: log_print(f"{Fore.RED}{Style.BRIGHT}      * tag initialized * {Fore.BLACK}{Style.NORMAL}")

        # handle comment
        description_old_4print = description.replace('\r','\\r').replace('\n','\\n')
        description_new = sanitize_text(description)
        if DEBUG_COMMENT_NEWLINES: log_print(f"\t\t{Fore.RED}{Style.NORMAL}description_old_4print={description_old_4print}{Fore.YELLOW}"); debug_char(description_new)

        description_new = re.sub(  '\n', '\r\n', description)
        description_new_4print = description_new.replace(r'\r','\\r'  ).replace('\n','\\n')
        if DEBUG_COMMENT_NEWLINES: log_print(f"\t\t{Fore.YELLOW}{Style.NORMAL}description_new_4print={description_new_4print}{Fore.YELLOW}" + f"\t{Fore.YELLOW}{Style.NORMAL}description_new="  + f"{description_new}"  + f"{Fore.YELLOW}")

        if description_new: audiofile.tag.comments.set(description_new)
        if DEBUG_TAGGING_CRASHES: log_print(f"{Fore.RED}{Style.BRIGHT}      * comment ready * {Fore.BLACK}{Style.NORMAL}")

        #handle the rest
        if orig_artist: set_artist_tags(audiofile=audiofile, artist=artist, orig_artist=orig_artist)            #handles several tags
        if url:         set_url_tag    (audiofile=audiofile, url=url)                                           #handles just one tag
        if genre:       audiofile.tag.genre      = sanitize_text(genre      ) #.decode('utf-8')
        if artist:      audiofile.tag.artist     = sanitize_text(artist     ) #.decode('utf-8')
        if year:        audiofile.tag.album_date = sanitize_text(year       ) #.decode('utf-8')
        if chapter_num: audiofile.tag.track_num  = sanitize_text(chapter_num) #.decode('utf-8')
        #todo remove this comment print(f"about to sanitize title {title}!")
        if title:       audiofile.tag.title      = sanitize_text(title      ) #.decode('utf-8')
        if publisher:   audiofile.tag.publisher  = sanitize_text(publisher  ) #.decode('utf-8')
        if num_mp3s > 0:                                                                                        #set to 1 to not tag album in single downloads, but we decided to include album in single downloads -- much like how a single is titled after the song it is
            if album_name: audiofile.tag.album   = sanitize_text(album_name ) #.decode('utf-8')
        if DEBUG_TAGGING_CRASHES: log_print(f"{Fore.RED}{Style.BRIGHT}      * about to save * {Fore.BLACK}{Style.NORMAL}")
        audiofile.tag.save(version=eyed3.id3.ID3_V2_3)                                                          #v2.3 tags play well with others. 2.4 don't. 2.4 was incompatible with metamp3.exe, for one thing
        if DEBUG_TAGGING_CRASHES: log_print(f"{Fore.RED}{Style.BRIGHT}      * saved * {Fore.BLACK}{Style.NORMAL}")


        ##### ACTUALLY MOVE / RENAME THE FILE(s):

        if num_mp3s == 1:
            log_print("\n")
            new_name = f"{artist} - {title}"
            if DEBUG_FILE_RENAMING: log_print(f"\n{Fore.YELLOW}{Style.BRIGHT}* new_name[a11]= {Fore.CYAN}{Style.NORMAL}{new_name}")
            if orig_artist is not artist:
                new_name = f"{new_name} (by {orig_artist})"
                #NO! new_name = strip_artist_from_album_or_filename(new_name,orig_artist)
            new_name = f"{new_name}.mp3"
            new_name = fix_unicode_filenames.convert_a_filename(new_name,silent=False)
            log_print(f"{Fore.CYAN}{Style.BRIGHT}* Renaming file: {Fore.CYAN}{Style.NORMAL}{file}")
            log_print(f"{Fore.CYAN}{Style.BRIGHT}             To: {Fore.BLUE}{Style.BRIGHT}{new_name}")
            rename_with_companion_rename(file, new_name, directory=directory)
        else:
            new_file  = f"{chapter_num}_{title}"
            base, ext = os.path.splitext(new_file)                       # Split the filename and extension
            base      = fix_filename_case(base)                          # Capitalize each word in filename, but not in extension
            ext       = ext.lower()
            if not ext: ext = ".mp3"
            new_file  = f"{base}{ext}"
            new_path  = os.path.join(our_new_folder, new_file)
            log_print(f"{Fore.BLUE}{Style.BRIGHT}\t* Renaming and moving file to: {new_path}")
            shutil.move(os.path.join(directory, file), new_path)





def sanitize_text(text):
    global DEBUG_SANITIZE_TEXT
    if not text: text=""
    if DEBUG_SANITIZE_TEXT: log_print(f"{Fore.RED}Debug: Text before sanitizing: {text}")   # Debug print
    if isinstance(text, int):
        text = str(int)
    if isinstance(text, bytes):
        try:
            text = text.decode('utf-8')                                             # Try to decode as utf-8
        except UnicodeDecodeError:
            text = text.decode('utf-8', 'replace')                                  # If error, decode and replace invalid characters
    # Ensure that the text is always encoded as UTF-8
    text = text.encode('utf-8').decode('utf-8')                                     # Encode and immediately decode to ensure text is a string
    if DEBUG_SANITIZE_TEXT: log_print(f"{Fore.GREEN}Debug: Text after sanitizing: {text}")    # Debug print
    return text





def set_url_tag(audiofile="", url="", filepath=""):
    if audiofile == "" and filepath != "": audiofile = eyed3.load(filepath)         # if passed filename instead of audiofile object, create audiofile object
    if audiofile is None: sys.exit(f"Could not open {filepath}")                    # error checking: file should exist
    if url       ==  "" : sys.exit( "Need URL!"                )                    # error checking:  URL should exist
    if audiofile.tag is None: audiofile.initTag()                                   # Create a UserUrlFrame object: ID3 tag: initialize
    url_frame = UserUrlFrame()                                                      # Create a UserUrlFrame object: URL tag: initialize
    url_frame.url = url                                                             # Create a UserUrlFrame object: URL tag: set the URL
    audiofile.tag.frame_set[b"WXXX"] = url_frame                                    # Create a UserUrlFrame object: ID3 tag: insert URL tag
                                                                                    # don't save the tag when we are done because we do that in our calling function



def set_artist_tags(audiofile="", artist="", orig_artist="", filepath=""):          # also sets 'composer' tag to the same value as 'original artist'
    if audiofile == "" and filepath != "": audiofile = eyed3.load(filepath)         # if passed filename instead of audiofile object, create audiofile object
    if audiofile     is None: sys.exit(f"Could not open {filepath}")                # error checking:     file    should exist
    if orig_artist   ==  "" : sys.exit( "Need original artist!"    )                # error checking: orig_artist should exist
    if      artist   ==  "" : sys.exit( "Artist!"                  )                # error checking:      artist should exist

    if audiofile.tag is None: audiofile.initTag()                                   # Create a OriginalArtist tag: ID3 tag: initialize

    if orig_artist != "": composer_artist = orig_artist                             #\___if the original artist exists (is not nothing), then we want our composer set to that...
    else                : composer_artist = artist                                  #/   ...otherwise, we want our composer set to the artist

    frames_to_add = { b"TOPE" : orig_artist    ,                                    # original artist
                      b"TPE2" : artist         ,                                    # album artist
                      b"TCOM" : composer_artist}                                    # composer

    for frame_type, value_to_use in frames_to_add.items():
        frame = TextFrame(frame_type, value_to_use)                                 # Create a <frametype> tag: <frametype> tag: initialize with value
        audiofile.tag.frame_set[frame_type] = frame                                 # Create a <frametype> tag: ID3 tag: insert <frametype> tag
                                                                                    # don't save the tag when we are done because we do that in our calling function

def create_bat_file(our_new_folder):
    log_print(f"\n{Fore.CYAN}{Style.BRIGHT}*** go-to-album.bat created{Style.NORMAL}")
    # Create a batch file that changes directory into our_new_folder, which will be used externally:
    with open('go-to-album.bat', 'w', encoding="utf-8") as bat_file: bat_file.write(f'cd "{our_new_folder}"\n') #this is basically our script's return value
    log_print("\n\n")



def remove_leading_zeroes(directory):
    while True:
        files = [f for f in os.listdir(directory) if f.lower().endswith('.mp3')]
        log_print(f"{Fore.RED}{Style.BRIGHT}* Checking for leading zeroes on every filename in: {Style.NORMAL}{directory}...", end="")
        if files and all(f.startswith('0') for f in files):
            #og_print(f"\n{Fore.RED}{Style.BRIGHT}\t* Unnecessary leading filename zeroes were found... {Fore.BLUE}{Style.NORMAL}[files={files}]{Style.NORMAL}{Fore.YELLOW}")
            log_print(f"\n{Fore.RED}{Style.BRIGHT}\t* Unnecessary leading filename zeroes were found... {Style.NORMAL}{Fore.YELLOW}")
            for file in files:
                log_print(f'\t\t{Fore.RED}{Style.NORMAL}- Removing leading "0" from: {file}{Style.NORMAL}{Fore.YELLOW} ')
                if file.startswith('0'):
                    new_name = file[1:]
                    os.rename(os.path.join(directory, file), os.path.join(directory, new_name))
        else:
            #og_print(f'\n\t\t{Fore.RED}{Style.NORMAL}- Removing leading "0" from: {Style.BRIGHT}{Fore.GREEN}NONE!!{Style.NORMAL}{Fore.YELLOW} ')
            log_print(f'\n\t\t{Fore.RED}{Style.NORMAL}- {Style.BRIGHT}{Fore.GREEN}All unnecessary leading filename zeroes have been successfully removed{Style.NORMAL}{Fore.YELLOW} ')
            break


def move_companion_files(directory, the_new_folder):
    global COMPANION_FILES
    files_to_move = COMPANION_FILES
    files_to_move.extend([file for file in os.listdir(directory) if file.startswith("cover.")])
    for filename in files_to_move: # Attempt to move each file
        try:                       shutil.move(os.path.join(directory, filename), os.path.join(the_new_folder, filename))
        except FileNotFoundError:  log_print(f"{Fore.RED}Companion file {filename} not found in {directory} - so nothing to move.{Fore.RESET}")







def strip_artist_from_album_or_filename(album_or_song_or_file_name, artist_name, num_mp3s="1234567"):
    if num_mp3s == 1:
        album_or_song_or_file_name = album_or_song_or_file_name.split(" - ", 1)[-1]
    else:
        if  album_or_song_or_file_name.startswith(f"{artist_name}'s"):
            album_or_song_or_file_name = album_or_song_or_file_name[len(f"{artist_name}'s"):]
        else:
            #print(f"No artist/album match found for album name: {album_or_song_or_file_name}")
            pass
    album_or_song_or_file_name = album_or_song_or_file_name.strip()
    return album_or_song_or_file_name





if __name__ == "__main__":
    init()                                                                          #colorama
    new_folder = rename_tag_move_incoming_youtube_album('.', 'info.json')

    ## some tests:
    #print("GA: " + get_artist_from_filename           ("The Pixies - Where is My Mind but with the SM64 Soundfont [ePL44jEEOCQ].mp3"))
    #print("SA: " + strip_artist_from_album_or_filename("The Pixies - Where is My Mind but with the SM64 Soundfont [ePL44jEEOCQ].mp3","The Pixies",num_mp3s=1))

