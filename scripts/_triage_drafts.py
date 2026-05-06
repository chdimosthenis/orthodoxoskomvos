"""Categorize draft saint files for the review-drafts triage pass.

Usage:
  python scripts/_triage_drafts.py            # report only (read-only)
  python scripts/_triage_drafts.py --publish  # apply: remove `draft: true`
                                              # from bot-publishable entries
                                              # (skips suspects, user-authored,
                                              # and the agathius/acacius duplicate)

Reads every .md in src/content/saints/ with `draft: true`, classifies into:
  - bot-publishable: auto-seeded by daily-saints.yml, real-saint name
  - bot-suspect:     auto-seeded but filename suggests place/date/object
  - user-authored:   license: original (or language: el with no auto notice)

In --publish mode, removes the `draft: true` line from bot-publishable
entries only. Idempotent.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAINTS_DIR = ROOT / "src" / "content" / "saints"

AUTO_SEEDED_MARKER = "auto-seeded from Wikipedia by the daily commemoration bot"

# Filename heuristics for likely false positives — places, dates, navigation
SUSPECT_PREFIXES = (
    "river-",
    "march-",
    "april-",
    "may-",
    "june-",
    "july-",
    "august-",
    "september-",
    "october-",
    "november-",
    "december-",
    "january-",
    "february-",
)
SUSPECT_KEYWORDS = (
    "basilica",
    "monastery-of",
    "cathedral",
    "abbey-of",
    "diocese",
)


def classify(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    if "draft: true" not in text:
        return ("not-draft", "")
    is_bot = AUTO_SEEDED_MARKER in text
    is_original = re.search(r"^license:\s*original", text, re.MULTILINE) is not None
    is_greek = re.search(r"^language:\s*el", text, re.MULTILINE) is not None
    if is_bot and not is_original:
        suspect = any(path.stem.startswith(p) for p in SUSPECT_PREFIXES) or any(
            kw in path.stem for kw in SUSPECT_KEYWORDS
        )
        return ("bot-suspect" if suspect else "bot-publishable", path.stem)
    return ("user-authored", path.stem) if is_original or is_greek else ("ambiguous", path.stem)


# Filenames to skip even if classified bot-publishable (known duplicates)
EXCLUDE_FROM_PUBLISH = {
    "agathius-of-byzantium.md",  # duplicate of acacius.md (same person, same icon)
}


def remove_draft_line(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(r"^draft:\s*true\s*\n", "", text, count=1, flags=re.MULTILINE)
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> int:
    if not SAINTS_DIR.is_dir():
        print(f"ERROR: not found: {SAINTS_DIR}", file=sys.stderr)
        return 1

    do_publish = "--publish" in sys.argv

    buckets: dict[str, list[str]] = {
        "bot-publishable": [],
        "bot-suspect": [],
        "user-authored": [],
        "ambiguous": [],
    }
    paths_by_bucket: dict[str, list[Path]] = {k: [] for k in buckets}
    for path in sorted(SAINTS_DIR.glob("*.md")):
        kind, _ = classify(path)
        if kind == "not-draft":
            continue
        buckets.setdefault(kind, []).append(path.name)
        paths_by_bucket.setdefault(kind, []).append(path)

    for kind, names in buckets.items():
        print(f"## {kind} ({len(names)})")
        for n in names:
            print(f"  {n}")
        print()

    total = sum(len(v) for v in buckets.values())
    print(f"TOTAL drafts: {total}")

    if do_publish:
        print()
        print("=== --publish mode: applying ===")
        published = []
        skipped_excluded = []
        for path in paths_by_bucket["bot-publishable"]:
            if path.name in EXCLUDE_FROM_PUBLISH:
                skipped_excluded.append(path.name)
                continue
            if remove_draft_line(path):
                published.append(path.name)
        print(f"Published: {len(published)}")
        print(f"Skipped (excluded): {skipped_excluded}")
        print(f"Suspects left as draft: {buckets['bot-suspect']}")
        print(f"User-authored left alone: {buckets['user-authored']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
