"""Aggregate Greek Orthodox news from public RSS feeds.

Output: src/data/news.json with the most-recent N items across all configured
sources. The Astro NewsWidget component reads this file at build time and
renders a sidebar list on the home page.

Sources are major Greek Orthodox news outlets that publish RSS:
- pemptousia.com — daily Orthodox content (Mt Athos-affiliated)
- vimaorthodoxias.gr — Vima Orthodoxias news portal
- dogma.gr — Orthodox news
- orthodoxianewsagency.gr — Orthodoxia News Agency

Usage:
    python fetch_news.py                # fetch all, write src/data/news.json
    python fetch_news.py --limit 20     # keep top-20 (default 30)
    python fetch_news.py --dry-run      # print summary, don't write

Run via .github/workflows/news.yml on a 6-hour cron.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import feedparser

from _common import REPO_ROOT, log


# (label, url, optional_category_hint)
SOURCES: list[tuple[str, str, str | None]] = [
    ("Πεμπτουσία",          "https://pemptousia.com/feed/",          None),
    ("Βῆμα Ὀρθοδοξίας",      "https://www.vimaorthodoxias.gr/feed/",   None),
    ("Δόγμα",               "https://www.dogma.gr/feed/",             None),
    ("Ὀρθοδοξία News",      "https://www.orthodoxianewsagency.gr/feed/", None),
]

OUTPUT_PATH = REPO_ROOT / "src" / "data" / "news.json"
ARCHIVE_DIR = REPO_ROOT / "src" / "data" / "news"

# Lightweight category classification by keyword scan.
CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    ("liturgy",  r"λιτανε[ίι]α|θε[ίι]α λειτουργ[ίι]α|ἁγιασμ[όος]ς|μνημόσυν"),
    ("synod",    r"σύνοδ[οου]ς|ἱερὰ σύνοδος|μητροπολίτ|πατριάρχ"),
    ("event",    r"ἑορτ[ήη]|πανήγυρ[ιη]|ἐκδήλωσ"),
    ("speech",   r"ὁμιλ[ίι]α|κήρυγμ[αα]|μήνυμ[αα]"),
    ("monastic", r"μοναχ[όού]ς|μοναστήρ|μονή\b|ἁγιορε[ίι]τ|ἀσκητ"),
    ("saints",   r"ἅγιος|ἁγία|ἁγίου|μάρτυρ"),
]


def classify_text(s: str) -> str:
    s_lower = s.lower()
    for label, pattern in CATEGORY_KEYWORDS:
        if re.search(pattern, s_lower, flags=re.IGNORECASE):
            return label
    return "general"


def host_of(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except Exception:
        return ""


def strip_html(html: str) -> str:
    """Quick HTML strip + collapse whitespace for excerpt rendering."""
    s = re.sub(r"<[^>]+>", " ", html or "")
    s = re.sub(r"&[a-zA-Z]+;", " ", s)
    s = re.sub(r"&#\d+;", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def to_iso(struct_time) -> str | None:
    """Convert feedparser's published_parsed (time.struct_time) to ISO 8601."""
    if not struct_time:
        return None
    try:
        dt = datetime(*struct_time[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    except (TypeError, ValueError):
        return None


def fetch_source(label: str, url: str) -> list[dict[str, Any]]:
    log(f"GET {url}")
    feed = feedparser.parse(url, agent="OrthodoxLogos/1.0 (news aggregator; +https://orthodoxoskomvos.gr)")

    if feed.bozo and not feed.entries:
        log(f"  failed to parse: {feed.bozo_exception}", level="warn")
        return []

    items: list[dict[str, Any]] = []
    for entry in feed.entries[:25]:  # cap per source
        title = (entry.get("title") or "").strip()
        link = entry.get("link") or ""
        if not title or not link:
            continue

        published_iso = to_iso(entry.get("published_parsed") or entry.get("updated_parsed"))
        summary_html = entry.get("summary") or entry.get("description") or ""
        excerpt = strip_html(summary_html)[:280]
        category = classify_text(f"{title} {excerpt}")

        items.append({
            "title": title,
            "url": link,
            "source": label,
            "host": host_of(link),
            "published": published_iso,
            "excerpt": excerpt,
            "category": category,
        })

    log(f"  got {len(items)} items", level="ok")
    return items


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=30, help="Keep top-N most recent across all sources (default 30)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    log(f"Aggregating from {len(SOURCES)} sources")

    all_items: list[dict[str, Any]] = []
    for label, url, _ in SOURCES:
        try:
            all_items.extend(fetch_source(label, url))
        except Exception as e:
            log(f"  source error ({label}): {e}", level="error")

    # Sort by published descending; entries without dates sink to bottom.
    def sort_key(item: dict[str, Any]) -> str:
        return item.get("published") or ""

    all_items.sort(key=sort_key, reverse=True)
    top = all_items[: args.limit]

    log(f"Total aggregated: {len(all_items)}; keeping top {len(top)}", level="ok")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(top),
        "items": top,
    }

    if args.dry_run:
        log(f"DRY RUN — would write {OUTPUT_PATH}")
        for it in top[:5]:
            log(f"  · [{it['source']}] {it['title'][:80]}")
        return

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"wrote {OUTPUT_PATH} ({len(top)} items)", level="ok")

    # Also persist a dated archive copy under src/data/news/YYYY-MM-DD.json
    # so old days remain browsable on the site even after the latest snapshot
    # is overwritten on the next fetch. If a file already exists for today,
    # we MERGE: keep all unique items by URL across the existing archive
    # and the new fetch, then re-trim to the limit. That way running the
    # fetcher multiple times in one day accumulates rather than replaces.
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    archive_path = ARCHIVE_DIR / f"{today}.json"

    merged_items = list(top)
    if archive_path.exists():
        try:
            existing = json.loads(archive_path.read_text(encoding="utf-8"))
            seen = {it["url"] for it in merged_items}
            for it in existing.get("items", []):
                if it["url"] not in seen:
                    merged_items.append(it)
                    seen.add(it["url"])
            merged_items.sort(key=sort_key, reverse=True)
            merged_items = merged_items[: args.limit]
        except (json.JSONDecodeError, KeyError) as e:
            log(f"  archive merge skipped (corrupt {archive_path.name}): {e}", level="warn")

    archive_payload = {
        "generated_at": output["generated_at"],
        "date": today,
        "count": len(merged_items),
        "items": merged_items,
    }
    archive_path.write_text(json.dumps(archive_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"wrote {archive_path} ({len(merged_items)} items)", level="ok")


if __name__ == "__main__":
    main()
