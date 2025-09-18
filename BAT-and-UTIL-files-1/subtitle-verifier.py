#!/usr/bin/env python3
# dupes_srt_v5.py — flag TRUE overlaps in SRT cues.
# Two cues overlap if their half‑open intervals [start, end) intersect for any non‑empty span.
# End == next Start is OK (no overlap).
#
# Table (Unicode, magenta lines):
#   Du (bright cyan) | Overlap (cyan) | li/ne/# (red) | Lyrics (orange)
# Header is bright green; "Lines" header is 3 rows: li / ne / #.
# --columns N uses N-3 for the table width. Silent when no overlaps.
#
# Usage:
#   python dupes_srt_v5.py input.srt
#   python dupes_srt_v5.py input.srt --columns 80

import re, sys, argparse, shutil
from collections import defaultdict, OrderedDict

# ---------- ANSI colors ----------
ESC = "\x1b"; RESET = f"{ESC}[0m"
BRIGHT_CYAN  = f"{ESC}[96m"               # column 1 (Du)
CYAN         = f"{ESC}[36m"               # column 2 (Overlap)
RED          = f"{ESC}[31m"               # column 3 (Lines)
BRIGHT_RED   = f"{ESC}[91m"
ORANGE       = f"{ESC}[38;2;235;107;0m"   # column 4 (Lyrics)
MAGENTA      = f"{ESC}[35m"               # borders/lines
BRIGHT_GREEN = f"{ESC}[92m"               # header text

BIG_TOP      = f"{ESC}#3"
BIG_BOT      = f"{ESC}#4"
BIG_OFF      = f"{ESC}#5"


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

# ---------- time utils ----------
def ts_to_ms(ts):
    # accept 00:00:00,000 or 00:00:00.000
    h, m, rest = ts.split(":")
    if "," in rest: s, ms = rest.split(",")
    else:           s, ms = rest.split(".")
    return (int(h)*3600 + int(m)*60 + int(s))*1000 + int(ms)

def ms_to_ts(ms):
    if ms < 0: ms = 0
    s, ms = divmod(ms, 1000)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

# ---------- parsing ----------
TS_RE = re.compile(r"(\d\d:\d\d:\d\d[,.:]\d+)\s*-->\s*(\d\d:\d\d:\d\d[,.:]\d+)")

