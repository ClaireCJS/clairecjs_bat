"""
    split those pesky youtube videos where the timestamps are only listed in a comment by some random commenter,
    in a format like:

    0:00 Battery
    05:11 Master of Puppets
    13:06 The Thing That Should Not Be
    19:17 Welcome Home (Sanitarium)
    25:39 Disposable Heores
    33:23 Leper Messiah
    38:59 Orion
    47:03 Damage, Inc.

"""
import re
from colorama import Fore, Style, init
import fix_unicode_filenames


def validate_input(timestamps):
    """ Validate user input """
    if not timestamps: return
    if len(timestamps) < 2: raise ValueError("Oh no! We need at least two timestamps to split the tracks. Could you provide some more?")
    for i, timestamp in enumerate(timestamps, start=1):
        time, title, end_time = timestamp_splitter(timestamp, timestamps, i)                                  #pylint: disable=W0612
        print(f"{Fore.LIGHTBLACK_EX}* Processing timestamp #{i} of '{timestamp}': time={time}, title={title}, end_time={end_time}")
        if not re.match(r'^\d?:?\d{1,2}:\d{2}$', time): raise ValueError(f"Oops! The time format for '{time}' seems incorrect. It should be in MM:SS format, like 00:30 or 2:15.")
        if not title:                                   raise ValueError(f"Hmm, we seem to be missing the title for the track at '{time}'. Could you check that for us?"                    )

def timestamp_splitter(timestamp, timestamps, i):
    if ' ' in timestamp:
        time, title = timestamp.split(' ', 1)
        time        = time     .strip()
        title       = title    .strip()
    else:
        time, title = "00:00", timestamp
    end_time =  timestamps[i]  .split(' ', 1)[0].strip() if i < len(timestamps) else "99:59:59"
    return time, title, end_time


def main():
    timestamps = []
    blank_lines = 0

    init()
    print(f"\n\n{Fore.RED}{Style.BRIGHT}>>>Enter timestamps in {Fore.GREEN}M[M]:SS Title{Fore.RED} format, followed by a couple blank lines:{Fore.WHITE}")
    print(f"{Fore.BLUE}{Style.NORMAL}>>>This is typically a set of timestamps found in a youtube comment by someone who cared more than the original poster")
    print(f"{Fore.CYAN}{Style.BRIGHT}>Example:")
    print(f"{Fore.CYAN}{Style.NORMAL}0:00 Happy Birthday")
    print(f"{Fore.CYAN}{Style.NORMAL}3:30 Jingle Bells")
    print(f"{Fore.CYAN}{Style.NORMAL}5:45 For Whom The Bells Toll")
    print(f"{Fore.RED}{Style.BRIGHT}>>>Enter timestamps in {Fore.GREEN}M[M]:SS Title{Fore.RED} format, followed by a couple blank lines:{Fore.WHITE}")

    # Ask for STDIN input of the timestamps and titles
    while True:
        try: line = input().strip()
        except EOFError:
            print("Unexpected end of input. Did you forget to provide the timestamps and track titles?")
            return

        if line.strip() == "": blank_lines += 1                     # Count consecutive blank lines
        else:                  blank_lines  = 0
        if blank_lines == 2 and len(timestamps) >= 2: break         # If we get 2 consecutive blank lines after receiving at least 2 timestamps, break
        if line == "" and len(timestamps) == 0: continue            # Ignore blank lines before any timestamps are entered

        #DEBUG: print(f"appending timestamps with line='{line}'")
        if line: timestamps.append(line)

    try: validate_input(timestamps)
    except ValueError as e:
        print(f"Invalid input: {e}")
        return

    # Generate the batch script
    with open('generated-splitter.bat', 'w', encoding="utf-8") as f:
        f.write("@Echo OFF\n")
        for i, timestamp in enumerate(timestamps, start=1):
            time, title, end_time = timestamp_splitter(timestamp, timestamps, i)
            f.write(f'REM    {time} {title}\n')
        f.write("\nset  INPUT_MP3=%@UNQUOTE[%1]\n")
        f.write("call validate-environment-variable INPUT_MP3\n")
        f.write("call validate-in-path ffmpeg eyeD3\n\n")
        for i, timestamp in enumerate(timestamps, start=1):
            time, title, end_time = timestamp_splitter(timestamp, timestamps, i)
            title_for_filename = f"{i}_{title}"
            title_for_filename = fix_unicode_filenames.convert_a_filename(title_for_filename,silent_if_unchanged=True)     #silent_if_unchanged=True suppresses output if nothing changes
            f.write(f'call ffmpeg -i "%INPUT_MP3%" -acodec copy -ss {time} -to {end_time} -f mp3 "{title_for_filename}.mp3"\n')
            f.write(f'eyeD3 --title "{title}" "{title_for_filename}.mp3"\n')
        f.write("\nif %@FILES[*.mp3] GT 8 del %INPUT_MP3%\n")

    print (f"{Fore.GREEN}\n* generated-splitter.bat has been successfully created!")


if __name__ == "__main__":
    main()
