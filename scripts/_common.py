"""Common helpers for the content scraping scripts.

All file output is UTF-8 with explicit `allow_unicode=True` for YAML so that
Greek polytonic text round-trips faithfully.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml
from bs4 import BeautifulSoup
from markdownify import markdownify
from slugify import slugify

# Windows: force UTF-8 stdout/stderr so log() can print ✓ and Greek text
# without crashing on the default cp1253 / cp1252 console encoding.
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is not None and hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = REPO_ROOT / "src" / "content"


# ---- slug & strings -------------------------------------------------------

def make_slug(text: str, language: str = "el") -> str:
    """Slugify a title. python-slugify transliterates Greek to ASCII."""
    s = slugify(text, lowercase=True, max_length=80, word_boundary=True)
    return s or "untitled"


# ---- HTML cleaning --------------------------------------------------------

DEFAULT_REMOVE_SELECTORS = [
    "nav", "footer", "header[role='banner']",
    ".navigation", ".nav", ".header", ".footer",
    ".sidebar", ".aside", ".menu",
    ".advertisement", ".ad", ".ads",
    ".social", ".share-buttons", ".social-share",
    "script", "style", "noscript",
    ".mw-editsection", ".reference", ".mw-cite-backlink",
    ".navbox", ".thumbinner", ".infobox",
    ".toc", "#toc",
]


def clean_html(html: str, extra_selectors: Iterable[str] = ()) -> str:
    """Strip out chrome / navigation / footer elements before extraction."""
    soup = BeautifulSoup(html, "html.parser")
    selectors = list(DEFAULT_REMOVE_SELECTORS) + list(extra_selectors)
    for sel in selectors:
        for tag in soup.select(sel):
            tag.decompose()
    return str(soup)


def html_to_markdown(html: str) -> str:
    """Convert (cleaned) HTML to Markdown."""
    md = markdownify(html, heading_style="ATX", strip=["script", "style"])
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def extract_title(html: str) -> str | None:
    """Try to find the most representative title in an HTML document."""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    title = soup.find("title")
    if title and title.get_text(strip=True):
        return title.get_text(strip=True)
    return None


# ---- file output ----------------------------------------------------------

def write_content(
    collection: str,
    slug: str,
    frontmatter: dict[str, Any],
    body: str,
    *,
    force: bool = False,
) -> Path:
    """Write a markdown file with YAML frontmatter to the collection directory."""
    target_dir = CONTENT_ROOT / collection
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{slug}.md"

    if target.exists() and not force:
        raise FileExistsError(f"{target} already exists. Use --force to overwrite.")

    yaml_str = yaml.safe_dump(
        frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=100,
    )
    out = f"---\n{yaml_str}---\n\n{body.rstrip()}\n"
    target.write_text(out, encoding="utf-8")
    return target


def check_exists(collection: str, slug: str) -> bool:
    return (CONTENT_ROOT / collection / f"{slug}.md").exists()


# ---- logging --------------------------------------------------------------

_PREFIX = {"info": "  ", "ok": "✓ ", "warn": "⚠ ", "error": "✗ "}


def log(msg: str, *, level: str = "info") -> None:
    prefix = _PREFIX.get(level, "  ")
    stream = sys.stderr if level == "error" else sys.stdout
    print(f"{prefix}{msg}", file=stream, flush=True)
