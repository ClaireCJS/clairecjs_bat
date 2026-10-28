"""Compare source-only release-history entries with surviving archived source.

The report is supporting evidence for retrospective changelog edits. It does
not import or run archived PAFPlayer versions.
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = Path(r"C:\BAT\PAFPlayer\releases")
REPORT = ROOT / "tests" / "reports" / "v571_release_history_diff_evidence.json"
BOILERPLATE = "This description comes from the filename"
VERSION_FILE = re.compile(r"^PAFPlayer_v(\d+)(?:[_-].*)?\.py$", re.IGNORECASE)
HEADING = re.compile(r"^## V(\d+)(?:\s|$)", re.MULTILINE)
DEF = re.compile(r"^\s*(?:async\s+)?(?:def|class)\s+([\w]+)")


def source_catalog() -> dict[int, Path]:
    choices: dict[int, list[Path]] = {}
    for path in ARCHIVE.glob("PAFPlayer_v*.py"):
        match = VERSION_FILE.match(path.name)
        if match and path.stat().st_size > 100_000:
            choices.setdefault(int(match.group(1)), []).append(path)
    return {version: max(paths, key=lambda path: path.stat().st_size)
            for version, paths in choices.items()}


def sections() -> list[tuple[int, str]]:
    source = (ROOT / "docs" / "PAFPlayer_changelog.md").read_text(encoding="utf-8")
    heads = list(HEADING.finditer(source))
    return [(int(head.group(1)), source[head.start():heads[index + 1].start()
            if index + 1 < len(heads) else len(source)])
            for index, head in enumerate(heads)]


def internal_version(path: Path) -> str | None:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for index, line in enumerate(handle):
            match = re.search(r"^PROGRAM_VERSION\s*=\s*['\"](V\d+)", line)
            if match:
                return match.group(1)
            if index > 1000:
                break
    return None


def audit_one(item: tuple[int, str], catalog: dict[int, Path]) -> dict:
    version, section = item
    evidence = re.search(r"Evidence: `([^`]+\.py)`", section)
    target = ARCHIVE / evidence.group(1) if evidence else catalog.get(version)
    result: dict = {"version": version, "target": target.name if target else None}
    if not target or not target.is_file():
        result["status"] = "missing source"
        return result
    result["target_bytes"] = target.stat().st_size
    result["internal_version"] = internal_version(target)
    if target.stat().st_size <= 100_000:
        result["status"] = "not a full source snapshot"
        return result
    predecessor_version = max((candidate for candidate in catalog if candidate < version), default=None)
    if predecessor_version is None:
        result["status"] = "no earlier full source snapshot"
        return result
    predecessor = catalog[predecessor_version]
    result["predecessor_version"] = predecessor_version
    result["predecessor"] = predecessor.name
    result["predecessor_internal_version"] = internal_version(predecessor)
    diff = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "diff", "--no-index", "--unified=0",
         "--", str(predecessor), str(target)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if diff.returncode not in (0, 1):
        result["status"] = "diff failed"
        result["error"] = diff.stderr[:500]
        return result
    added: list[str] = []
    removed: list[str] = []
    for line in diff.stdout.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            if len(line) < 1000:
                added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            if len(line) < 1000:
                removed.append(line[1:])
    version_comment = re.compile(rf"(?:#|//|/\*)\s*V{version}\b", re.IGNORECASE)
    result.update({
        "status": "compared",
        "added_count": len(added),
        "removed_count": len(removed),
        "version_comments": [line.strip()[:300] for line in added
                             if version_comment.search(line)][:12],
        "added_defs": [match.group(1) for line in added
                       if (match := DEF.match(line)) and not match.group(1).startswith("test_")][:30],
        "added_tests": [match.group(1) for line in added
                        if (match := DEF.match(line)) and match.group(1).startswith("test_")][:15],
        "added_code": [line.strip()[:220] for line in added
                       if line.strip() and not line.lstrip().startswith(("#", "//", "*"))
                       and not re.search(r"(?:PROGRAM_VERSION|PLAYER_BUILD_ID|PROGRAM_RELEASE_LABEL|ARTIFACT BUILD)", line)
                       and not re.search(r"\b(?:assert|self\.assert|source =|html =|inspect\.)", line)][:65],
        "removed_code": [line.strip()[:220] for line in removed
                         if line.strip() and not line.lstrip().startswith(("#", "//", "*"))
                         and not re.search(r"(?:PROGRAM_VERSION|PLAYER_BUILD_ID|PROGRAM_RELEASE_LABEL|ARTIFACT BUILD)", line)][:30],
    })
    return result


def main() -> None:
    catalog = source_catalog()
    previous_versions: set[int] = set()
    if REPORT.exists():
        previous_versions = {row["version"] for row in
                             json.loads(REPORT.read_text(encoding="utf-8"))["entries"]}
    targets = [item for item in sections()
               if item[0] in previous_versions or BOILERPLATE in item[1]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda item: audit_one(item, catalog), targets))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"method": "git diff --no-index against nearest earlier full archived source",
                                  "entries": results}, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    status_counts = {status: sum(row["status"] == status for row in results)
                     for status in sorted({row["status"] for row in results})}
    print(f"Audited {len(results)} source-only entries: {status_counts}")
    print(REPORT)


if __name__ == "__main__":
    main()
