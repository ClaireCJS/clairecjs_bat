#!/usr/bin/env python3
import sys, os, re, itertools
from collections import defaultdict

COLORS = [
    "\033[31m", "\033[32m", "\033[33m", "\033[34m",
    "\033[35m", "\033[36m", "\033[91m", "\033[92m",
    "\033[93m", "\033[94m", "\033[95m", "\033[96m"
]
BRIGHT_YELLOW = "\033[93m"
RESET = "\033[0m"
CIRCLED = ["❶","❷","❸","❹","❺","❻","❼","❽","❾","❿"]

def usage():
    print("Usage: srt_comparator.py [options] file1.srt file2.srt ...")
    print("Options:")
    print("  -hi, --hide-identical-lines  Hide lines identical across all files")
    print("  -sf, --show-filenames, --key Show color/filename key for files")
    print("  -lr, --low-res-timestamps    Don’t consider 10ths & 100ths of a second")
    sys.exit(1)

def parse_srt(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    entries = re.findall(r"(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?=\n\n|\Z)", content, re.S)
    return [{"start": s, "end": e, "text": t.strip()} for _, s, e, t in entries]

def fmt_ms(ms_str):
    try:
        msi = int(ms_str)
    except:
        return "0"
    if msi == 0:
        return "0"
    s = str(msi).rstrip("0")
    return s or "0"

def format_timestamp(hms_ms):
    # Trim hours, adjust leading zeros, convert commas to dots, drop trailing zeros
    m = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3})", hms_ms)
    if not m:
        return hms_ms.replace(",", ".")
    hh, mm, ss, ms = m.groups()
    hh_i, mm_i, ss_i = int(hh), int(mm), int(ss)
    ms_fmt = fmt_ms(ms)
    if hh_i == 0:
        # drop hour if 00
        return f"{mm_i}:{ss_i:02d}.{ms_fmt}" if mm_i > 0 else f"{ss_i}.{ms_fmt}"
    else:
        return f"{hh_i}:{mm_i:02d}:{ss_i:02d}.{ms_fmt}"

def format_stamp_range(key):
    s, e = [p.strip() for p in key.split("-->")]
    return f"{format_timestamp(s)} --> {format_timestamp(e)}"

def num_label(i, total):
    return CIRCLED[i] if i < len(CIRCLED) else f"[{i+1}]"

def normalize_time_lowres(ts):
    m = re.match(r"(\d{2}):(\d{2}):(\d{2})", ts)
    return f"{m.group(1)}:{m.group(2)}:{m.group(3)}" if m else ts


def main():
    args = sys.argv[1:]
    if not args: usage()
    hide_identical     = False
    show_filenames     = False
    low_res_timestamps = False
    files = []
    for a in args:
        if   a in ('-lr', '--lr', '--low-res-timestamps'             ): low_res_timestamps = True
        elif a in ('-hi', '--hi', '--hide-identical-lines'           ): hide_identical     = True
        elif a in ('-sf', '--sf', '--show-filenames', '--key', '-key'): show_filenames     = True
        else: files.append(a)

    if not files: usage()
    for f in files:
        if not os.path.isfile(f):
            print(f"Error: file not found: {f}")
            sys.exit(1)

    srts = [parse_srt(f) for f in files]
    colors = [COLORS[i % len(COLORS)] for i in range(len(files))]

    index_by_time = defaultdict(lambda: [''] * len(files))
    for i, srt in enumerate(srts):
        for e in srt:
            start = normalize_time_lowres(e['start']) if low_res_timestamps else e['start']
            end   = normalize_time_lowres(e['end'])   if low_res_timestamps else e['end']
            key = f"{start} --> {end}"
            index_by_time[key][i] = e['text']

    all_keys = sorted(index_by_time.keys(), key=lambda k: k)

    if show_filenames:
        print(f"{BRIGHT_YELLOW}⸎  Files being compared: ⸎{RESET}")
        for i, f in enumerate(files):
            label = num_label(i, len(files))
            print(f"    {colors[i]}{label}  {f}{RESET}")
        print()

    for key in all_keys:
        texts = index_by_time[key]
        trimmed = [t.strip() for t in texts]
        non_empty = [t for t in trimmed if t != ""]
        # Only hide if all are identical *and* non-empty
        if hide_identical and non_empty and len(non_empty) == len(trimmed) and len(set(non_empty)) == 1:
            continue

        print(f"{BRIGHT_YELLOW}⸎ ", format_stamp_range(key) + ":")
        for i, t in enumerate(texts):
            label = num_label(i, len(files))
            if t.strip() == "":
                #print(f"    {colors[i]}{label}  [missing]{RESET}")
                pass
            else:
                lines = t.splitlines()
                for li, L in enumerate(lines):
                    prefix = label if li == 0 else " " * len(label)
                    print(f"    {colors[i]}{prefix}  {L}{RESET}")
        print()

if __name__ == "__main__":
    main()
