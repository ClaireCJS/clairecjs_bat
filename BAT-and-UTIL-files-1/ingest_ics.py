"""

    Google Calendar events created by saving ICS files to c:\calendar ***

    Or use this to ingest an individual file by specifying it at the command line

    USAGE:
        python ingest-ics.py                      -     monitors c:\calendar for ics files being dropped into
        python ingest-ics.py whatever.ics         -     create event from a single ics file
        python ingest-ics.py help                 -     prints usage


    *** NOTE: Processed files will be moved to c:\calendar\processed

"""



# TODO: possible issue: 0-byte ics files may crash it?


import os
import re
import sys
import time
import glob
import random
import ctypes
import traceback
import webbrowser
from urllib.parse import urlencode
from datetime import datetime


def show_error_popup(title, message):
    """Display a real, foreground Windows error dialog."""
    try:
        flags = 0x00000010 | 0x00010000 | 0x00040000
        ctypes.windll.user32.MessageBoxW(None, str(message), str(title), flags)
    except Exception as popup_error:
        print(f"ERROR: Could not display Windows error dialog: {popup_error}", file=sys.stderr)


try:
    import emoji
    import arrow
    import pyperclip
    from ics import Calendar as icsCalendar
    from colorama import Fore, Style, init
except Exception as import_error:
    show_error_popup(
        "Calendar ingest could not start",
        f"A required Python package could not be loaded.\n\n"
        f"{type(import_error).__name__}: {import_error}",
    )
    raise

init(autoreset=True)




#################################### CONFIG: ####################################
MY_TIME_ZONE                 = "America/New_York"
FOLDER_TO_DROP_ICS_FILES_IN  = r"c:/calendar"                                       #processed ics files will be moved to a subfolder named "processed" along with a companion file containing the event creation URL
#################################### CONFIG! ####################################










HOW_OFTEN_TO_CHECK                           = 1                                #how many seconds between checking FOLDER_TO_DROP_ICE_FILES_IN repeatedly
AUTOMATICALLY_GO_TO_GOOGLE_CALENDAR_CREATION = True                             #open link in web browser automatically?
COPY_URL_TO_CLIPBOARD                        = False                            #copy event link to clipboard?
EMOJI_TO_ADD_TO_BEGINNING_OF_EVENT_TITLE     = "smiling_face_with_horns"        #set to "" to disable, or change to another emoji
DOT_COLORS                                   = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA, Fore.WHITE, Fore.LIGHTBLACK_EX, Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX]

DEBUG_ICS_PROCESSING = False
DEBUG_DATE_TIMEZONE  = True


class IcsProcessingError(Exception):
    """An ICS file could not be converted into a Google Calendar URL."""


def report_error(context, error, file_path=None):
    """Log an exception and notify the user with a foreground Windows dialog."""
    path_text = f"\n\nFile: {file_path}" if file_path else ""
    detail = f"{type(error).__name__}: {error}"
    print(f"\n{Fore.RED}{context}{path_text}\n{detail}{Fore.RESET}", file=sys.stderr)
    if DEBUG_ICS_PROCESSING:
        traceback.print_exc()
    show_error_popup("Calendar ingest failure", f"{context}{path_text}\n\n{detail}")


def unique_path(path):
    """Return a non-colliding path, preserving both files with ' (N)' suffixes."""
    if not os.path.exists(path):
        return path
    stem, extension = os.path.splitext(path)
    counter = 1
    while True:
        candidate = f"{stem} ({counter}){extension}"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def create_google_calendar_link(start, end, title, location, description):
    """
    Creates a google calendar link with the appropriate attributes
    """
    global EMOJI_TO_ADD_TO_BEGINNING_OF_EVENT_TITLE
    BASE_URL   = "https://www.google.com/calendar/render"
    start      = arrow.get(start).to("UTC").format("YYYYMMDDTHHmmss") + "Z"
    end        = arrow.get(end  ).to("UTC").format("YYYYMMDDTHHmmss") + "Z"

    if EMOJI_TO_ADD_TO_BEGINNING_OF_EVENT_TITLE:
        emoj  = emoji.emojize(":" + EMOJI_TO_ADD_TO_BEGINNING_OF_EVENT_TITLE  + ":")
        title = emoj + title

    event_data = {
        "action"   : "TEMPLATE"         ,
        "text"     : title              ,
        "dates"    : f"{start}/{end}"   ,
        "location" : location           ,
        "details"  : description        ,
    }
    url = BASE_URL + "?" + urlencode(event_data)
    return url


