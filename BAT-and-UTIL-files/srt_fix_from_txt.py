import re
import difflib
from datetime import timedelta
from pysrt import SubRipFile, SubRipItem
import sys
from colorama import Fore, Style, init
import logging
import shutil

# ANSI codes for double-height text
DOUBLE_HEIGHT_TOP = "\x1b#3"
DOUBLE_HEIGHT_BOT = "\x1b#4"
RESET_HEIGHT = "\x1b#5"
BLINK = "\x1b[5m"
ITALIC = "\x1b[3m"
RESET = "\x1b[0m"

# Set up logging
logging.basicConfig(filename='srt_fix.log', level=logging.INFO, format='%(message)s')

# Load the SRT and TXT files
def load_files(srt_path, txt_path):
    srt = SubRipFile.open(srt_path, encoding='utf-8')
    with open(txt_path, 'r', encoding='utf-8') as txt_file:
        txt = '\n'.join([line for line in txt_file.read().splitlines() if line.strip()])
    return srt, txt

# Normalize text for comparison
def normalize_text(text):
    return re.sub(r"(?<!\b)-|[^a-z0-9\s'\-]", '', text.lower())

# Print headers with double-height text
def print_headers(col_width, col_width_big):
    if ((col_width % 2) == 1): col_width -= 1
    print("=" * 150)
    print(f"\n{DOUBLE_HEIGHT_TOP}{Style.BRIGHT}  {Fore.LIGHTRED_EX}{ITALIC}{'SRT [old]':<{col_width_big}}{RESET} "
          f"{Style.BRIGHT}{Fore.YELLOW}{BLINK}{'SRT [new]':<{col_width_big}}{RESET} "
          f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}{'TXT used':<{col_width_big}}  #{RESET}", end="")
    print(f"\n{DOUBLE_HEIGHT_BOT}{Style.BRIGHT}  {Fore.LIGHTRED_EX}{ITALIC}{'SRT [old]':<{col_width_big}}{RESET} "
          f"{Style.BRIGHT}{Fore.YELLOW}{BLINK}{'SRT [new]':<{col_width_big}}{RESET} "
          f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}{'TXT used':<{col_width_big}}  #{RESET}", end="")
    print("\n" + RESET_HEIGHT + "=" * 150)

# Correct individual words in the line
def correct_words_in_line(subtitle, reference_text):
    subtitle_words = subtitle.split()
    reference_words = reference_text.split()
    corrected_words = []

    matcher = difflib.SequenceMatcher(None, subtitle_words, reference_words)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            corrected_words.extend(subtitle_words[i1:i2])
        elif tag == 'replace':
            corrected_words.extend(reference_words[j1:j2])
        elif tag == 'delete':
            corrected_words.extend(subtitle_words[i1:i2])  # Keep the original words if there's no direct replacement
        elif tag == 'insert':
            corrected_words.extend(reference_words[j1:j2])

    # Remove unintended repeated words only if they are consecutive and identical, but allow expected repetitions
    final_corrected_words = []
    previous_word = None
    for word in corrected_words:
        if word != previous_word or (reference_words.count(word) > 1):  # Allow expected repeated words in reference text
            final_corrected_words.append(word)
        previous_word = word

    corrected_text = ' '.join(final_corrected_words)
    return corrected_text

# Match single lines from TXT
def match_single_line(normalized_subtitle, txt_lines):
    return difflib.get_close_matches(normalized_subtitle, [normalize_text(line) for line in txt_lines], n=1, cutoff=0.6)

# Match combined lines from TXT for multi-line matching
def match_combined_lines(normalized_subtitle, txt_lines):
    combined_txt_lines = [txt_lines[i] + ' ' + txt_lines[i + 1] for i in range(len(txt_lines) - 1)]
    return difflib.get_close_matches(normalized_subtitle, [normalize_text(line) for line in combined_txt_lines], n=1, cutoff=0.5)

