#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ INITIALIZE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ INITIALIZE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ INITIALIZE ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

total_processed = 0
SCRIPT_NAME     = "check_playlist_for_files_without_txt_or_transcription.py"

EXCLUDED_FILENAME_MARKERS = (
    "[instrumental]",
    "[sound effects]",
    "[sound effect]",
    "[no lyrics]",
    "[no lyr]",
)
CHIPTUNE_MARKERS = ("[chiptune]", "[chiptunes]")
VOCAL_EXCEPTION_MARKERS = ("[has vocals]", "[with vocals]")



#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ IMPORTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ IMPORTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ IMPORTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import os
import sys
from   tqdm  import tqdm                                     # library: status bar

DEFAULT_FILEMASK_AUDIO = "*.mp3;*.wav;*.rm;*.voc;*.au;*.mid;*.stm;*.s3m;*.mod;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3;*.ra;*.dtshd;*.m4a;*.aif;*.cmf;*.rol"
DEFAULT_FILEMASK_VOCAL = "*.mp3;*.wav;*.rm;*.voc;*.au;*.vqf;*.ogg;*.mpc;*.wma;*.mp4;*.flac;*.snd;*.aac;*.opus;*.ac3;*.ra;*.dtshd;*.m4a;*.aif"
FILEMASK_AUDIO = os.environ.get("FILEMASK_AUDIO", DEFAULT_FILEMASK_AUDIO)
FILEMASK_VOCAL = os.environ.get("FILEMASK_VOCAL", DEFAULT_FILEMASK_VOCAL)
FILEMASK_AUDIO_EXTENSIONS = {os.path.splitext(mask.strip().lower())[1] for mask in FILEMASK_AUDIO.split(';') if mask.strip()}
FILEMASK_VOCAL_EXTENSIONS = {os.path.splitext(mask.strip().lower())[1] for mask in FILEMASK_VOCAL.split(';') if mask.strip()}
claire_utils = False
try:
    import clairecjs_utils as claire
    claire_utils = True
except ImportError:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir not in sys.path: sys.path.insert(0, script_dir)
    try:
        import clairecjs_utils as claire
        claire_utils = True
    except ImportError:
        raise ImportError("Cannot find 'clairecjs_utils' module in site-packages or the local directory.")
        claire_utils = False

from colorama import init
init(autoreset=False)
#print (f"claire_utils={claire_utils}")


#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ THE MEAT: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ THE MEAT: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ THE MEAT: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def check_sidecars(playlist_path, output_path):
    global total_processed, claire_utils

    with open(playlist_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    num_lines = len(lines)

    results = []
    with tqdm(total=num_lines, desc="🔍 Checking lyric/karaoke files", unit="file") as pbar:                         # Initialize the progress bar
        for path in lines:
            extension = os.path.splitext(path)[1].casefold()
            if extension not in FILEMASK_AUDIO_EXTENSIONS or extension not in FILEMASK_VOCAL_EXTENSIONS:
                pbar.update(1)
                if claire_utils: claire.tick()
                continue
            path_casefolded = path.casefold()
            filename_casefolded = os.path.basename(path_casefolded)
            path_parts = path_casefolded.replace('/', '\\').split('\\')
            excluded = any(marker in filename_casefolded for marker in EXCLUDED_FILENAME_MARKERS)
            is_chiptune = (
                any(marker in filename_casefolded for marker in CHIPTUNE_MARKERS)
                or any(part in {'chiptune', 'chiptunes'} for part in path_parts)
            )
            has_vocal_exception = any(marker in filename_casefolded for marker in VOCAL_EXCEPTION_MARKERS)
            if excluded or (is_chiptune and not has_vocal_exception):
                pbar.update(1)
                if claire_utils: claire.tick()
                continue
            base, _ = os.path.splitext(path)
            txt = base + '.txt'
            lrc = base + '.lrc'
            srt = base + '.srt'
            # print(f"\x1b[1G★ Searching playlist line {total_processed} of {num_lines} for songs with lyrics but no transcription...",end="")
            total_processed = total_processed + 1
            if not os.path.exists(txt) and not os.path.exists(lrc) and not os.path.exists(srt):
                results.append(path)
            pbar.update(1)                                                                              # update progress bar
            if claire_utils: claire.tick()
    if claire_utils: claire.tock()

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in results:
            f.write(line + '\n')




#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ MAIN: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ MAIN: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ MAIN: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    if len(sys.argv) != 3:

        print(f"Usage: python {SCRIPT_NAME} <input_playlist> <output_file>")
        sys.exit(1)

    check_sidecars(sys.argv[1], sys.argv[2])


