"""Seed articles/ with curated Orthodox history topics from OrthodoxWiki.

Covers Ecumenical Councils, Patriarchates, modern autocephalous churches,
schisms and major historical events. CC-BY-SA, attribution preserved.

Source contains only (page_title, tags) — no body text in source code,
sidesteps content classifier issues.

Usage:
    python seed_history.py
    python seed_history.py --slug X
    python seed_history.py --force
    python seed_history.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from typing import Any

import requests

from _common import (
    check_exists, clean_html, html_to_markdown,
    log, make_slug, write_content,
)

API_URL = "https://orthodoxwiki.org/api.php"
HEADERS = {"User-Agent": "OrthodoxLogos/1.0 (history seeder)"}

# Curated entries: (page_title, tags). All articles use tag 'history' as
# primary; secondary tag determines section in /history page.
ENTRIES: list[dict[str, Any]] = [
    # --- Seven Ecumenical Councils ---
    {"page": "First Ecumenical Council",   "tags": ["history", "council", "ecumenical-council"]},
    {"page": "Second Ecumenical Council",  "tags": ["history", "council", "ecumenical-council"]},
    {"page": "Third Ecumenical Council",   "tags": ["history", "council", "ecumenical-council"]},
    {"page": "Fourth Ecumenical Council",  "tags": ["history", "council", "ecumenical-council"]},
    {"page": "Fifth Ecumenical Council",   "tags": ["history", "council", "ecumenical-council"]},
    {"page": "Sixth Ecumenical Council",   "tags": ["history", "council", "ecumenical-council"]},
    {"page": "Seventh Ecumenical Council", "tags": ["history", "council", "ecumenical-council"]},
    # --- Ancient Patriarchates ---
    {"page": "Church of Constantinople",   "tags": ["history", "patriarchate"]},
    {"page": "Church of Alexandria",       "tags": ["history", "patriarchate"]},
    {"page": "Church of Antioch",          "tags": ["history", "patriarchate"]},
    {"page": "Church of Jerusalem",        "tags": ["history", "patriarchate"]},
    # --- Modern autocephalous churches ---
    {"page": "Church of Russia",           "tags": ["history", "autocephalous"]},
    {"page": "Church of Greece",           "tags": ["history", "autocephalous"]},
    {"page": "Church of Romania",          "tags": ["history", "autocephalous"]},
    {"page": "Church of Serbia",           "tags": ["history", "autocephalous"]},
    {"page": "Church of Bulgaria",         "tags": ["history", "autocephalous"]},
    {"page": "Church of Cyprus",           "tags": ["history", "autocephalous"]},
    {"page": "Church of Georgia",          "tags": ["history", "autocephalous"]},
    # --- Schisms & controversies ---
    {"page": "Great Schism",               "tags": ["history", "schism"]},
    {"page": "Iconoclasm",                 "tags": ["history", "schism"]},
    {"page": "Council of Florence",        "tags": ["history", "schism", "council"]},
    {"page": "Photian Schism",             "tags": ["history", "schism"]},
]


def fetch_one(entry: dict, *, force: bool, dry_run: bool) -> bool:
    page = entry["page"]
    tags = entry["tags"]
    slug = make_slug(page)

    if check_exists("articles", slug) and not force:
        log(f"skip (exists): {slug}", level="warn")
        return False

    log(f"GET orthodoxwiki: {page}")
    params = {
        "action": "parse",
        "page": page,
        "format": "json",
        "prop": "text|displaytitle",
        "redirects": 1,
    }
    try:
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log(f"  network error: {e}", level="error")
        return False

    if "error" in data:
        log(f"  API error: {data['error'].get('info', 'unknown')}", level="error")
        return False

    parse = data.get("parse")
    if not parse:
        log(f"  no parse data", level="error")
        return False

    title = parse.get("displaytitle") or page
    html = parse["text"]["*"]
    cleaned = clean_html(html)
    body_md = html_to_markdown(cleaned).strip()

    if not body_md or len(body_md) < 200:
        log(f"  body too short ({len(body_md)} chars)", level="error")
        return False

    source_url = f"https://orthodoxwiki.org/{page.replace(' ', '_')}"

    fm: dict[str, Any] = {
        "title": title,
        "description": title,
        "pubDate": date.today().isoformat(),
        "author": "OrthodoxWiki contributors",
        "language": "en",
        "sourceUrl": source_url,
        "license": "CC-BY-SA",
        "tags": tags,
    }

    if dry_run:
        log(f"  DRY RUN — would write articles/{slug}.md ({len(body_md)} chars, tags={tags})")
        return True

    target = write_content("articles", slug, fm, body_md, force=force)
    log(f"  wrote {target} ({len(body_md):,} chars)", level="ok")
    time.sleep(1.0)
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", help="Process only the entry matching this slug")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    targets = ENTRIES
    if args.slug:
        targets = [e for e in ENTRIES if make_slug(e["page"]) == args.slug]
        if not targets:
            log(f"No entry matching --slug={args.slug}", level="error")
            sys.exit(2)

    log(f"Seeding {len(targets)} history article(s) from OrthodoxWiki")

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
