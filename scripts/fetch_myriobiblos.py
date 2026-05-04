"""Fetch a Greek text from myriobiblos.gr.

License notice: myriobiblos.gr hosts a mix of public-domain and copyrighted
texts. This script defaults to license=public-domain and prints a warning;
verify each text manually before publishing.

Usage:
    python fetch_myriobiblos.py <url> --author "<name>" [--collection articles]
                                [--force] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

import requests
import trafilatura

from _common import (
    check_exists, clean_html, extract_title, html_to_markdown,
    log, make_slug, write_content,
)


HEADERS = {
    "User-Agent": "OrthodoxLogos/1.0 (content seeder)",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.5",
}


def fetch_myriobiblos(
    url: str,
    author: str,
    collection: str = "articles",
    *,
    force: bool = False,
    dry_run: bool = False,
) -> None:
    log(f"Fetching {url}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.encoding = "utf-8"  # be explicit so polytonic survives
    resp.raise_for_status()
    html = resp.text

    body_md = trafilatura.extract(
        html, include_links=False, include_formatting=True,
        output_format="markdown", favor_recall=True,
    )
    if not body_md:
        log("trafilatura yielded no content; falling back to manual cleaning", level="warn")
        cleaned = clean_html(html)
        body_md = html_to_markdown(cleaned)

    title = extract_title(html) or "myriobiblos"
    slug = make_slug(title)

    if check_exists(collection, slug) and not force:
        log(f"already exists: {collection}/{slug}.md", level="warn")
        return

    log("license assumed 'public-domain' — VERIFY MANUALLY before publishing", level="warn")

    fm = {
        "title": title,
        "description": title,
        "pubDate": date.today().isoformat(),
        "author": author,
        "language": "el",
        "sourceUrl": url,
        "license": "public-domain",
    }

    if dry_run:
        log(f"DRY RUN — would write {collection}/{slug}.md ({len(body_md)} chars)")
        return

    target = write_content(collection, slug, fm, body_md, force=force)
    log(f"wrote {target}", level="ok")


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch a myriobiblos.gr page.")
    p.add_argument("url")
    p.add_argument("--author", required=True)
    p.add_argument("--collection", default="articles")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if "myriobiblos.gr" not in args.url:
        log("URL must be from myriobiblos.gr", level="error")
        sys.exit(2)

    try:
        fetch_myriobiblos(args.url, args.author, args.collection, force=args.force, dry_run=args.dry_run)
    except requests.RequestException as e:
        log(f"Network error: {e}", level="error")
        sys.exit(1)


if __name__ == "__main__":
    main()