def fix_malformed_ics(ics_string):
    """
    Fixes malformed ics files that are missing DESCRIPTION tags from the VEVENT and VALARM subsections
    """
    print("* Fixing ics data...")
    summary_search = re.search(r"^SUMMARY(?:;[^:]*)?:(.*)$", ics_string, re.MULTILINE)
    if summary_search is not None:
        summary = summary_search.group(1)
    else:
        summary = "Summary unavailable"
    vevent_search = re.compile(r"(BEGIN:VEVENT.*?)(END:VEVENT)", re.DOTALL)
    valarm_search = re.compile(r"(BEGIN:VALARM.*?)(END:VALARM)", re.DOTALL)
    updated_ics   = ics_string
    def replace_vevent_func(match):
        if re.search(r"^DESCRIPTION(?:;[^:]*)?:", match.group(0), re.MULTILINE):
            return match.group(0)
        return match.group(1) + "\nDESCRIPTION:" + summary + "\n" + match.group(2)
    def replace_valarm_func(match):
        if re.search(r"^DESCRIPTION(?:;[^:]*)?:", match.group(0), re.MULTILINE):
            return match.group(0)
        return match.group(1) + "\nDESCRIPTION:Alarm\n" + match.group(2)
    if summary_search is None:
        print("WARNING: Could not find SUMMARY in the ICS file; using a fallback title.")
    updated_ics = vevent_search.sub(replace_vevent_func, updated_ics)
    updated_ics = valarm_search.sub(replace_valarm_func, updated_ics)
    updated_ics = updated_ics.replace("\n\n", "\n")
    return updated_ics


def generate_google_calendar_url_from_ics_file(file_path):                                                                                  #pylint: disable=C0103
    """
    Process an individual ics file and opens a Google Calendar event create page in cresponse
    """
    global COPY_URL_TO_CLIPBOARD, AUTOMATICALLY_GO_TO_GOOGLE_CALENDAR_CREATION, DEBUG_ICS_PROCESSING, DEBUG_DATE_TIMEZONE

    print(f"\n{Fore.YELLOW}* Processing ics file: {file_path}{Fore.WHITE}")
    try:
        with open(file_path, 'r', encoding="utf-8-sig") as file:
            ics_content = file.read()
    except (OSError, UnicodeError) as error:
        raise IcsProcessingError(f"Could not read the ICS file: {error}") from error
    if not ics_content.strip():
        raise IcsProcessingError("The ICS file is empty.")
    fixed_ics = fix_malformed_ics(ics_content)

    try:
        calendar = icsCalendar(fixed_ics)
    except Exception as error:
        raise IcsProcessingError(f"The ICS data could not be parsed: {error}") from error

    events = calendar.events
    if not events:
        raise IcsProcessingError("The ICS file does not contain any calendar events.")

    if DEBUG_ICS_PROCESSING:
        print(f"\t- contents of original ics file={Fore.RED}{ics_content}{Fore.WHITE}")
        print(f"\t- fixed_ics is: {Fore.YELLOW}{fixed_ics}{Fore.WHITE}")
        print(f"{Fore.GREEN}\t- calendar={calendar}{Fore.WHITE}")
        print(f"\t- # events={len(events)}")

    for event in events:
        title       = event.name or "Untitled event"
        location    = event.location or ""
        description = (event.description or "").replace('\n','<BR>')
        if event.begin is None or event.end is None:
            raise IcsProcessingError("An event is missing its start or end date/time.")
        local_tz    = arrow.now().tzinfo
        start       = arrow.get(event.begin.datetime).to(local_tz)
        end         = arrow.get(event.end  .datetime).to(local_tz)
        url         = create_google_calendar_link(start, end, title, location, description)

        if DEBUG_DATE_TIMEZONE:
            print(f"{Fore.CYAN}\tevent.begin={event.begin}{Fore.WHITE}")
            print(f"{Fore.BLUE}\tevent.begin.datetime={event.begin.datetime}{Fore.WHITE}")
            print(f"{Fore.LIGHTBLUE_EX}\tarrow.get(event.begin.datetime)={arrow.get(event.begin.datetime)}{Fore.WHITE}")
            print(f"{Fore.LIGHTCYAN_EX}\tarrow.get(event.begin.datetime).to(local_tz)={arrow.get(event.begin.datetime).to(local_tz)}{Fore.WHITE}")

        print(f"{Fore.GREEN}{Style.BRIGHT}* Generated URL is: {Style.NORMAL}{url}{Fore.WHITE}")
        if AUTOMATICALLY_GO_TO_GOOGLE_CALENDAR_CREATION:
            successful = webbrowser.open_new(url)                                              # open in browser (remove "_new" to not open in new window)
            if not successful:
                print(f"{Fore.RED}ERROR: Couldn't open web browser, so copying URL to clipboard instead.")
                pyperclip.copy(url)
    if COPY_URL_TO_CLIPBOARD: pyperclip.copy(url)                                              # if the ics has multiple events (which it won't, ever, in our cases), only copy the last one to the clipboard
    return url





