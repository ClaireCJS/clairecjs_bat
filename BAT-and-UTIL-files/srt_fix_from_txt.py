import re
import difflib
from difflib import SequenceMatcher
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

line_color = f"{Fore.CYAN}"

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
def print_headers(col_width, col_width_big, screen_width):
    if (col_width % 2) == 1:
        col_width -= 1
    line = f"{line_color}" + "=" * (screen_width - 10)
    print(line)
    print(f"{DOUBLE_HEIGHT_TOP}{Style.BRIGHT}  {Fore.LIGHTRED_EX}{'SRT ' + ITALIC + '[old]  ':<{col_width_big + len(ITALIC)}}{RESET} "
          f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}{BLINK}{'SRT [new]':<{col_width_big}}{RESET} "
          f"{Style.BRIGHT}{Fore.YELLOW}{Style.BRIGHT}{'TXT used':<{col_width_big}}    #{RESET}", end="")
    print(f"\n{DOUBLE_HEIGHT_BOT}{Style.BRIGHT}  {Fore.LIGHTRED_EX}{'SRT ' + ITALIC + '[old]  ':<{col_width_big + len(ITALIC)}}{RESET} "
          f"{Style.BRIGHT}{Fore.LIGHTGREEN_EX}{BLINK}{'SRT [new]':<{col_width_big}}{RESET} "
          f"{Style.BRIGHT}{Fore.YELLOW}{Style.BRIGHT}{'TXT used':<{col_width_big}}    #{RESET}", end="")
    print("\n" + line)

