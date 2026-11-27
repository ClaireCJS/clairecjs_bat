from __future__ import annotations

import datetime
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def backup(path: Path, archive: Path) -> Path:
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
    stem = path.name + f".bak.{stamp}.replaced-by-chatgpt"
    candidate = path.with_name(stem + ".bak")
    number = 0
    while candidate.exists():
        number += 1
        candidate = path.with_name(stem + f" ({number}).bak")
    shutil.copy2(path, candidate)
    original_hash = hashlib.sha256(path.read_bytes()).digest()
    if hashlib.sha256(candidate.read_bytes()).digest() != original_hash:
        raise RuntimeError(f"Backup verification failed: {candidate}")
    archive.mkdir(parents=True, exist_ok=True)
    destination = archive / candidate.name
    number = 0
    while destination.exists():
        number += 1
        destination = archive / (stem + f" ({number}).bak")
    candidate.rename(destination)
    return destination


def replace_once(path: Path, before: str, after: str) -> None:
    data = path.read_text(encoding="utf-8-sig")
    count = data.count(before)
    if count != 1:
        raise RuntimeError(f"Expected exactly one target in {path}; got {count}: {before[:100]!r}")
    path.write_text(data.replace(before, after), encoding="utf-8", newline="")


main = ROOT / "PAFPlayer.py"
readme = ROOT / "docs" / "README.md"
changelog = ROOT / "docs" / "PAFPlayer_changelog.md"
release = ROOT / "releases" / "PAFPlayer_v763_circled_number_spacing.py"
for path, archive in (
    (main, ROOT / "releases"),
    (readme, ROOT / "docs" / "backups"),
    (changelog, ROOT / "docs" / "backups"),
    (release, ROOT / "releases"),
):
    print("BACKUP", backup(path, archive))

replace_once(main, "PLAYER_BUILD_ID = '2026-11-27-v763-circled-number-spacing'",
             "PLAYER_BUILD_ID = '2026-11-27-v764-circled-number-single-gap'")
replace_once(main, "PROGRAM_VERSION = 'V763'", "PROGRAM_VERSION = 'V764'")
replace_once(main, "PROGRAM_RELEASE_LABEL = 'V763'", "PROGRAM_RELEASE_LABEL = 'V764'")
replace_once(
    main,
    '''    # Circled-number substitutions already have their source lyric spacing.
    # Adding terminal-only padding here made Windows Terminal show a visible
    # gap after ❶–❿, so preserve those replacements exactly. Keep the separate
    # single safety cell for the small set of glyphs that still needs it.
    result = str(replacement)
    if str(semantic_key).casefold() in WINDOWS_TERMINAL_SINGLE_SPACE_EMOJIMAX_KEYS:
        result += " "
    return result''',
    '''    # One safety cell is consumed by Windows Terminal's double-height glyph
    # advance; the lyric's own separator supplies the visible one-cell gap.
    result = re.sub(
        rf"(?:[{re.escape(WINDOWS_TERMINAL_SPACED_EMOJIMAX_GLYPHS)}]+⓿?|⓿)",
        lambda match: match.group(0) + " ",
        str(replacement),
    )
    if str(semantic_key).casefold() in WINDOWS_TERMINAL_SINGLE_SPACE_EMOJIMAX_KEYS:
        result += " "
    return result''',
)
replace_once(
    main,
    '''    def test_v763_circled_number_spacing_preserves_only_lyric_spacing(self) -> None:
        self.assertEqual("❶", windows_terminal_emojimax_replacement("❶"))
        self.assertEqual("❶❽", windows_terminal_emojimax_replacement("❶❽"))
        terminal = stylize_karaoke_with_emojimax(
            "1 8 qzv", 1, True, 1.0,
            force_emoji_when_enabled=True,
            windows_terminal_compat=True,
        )
        self.assertIn("❶ ❽ qzv", ANSI_CSI_RE.sub("", terminal))
        for glyph in WINDOWS_TERMINAL_SPACED_EMOJIMAX_GLYPHS:
            self.assertEqual(glyph + " word", windows_terminal_emojimax_replacement(glyph + " word"))''',
    '''    def test_v764_circled_number_spacing_leaves_one_visible_gap(self) -> None:
        self.assertEqual("❶ ", windows_terminal_emojimax_replacement("❶"))
        self.assertEqual("❶❽ ", windows_terminal_emojimax_replacement("❶❽"))
        self.assertEqual("❹⓿ ", windows_terminal_emojimax_replacement("❹⓿"))
        terminal = stylize_karaoke_with_emojimax(
            "1 8 qzv", 1, True, 1.0,
            force_emoji_when_enabled=True,
            windows_terminal_compat=True,
        )
        self.assertIn("❶  ❽  qzv", ANSI_CSI_RE.sub("", terminal))
        for glyph in WINDOWS_TERMINAL_SPACED_EMOJIMAX_GLYPHS:
            self.assertEqual(glyph + "  word", windows_terminal_emojimax_replacement(glyph + " word"))''',
)
replace_once(main, 'self.assertEqual("❹⓿", windows_terminal_emojimax_replacement("❹⓿"))',
             'self.assertEqual("❹⓿ ", windows_terminal_emojimax_replacement("❹⓿"))')
