"""Fetch a page from orthodoxwiki.org via the MediaWiki API.

OrthodoxWiki content is licensed CC-BY-SA. Attribution is mandatory and is
encoded in the frontmatter (sourceUrl + license=CC-BY-SA).

Usage:
    python fetch_orthodoxwiki.py "Page Title" [--collection articles|saints|fathers]
                                 [--force] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date

import requests

from _common import (
    check_exists, clean_html, extract_title, html_to_markdown,
    log, make_slug, write_content,
)


API_URL = "https://orthodoxwiki.org/api.php"

HEADERS = {
    "User-Agent": "OrthodoxLogos/1.0 (content seeder)",
}


def fetch_orthodoxwiki(
    page: str,
    collection: str = "articles",
    *,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    log(f"Fetching OrthodoxWiki page: {page}")

    params = {
        "action": "parse",
        "page": page,
        "format": "json",
        "prop": "text|displaytitle",
        "redirects": 1,
    }
    resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        log(f"API error: {data['error'].get('info', 'unknown')}", level="error")
        sys.exit(1)

    parse = data.get("parse")
    if not parse:
        log("No parse data returned", level="error")
        sys.exit(1)

    title = parse.get("displaytitle") or page
    html = parse["text"]["*"]

    cleaned = clean_html(html)
    body_md = html_to_markdown(cleaned)

    slug = make_slug(page)

    if check_exists(collection, slug) and not force:
        log(f"already exists: {collection}/{slug}.md", level="warn")
        return

    source_url = f"https://orthodoxwiki.org/{page.replace(' ', '_')}"

    if collection == "saints":
        log("collection=saints requires manual feastDay/category fields after fetch", level="warn")
        fm = {
            "name": title,
            "feastDay": "01-01",  # placeholder, edit manually
            "category": "other",  # placeholder, edit manually
            "life": title,
            "language": "en",
        }
    elif collection == "fathers":
        fm = {
            "name": title,
            "fullName": title,
            "century": 0,  # placeholder, edit manually
            "summary": title,
            "language": "en",
        }
    else:
        fm = {
            "title": title,
            "description": title,
            "pubDate": date.today().isoformat(),
            "author": "OrthodoxWiki contributors",
            "language": "en",
            "sourceUrl": source_url,
            "license": "CC-BY-SA",
        }

    if dry_run:
        log(f"DRY RUN — would write {collection}/{slug}.md ({len(body_md)} chars)")
        return

    target = write_content(collection, slug, fm, body_md, force=force)
    log(f"wrote {target}", level="ok")
    time.sleep(1)  # be polite


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch a page from orthodoxwiki.org via MediaWiki API.")
    p.add_argument("page", help="Page title (e.g. 'Hesychasm')")
    p.add_argument("--collection", default="articles", choices=["articles", "saints", "fathers"])
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    try:
        fetch_orthodoxwiki(args.page, args.collection, force=args.force, dry_run=args.dry_run)
    except requests.RequestException as e:
        log(f"Network error: {e}", level="error")
        sys.exit(1)


if __name__ == "__main__":
    main()
