"""Fetch a representative icon from Wikipedia/Wikimedia Commons for saints.

Strategy:
1. Wikipedia's PageImages API returns the article's main (lead/infobox) image filename.
2. Commons' imageinfo API returns URL + license + author for that file.
3. We persist iconUrl + iconAttribution back into the saint's frontmatter.

Modes:
  python fetch_icon.py --title "Nicholas of Myra"
      Look up a single Wikipedia article and print results.

  python fetch_icon.py --update-all
      Iterate every src/content/saints/*.md, look up the saint's
      `wikipediaTitle` frontmatter field, fetch icon, write back.

Wikipedia returns the same iconography image regardless of UI language
(Greek or English Wikipedia infobox usually shares the Commons file), so
one fetch populates both el-language and (future) en-language entries
when they share the same wikipediaTitle.
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import requests
import yaml

from _common import CONTENT_ROOT, log


COMMONS_API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "OrthodoxLogos/1.0 (icon fetcher; +https://orthodoxoskomvos.gr)"}

# Try Greek Wikipedia first — its infobox usually shows an Orthodox icon
# rather than a Western painting (which the English article often leads with).
WIKIPEDIA_HOSTS = [
    ("el.wikipedia.org", "el"),
    ("en.wikipedia.org", "en"),
]

# How wide we want the rendered Commons thumbnail (px). Plenty for a 280px display.
THUMB_WIDTH = 600

# ---- Byzantine-style icon classification (filename-based heuristics) -------
#
# We can't tell with certainty whether a Wikimedia Commons file shows a
# Byzantine icon or a Western painting without OCR/image analysis. But the
# filename itself is usually descriptive enough for high-confidence calls.
# Use these to flag suspect entries via `--audit`.

_ICON_ALLOW_KEYWORDS = (
    "icon", "ikon", "byzantine", "sinai", "athos", "novgorod",
    "pskov", "rublev", "theophanes_the_greek", "cretan_school",
    "macedonian_school", "fresco", "mosaic", "menaion",
    "imitation_of_byzantine", "russian_orthodox",
    "agia_", "agios_", "pantocrator", "panagia",
    "13th_century", "14th_century", "15th_century",
    "16th_century", "17th_century",  # most clearly-Byzantine icons
)

_ICON_DENY_KEYWORDS = (
    "raphael", "vasnetsov", "repin", "caravaggio", "rembrandt",
    "rubens", "guercino", "ceragioli", "cermak", "čermák",
    "tiepolo", "veronese", "tintoretto", "el_greco",
    "renaissance", "baroque", "rococo", "neoclass",
    "_painting_by_", "oil_on_canvas", "oil_on_panel",
    "by_giovanni_", "by_carlo_", "by_paolo_", "by_pietro_",
    "by_francesco_", "by_titian", "by_botticelli",
)


def classify_icon(filename: str) -> str:
    """Return one of: 'byzantine', 'western', 'uncertain'.

    Pure filename heuristic — won't catch every case, but flags the obvious
    "Western painting that crept in" issue we see when Wikipedia's English
    infobox gives us a Renaissance canvas instead of an Orthodox icon.
    """
    if not filename:
        return "uncertain"
    f = filename.lower().replace(" ", "_").replace("%20", "_")
    if any(k in f for k in _ICON_DENY_KEYWORDS):
        return "western"
    if any(k in f for k in _ICON_ALLOW_KEYWORDS):
        return "byzantine"
    return "uncertain"


def filename_from_url(url: str) -> str:
    """Extract decoded filename from a Wikimedia Commons thumbnail URL."""
    if not url:
        return ""
    # Wikimedia thumbnail URLs end with '/<width>px-<filename>' OR
    # plain Commons URLs with '/<filename>' as the last segment.
    import urllib.parse
    last = url.rstrip("/").rsplit("/", 1)[-1]
    if "-" in last and last[: last.find("-")].rstrip("px").isdigit():
        last = last.split("-", 1)[1]
    return urllib.parse.unquote(last)


def get_main_image(wikipedia_title: str, host: str) -> str | None:
    """Get the lead image filename for a Wikipedia article on a given host."""
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "name",
        "titles": wikipedia_title,
        "redirects": 1,
    }
    url = f"https://{host}/w/api.php"
    resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    for p in pages.values():
        return p.get("pageimage")
    return None


def strip_html(s: str) -> str:
    """Quick & dirty HTML strip for extmetadata fields."""
    s = re.sub(r"<[^>]+>", "", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    # Wikimedia's "Unknown author" template renders the text twice when
    # nested in <span class="vcard"><span class="fn">…</span></span> — strip
    # that case to a single occurrence.
    n = len(s)
    if n > 0 and n % 2 == 0 and s[: n // 2] == s[n // 2:]:
        s = s[: n // 2]
    return s


def get_image_info(filename: str) -> dict | None:
    """Get URL + license info for a Commons file."""
    params = {
        "action": "query",
        "format": "json",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": THUMB_WIDTH,
    }
    resp = requests.get(COMMONS_API, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    for p in pages.values():
        ii = p.get("imageinfo")
        if not ii:
            return None
        info = ii[0]
        ext = info.get("extmetadata", {})
        artist = strip_html(ext.get("Artist", {}).get("value", ""))
        license_short = strip_html(ext.get("LicenseShortName", {}).get("value", ""))
        return {
            "url": info.get("thumburl") or info.get("url"),
            "artist": artist,
            "license": license_short,
            "descriptionurl": info.get("descriptionurl", ""),
        }
    return None


def get_langlink(host: str, title: str, target_lang: str) -> str | None:
    """Find the equivalent article title in another language via interlanguage links."""
    params = {
        "action": "query",
        "format": "json",
        "prop": "langlinks",
        "titles": title,
        "redirects": 1,
        "lllang": target_lang,
        "lllimit": 1,
    }
    url = f"https://{host}/w/api.php"
    resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    for p in pages.values():
        ll = p.get("langlinks", [])
        if ll:
            return ll[0].get("*")
    return None


def fetch_icon(wikipedia_title: str) -> dict | None:
    """
    Resolve the best icon for a saint:
      1. Look up the article on en.wikipedia.org (definitive title space).
      2. Use langlinks to find the el.wikipedia.org equivalent.
      3. Prefer the image used by the Greek Wikipedia infobox — for Orthodox
         saints this is usually a traditional icon, while the English article
         often leads with a Western painting.
      4. Fall back to the English image if no Greek article exists or its
         infobox has no image.
    """
    en_filename: str | None = None
    el_filename: str | None = None

    # 1. English article + image
    try:
        en_filename = get_main_image(wikipedia_title, "en.wikipedia.org")
    except requests.RequestException:
        pass

    # 2. Find Greek article via langlinks
    try:
        el_title = get_langlink("en.wikipedia.org", wikipedia_title, "el")
        if el_title:
            el_filename = get_main_image(el_title, "el.wikipedia.org")
    except requests.RequestException:
        pass

    # 3. Or maybe the input title is already a Greek article
    if not el_filename:
        try:
            el_filename = get_main_image(wikipedia_title, "el.wikipedia.org")
        except requests.RequestException:
            pass

    # 4. Choose: prefer Greek-Wikipedia image
    chosen_filename = el_filename or en_filename
    if not chosen_filename:
        return None

    info = get_image_info(chosen_filename)
    if not info or not info.get("url"):
        return None

    info["wikipedia_lang"] = "el" if chosen_filename == el_filename else "en"
    return {"filename": chosen_filename, **info}


def format_attribution(info: dict) -> str:
    """Build a short, readable attribution string."""
    parts: list[str] = []
    if info.get("artist"):
        parts.append(info["artist"])
    parts.append("Wikimedia Commons")
    if info.get("license"):
        parts.append(info["license"])
    return " · ".join(parts)


# ----------------------------------------------------------------------
# Frontmatter rewriting
# ----------------------------------------------------------------------

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def read_md(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        raise ValueError(f"No frontmatter in {path}")
    fm = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    return fm, body


def write_md(path: Path, fm: dict, body: str) -> None:
    yaml_str = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100)
    path.write_text(f"---\n{yaml_str}---\n\n{body.lstrip()}", encoding="utf-8")


def update_saint_file(path: Path, *, force: bool, dry_run: bool) -> str:
    """Returns one of: 'updated', 'no-title', 'no-image', 'already', 'error'."""
    try:
        fm, body = read_md(path)
    except Exception as e:
        log(f"  {path.name}: parse error — {e}", level="error")
        return "error"

    title = fm.get("wikipediaTitle")
    if not title:
        return "no-title"

    if fm.get("iconUrl") and not force:
        return "already"

    log(f"  {path.name}: looking up '{title}'…")
    try:
        info = fetch_icon(title)
    except requests.RequestException as e:
        log(f"  {path.name}: network error — {e}", level="warn")
        return "error"
    if not info:
        log(f"  {path.name}: no image found for '{title}'", level="warn")
        return "no-image"

    fm["iconUrl"] = info["url"]
    fm["iconAttribution"] = format_attribution(info)

    if dry_run:
        log(f"  {path.name}: would set iconUrl={info['url']}")
        return "updated"

    write_md(path, fm, body)
    log(f"  {path.name}: updated", level="ok")
    time.sleep(1)  # be polite to APIs
    return "updated"


def update_all(*, force: bool, dry_run: bool) -> None:
    saints_dir = CONTENT_ROOT / "saints"
    files = sorted(saints_dir.glob("*.md"))
    log(f"Scanning {len(files)} saint files in {saints_dir}")

    counts = {"updated": 0, "already": 0, "no-title": 0, "no-image": 0, "error": 0}
    for f in files:
        result = update_saint_file(f, force=force, dry_run=dry_run)
        counts[result] += 1

    log(
        f"done — updated: {counts['updated']}, "
        f"already had icon: {counts['already']}, "
        f"no wikipediaTitle: {counts['no-title']}, "
        f"no image found: {counts['no-image']}, "
        f"errors: {counts['error']}",
        level="ok",
    )


def audit_all() -> None:
    """Classify the iconUrl of every saint file. Prints a flagged report.

    No network calls — pure filename-based classification.
    """
    saints_dir = CONTENT_ROOT / "saints"
    files = sorted(saints_dir.glob("*.md"))
    log(f"Auditing {len(files)} saint files in {saints_dir}")

    counts = {"byzantine": 0, "western": 0, "uncertain": 0, "missing": 0}
    flagged: list[tuple[str, str, str]] = []  # (slug, classification, filename)

    for path in files:
        try:
            fm, _ = read_md(path)
        except Exception as e:
            log(f"  {path.name}: parse error — {e}", level="error")
            continue
        url = fm.get("iconUrl") or ""
        if not url:
            counts["missing"] += 1
            continue
        fn = filename_from_url(url)
        cls = classify_icon(fn)
        counts[cls] += 1
        if cls != "byzantine":
            flagged.append((path.stem, cls, fn))

    log("")
    log(f"summary: byzantine={counts['byzantine']}, "
        f"uncertain={counts['uncertain']}, "
        f"western={counts['western']}, "
        f"missing-iconUrl={counts['missing']}",
        level="ok")

    if flagged:
        log("")
        log("flagged entries (review with `fix-icon` skill if needed):")
        for slug, cls, fn in flagged:
            tag = "✗" if cls == "western" else "?"
            log(f"  {tag} [{cls:9}] {slug:36} → {fn}")


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch saint icons from Wikipedia/Wikimedia Commons.")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--title", help="Wikipedia article title (single lookup, prints to stdout)")
    g.add_argument("--update-all", action="store_true", help="Iterate over saints/*.md")
    g.add_argument("--audit", action="store_true",
                   help="Classify existing iconUrls — flag non-Byzantine entries (no network)")
    p.add_argument("--force", action="store_true", help="Overwrite existing iconUrl")
    p.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = p.parse_args()

    try:
        if args.title:
            info = fetch_icon(args.title)
            if not info:
                log(f"No image found for: {args.title}", level="error")
                sys.exit(1)
            log(f"filename: {info['filename']}", level="ok")
            log(f"     url: {info['url']}")
            log(f"  artist: {info['artist']}")
            log(f" license: {info['license']}")
            log(f"  source: {info['descriptionurl']}")
            log(f"  attribution: {format_attribution(info)}")
            log(f"  byzantine?: {classify_icon(info['filename'])}")
        elif args.audit:
            audit_all()
        else:
            update_all(force=args.force, dry_run=args.dry_run)
    except requests.RequestException as e:
        log(f"Network error: {e}", level="error")
        sys.exit(1)


if __name__ == "__main__":
    main()