def parse_srt(path):
    """Return list of cues: dicts with index, line, start_ms, end_ms, start_ts, end_ts, lyric."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    n = len(lines); cues = []
    i = 0; idx = 0
    while i < n:
        line = lines[i]
        m = TS_RE.fullmatch(line.strip()) or TS_RE.search(line)
        if m:
            s_ts, e_ts = m.group(1), m.group(2)
            s_ms, e_ms = ts_to_ms(s_ts), ts_to_ms(e_ts)
            j = i + 1; lyric_lines = []
            while j < n and lines[j].strip() != "":
                lyric_lines.append(lines[j].strip()); j += 1
            lyric = " / ".join(lyric_lines).strip()
            cues.append({
                "idx": idx,
                "line": i+1,
                "s_ms": s_ms, "e_ms": e_ms,
                "s_ts": s_ts, "e_ts": e_ts,
                "lyric": lyric
            })
            idx += 1
            i = j + 1   # skip blank
        else:
            i += 1
    return cues



import re

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

def _strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)

def reduce_vertical_whitespace(table_str: str, threshold: int = 2, reduce_if_header_text: bool = False) -> str:
    """
    Shrink a box-drawn table by removing vertical runs of columns that are spaces on every relevant line.
    - threshold: minimum width (in visible columns) of an all-space run to remove
    - reduce_if_header_text:
        False (default): header lines participate in the “all-space” check, so any header text blocks removal
        True: header lines are *ignored* when checking (lets you remove whitespace even under header text)
    Assumptions:
      * All lines are same visible width (typical for these tables).
      * Borders use box-drawing chars; we’ll detect them and keep them, but trim them consistently.
    """
    lines_raw = table_str.splitlines()
    if not lines_raw:
        return table_str

    # Identify border + header rows so we don’t base “blank column” solely on top/bottom borders
    border_chars = "┏┓┗┛┯┷┠┨┼━"
    is_border = [any(ch in ln for ch in border_chars) for ln in lines_raw]

    # Header lines are those between the top border and the first “mid” separator (┼)
    header_start = 1 if len(lines_raw) > 1 and is_border[0] else 0
    try:
        mid_idx = next(i for i, ln in enumerate(lines_raw) if "┼" in ln)
    except StopIteration:
        mid_idx = header_start  # if no mid line, treat as zero header rows
    header_range = range(header_start, max(header_start, mid_idx))

    # Build plain versions for visible-column analysis; pick which lines to consider
    consider_idxs = []
    for i, raw in enumerate(lines_raw):
        if is_border[i]:
            continue  # ignore borders for the “are these columns blank?” test
        if (i in header_range) and reduce_if_header_text:
            continue  # ignore header lines if user allows shrinking under header text
        consider_idxs.append(i)

    # If nothing to consider, nothing to remove
    if not consider_idxs:
        return table_str

    plains = [_strip_ansi(lines_raw[i]) for i in range(len(lines_raw))]
    width = max(len(plains[i]) for i in consider_idxs)
    # Pad plains to uniform width for indexing
    plains = [p + " " * max(0, width - len(p)) for p in plains]

    # Determine which visible columns are blank across considered lines
    blank = [False] * width
    for col in range(width):
        all_spaces = True
        for i in consider_idxs:
            ch = plains[i][col] if col < len(plains[i]) else " "
            if ch != " ":
                all_spaces = False
                break
        blank[col] = all_spaces

    # Find contiguous runs of blank >= threshold to remove
    remove = [False] * width
    col = 0
    while col < width:
        if blank[col]:
            start = col
            while col < width and blank[col]:
                col += 1
            if (col - start) >= threshold:
                for k in range(start, col):
                    remove[k] = True
        else:
            col += 1

    # Fast path: nothing to remove
    if not any(remove):
        return table_str

    # Rebuild each line: keep ANSI sequences always; skip visible chars whose column is marked remove
    def reconstruct(raw: str) -> str:
        out = []
        i = 0
        vis_col = 0
        while i < len(raw):
            if raw[i] == "\x1b":
                # copy whole ANSI CSI sequence
                j = i + 1
                while j < len(raw) and raw[j] != "m":
                    j += 1
                j = min(j + 1, len(raw))
                out.append(raw[i:j])
                i = j
            else:
                # normal visible char
                if vis_col < width and not remove[vis_col]:
                    out.append(raw[i])
                vis_col += 1
                i += 1
        return "".join(out)

    return "\n".join(reconstruct(ln) for ln in lines_raw)


# ---------- overlap detection (sweep line) ----------
def find_overlap_segments(cues):
    """Return chronological list of overlap segments.
       Each segment: { 'start': ms, 'end': ms, 'members': [idx,...] } with end>start and len(members)>=2.
       Uses half-open intervals: [start, end) so end==next start is NOT overlapping.
    """
    events = []  # (time, typ, idx) where typ: 0=end, 1=start  (end before start at same time)
    for c in cues:
        events.append((c["s_ms"], 1, c["idx"]))
        events.append((c["e_ms"], 0, c["idx"]))
    events.sort()

    active = set()
    segments = []
    prev_t = None

    # group events by identical time
    i = 0; L = len(events)
    while i < L:
        t = events[i][0]
        # record segment up to t if currently overlapping
        if prev_t is not None and t > prev_t and len(active) >= 2:
            segments.append({"start": prev_t, "end": t, "members": tuple(sorted(active))})
        # process all end events at t
        while i < L and events[i][0] == t and events[i][1] == 0:
            active.discard(events[i][2]); i += 1
        # then all start events at t
        while i < L and events[i][0] == t and events[i][1] == 1:
            active.add(events[i][2]); i += 1
        prev_t = t

    return segments

def coalesce_segments(segments):
    """Merge consecutive segments that have identical member sets."""
    if not segments: return []
    merged = [segments[0].copy()]
    for seg in segments[1:]:
        last = merged[-1]
        if seg["members"] == last["members"] and seg["start"] == last["end"]:
            last["end"] = seg["end"]
        else:
            merged.append(seg.copy())
    return merged

# ---------- table building ----------
def term_width(override):
    if override: return max(20, override - 3)   # per user: N-3
    try:
        return shutil.get_terminal_size(fallback=(100, 24)).columns
    except Exception:
        return 100

def pad_visible_plain(s, width, align="left"):
    vis = strip_ansi(s)
    if len(vis) > width:
        vis = vis[:width]
    if align == "right":  return vis.rjust(width)
    if align == "center": return vis.center(width)
    return vis.ljust(width)

def fmt_lines(nums, width_each, sep=" "):
    return sep.join(f"{n:>{width_each}d}" for n in nums)

def build_table_from_segments(cues, segments, total_cols):
    # Resolve segment members to lines/lyrics and compose overlap label
    rows = []
    by_idx = {c["idx"]: c for c in cues}
    for seg in segments:
        members = [by_idx[i] for i in seg["members"]]
        lines = [m["line"] for m in members]
        lyrics = [m["lyric"] for m in members if m["lyric"]]
        overlap_pair = f"{ms_to_ts(seg['start'])} --> {ms_to_ts(seg['end'])}"
        rows.append({
            "count": len(members),
            "overlap": overlap_pair,
            "lines": sorted(lines),
            "lyrics": list(OrderedDict.fromkeys(lyrics))
        })

    if not rows: return ""

    # Column headers (3-line for Lines)
    H1, H2, H4 = "Dupes", "Timestamp", "Lyrics"
    H3_parts = ["Line #s"]

    max_count   = max(r["count"] for r in rows)
    max_line_no = max(max(r["lines"]) for r in rows)
    line_w = max(2, len(str(max_line_no)))
    row_line_strs = [fmt_lines(r["lines"], width_each=line_w) for r in rows]
    max_overlap_len = max(len(r["overlap"]) for r in rows)

    w1 = max(len(H1), len(str(max_count)))
    w2 = max(len(H2), max_overlap_len, len("00:00:00,000 --> 00:00:00,000"))
    tmp_w3_needed = max([len("Lines")] + ([len(s) for s in row_line_strs] or [len("Lines")]))

    budget = max(20, total_cols - 2)  # minus borders
    sep_spaces = 9
    w3 = min(tmp_w3_needed, max(8, (budget - (w1 + w2 + sep_spaces)) // 3))
    w4 = max(10, budget - (w1 + w2 + w3 + sep_spaces))
    if w4 < 10:
        reclaim = 10 - w4
        w3 = max(8, w3 - reclaim)
        w4 = max(10, budget - (w1 + w2 + w3 + sep_spaces))

    def bar(ch_left, ch_mid, ch_right, ch_fill="━"):
        return f"{MAGENTA}{ch_left}{ch_fill*(w1+2)}{ch_fill[0:0]}{ch_mid}{ch_fill*(w2+2)}{ch_mid}{ch_fill*(w3+2)}{ch_mid}{ch_fill*(w4+2)}{ch_right}{RESET}"
    top    = bar("┏","┯","┓")
    mid    = bar("┠","┼","┨")
    bottom = bar("┗","┷","┛")

    def row(c1, c2, c3, c4, colors):
        p1 = pad_visible_plain(c1, w1); p2 = pad_visible_plain(c2, w2); p3 = pad_visible_plain(c3, w3); p4 = pad_visible_plain(c4, w4)
        p1 = f"{colors[0]}{p1}{RESET}"; p2 = f"{colors[1]}{p2}{RESET}"; p3 = f"{colors[2]}{p3}{RESET}"; p4 = f"{colors[3]}{p4}{RESET}"
        return (f"{MAGENTA}┃{RESET} {p1} {MAGENTA}┃{RESET} "
                f"{p2} {MAGENTA}┃{RESET} "
                f"{p3} {MAGENTA}┃{RESET} "
                f"{p4} {MAGENTA}┃{RESET}")

    out = [top]
    out.append(row(H1, H2, H3_parts[0], H4, (BRIGHT_GREEN, BRIGHT_GREEN, BRIGHT_GREEN, BRIGHT_GREEN)))
    #out.append(row("",  "",  H3_parts[1], "",  (BRIGHT_GREEN, BRIGHT_GREEN, BRIGHT_GREEN, BRIGHT_GREEN)))
    #out.append(row("",  "",  H3_parts[2], "",  (BRIGHT_GREEN, BRIGHT_GREEN, BRIGHT_GREEN, BRIGHT_GREEN)))
    out.append(mid)

    for i, r in enumerate(rows):
        lines_str = fmt_lines(r["lines"], width_each=line_w)
        lyric_join = " • ".join(OrderedDict.fromkeys([l for l in r["lyrics"] if l]))
        if len(lyric_join) > w4: lyric_join = lyric_join[:w4]
        out.append(row(str(r["count"]), r["overlap"], lines_str, lyric_join,
                       (BRIGHT_CYAN, CYAN, RED, ORANGE)))

    out.append(bottom)
    return "\n".join(out)

# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Detect true subtitle overlaps (end==next start allowed).")
    ap.add_argument("srt", help="input .srt file")
    ap.add_argument("--columns","-c", type=int, help="override detected console width (uses N-3)")
    args = ap.parse_args()

    cues = parse_srt(args.srt)
    if not cues:
        return

    segs = find_overlap_segments(cues)
    segs = coalesce_segments(segs)
    if not segs:
        return  # silent when no overlaps

    cols = term_width(args.columns)
    table = build_table_from_segments(cues, segs, cols)
    if table:
        MSG = f"{BRIGHT_RED}✨ ✪ ✪ ✪ Karaoke Timestamp Problems! ✪ ✪ ✪ ✨"
        print(f"{BIG_TOP}{MSG}")
        print(f"{BIG_BOT}{MSG}")
        print(f"{BIG_OFF}", end="")
        print(reduce_vertical_whitespace(table))

if __name__ == "__main__":
    main()
