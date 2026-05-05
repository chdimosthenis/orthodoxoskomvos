"""Seed liturgical collection with full akolouthia texts from glt.goarch.org.

The Greek Orthodox Archdiocese of America's Liturgical Texts Project
(glt.goarch.org) hosts public-domain Byzantine-rite akolouthies in clean
polytonic Greek. Underlying texts are centuries-old (public-domain by age);
attribution to the GOA digital edition is preserved in `source` and
`sourceUrl`.

This script intentionally does NOT contain the prayer texts in its source.
It maps slugs to GOA URLs and downloads at runtime — that's what keeps the
fetch-and-write pipeline reproducible without ballooning the script file.

Usage:
    python seed_akolouthies.py            # fetch all entries
    python seed_akolouthies.py --slug esperinos   # one entry
    python seed_akolouthies.py --force    # overwrite existing files
    python seed_akolouthies.py --dry-run  # don't write
"""
from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from _common import (
    check_exists,
    clean_html,
    html_to_markdown,
    log,
    write_content,
)

BASE_URL = "https://glt.goarch.org/texts/"

HEADERS = {
    "User-Agent": "OrthodoxLogos/1.0 (educational seeder; https://orthodox-site.pages.dev)",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.5",
}

SOURCE_CREDIT = (
    "Παραδοσιακὸ λειτουργικὸ κείμενο — Public domain. "
    "Ψηφιακὴ ἔκδοση: Ἑλληνικὴ Ὀρθόδοξος Ἀρχιεπισκοπὴ Ἀμερικῆς, "
    "Liturgical Texts Project (glt.goarch.org)."
)

# Each entry: slug → (title, type, GOA relative path).
# Path is relative to BASE_URL — e.g. "Oro/Esperinos.html" or "Euch/Baptism.html".
# Slugs are stable URL identifiers; titles are display strings (polytonic Greek).
ENTRIES: list[dict[str, str]] = [
    # --- Daily cycle (Ωρολόγιον) ---
    {"slug": "mikron-apodeipnon", "title": "Μικρὸν Ἀπόδειπνον",
     "type": "apodeipno", "path": "Oro/Apodeipnon.html"},
    {"slug": "mega-apodeipnon", "title": "Μέγα Ἀπόδειπνον",
     "type": "apodeipno", "path": "Oro/Great.html"},
    {"slug": "mesonyktikon", "title": "Μεσονυκτικόν",
     "type": "akolouthia", "path": "Oro/Meso.html"},
    {"slug": "esperinos", "title": "Ἑσπερινός",
     "type": "akolouthia", "path": "Oro/Esperinos.html"},
    {"slug": "esperinos-kyriakis", "title": "Ἑσπερινὸς τῆς Κυριακῆς",
     "type": "akolouthia", "path": "Oro/Esperinos%20Sunday.html"},
    {"slug": "orthros", "title": "Ὄρθρος",
     "type": "akolouthia", "path": "Oro/Orthros.html"},
    {"slug": "orthros-kyriakis", "title": "Ὄρθρος τῆς Κυριακῆς",
     "type": "akolouthia", "path": "Oro/OrthrosSun.html"},
    {"slug": "ora-prote", "title": "Ὧρα Α'",
     "type": "akolouthia", "path": "Oro/one.html"},
    {"slug": "ora-trite", "title": "Ὧρα Γ'",
     "type": "akolouthia", "path": "Oro/three.html"},
    {"slug": "ora-ekte", "title": "Ὧρα ΣΤ'",
     "type": "akolouthia", "path": "Oro/six.html"},
    {"slug": "ora-enate", "title": "Ὧρα Θ'",
     "type": "akolouthia", "path": "Oro/nine.html"},
    # --- Παρακλήσεις & Ακάθιστος ---
    {"slug": "paraklesis-mikra", "title": "Μικρὰ Παράκλησις στὴν Παναγία",
     "type": "paraklesis", "path": "Oro/paraklesis.html"},
    {"slug": "paraklesis-megale", "title": "Μεγάλη Παράκλησις στὴν Παναγία",
     "type": "paraklesis", "path": "Oro/paraklesis_Great.html"},
    {"slug": "akathistos-ymnos", "title": "Ἀκάθιστος Ὕμνος",
     "type": "akathistos", "path": "Oro/Akathist5.html"},
    {"slug": "chairetismoi-staseis", "title": "Χαιρετισμοί — Α', Β', Γ', Δ' Στάσεις",
     "type": "chairetismoi", "path": "Oro/Staseis.html"},
    # --- Θεῖες Λειτουργίες ---
    {"slug": "theia-leitourgia-chrysostomou",
     "title": "Θεία Λειτουργία τοῦ Ἁγίου Ἰωάννου τοῦ Χρυσοστόμου",
     "type": "akolouthia", "path": "Oro/Sun_Liturgy.html"},
    {"slug": "theia-leitourgia-vasileiou",
     "title": "Θεία Λειτουργία τοῦ Μεγάλου Βασιλείου",
     "type": "akolouthia", "path": "Oro/Basil_Liturgy.html"},
    {"slug": "leitourgia-proegiasmenon",
     "title": "Λειτουργία τῶν Προηγιασμένων Δώρων",
     "type": "akolouthia", "path": "Oro/Pro.html"},
    {"slug": "theia-leitourgia-iakovou",
     "title": "Θεία Λειτουργία τοῦ Ἁγίου Ἰακώβου τοῦ Ἀδελφοθέου",
     "type": "akolouthia", "path": "Oro/StJames.html"},
    # --- Ευχολόγιον (Μυστήρια) ---
    {"slug": "mikros-agiasmos", "title": "Μικρὸς Ἁγιασμός",
     "type": "akolouthia", "path": "Euch/Agiasmos.html"},
    {"slug": "vaptisma", "title": "Ἀκολουθία τοῦ Ἁγίου Βαπτίσματος",
     "type": "akolouthia", "path": "Euch/Baptism.html"},
    {"slug": "stefanoma-gamou", "title": "Ἀκολουθία τοῦ Στεφανώματος (Γάμος)",
     "type": "akolouthia", "path": "Euch/Wedding.html"},
    {"slug": "nekrosimos-akolouthia", "title": "Νεκρώσιμος Ἀκολουθία",
     "type": "akolouthia", "path": "Euch/Funeral.html"},
    {"slug": "mnimosyno-trisagion", "title": "Τρισάγιον (Μνημόσυνον)",
     "type": "akolouthia", "path": "Euch/Trisagion.html"},
    # --- Δεσποτικαὶ Ἑορταί (Μηναῖα) ---
    {"slug": "megas-agiasmos", "title": "Μέγας Ἁγιασμὸς τῶν Θεοφανείων",
     "type": "akolouthia", "path": "Jan/Jan06.html"},
]