# Update subtitle text based on reference text
def correct_srt_using_txt(srt, txt, srt_path, txt_path, col_width, col_width_big):
    txt_lines = txt.splitlines()
    modified_lines = {}
    total_lines = len(srt)
    matched_lines = 0
    total_chars_original = 0
    total_chars_corrected = 0
    total_words_original = 0
    total_words_changed = 0

    print_headers(col_width, col_width_big)

    # First pass for single-line matching
    for i, item in enumerate(srt):
        original_text = item.text
        normalized_subtitle = normalize_text(item.text)
        best_match = match_single_line(normalized_subtitle, txt_lines)

        if best_match:
            reference_text = next((line for line in txt_lines if normalize_text(line) == best_match[0]), "")
            reference_index = txt_lines.index(reference_text) if reference_text else -1
            corrected_text = correct_words_in_line(item.text, reference_text)
            item.text = corrected_text
            modified_lines[i] = (reference_text, reference_index)
            matched_lines += 1
        else:
            # Handle multi-line matching if a single line match is not found
            best_combined_match = match_combined_lines(normalized_subtitle, txt_lines)
            if best_combined_match:
                reference_text = next((line for line in txt_lines if normalize_text(line) in best_combined_match[0]), "")
                if reference_text:
                    combined_match_index = txt_lines.index(reference_text)
                    reference_text = txt_lines[combined_match_index] + ' ' + txt_lines[combined_match_index + 1]
                    reference_index = combined_match_index
                    corrected_text = correct_words_in_line(item.text, reference_text)
                    item.text = corrected_text
                    modified_lines[i] = (reference_text, reference_index)
                    matched_lines += 1
            else:
                reference_text = ""
                corrected_text = original_text

        # Calculate character changes for stats
        total_chars_original += len(original_text)
        total_chars_corrected += len(corrected_text)

        # Calculate word changes for stats
        total_words_original += len(original_text.split())
        total_words_changed += sum(1 for a, b in zip(original_text.split(), corrected_text.split()) if a != b)

        # Print original, corrected, and reference text as a table row
        print(f"{Fore.LIGHTCYAN_EX}{i + 1:<2}{Style.RESET_ALL}"
              f"{Fore.LIGHTRED_EX}{original_text:<{col_width}}{Style.RESET_ALL} "
              f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{corrected_text:<{col_width}}{Style.RESET_ALL} "
              f"{Fore.LIGHTGREEN_EX}{reference_text:<{col_width}}{Style.RESET_ALL} "
              f"{Fore.CYAN}{reference_index + 1 if reference_text else ' ':<{col_width // 4}}{Style.RESET_ALL}")

        # Log the change
        if reference_text:
            logging.info(f"{srt_path},{original_text},{corrected_text},{txt_path},{reference_text}")

    # Post-process unmatched lines between matched lines
    post_process_unmatched_lines(srt, txt_lines, modified_lines)

    # Print stats
    print("=" * 150)
    line_match_percentage = (matched_lines / total_lines) * 100 if total_lines > 0 else 0
    words_changed_percentage = (total_words_changed / total_words_original) * 100 if total_words_original > 0 else 0
    letters_changed_percentage = (1 - (total_chars_corrected / total_chars_original)) * 100 if total_chars_original > 0 else 0

    # Print stats in bright rainbow colors
    bright_rainbow_colors = [Fore.LIGHTRED_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX]
    stats_text = (
        f"   Line Match: {line_match_percentage       :.0f}%         "
        f"Words Changed: {words_changed_percentage    :.0f}%         "
        f"Letters Changed?: {letters_changed_percentage:.0f}%"
    )
    rainbow_stats = ''.join([bright_rainbow_colors[i % len(bright_rainbow_colors)] + char for i, char in enumerate(stats_text)])
    print(rainbow_stats + Style.RESET_ALL)

    return srt

# Post-process unmatched lines between matched lines
def post_process_unmatched_lines(srt, txt_lines, modified_lines):
    for i, item in enumerate(srt):
        if i not in modified_lines and 0 < i < len(srt) - 1:
            if (i - 1) in modified_lines and (i + 1) in modified_lines:
                previous_txt, previous_index = modified_lines[i - 1]
                next_txt, next_index = modified_lines[i + 1]
                if len(set(normalize_text(previous_txt)) & set(normalize_text(next_txt))) > 0.1 * len(set(normalize_text(item.text))):
                    middle_index = (previous_index + next_index) // 2
                    corrected_text = txt_lines[middle_index] if middle_index < len(txt_lines) else item.text
                    item.text = corrected_text
                    modified_lines[i] = (corrected_text, middle_index)

                    # Log the change
                    logging.info(f"{corrected_text}")

if __name__ == "__main__":
    screen_width = shutil.get_terminal_size().columns
    col_width = int(round(screen_width * 0.27))
    col_width_big = int(round((col_width / 2) - 0.5))

    init(autoreset=True)  # Initialize colorama for colored output

    if len(sys.argv) != 4:
        print("Usage: python script.py <srt_file> <txt_file> <output_file>")
        sys.exit(1)

    srt_path = sys.argv[1]
    txt_path = sys.argv[2]
    output_path = sys.argv[3]

    srt, txt = load_files(srt_path, txt_path)
    updated_srt = correct_srt_using_txt(srt, txt, srt_path, txt_path, col_width, col_width_big)

    # Save the updated SRT file
    updated_srt.save(output_path, encoding='utf-8')