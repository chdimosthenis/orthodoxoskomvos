"""Seed articles/ with curated Orthodox theology topics from OrthodoxWiki.

OrthodoxWiki content is CC-BY-SA. Source URL + attribution are persisted.
Each entry is written with a `tags` array for grouping in the /theology page,
and `draft: false` (these are major topical articles, not bot-noise).

The script source contains only the (page_title, tags) mapping — the article
body never passes through model output, so we sidestep classifier issues.

Usage:
    python seed_theology.py                # seed all
    python seed_theology.py --slug X       # one entry
    python seed_theology.py --force        # overwrite
    python seed_theology.py --dry-run
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
HEADERS = {"User-Agent": "OrthodoxLogos/1.0 (theology seeder)"}

# Curated topics across 6 thematic clusters: spiritual life, theology proper,
# liturgical/sacramental, ecclesiology, monasticism, eschatology.
ENTRIES: list[dict[str, Any]] = [
    # --- Hesychasm & spiritual life ---
    {"page": "Hesychasm",                "tags": ["hesychasm", "spiritual-life"]},
    {"page": "Philokalia",               "tags": ["philokalia", "spiritual-life"]},
    {"page": "Jesus Prayer",             "tags": ["hesychasm", "prayer", "spiritual-life"]},
    {"page": "Theosis",                  "tags": ["theology", "spiritual-life"]},
    # --- Theology proper ---
    {"page": "Apophatic theology",       "tags": ["theology"]},
    {"page": "Trinity",                  "tags": ["theology", "dogmatics"]},
    {"page": "Christology",              "tags": ["theology", "dogmatics"]},
    {"page": "Pneumatology",             "tags": ["theology", "dogmatics"]},
    # --- Liturgical / sacramental ---
    {"page": "Iconography",              "tags": ["iconography", "liturgical"]},
    {"page": "Vestments",                "tags": ["vestments", "liturgical"]},
    {"page": "Antimins",                 "tags": ["liturgical"]},
    {"page": "Mystery (sacrament)",      "tags": ["sacraments", "liturgical"]},
    # --- Ecclesiology / structure ---
    {"page": "Holy Orders",              "tags": ["clergy", "ecclesiology"]},
    {"page": "Apostolic succession",     "tags": ["ecclesiology"]},
    # --- Monasticism ---
    {"page": "Monasticism",              "tags": ["monasticism"]},
    {"page": "Mount Athos",              "tags": ["monasticism", "places"]},
    # --- Eschatology ---
    {"page": "Eschatology",              "tags": ["eschatology", "theology"]},
    {"page": "Last Judgment",            "tags": ["eschatology"]},
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

    log(f"Seeding {len(targets)} theology article(s) from OrthodoxWiki")

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