def monitor_folder(folder_to_drop_ics_files_in):
    """
    Monitors a folder for new ics files and processes them accordingly.
    After processing, they are moved into a processing subfolder.
    A new file with the same filename but ".url" added on to the end will be created with the generated URL, so that it is also saved
    """
    global HOW_OFTEN_TO_CHECK, DOT_COLORS
    processed_files = 0
    failed_file_signatures = {}
    processed_folder = os.path.join(folder_to_drop_ics_files_in, 'processed')
    if not os.path.exists(folder_to_drop_ics_files_in):
        os.makedirs(folder_to_drop_ics_files_in)
        print(Fore.RED + '\n' + 'Folder did not exist, created new one at ' + folder_to_drop_ics_files_in + '\n\n')
        print(Fore.RED + 'You can now drop your .ics files into this folder for processing!!!\n' * 5)
    print('\n' + f'{Fore.GREEN}{Style.BRIGHT}!!!!!!!!!!!!!!!!!!!!! Starting calendar monitor !!!!!!!!!!!!!!!!!!!!!!\n' * 5, end="")
    dot_count = 0
    while True:
        dot_count += 1
        print(random.choice(DOT_COLORS) + ".", end="")
        if dot_count > 1000: dot_count = 1
        if dot_count == 1:
            print(f'\n\n{Fore.GREEN}{Style.NORMAL}Just save ics files into {folder_to_drop_ics_files_in} to create Google Calendar events!\n')
        ics_files = glob.glob(folder_to_drop_ics_files_in + '/*.ics')
        for ics_file in ics_files:
            try:
                stat = os.stat(ics_file)
                signature = (stat.st_size, stat.st_mtime_ns)
                if failed_file_signatures.get(ics_file) == signature:
                    continue

                url = generate_google_calendar_url_from_ics_file(ics_file)

                if not os.path.exists(processed_folder):
                    print(f"\n\n{Fore.YELLOW}Creating processed folder: {processed_folder}{Fore.RESET}")
                    print("ics files will be moved here as they are processed")
                    print("url files will be moved here as they are generated from the processed ics files")
                    os.makedirs(processed_folder)

                file_name = os.path.basename(ics_file)
                new_file_path = unique_path(os.path.join(processed_folder, file_name))
                os.rename(ics_file, new_file_path)

                processed_files += 1
                failed_file_signatures.pop(ics_file, None)
                print(f"{Fore.GREEN}{Style.BRIGHT}\n...Successfully processed file: {Style.NORMAL}{ics_file}")
                print(f"{Fore.CYAN}Total processed files: {Style.BRIGHT}{str(processed_files)}{Fore.WHITE}{Style.NORMAL}")

                results_file = unique_path(new_file_path + ".url")
                with open(results_file, 'x', encoding="utf-8") as file:
                    file.write(url)
            except KeyboardInterrupt:
                raise
            except Exception as error:
                try:
                    stat = os.stat(ics_file)
                    failed_file_signatures[ics_file] = (stat.st_size, stat.st_mtime_ns)
                except OSError:
                    failed_file_signatures[ics_file] = None
                report_error(
                    "This ICS file could not be processed. The monitor will keep running. "
                    "It will retry after the file changes or after the monitor is restarted.",
                    error,
                    ics_file,
                )
        time.sleep(HOW_OFTEN_TO_CHECK)                                                  # check every HOW_OFTEN_TO_CHECK seconds


def main():
    global FOLDER_TO_DROP_ICS_FILES_IN                                                  #, MY_TIME_ZONE
    if len(sys.argv) == 2 and sys.argv[1].lower() in ["help", "-help", "--help", "?", "/?", "-?", "--?"]:
        print(f"{Fore.CYAN}{Style.BRIGHT}\n* Options:\n")
        print(f"{Fore.CYAN}{Style.NORMAL}1. Run with a filename of an .ics file as argument.")
        print(f"{Fore.CYAN}{Style.NORMAL}2. Run with 'monitor' as argument to monitor the folder {FOLDER_TO_DROP_ICS_FILES_IN} for new .ics files")
        return 0

    if len(sys.argv) == 1 or bool(len(sys.argv) == 2 and sys.argv[1] == 'monitor'):
        monitor_folder(FOLDER_TO_DROP_ICS_FILES_IN)
        return 0
    elif not os.path.exists(sys.argv[1]):
        error = FileNotFoundError(f"File {sys.argv[1]} does not exist.")
        report_error("The requested ICS file could not be processed.", error, sys.argv[1])
        return 1
    try:
        generate_google_calendar_url_from_ics_file(sys.argv[1])
    except Exception as error:
        report_error("The requested ICS file could not be processed.", error, sys.argv[1])
        return 1
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCalendar monitor stopped by user.")
    except Exception as fatal_error:
        report_error("The calendar monitor stopped because of an unexpected fatal error.", fatal_error)
        sys.exit(1)
