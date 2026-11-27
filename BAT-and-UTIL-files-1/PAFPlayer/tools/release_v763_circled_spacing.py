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
    n = 0
    while candidate.exists():
        n += 1
        candidate = path.with_name(stem + f" ({n}).bak")
    shutil.copy2(path, candidate)
    digest = hashlib.sha256(path.read_bytes()).digest()
    if hashlib.sha256(candidate.read_bytes()).digest() != digest:
        raise RuntimeError(f"Backup verification failed: {candidate}")
    archive.mkdir(parents=True, exist_ok=True)
    destination = archive / candidate.name
    n = 0
    while destination.exists():
        n += 1
        destination = archive / (stem + f" ({n}).bak")
    candidate.rename(destination)
    if hashlib.sha256(destination.read_bytes()).digest() != digest:
        raise RuntimeError(f"Archived backup verification failed: {destination}")
    return destination


def replace(path: Path, old: str, new: str) -> None:
    data = path.read_text(encoding="utf-8-sig")
    count = data.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match in {path}, found {count}: {old[:80]!r}")
    path.write_text(data.replace(old, new), encoding="utf-8", newline="")


main = ROOT / "PAFPlayer.py"
readme = ROOT / "docs" / "README.md"
changelog = ROOT / "docs" / "PAFPlayer_changelog.md"
for path, archive in (
    (main, ROOT / "releases"),
    (readme, ROOT / "docs" / "backups"),
    (changelog, ROOT / "docs" / "backups"),
):
    print("BACKUP", backup(path, archive))

replace(main, "PLAYER_BUILD_ID = '2026-11-26-v762-late-preview-handoff'",
        "PLAYER_BUILD_ID = '2026-11-27-v763-circled-number-spacing'")
replace(main, "PROGRAM_VERSION = 'V762'", "PROGRAM_VERSION = 'V763'")
replace(main, "PROGRAM_RELEASE_LABEL = 'V762'", "PROGRAM_RELEASE_LABEL = 'V763'")
replace(
    main,
    '''    result = pattern.sub(lambda match: match.group(0) + "  ", str(replacement))
    if str(semantic_key).casefold() in WINDOWS_TERMINAL_SINGLE_SPACE_EMOJIMAX_KEYS:
        result += " "
    return result''',
    '''    # Circled-number substitutions already have their source lyric spacing.
    # Adding terminal-only padding here made Windows Terminal show a visible
    # gap after ❶–❿, so preserve those replacements exactly. Keep the separate
    # single safety cell for the small set of glyphs that still needs it.
    result = str(replacement)
    if str(semantic_key).casefold() in WINDOWS_TERMINAL_SINGLE_SPACE_EMOJIMAX_KEYS:
        result += " "
    return result''',
)
replace(
    main,
    '''    def test_v367_circled_number_terminal_spacing_has_two_generated_safety_cells(self) -> None:
        self.assertEqual("❶  ", windows_terminal_emojimax_replacement("❶"))
        self.assertEqual("❶  ❽  ", windows_terminal_emojimax_replacement("❶❽"))
        self.assertEqual("❶    word", compensate_current_circled_number_spacing("❶ word"))
        terminal = stylize_karaoke_with_emojimax(
            "1 8 qzv", 1, True, 1.0,
            force_emoji_when_enabled=True,
            windows_terminal_compat=True,
        )
        self.assertIn("❶   ❽   qzv", ANSI_CSI_RE.sub("", terminal))''',
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
)
replace(main, 'self.assertEqual("❹⓿  ", windows_terminal_emojimax_replacement("❹⓿"))',
        'self.assertEqual("❹⓿", windows_terminal_emojimax_replacement("❹⓿"))')
replace(main, 'self.assertEqual("❶  ❽  ", windows_terminal_emojimax_replacement("❶❽"))',
        'self.assertEqual("❶❽", windows_terminal_emojimax_replacement("❶❽"))')

replace(readme, "Current release: **V754** — X accepts arbitrary positive speed multipliers.\n[Release notes](../releases/PAFPlayer_v754_arbitrary_speed_release_notes.md).",
        "Current release: **V763** — remove unwanted extra spaces after circled-number lyrics in Windows Terminal.\n[Release notes](../releases/PAFPlayer_v763_circled_number_spacing_release_notes.md).")
replace(changelog, "# PAFPlayer changelog\n\n",
        "# PAFPlayer changelog\n\n## V763 — November 27, 2026\n\nRemove terminal-added padding after ❶–❿ lyric substitutions so only the lyric's own whitespace remains. Preserve the unrelated pen-glyph safety spacing. [Release notes](../releases/PAFPlayer_v763_circled_number_spacing_release_notes.md).\n\n")
replace(readme, "### V762: pause peers only when preview audio is ready",
        "### V763: remove extra spacing after circled lyric numbers\n\nWindows Terminal no longer receives two synthetic spaces after ❶–❿ Emojimax substitutions. The lyric's original whitespace is preserved, including spaces between adjacent enclosed digits. The separate one-cell pen-glyph workaround remains.\n\n\n### V762: pause peers only when preview audio is ready")

notes = ROOT / "releases" / "PAFPlayer_v763_circled_number_spacing_release_notes.md"
if notes.exists():
    raise FileExistsError(notes)
notes.write_text(
    "# PAFPlayer V763 — circled-number lyric spacing\n\n"
    "Windows Terminal karaoke no longer inserts two extra cells after bold circled-number substitutions ❶–❿. The original lyric spacing is kept, so the next sung word appears at the intended distance. Adjacent enclosed-number glyphs remain adjacent except for whitespace already present in the source text. The unrelated pen-glyph safety cell is unchanged.\n\n"
    "## Validation\n\n"
    "Validated the spacing helper and Windows Terminal-styled lyric output for ❶–❿, adjacent number glyphs, and the distinct pen safety case; compiled the runnable file and verified the release copy matches the active source.\n",
    encoding="utf-8",
    newline="",
)

release = ROOT / "releases" / "PAFPlayer_v763_circled_number_spacing.py"
if release.exists():
    raise FileExistsError(release)
shutil.copy2(main, release)
if hashlib.sha256(main.read_bytes()).digest() != hashlib.sha256(release.read_bytes()).digest():
    raise RuntimeError("Versioned release does not match active source")
print("ACTIVE", main)
print("RELEASE", release)
print("NOTES", notes)
print("SHA256", hashlib.sha256(main.read_bytes()).hexdigest())
