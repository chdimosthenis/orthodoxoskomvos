"""Fetch a single CCEL page (Christian Classics Ethereal Library) and save as
a Markdown article.

Usage:
    python fetch_ccel.py <url> --author "<name>" [--collection articles]
                         [--force] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from urllib.parse import urlparse

import requests
import trafilatura

from _common import (
    check_exists, clean_html, extract_title, html_to_markdown,
    log, make_slug, write_content,
)


HEADERS = {
    "User-Agent": "OrthodoxLogos/1.0 (content seeder; +https://orthodox-site.pages.dev)",
}


def fetch_ccel(
    url: str,
    author: str,
    collection: str = "articles",
    *,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    log(f"Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    html = resp.text

    # Try trafilatura first (handles boilerplate removal well)
    body_md = trafilatura.extract(
        html, include_links=False, include_formatting=True,
        output_format="markdown", favor_recall=True,
    )
    if not body_md:
        log("trafilatura yielded no content; falling back to manual cleaning", level="warn")
        cleaned = clean_html(html)
        body_md = html_to_markdown(cleaned)

    title = extract_title(html) or urlparse(url).path.rstrip("/").split("/")[-1] or "ccel"
    slug = make_slug(title)

    if check_exists(collection, slug) and not force:
        log(f"already exists: {collection}/{slug}.md (use --force to overwrite)", level="warn")
        return

    fm = {
        "title": title,
        "description": title,
        "pubDate": date.today().isoformat(),
        "author": author,
        "language": "en",
        "sourceUrl": url,
        "license": "public-domain",
    }

    if dry_run:
        log(f"DRY RUN — would write {collection}/{slug}.md ({len(body_md)} chars)")
        return

    target = write_content(collection, slug, fm, body_md, force=force)
    log(f"wrote {target}", level="ok")


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch a CCEL page and save as Markdown article.")
    p.add_argument("url", help="CCEL URL")
    p.add_argument("--author", required=True, help="Author of the work")
    p.add_argument("--collection", default="articles", help="Content collection (default: articles)")
    p.add_argument("--force", action="store_true", help="Overwrite existing file")
    p.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = p.parse_args()

    if "ccel.org" not in args.url:
        log("URL must be from ccel.org", level="error")
        sys.exit(2)

    try:
        fetch_ccel(args.url, args.author, args.collection, force=args.force, dry_run=args.dry_run)
    except requests.RequestException as e:
        log(f"Network error: {e}", level="error")
        sys.exit(1)


if __name__ == "__main__":
    main()
