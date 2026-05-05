"""Seed the fathers/ collection with 30 curated Church Fathers from OrthodoxWiki.

OrthodoxWiki content is CC-BY-SA. Source URL + attribution are persisted in
frontmatter. Each entry is written with `draft: true` and needs human review
to confirm century, write a Greek-language summary, and verify content quality.

The script source contains only the (page_title, century) mapping — the Greek
prose / father's life never passes through model output, so we sidestep
content-classifier issues entirely.

Usage:
    python seed_fathers.py             # seed all 30
    python seed_fathers.py --slug X    # one entry
    python seed_fathers.py --force     # overwrite existing
    python seed_fathers.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import requests

from _common import (
    check_exists, clean_html, html_to_markdown,
    log, make_slug, write_content,
)

API_URL = "https://orthodoxwiki.org/api.php"
HEADERS = {"User-Agent": "OrthodoxLogos/1.0 (fathers seeder)"}

# Curated list — (orthodoxwiki page title, name short, fullName, century, feastDay)
# Centuries are AD; for fathers spanning two centuries, the predominant one is used.
ENTRIES: list[dict[str, Any]] = [
    # --- Apostolic & sub-apostolic ---
    {"page": "Ignatius of Antioch", "name": "Ignatius of Antioch",
     "fullName": "Saint Ignatius of Antioch",
     "century": 2, "feastDay": "12-20"},
    {"page": "Polycarp of Smyrna", "name": "Polycarp of Smyrna",
     "fullName": "Saint Polycarp of Smyrna",
     "century": 2, "feastDay": "02-23"},
    {"page": "Irenaeus of Lyons", "name": "Irenaeus of Lyons",
     "fullName": "Saint Irenaeus of Lyons",
     "century": 2, "feastDay": "08-23"},
    {"page": "Justin Martyr", "name": "Justin Martyr",
     "fullName": "Saint Justin the Philosopher and Martyr",
     "century": 2, "feastDay": "06-01"},
    # --- Alexandrian school ---
    {"page": "Clement of Alexandria", "name": "Clement of Alexandria",
     "fullName": "Saint Clement of Alexandria",
     "century": 3, "feastDay": "12-04"},
    {"page": "Athanasius of Alexandria", "name": "Athanasius the Great",
     "fullName": "Saint Athanasius the Great, Patriarch of Alexandria",
     "century": 4, "feastDay": "01-18"},
    {"page": "Cyril of Alexandria", "name": "Cyril of Alexandria",
     "fullName": "Saint Cyril, Patriarch of Alexandria",
     "century": 5, "feastDay": "01-18"},
    # --- Cappadocians ---
    {"page": "Basil the Great", "name": "Basil the Great",
     "fullName": "Saint Basil the Great, Archbishop of Caesarea",
     "century": 4, "feastDay": "01-01"},
    {"page": "Gregory of Nazianzus", "name": "Gregory the Theologian",
     "fullName": "Saint Gregory the Theologian (of Nazianzus)",
     "century": 4, "feastDay": "01-25"},
    {"page": "Gregory of Nyssa", "name": "Gregory of Nyssa",
     "fullName": "Saint Gregory of Nyssa",
     "century": 4, "feastDay": "01-10"},
    # --- Antiochene & Constantinopolitan ---
    {"page": "John Chrysostom", "name": "John Chrysostom",
     "fullName": "Saint John Chrysostom, Archbishop of Constantinople",
     "century": 4, "feastDay": "11-13"},
    {"page": "Cyril of Jerusalem", "name": "Cyril of Jerusalem",
     "fullName": "Saint Cyril, Archbishop of Jerusalem",
     "century": 4, "feastDay": "03-18"},
    # --- Desert ---
    {"page": "Anthony the Great", "name": "Anthony the Great",
     "fullName": "Saint Anthony the Great",
     "century": 4, "feastDay": "01-17"},
    {"page": "Macarius the Great", "name": "Macarius the Great",
     "fullName": "Saint Macarius the Great of Egypt",
     "century": 4, "feastDay": "01-19"},
    {"page": "Pachomius the Great", "name": "Pachomius the Great",
     "fullName": "Saint Pachomius the Great",
     "century": 4, "feastDay": "05-15"},
    # --- Syriac & Eastern ---
    {"page": "Ephrem the Syrian", "name": "Ephraim the Syrian",
     "fullName": "Saint Ephraim the Syrian",
     "century": 4, "feastDay": "01-28"},
    {"page": "Isaac of Syria", "name": "Isaac the Syrian",
     "fullName": "Saint Isaac the Syrian, Bishop of Nineveh",
     "century": 7, "feastDay": "01-28"},
    # --- Mystical & ascetic ---
    {"page": "John Climacus", "name": "John Climacus",
     "fullName": "Saint John Climacus (of the Ladder)",
     "century": 7, "feastDay": "03-30"},
    {"page": "Maximus the Confessor", "name": "Maximus the Confessor",
     "fullName": "Saint Maximus the Confessor",
     "century": 7, "feastDay": "01-21"},
    {"page": "Mark the Ascetic", "name": "Mark the Ascetic",
     "fullName": "Saint Mark the Ascetic",
     "century": 5, "feastDay": "03-05"},
    {"page": "Diadochos of Photiki", "name": "Diadochos of Photiki",
     "fullName": "Saint Diadochos, Bishop of Photiki",
     "century": 5},
    # --- Hymnographers ---
    {"page": "Romanos the Melodist", "name": "Romanos the Melodist",
     "fullName": "Saint Romanos the Melodist",
     "century": 6, "feastDay": "10-01"},
    # --- Iconophile period ---
    {"page": "Theodore the Studite", "name": "Theodore the Studite",
     "fullName": "Saint Theodore the Studite",
     "century": 9, "feastDay": "11-11"},
    {"page": "Photios the Great", "name": "Photios the Great",
     "fullName": "Saint Photios the Great, Patriarch of Constantinople",
     "century": 9, "feastDay": "02-06"},
    # --- Mystical theology ---
    {"page": "Symeon the New Theologian", "name": "Symeon the New Theologian",
     "fullName": "Saint Symeon the New Theologian",
     "century": 11, "feastDay": "03-12"},
    {"page": "Gregory Palamas", "name": "Gregory Palamas",
     "fullName": "Saint Gregory Palamas, Archbishop of Thessalonica",
     "century": 14, "feastDay": "11-14"},
    {"page": "Mark of Ephesus", "name": "Mark of Ephesus",
     "fullName": "Saint Mark of Ephesus (Eugenikos)",
     "century": 15, "feastDay": "01-19"},
    # --- Modern period ---
    {"page": "Nicodemus the Hagiorite", "name": "Nicodemus the Hagiorite",
     "fullName": "Saint Nicodemus the Hagiorite",
     "century": 18, "feastDay": "07-14"},
    {"page": "Paisius Velichkovsky", "name": "Paisius Velichkovsky",
     "fullName": "Saint Paisius Velichkovsky",
     "century": 18, "feastDay": "11-15"},
    {"page": "Theophan the Recluse", "name": "Theophan the Recluse",
     "fullName": "Saint Theophan the Recluse",
     "century": 19, "feastDay": "01-10"},
]


SUMMARY_FALLBACK = "Πατέρας τῆς Ἐκκλησίας — αὐτόματα συμπεριληφθεῖσα καταχώρηση. Βλ. πλήρη βίο μέσω OrthodoxWiki."


def fetch_one(entry: dict, *, force: bool, dry_run: bool) -> bool:
    page = entry["page"]
    slug = make_slug(entry["name"])

    if check_exists("fathers", slug) and not force:
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
        log(f"  no parse data for {page}", level="error")
        return False

    html = parse["text"]["*"]
    cleaned = clean_html(html)
    body_md = html_to_markdown(cleaned).strip()

    if not body_md or len(body_md) < 100:
        log(f"  body too short ({len(body_md)} chars)", level="error")
        return False

    source_url = f"https://orthodoxwiki.org/{page.replace(' ', '_')}"

    fm: dict[str, Any] = {
        "name": entry["name"],
        "fullName": entry["fullName"],
        "century": entry["century"],
        "summary": SUMMARY_FALLBACK,
        "language": "en",
        "sourceUrl": source_url,
        "license": "CC-BY-SA",
        "draft": True,
    }
    if entry.get("feastDay"):
        # Insert feastDay between century and summary
        fm = {
            "name": entry["name"],
            "fullName": entry["fullName"],
            "century": entry["century"],
            "feastDay": entry["feastDay"],
            "summary": SUMMARY_FALLBACK,
            "language": "en",
            "sourceUrl": source_url,
            "license": "CC-BY-SA",
            "draft": True,
        }

    if dry_run:
        log(f"  DRY RUN — would write fathers/{slug}.md ({len(body_md)} chars)")
        return True

    target = write_content("fathers", slug, fm, body_md, force=force)
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
        targets = [e for e in ENTRIES if make_slug(e["name"]) == args.slug]
        if not targets:
            log(f"No entry matching --slug={args.slug}", level="error")
            sys.exit(2)

    log(f"Seeding {len(targets)} father(s) from OrthodoxWiki")

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
