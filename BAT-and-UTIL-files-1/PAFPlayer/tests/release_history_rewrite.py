"""Rewrite archival history entries from the V571 source-comparison audit.

Run after release_history_audit.py. This emits a draft into tests/reports;
the reviewed draft is copied into the changelog only after a verified backup.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "tests" / "reports" / "v571_release_history_diff_evidence.json"
DRAFT = ROOT / "tests" / "reports" / "v571_changelog_draft.md"
SOURCE = ROOT / "docs" / "PAFPlayer_changelog.md"
HEADING = re.compile(r"^## V(\d+)(?:\s|$)", re.MULTILINE)
BOILERPLATE = "This description comes from the filename"


def curated_summaries() -> dict[int, str]:
    summaries: dict[int, str] = {}
    for path in sorted((ROOT / "tests" / "reports").glob("v571_curated_*.tsv")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            label, summary = line.split("\t", 1)
            version = int(label.removeprefix("V"))
            assert version not in summaries, (version, path)
            summaries[version] = summary.strip()
    return summaries


# These entries need a close reading because no version-specific test was added,
# the nearest archived predecessor is distant, or the change has several parts.
MANUAL: dict[int, str] = {
    472: "The surviving V472 file is a one-time integration script, not a full player snapshot. It embeds the visual screensaver module into V471, adds screensaver web routes and activity tracking, and updates the program version after checking and backing up the starting source. The resulting V472 source is not present in this archive.",
    457: "Bundled feature modules into the single-file player through an import finder and loader, allowing the archived release to run without separate feature files.",
    425: "Filtered a Nest camera's ‘Live video from your Nest camera’ media session out of the active-audio monitor. The media probe now reads each session title before deciding whether its app family should count, and the HUD-row handling is adjusted with that exclusion.",
    414: "Added explicit repeat and shuffle play-order modes, including Repeat 1, Repeat Folder, Repeat playlist, Sequential, history shuffle, random shuffle, and Repeat OFF. Added actions to cycle modes forward, backward, or by double action, with bounded saved mode values.",
    413: "Added a Repeat transport button and a playback-speed selector to the web interface. The repeat state is reflected in the button, and changing speed dispatches the existing web-set action.",
    412: "Removed extra control and status redraws from the volume restart path, reducing work done during a volume adjustment.",
    411: "Carried the current DRCS and Sixel enable state into visualizer transitions so a transition uses the live state rather than a stale captured value.",
    410: "Kept visualizer command-line choices session-only and added a Ctrl+Alt+V visualizer toggle to both character and asynchronous key handling, with a latch that prevents duplicate actions while held.",
    409: "Reduced pause/resume audio-start latency by capping the buffer used on resume at 50 ms while leaving normal launches on their configured buffer.",
    408: "Made shuffle and repeat state visible and unambiguous: the web transport uses distinct active styling, the console announces the resulting enabled/disabled state, and the help/status display shows both modes.",
    407: "Centralized detection of command-line preference overrides and kept those values in runtime settings only. Saving through the web interface no longer writes temporary CLI choices into global preferences.",
    406: "Kept --no-visualizers and related visualizer command-line overrides temporary for the current run, using a runtime settings merge rather than persisting them.",
    403: "Changed the default visualizer/karaoke compositing mode to the legacy layout, validated the saved mode range, and regrouped web controls into their playback and visualizer sections.",
    396: "Highlighted the experimental cursive-fix control in the web karaoke section with its own color treatment so it remains visually distinct.",
    392: "Added --simple and --light as lightweight-run presets that disable console and popup artwork, the web server, the now-playing sidecar, and visualizers for the current launch.",
    391: "Added --no-chafa-album-art-in-console to suppress the pre-play Chafa artwork grid while retaining popup artwork, web artwork, and visualizers. The same source also adjusts several EmojiMaxx mappings.",
    365: "Extended the EmojiMaxx CLI preview to print both the normal substituted lyric and a double-height karaoke preview using the terminal's upper/lower line sequences.",
    363: "The compared source changes release identity strings only; no playback or UI code change is visible in the surviving V362→V363 diff. Its ‘extended release summary’ title cannot be verified from this source alone.",
    360: "The compared source changes release identity strings only; no command-line parser or help-text change is visible in the surviving V359→V360 diff.",
    354: "Changed the pause action's on-screen interaction label to ‘Pause’ when the pause toggle is pressed.",
    353: "Anchored the final HUD field to the right edge whenever there is room, while preserving the minimum gap from the preceding field.",
    352: "Included Album among the HUD metadata fields allowed to anchor at the right edge of a row.",
    351: "Treated circled-number symbols as text-width glyphs during HUD/lyric cell measurement instead of letting them take emoji-width spacing.",
    350: "Closed the all-tags view when navigation or natural track completion changes the active track, instead of carrying the old tag panel into the next track.",
    349: "Added continuous volume adjustment while a volume key is held: repeat begins after about 320 ms and continues every 85 ms until release.",
    348: "Stopped toggling the native Tk artwork-window style on focus changes. Keeping the HWND style stable prevents focus and position bounce, while the transparent wrapper still supplies the focus border.",
    345: "Centered Song between Act and a right-side metadata field, and Genre between Year and a right-side field, when the HUD row has enough space.",
    343: "Restored natural left-to-right placement for ordinary metadata rows. Only selected tail fields take the right edge, avoiding large gaps in wide terminals.",
    342: "Suppressed a startup interaction notice for web requests that lock or unlock artwork-color autoslide; the setting action still runs.",
    341: "Made the album-art karaoke toggle a hard gate for artwork lyrics: when disabled, the current artwork lyric is cleared rather than rendered through an old state.",
    340: "Delayed the visualizer interaction overlay for four seconds after startup and suppressed its notice for the dismiss action.",
    339: "Removed the automatic EmojiMaxx substitution of ‘shocked’ with the surprised-face symbol.",
    338: "Rendered floating karaoke lyrics immediately on the synchronization path instead of only scheduling a later floating-window render.",
    325: "Restored the normal terminal character set while drawing the volume feedback box border, preventing the bottom border glyphs from inheriting the visualizer's soft-font state.",
    315: "Added extra spacing after a sung circled number in the current double-height lyric line so Windows Terminal does not visually glue the number to the following word. Adjacent lyric lines retain their original spacing.",
    313: "Accepted either Claire audio-processing API version attribute and parsed its numeric value defensively, improving compatibility with older helper modules.",
    275: "Replaced the visualizer worker's imprecise event wait with a coarse sleep followed by a short deadline spin for 120 Hz pacing. Synchronized profiler totals between worker and owner threads, kept the profiler open until Escape, and refreshed benchmark progress between samples.",
    274: "Moved visualizer rendering onto a dedicated thread, enabled finer Windows timer resolution for the worker, and made profiler collection cumulative and explicit.",
    236: "Resized the web layout to reserve a larger lyric area, added a dedicated Web Karaoke section with its own enable switch and controls, and placed autoslide and lyric actions alongside it.",
    224: "Made direct web controls resilient to status polling by tracking a pending user change for up to 2.5 seconds. Poll updates no longer immediately snap a newly changed control back to its old value.",
    223: "Tried a shared artwork/karaoke compositor that can apply separate background strengths to karaoke rows and visualizer rows. The archived experiment is marked broken; the source diff establishes the implementation attempt, not a working release.",
    222: "Switched fitted cover art from bilinear resize to Lanczos and cached an edge-aware unsharp-mask pass for the console artwork grid.",
    221: "Reduced the browser analyzer to 48 bins and made karaoke-owned artwork rows use delta-row updates. Also preserved natural art-strip alignment when the strip already fills the width.",
    219: "Built a multi-artwork strip from each cover's fitted natural width, then tiled the strip only when it was narrower than the console area.",
    218: "Added a tall visualizer layout and an alternate HUD action on Ctrl+Alt+H. The renderer also uses row-independent colors when available.",
    217: "Expanded the console artwork colormap from one cover to as many as four embedded artwork variants, fitting each panel to the terminal cell aspect ratio.",
    216: "Saved visualizer row count, top-row truncation, artwork coloring, and karaoke-expansion choices as player settings. Karaoke expansion now defaults off.",
    215: "Changed the web grid so the karaoke lyric area can occupy the full content width rather than sharing the narrower left column.",
    214: "Widened the web controls layout and split Console Visualizer and Console Karaoke into visible groups. Renamed artwork saturation controls and added a cover-art visualizer demo action.",
    213: "Fitted cover art using the actual terminal cell aspect ratio and reserved karaoke background rows in the artwork-colored visualizer when those modes are active.",
    212: "Added a live karaoke display offset that shifts lyric lookup without altering audio or lyric files. The web transport exposes K−/K+ buttons and shows the active offset.",
    211: "Made console cover art fit vertically and tile across the available width. Replaced the demo dropdown with a reversible Cover Demo button that restores the prior artwork-color settings.",
    210: "Repaired the web control builder's JavaScript selection logic by replacing a nested conditional with explicit control-group branches.",
    209: "Split experimental artwork coloring into independent checkboxes for blackness, bars, karaoke sides, and karaoke text, with matching web-control state and aspect-aware tiling.",
    207: "Grouped web configuration controls into Playback, Visualizer, Karaoke, and Progress sections with distinct colors and separate hosts for each control type.",
    206: "Expanded and regrouped command-line help into playback history, karaoke, and progress sections, with more room for explanations and defaults.",
    205: "Added experimental web controls for artwork color source, strength, and cover demos, and split the configuration page into Visualizer and Karaoke groups.",
    202: "Changed the artwork lyrics-mode control to switch between artwork-enabled and floating-lyrics modes, save the selected mode, and expose a command to reveal the floating lyrics window.",
    199: "The V198→V199 source diff changes release identity only. The archived label mentions history and idle fixes, but this source does not show those changes; they may have been in an unarchived intermediate build.",
    165: "The V165 source contains a viewport-based HUD anchor that follows terminal resizing, plus floating-lyrics geometry handling. The nearest earlier full snapshot is V119, so the archive cannot isolate which intervening version introduced each part; the archived build is also marked as having title-bar trouble.",
    49: "Added analyzer diagnostic theories 36–40 to separate spectrum capture cost from visualizer rendering: disable or delay capture, use dummy levels, discard publication, or render synthetic levels without the analyzer.",
    13: "The earliest surviving full source already includes DRCS and Sixel visualizer actions, album-art visualizer and karaoke overlay controls, and URL extraction from track comments. No earlier full source survives to isolate what V13 introduced.",
}


def evidence(row: dict) -> str:
    if row["status"] != "compared":
        return f"Evidence: `{row['target']}` in `C:\\BAT\\PAFPlayer\\releases`; {row['status']}."
    old = row["predecessor_version"]
    new = row["version"]
    detail = f"compared V{old}→V{new} archived source"
    names = row.get("added_defs", [])[:3]
    if names:
        detail += "; added " + ", ".join(f"`{name}`" for name in names)
    tests = [name for name in row.get("added_tests", []) if name.startswith(f"test_v{new}_")][:2]
    if tests:
        detail += "; tests " + ", ".join(f"`{name}`" for name in tests)
    return "Evidence: " + detail + "."


def main() -> None:
    rows = {row["version"]: row for row in json.loads(AUDIT.read_text(encoding="utf-8"))["entries"]}
    curated = curated_summaries()
    assert set(rows) == set(MANUAL) | set(curated)
    assert not set(MANUAL) & set(curated)
    source = SOURCE.read_text(encoding="utf-8")
    heads = list(HEADING.finditer(source))
    chunks = [source[:heads[0].start()]]
    changed = 0
    for index, head in enumerate(heads):
        end = heads[index + 1].start() if index + 1 < len(heads) else len(source)
        section = source[head.start():end]
        version = int(head.group(1))
        if version in rows:
            row = rows[version]
            summary = MANUAL.get(version) or curated[version]
            section = f"## V{version}\n\n{summary}\n\n{evidence(row)}\n\n"
            changed += 1
        chunks.append(section)
    DRAFT.write_text("".join(chunks), encoding="utf-8")
    print(f"Drafted {changed} entries: {DRAFT}")
    print("Manual summaries:", len(MANUAL))


if __name__ == "__main__":
    main()
