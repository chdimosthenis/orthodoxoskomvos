"""Seed bible/ collection with the 27 books of the New Testament from
el.wikisource.org (Patriarchal Text of 1904, public domain).

Each book is fetched as a single Wikisource page → cleaned HTML → markdown.
We write one .md per book (not per chapter): chapter boundaries within the
text are preserved as inline anchors that the user can jump to from the
per-book TOC rendered by the Astro page.

Usage:
    python fetch_bible.py             # seed all 27 books
    python fetch_bible.py --slug X    # one book
    python fetch_bible.py --force     # overwrite
    python fetch_bible.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from typing import Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from _common import (
    check_exists,
    clean_html,
    html_to_markdown,
    log,
    write_content,
)


HEADERS = {
    "User-Agent": "OrthodoxLogos/1.0 (bible seeder; +https://orthodoxoskomvos.gr)",
    "Accept-Language": "el-GR,el;q=0.9",
}

API_URL = "https://el.wikisource.org/w/api.php"

SOURCE_CREDIT = (
    "Πατριαρχικὸ Κείμενο τῆς Καινῆς Διαθήκης (Κωνσταντινούπολις 1904) — "
    "ἐπίσημη ἔκδοσις τοῦ Οἰκουμενικοῦ Πατριαρχείου. Public domain. "
    "Ψηφιακὴ ἔκδοση: el.wikisource.org."
)


# (slug, page_title, book_name_el, book_name_en, order, division)
ENTRIES: list[dict[str, Any]] = [
    # Gospels
    {"slug": "kata-matthaion", "page": "Κατά Ματθαίον",
     "book": "Κατὰ Ματθαῖον", "bookEnglish": "Gospel of Matthew",
     "order": 1, "division": "gospel"},
    {"slug": "kata-markon", "page": "Κατά Μάρκον",
     "book": "Κατὰ Μᾶρκον", "bookEnglish": "Gospel of Mark",
     "order": 2, "division": "gospel"},
    {"slug": "kata-loukan", "page": "Κατά Λουκάν",
     "book": "Κατὰ Λουκᾶν", "bookEnglish": "Gospel of Luke",
     "order": 3, "division": "gospel"},
    {"slug": "kata-ioannin", "page": "Κατά Ιωάννην",
     "book": "Κατὰ Ἰωάννην", "bookEnglish": "Gospel of John",
     "order": 4, "division": "gospel"},
    # Acts
    {"slug": "praxeis", "page": "Πράξεις των Αποστόλων",
     "book": "Πράξεις τῶν Ἀποστόλων", "bookEnglish": "Acts of the Apostles",
     "order": 5, "division": "acts"},
    # Pauline epistles
    {"slug": "pros-romaious", "page": "Προς Ρωμαίους",
     "book": "Πρὸς Ῥωμαίους", "bookEnglish": "Romans",
     "order": 6, "division": "paul"},
    {"slug": "pros-korinthious-a", "page": "Προς Κορινθίους Α'",
     "book": "Πρὸς Κορινθίους Α'", "bookEnglish": "1 Corinthians",
     "order": 7, "division": "paul"},
    {"slug": "pros-korinthious-b", "page": "Προς Κορινθίους Β'",
     "book": "Πρὸς Κορινθίους Β'", "bookEnglish": "2 Corinthians",
     "order": 8, "division": "paul"},
    {"slug": "pros-galatas", "page": "Προς Γαλάτας",
     "book": "Πρὸς Γαλάτας", "bookEnglish": "Galatians",
     "order": 9, "division": "paul"},
    {"slug": "pros-efesious", "page": "Προς Εφεσίους",
     "book": "Πρὸς Ἐφεσίους", "bookEnglish": "Ephesians",
     "order": 10, "division": "paul"},
    {"slug": "pros-filippisious", "page": "Προς Φιλιππησίους",
     "book": "Πρὸς Φιλιππησίους", "bookEnglish": "Philippians",
     "order": 11, "division": "paul"},
    {"slug": "pros-kolossaeis", "page": "Προς Κολοσσαείς",
     "book": "Πρὸς Κολοσσαεῖς", "bookEnglish": "Colossians",
     "order": 12, "division": "paul"},
    {"slug": "pros-thessalonikeis-a", "page": "Προς Θεσσαλονικείς Α'",
     "book": "Πρὸς Θεσσαλονικεῖς Α'", "bookEnglish": "1 Thessalonians",
     "order": 13, "division": "paul"},
    {"slug": "pros-thessalonikeis-b", "page": "Προς Θεσσαλονικείς Β'",
     "book": "Πρὸς Θεσσαλονικεῖς Β'", "bookEnglish": "2 Thessalonians",
     "order": 14, "division": "paul"},
    {"slug": "pros-timotheon-a", "page": "Προς Τιμόθεον Α'",
     "book": "Πρὸς Τιμόθεον Α'", "bookEnglish": "1 Timothy",
     "order": 15, "division": "paul"},
    {"slug": "pros-timotheon-b", "page": "Προς Τιμόθεον Β'",
     "book": "Πρὸς Τιμόθεον Β'", "bookEnglish": "2 Timothy",
     "order": 16, "division": "paul"},
    {"slug": "pros-titon", "page": "Προς Τίτον",
     "book": "Πρὸς Τίτον", "bookEnglish": "Titus",
     "order": 17, "division": "paul"},
    {"slug": "pros-filimona", "page": "Προς Φιλήμονα",
     "book": "Πρὸς Φιλήμονα", "bookEnglish": "Philemon",
     "order": 18, "division": "paul"},
    {"slug": "pros-evraious", "page": "Προς Εβραίους",
     "book": "Πρὸς Ἑβραίους", "bookEnglish": "Hebrews",
     "order": 19, "division": "paul"},
    # Catholic epistles
    {"slug": "iakovou", "page": "Ιακώβου",
     "book": "Ἰακώβου", "bookEnglish": "James",
     "order": 20, "division": "general"},
    {"slug": "petrou-a", "page": "Πέτρου Α'",
     "book": "Πέτρου Α'", "bookEnglish": "1 Peter",
     "order": 21, "division": "general"},
    {"slug": "petrou-b", "page": "Πέτρου Β'",
     "book": "Πέτρου Β'", "bookEnglish": "2 Peter",
     "order": 22, "division": "general"},
    {"slug": "ioannou-a", "page": "Ιωάννου Α'",
     "book": "Ἰωάννου Α'", "bookEnglish": "1 John",
     "order": 23, "division": "general"},
    {"slug": "ioannou-b", "page": "Ιωάννου Β'",
     "book": "Ἰωάννου Β'", "bookEnglish": "2 John",
     "order": 24, "division": "general"},
    {"slug": "ioannou-g", "page": "Ιωάννου Γ'",
     "book": "Ἰωάννου Γ'", "bookEnglish": "3 John",
     "order": 25, "division": "general"},
    {"slug": "iouda", "page": "Ιούδα",
     "book": "Ἰούδα", "bookEnglish": "Jude",
     "order": 26, "division": "general"},
    # Revelation
    {"slug": "apokalypsis", "page": "Αποκάλυψις Ιωάννου",
     "book": "Ἀποκάλυψις Ἰωάννου", "bookEnglish": "Revelation",
     "order": 27, "division": "revelation"},
]


# Wikisource chapter anchors look like `[Ι.](#1:1)` after markdown conversion.
# Roman-numeral run before the dot.
CHAPTER_ANCHOR_RE = re.compile(
    r"\[(?P<roman>[ΙIVXLCDMιvx]+)\.\]\(#(?P<chap>\d+):1\)"
)
# Strip in-page citations like `[1]` or `[α]` that aren't useful in the markdown body.
CITATION_RE = re.compile(r"\[\d+\]")


def fetch_via_api(page_title: str) -> str | None:
    """Fetch a Wikisource page via the parse API → returns rendered HTML."""
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
        "redirects": 1,
    }
    try:
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            return None
        return data.get("parse", {}).get("text", {}).get("*")
    except (requests.RequestException, ValueError):
        return None


def count_chapters(body: str) -> int:
    """Count chapter anchors in the markdown body."""
    return len(CHAPTER_ANCHOR_RE.findall(body))


def normalize_body(body: str) -> str:
    """Convert Wikisource chapter anchors into proper h2 headings.

    `[Ι.](#1:1) Βίβλος γενέσεως...` → `## Κεφάλαιον 1\n\nΒίβλος γενέσεως...`
    """
    def replace_anchor(match: re.Match) -> str:
        chap = match.group("chap")
        return f"\n\n## Κεφάλαιον {chap}\n\n"

    body = CHAPTER_ANCHOR_RE.sub(replace_anchor, body)
    body = CITATION_RE.sub("", body)
    # Collapse runs of blank lines
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


def fetch_one(entry: dict, *, force: bool, dry_run: bool) -> bool:
    slug = entry["slug"]
    page = entry["page"]

    if check_exists("bible", slug) and not force:
        log(f"skip (exists): {slug}", level="warn")
        return False

    log(f"GET wikisource: {page}")
    html = fetch_via_api(page)
    if not html:
        log(f"  failed to fetch {page}", level="error")
        return False

    # Strip mediawiki chrome (TOC, edit links, navigation, references list)
    cleaned_html = clean_html(html, extra_selectors=[
        ".reference", ".references", "ol.references",
        ".mw-references-wrap", ".mw-cite-backlink",
        ".prev_next", ".header_search", ".navbox-bible",
        "div[role='note']", "div.hatnote",
    ])
    body_md = html_to_markdown(cleaned_html).strip()

    if not body_md or len(body_md) < 500:
        log(f"  body too short ({len(body_md)} chars)", level="error")
        return False

    body_md = normalize_body(body_md)
    chapters = count_chapters(html_to_markdown(cleaned_html))  # count from pre-normalize markdown

    fm: dict[str, Any] = {
        "book": entry["book"],
        "bookEnglish": entry["bookEnglish"],
        "order": entry["order"],
        "division": entry["division"],
        "chapters": chapters or None,
        "language": "el",
        "sourceUrl": f"https://el.wikisource.org/wiki/{quote(page.replace(' ', '_'), safe='')}",
        "license": "public-domain",
    }
    # Drop None values from frontmatter
    fm = {k: v for k, v in fm.items() if v is not None}

    if dry_run:
        log(f"  DRY RUN — would write bible/{slug}.md ({len(body_md):,} chars, {chapters} chapters)")
        return True

    target = write_content("bible", slug, fm, f"_{SOURCE_CREDIT}_\n\n{body_md}", force=force)
    log(f"  wrote {target} ({len(body_md):,} chars, {chapters} chapters)", level="ok")
    time.sleep(1.0)
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", help="Process only this slug")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    targets = ENTRIES
    if args.slug:
        targets = [e for e in ENTRIES if e["slug"] == args.slug]
        if not targets:
            log(f"No entry with slug={args.slug}", level="error")
            sys.exit(2)

    log(f"Seeding {len(targets)} NT book(s) from el.wikisource.org")

    ok = 0
    fail = 0
    for entry in targets:
        if fetch_one(entry, force=args.force, dry_run=args.dry_run):
            ok += 1
        else:
            fail += 1

    log(f"Done: {ok} written, {fail} failed/skipped",
        level="ok" if fail == 0 else "info")


if __name__ == "__main__":
    main()
