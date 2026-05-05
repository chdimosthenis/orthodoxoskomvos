"""Auto-seed src/content/saints/ from Wikipedia's Eastern Orthodox liturgics
calendar pages.

Strategy:
1. For each target date (default: today+1 and today+2), fetch the Wikipedia
   page titled "<Month> <Day> (Eastern Orthodox liturgics)".
2. Walk the rendered HTML in document order, tracking the current section
   heading (Wikipedia wraps h2/h3 in a `<div class="mw-heading">`, so
   find_next_sibling on the h2 itself returns nothing — we walk the parent
   container's children instead).
3. When inside a relevant section ("Saints", "Pre-Schism…", "Post-Schism…",
   "New martyrs…"), extract <li> items with internal article links.
4. For each new saint not already in our content, write a stub entry
   (language='en', sourceUrl + license=CC-BY-SA) with a notice that it was
   machine-seeded and needs review.

Run manually:
    python daily_seed.py [--date MM-DD] [--days 2] [--dry-run]

Run via .github/workflows/daily-saints.yml on a daily cron.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup, Tag

from _common import check_exists, log, make_slug, write_content


WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "OrthodoxLogos/1.0 (daily seed bot; +https://orthodox-site.pages.dev)"}

# Map keywords found in section headings to our `category` enum
SECTION_CATEGORY: list[tuple[str, str]] = [
    ("hieromart", "martyr"),
    ("new martyr", "martyr"),
    ("martyr", "martyr"),
    ("apostle", "apostle"),
    ("prophet", "prophet"),
    ("hierarch", "hierarch"),
    ("bishop", "hierarch"),
    ("patriarch", "hierarch"),
    ("venerable", "monastic"),
    ("ascetic", "monastic"),
    ("monastic", "monastic"),
]

# Whitelist of section headings that contain saint commemorations
SAINT_SECTION_KEYWORDS = (
    "saint", "martyr", "venerable", "hieromartyr",
    "apostle", "prophet", "hierarch", "confessor",
    "pre-schism", "post-schism", "monastic",
)

# Sections to explicitly skip even if they contain matching keywords
SKIP_SECTION_KEYWORDS = (
    "icon gallery", "notes", "references", "sources",
    "see also", "external links",
)

# Pages whose link text is a calendar date (e.g., "March 19", "December 6")
# — these are cross-references to other liturgical calendar entries, not saints.
_DATE_TITLE_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}",
    re.IGNORECASE,
)

# Heuristic: page titles that look like place / city names rather than saints.
# We can't be perfectly accurate without category info, but reject the obvious
# cases where the link text is a single capitalised word AND the surrounding
# li text suggests a location (the saint's name appears separately).
_NON_SAINT_KEYWORDS = (
    "(town)", "(city)", "(diocese)", "(region)", "(province)",
    "(river)", "(mountain)", "(country)", "(municipality)",
    "(disambiguation)",
    " abbey", " monastery", " cathedral", " convent", " basilica",
    "degrees of eastern orthodox monasticism",
)

# Page titles that are unambiguously historical regions / city-states with
# the same name as the article — never a person.
_NON_SAINT_TITLES = frozenset({
    "epirus", "lycaonia", "livadeia", "philadelphia", "alaşehir",
    "thessalonica", "antioch", "byzantium", "rome", "constantinople",
    "athens", "corinth", "ephesus",
})

# Words that, when present in a list item's text, give us reasonable confidence
# that the entry is about a person who is venerated as a saint. If none of
# these markers nor a year-in-parens are present, we drop the entry rather
# than emit noise (place names, region articles, etc.).
_SAINT_MARKER_WORDS = (
    "saint", "martyr", "bishop", "abbot", "abbess", "priest", "monk",
    "nun", "venerable", "patriarch", "pope", "presbyter", "deacon",
    "archbishop", "metropolitan", "ascetic", "holy", "blessed", "elder",
    "wonderworker", "confessor", "righteous", "evangelist", "apostle",
    "prophet", "great martyr", "hieromartyr", "ecumenical",
)
_YEAR_IN_PARENS_RE = re.compile(r"\((?:c\.\s*)?\d{1,4}\b")


def looks_like_saint_entry(description: str) -> bool:
    """Return True if the li description plausibly describes a person/saint."""
    if not description:
        return False
    d = description.lower()
    if any(w in d for w in _SAINT_MARKER_WORDS):
        return True
    if _YEAR_IN_PARENS_RE.search(description):
        return True
    return False

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def fetch_wikipedia_page(page_title: str) -> str | None:
    """Get rendered HTML of an English Wikipedia page."""
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
        "redirects": 1,
    }
    try:
        resp = requests.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            log(f"  page '{page_title}' not found on Wikipedia", level="warn")
            return None
        return data["parse"]["text"]["*"]
    except (requests.RequestException, KeyError, ValueError) as e:
        log(f"  fetch error for '{page_title}': {e}", level="warn")
        return None


def categorize_from_heading(heading_text: str) -> str:
    h = heading_text.lower()
    for kw, cat in SECTION_CATEGORY:
        if kw in h:
            return cat
    return "other"


def heading_text_from_node(node: Tag) -> str | None:
    """Extract heading text from either a bare h2/h3 or a mw-heading wrapper."""
    if node.name in ("h2", "h3"):
        return node.get_text(strip=True)
    if node.name == "div" and "mw-heading" in (node.get("class") or []):
        h = node.find(["h2", "h3"])
        if h:
            return h.get_text(strip=True)
    return None


def parse_commemorations(html: str) -> list[dict]:
    """Extract saint commemorations from a Wikipedia EO-liturgics day-page."""
    soup = BeautifulSoup(html, "html.parser")

    # Strip wiki chrome
    for sel in [".mw-editsection", ".reference", ".mw-cite-backlink",
                ".navbox", ".thumbinner", ".infobox", ".toc", "#toc",
                ".hatnote", ".shortdescription"]:
        for tag in soup.select(sel):
            tag.decompose()

    container = soup.select_one(".mw-parser-output") or soup

    saints: list[dict] = []
    seen_slugs: set[str] = set()
    current_section: str | None = None
    current_category: str = "other"

    for child in container.children:
        if not isinstance(child, Tag):
            continue

        new_heading = heading_text_from_node(child)
        if new_heading is not None:
            current_section = new_heading
            current_category = categorize_from_heading(new_heading)
            continue

        if child.name not in ("ul", "ol"):
            continue
        if current_section is None:
            continue

        s_lower = current_section.lower()
        if any(kw in s_lower for kw in SKIP_SECTION_KEYWORDS):
            continue
        if not any(kw in s_lower for kw in SAINT_SECTION_KEYWORDS):
            continue

        for li in child.find_all("li", recursive=False):
            # Find the FIRST internal article link that plausibly refers to a
            # saint — skip namespace links, red-links, and obvious cross-refs
            # (calendar dates, disambiguation pages).
            a = None
            for candidate in li.find_all("a", href=re.compile(r"^/wiki/[^:]")):
                # red link?
                cls = candidate.get("class") or []
                if "new" in cls:
                    continue
                title = (candidate.get("title") or "").strip()
                text = candidate.get_text(strip=True)
                if not title or not text:
                    continue
                if title.lower().startswith(("help:", "wikipedia:", "category:", "file:")):
                    continue
                if _DATE_TITLE_RE.match(title):
                    continue
                if any(kw in title.lower() for kw in _NON_SAINT_KEYWORDS):
                    continue
                if title.lower() in _NON_SAINT_TITLES:
                    continue
                a = candidate
                break
            if not a:
                continue
            page_title = (a.get("title") or "").strip()
            display_name = a.get_text(strip=True)

            slug = make_slug(display_name)
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            full_li_text = li.get_text(" ", strip=True)
            description = full_li_text
            if description.lower().startswith(display_name.lower()):
                description = description[len(display_name):].lstrip(" ,;-—()")
            description = re.sub(r"\[\d+\]", "", description)  # drop footnote markers
            description = re.sub(r"\s+", " ", description).strip()

            # Skip noise: list items whose description gives no saint signal
            # (place name links, navigation cross-refs, etc.)
            if not looks_like_saint_entry(full_li_text):
                continue

            saints.append({
                "slug": slug,
                "page_title": page_title,
                "name": display_name,
                "description": description,
                "category": current_category,
            })

    return saints


def feast_day_for_date(d: date) -> str:
    return f"{d.month:02d}-{d.day:02d}"


def date_page_title(d: date) -> str:
    return f"{MONTH_NAMES[d.month - 1]} {d.day} (Eastern Orthodox liturgics)"


def seed_for_date(d: date, *, dry_run: bool) -> int:
    page = date_page_title(d)
    log(f"Fetching commemorations for {page} ({feast_day_for_date(d)})…")

    html = fetch_wikipedia_page(page)
    if not html:
        return 0

    commemorations = parse_commemorations(html)
    log(f"  found {len(commemorations)} commemorations")

    feast_day = feast_day_for_date(d)
    written = 0

    for c in commemorations:
        slug = c["slug"]
        if check_exists("saints", slug):
            continue

        source_url = f"https://en.wikipedia.org/wiki/{c['page_title'].replace(' ', '_')}"

        body_parts: list[str] = []
        if c["description"]:
            body_parts.append(c["description"])
        body_parts.append(
            f"_Full life and source: [{c['page_title']}]({source_url})._"
        )
        body_parts.append(
            "_(This entry was auto-seeded from Wikipedia by the daily commemoration "
            "bot. Please review and expand with original Greek prose where possible.)_"
        )
        body = "\n\n".join(body_parts)

        life = c["description"][:200] if c["description"] else c["name"]

        fm = {
            "name": c["name"],
            "wikipediaTitle": c["page_title"],
            "feastDay": feast_day,
            "category": c["category"],
            "life": life,
            "language": "en",
            "sourceUrl": source_url,
            "license": "CC-BY-SA",
            # Mark as draft so the entry is hidden from listings & RSS until
            # a human reviews it (and removes the parser noise that some pages
            # produce — first link in li is occasionally a place name).
            "draft": True,
        }

        if dry_run:
            log(f"  [dry-run] would write saints/{slug}.md ({c['name']})")
            written += 1
            continue

        try:
            write_content("saints", slug, fm, body)
            log(f"  wrote saints/{slug}.md ({c['name']})", level="ok")
            written += 1
        except FileExistsError:
            pass

    return written


def main() -> None:
    p = argparse.ArgumentParser(description="Daily commemoration seeder via Wikipedia EO-liturgics calendar.")
    p.add_argument("--date", help="Start date in MM-DD format (defaults to today+1)")
    p.add_argument("--days", type=int, default=2, help="How many consecutive days to scan")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.date:
        try:
            mm, dd = args.date.split("-")
            year = date.today().year
            start = date(year, int(mm), int(dd))
        except (ValueError, IndexError):
            log(f"Invalid --date: {args.date} (expected MM-DD)", level="error")
            sys.exit(2)
    else:
        start = date.today() + timedelta(days=1)

    total = 0
    for offset in range(args.days):
        d = start + timedelta(days=offset)
        try:
            total += seed_for_date(d, dry_run=args.dry_run)
        except Exception as e:
            log(f"  error seeding {d}: {e}", level="error")
        time.sleep(1)

    log(f"\ndone — new saints written: {total}", level="ok")


if __name__ == "__main__":
    main()