replace_once(main, 'self.assertEqual("❶❽", windows_terminal_emojimax_replacement("❶❽"))',
             'self.assertEqual("❶❽ ", windows_terminal_emojimax_replacement("❶❽"))')

replace_once(readme,
             "Current release: **V763** — remove unwanted extra spaces after circled-number lyrics in Windows Terminal.\n[Release notes](../releases/PAFPlayer_v763_circled_number_spacing_release_notes.md).",
             "Current release: **V764** — tune Windows Terminal circled-number spacing to leave one visible gap in karaoke.\n[Release notes](../releases/PAFPlayer_v764_circled_number_single_gap_release_notes.md).")
replace_once(changelog, "# PAFPlayer changelog\n\n",
             "# PAFPlayer changelog\n\n## V764 — November 27, 2026\n\nRestore one Windows Terminal safety cell after ❶–❿ substitutions. The renderer consumes that cell, leaving the lyric's own separator visible as one gap; contiguous number glyphs receive padding only after the whole run. [Release notes](../releases/PAFPlayer_v764_circled_number_single_gap_release_notes.md).\n\n")
replace_once(readme,
             "### V763: remove extra spacing after circled lyric numbers\n\nWindows Terminal no longer receives two synthetic spaces after ❶–❿ Emojimax substitutions. The lyric's original whitespace is preserved, including spaces between adjacent enclosed digits. The separate one-cell pen-glyph workaround remains.\n\n\n",
             "### V764: keep one visible gap after circled lyric numbers\n\nWindows Terminal receives one safety cell after each contiguous run of ❶–❿ substitutions. Double-height rendering consumes that compatibility cell, while the lyric's own separator remains visible as one gap. A run such as ❶❽ is padded only after its final digit. The separate pen-glyph workaround remains.\n\n\n")

notes = ROOT / "releases" / "PAFPlayer_v764_circled_number_single_gap_release_notes.md"
if notes.exists():
    raise FileExistsError(notes)
notes.write_text(
    "# PAFPlayer V764 — one visible circled-number gap\n\n"
    "Restore exactly one Windows Terminal compatibility cell after each contiguous run of bold circled-number substitutions. Double-height rendering consumes that cell; the lyric's normal separator remains as the single visible gap before the next word. Contiguous number glyphs stay together and receive padding only after the run. The separate pen glyph workaround is unchanged.\n\n"
    "## Validation\n\n"
    "The embedded checks cover a single ❶, adjacent circled glyphs, a ❹⓿ compound, lyrics with one source separator, and all ❶–❿ markers. The active runnable source was syntax-compiled and copied byte-for-byte to the release artifact. Use `pafplayer --emojimax \"4 3 2 1 5 6\"` to inspect number glyph rendering in the console.\n",
    encoding="utf-8",
    newline="",
)

shutil.copy2(main, release)
digest = hashlib.sha256(main.read_bytes()).digest()
if hashlib.sha256(release.read_bytes()).digest() != digest:
    raise RuntimeError("Release file does not match active source")
print("ACTIVE", main)
print("RELEASE", release)
print("NOTES", notes)
print("SHA256", hashlib.sha256(digest).hexdigest())