def strip_chrome(html: str) -> str:
    """Remove the GOA Archdiocese seal and any obvious chrome."""
    soup = BeautifulSoup(html, "html.parser")
    # Drop the Archdiocese seal image (and its anchor wrapper, if any).
    for img in soup.find_all("img"):
        src = img.get("src") or ""
        if "ArchdioceseSeal" in src or "seal" in src.lower():
            parent = img.parent
            if parent and parent.name == "a":
                parent.decompose()
            else:
                img.decompose()
    return str(soup)


def fetch_one(entry: dict[str, str], *, force: bool, dry_run: bool) -> bool:
    slug = entry["slug"]
    title = entry["title"]
    typ = entry["type"]
    path = entry["path"]
    url = BASE_URL + path.lstrip("/")

    if check_exists("liturgical", slug) and not force:
        log(f"skip (exists): {slug}", level="warn")
        return False

    log(f"GET {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=45)
        resp.encoding = "utf-8"
        resp.raise_for_status()
    except requests.RequestException as e:
        log(f"  network error: {e}", level="error")
        return False

    html = resp.text
    cleaned = strip_chrome(html)
    cleaned = clean_html(cleaned)
    body_md = html_to_markdown(cleaned).strip()

    if not body_md or len(body_md) < 200:
        log(f"  body too short ({len(body_md)} chars) — likely a fetch issue", level="error")
        return False

    fm: dict[str, Any] = {
        "title": title,
        "type": typ,
        "source": SOURCE_CREDIT,
        "language": "el",
        "sourceUrl": url,
        "license": "public-domain",
    }

    if dry_run:
        log(f"  DRY RUN — would write liturgical/{slug}.md ({len(body_md)} chars)")
        return True

    target = write_content("liturgical", slug, fm, body_md, force=force)
    log(f"  wrote {target} ({len(body_md):,} chars)", level="ok")
    time.sleep(1.5)  # be polite to the GOA server
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", help="Fetch only this slug")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing files")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    targets = ENTRIES
    if args.slug:
        targets = [e for e in ENTRIES if e["slug"] == args.slug]
        if not targets:
            log(f"No entry with slug={args.slug}", level="error")
            sys.exit(2)

    log(f"Seeding {len(targets)} akolouthia(s) from glt.goarch.org")

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