# Correct individual words in the line
def correct_words_in_line(subtitle, reference_text):
    global total_words_changed, total_words_original
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

    # Ensure no unnecessary repetition occurs by avoiding duplicate segments from the original text
    total_words_original += len(subtitle_words)
    total_words_changed += sum(1 for sw, cw in zip(subtitle_words, final_corrected_words) if sw != cw)
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
def correct_srt_using_txt(srt, txt, srt_path, txt_path, col_width, col_width_big, screen_width):
    global total_words_changed, total_words_original
    total_words_changed = 0
    total_words_original = 0
    txt_lines = txt.splitlines()
    modified_lines = {}
    original_texts = [item.text for item in srt]  # Store original texts
    total_lines = len(srt)
    matched_lines = 0
    total_chars_original = 0
    total_chars_corrected = 0
    total_words_original = 0
    total_words_changed = 0

    # First pass for single-line matching
    for i, item in enumerate(srt):
        print(f"Processing SRT content line {i + 1}: '{item.text}'")
        original_text = original_texts[i]
        normalized_subtitle = normalize_text(original_text)
        best_match = match_single_line(normalized_subtitle, txt_lines)

        if best_match:
            reference_text = next((line for line in txt_lines if normalize_text(line) == best_match[0]), "")
            print(f"  Match found: '{reference_text}' from TXT line {txt_lines.index(reference_text) + 1}")
            reference_index = txt_lines.index(reference_text) if reference_text else -1
            corrected_text = correct_words_in_line(original_text, reference_text)
            if corrected_text != original_text and reference_text != "":
                item.text = corrected_text
            match_score = difflib.SequenceMatcher(None, normalized_subtitle, normalize_text(reference_text)).ratio()
            modified_lines[i] = (reference_text, reference_index, match_score)
            matched_lines += 1

            # Log the change
            logging.info(f"{srt_path},{original_text},{corrected_text},{txt_path},{reference_text}")
        else:
            print(f"  No direct match found for line {i + 1}. Finding closest matches...")
            all_matches = difflib.get_close_matches(normalized_subtitle, [normalize_text(line) for line in txt_lines], n=10, cutoff=0.3)
            matches_with_scores = [(match, difflib.SequenceMatcher(None, normalize_text(original_text), match).ratio()) for match in all_matches]
            matches_with_scores.sort(key=lambda x: x[1], reverse=True)
            top_3_matches = matches_with_scores[:3]
            if top_3_matches:
                print("  Closest matches (in descending score order):")
                for match, match_score in top_3_matches:
                    match_index = [normalize_text(line) for line in txt_lines].index(match)
                    print(f"    line {match_index + 1}: '{txt_lines[match_index]}' (score: {match_score:.2f})")

            # Handle multi-line matching if a single line match is not found
            best_combined_match = match_combined_lines(normalized_subtitle, txt_lines)
            if best_combined_match:
                reference_text = next((line for line in txt_lines if normalize_text(line) in best_combined_match[0]), "")
                if reference_text:
                    combined_match_index = txt_lines.index(reference_text)
                    if combined_match_index + 1 < len(txt_lines):
                        reference_text = txt_lines[combined_match_index] + ' ' + txt_lines[combined_match_index + 1]
                    reference_index = combined_match_index
                    corrected_text = correct_words_in_line(original_text, reference_text)
                    if corrected_text != original_text and reference_text != "":
                        item.text = corrected_text
                    match_score = difflib.SequenceMatcher(None, normalized_subtitle, normalize_text(reference_text)).ratio()
                    modified_lines[i] = (reference_text, reference_index, match_score)
                    matched_lines += 1

                    # Log the change
                    logging.info(f"{srt_path},{original_text},{corrected_text},{txt_path},{reference_text}")

    # Post-process unmatched lines between matched lines
    post_process_unmatched_lines(srt, txt_lines, modified_lines)

    # Post-post-processing unmatched lines with a lower threshold
    for i, item in enumerate(srt):
        if i not in modified_lines:
            original_text = original_texts[i]
            normalized_subtitle = normalize_text(original_text)
            best_match = difflib.get_close_matches(normalized_subtitle, [normalize_text(line) for line in txt_lines], n=1, cutoff=0.45)

            if best_match:
                reference_text = next((line for line in txt_lines if normalize_text(line) == best_match[0]), "")
                reference_index = txt_lines.index(reference_text) if reference_text else -1
                corrected_text = correct_words_in_line(original_text, reference_text)
                if corrected_text != original_text and reference_text != "":
                    item.text = corrected_text
                match_score = difflib.SequenceMatcher(None, normalized_subtitle, normalize_text(reference_text)).ratio()
                modified_lines[i] = (reference_text, reference_index, match_score)

                # Log the change
                logging.info(f"{srt_path},{original_text},{corrected_text},{txt_path},{reference_text}")

    # Additional step: Fix length discrepancies
    fix_length_discrepancies(srt, original_texts, txt_lines)


    # post-processing to fix punctuation spacing
    for item in srt:
        item.text = item.text.replace(" ,", ",")


    # Print headers and final output after all processing steps
    print_headers(col_width, col_width_big, screen_width)

    for i, item in enumerate(srt):
        original_text = original_texts[i]
        reference_text, reference_index, match_score = modified_lines.get(i, ("", -1, 0.00))

        # Print original, corrected, and reference text as a table row
        print(f"{Fore.LIGHTCYAN_EX}{i + 1:<2}{Style.RESET_ALL}"
              f"{Fore.LIGHTYELLOW_EX}{len(original_text):<2}{Fore.LIGHTRED_EX  }{original_text:<{col_width}}{Style.RESET_ALL} "
              f"{Fore.LIGHTYELLOW_EX}{len(    item.text):<2}{Fore.LIGHTGREEN_EX}{    item.text:<{col_width}}{Style.RESET_ALL} "
              f"{Fore.LIGHTYELLOW_EX}{Style.BRIGHT}{reference_text:<{col_width}}{Style.RESET_ALL} "
              f"{Fore.CYAN}{reference_index + 1 if reference_text else ' ':{col_width // 4}}{Style.RESET_ALL} "
              f"{Fore.LIGHTBLUE_EX}{match_score:.2f}{Style.RESET_ALL}")

        # Display top 3 closest matches if no match was found
        if reference_index == -1:
            print("  No valid match found for this line. Keeping original.")

    # Print stats
    line = f"{line_color}=" * (screen_width - 10)
    print(line)
    line_match_percentage = (matched_lines / total_lines) * 100 if total_lines > 0 else 0
    words_changed_percentage = (total_words_changed / total_words_original) * 100 if total_words_original > 0 else 0
    letters_changed_percentage = (total_chars_changed / total_chars_original) * 100 if total_chars_original > 0 else 0

    # Print stats in bright rainbow colors
    bright_rainbow_colors = [Fore.LIGHTRED_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX]
    stats_text = (
        f"Line Match: {line_match_percentage:.0f}%  \t\t"
        f"Words Changed: {words_changed_percentage:.0f}%  \t\t"
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
                previous_txt, previous_index, _ = modified_lines[i - 1]
                next_txt, next_index, _ = modified_lines[i + 1]
                original_text = item.text

                # Determine the middle index between the previous and next matched lines
                if len(set(normalize_text(previous_txt)) & set(normalize_text(next_txt))) > 0.1 * len(set(normalize_text(original_text))):
                    middle_index = (previous_index + next_index) // 2
                    if middle_index < len(txt_lines):
                        corrected_text = txt_lines[middle_index]
                    else:
                        corrected_text = original_text

                    if corrected_text != original_text and corrected_text != "":
                        item.text = corrected_text
                        match_score = difflib.SequenceMatcher(None, normalize_text(original_text), normalize_text(corrected_text)).ratio()
                        modified_lines[i] = (corrected_text, middle_index, match_score)

                        # Log the change
                        logging.info(f"{corrected_text}")

# Fix length discrepancies between original and new values
def fix_length_discrepancies(srt, original_texts, txt_lines):
    for i, item in enumerate(srt):
        original_text = original_texts[i]
        corrected_text = item.text
        #if len(corrected_text) < 0.66 * len(original_text):
        if len(corrected_text) < 0.66 * len(original_text) or len(corrected_text) > 1.33 * len(original_text):

            # Find the best-matching subset of the original line
            matcher = SequenceMatcher(None, original_text, corrected_text)
            matching_blocks = matcher.get_matching_blocks()
            non_matching_parts = []

            for j in range(len(matching_blocks) - 1):
                start = matching_blocks[j].a + matching_blocks[j].size
                end = matching_blocks[j + 1].a
                non_matching_parts.append(original_text[start:end])

            unmatched_text = ' '.join(non_matching_parts)

            # Append non-matching parts from the original line to restore context
            if unmatched_text.strip():
                item.text = corrected_text + ' ' + unmatched_text

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
    updated_srt = correct_srt_using_txt(srt, txt, srt_path, txt_path, col_width, col_width_big, screen_width)

    # Save the updated SRT file
    updated_srt.save(output_path, encoding='utf-8')