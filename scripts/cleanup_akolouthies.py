"""Post-process glt.goarch.org-fetched akolouthia markdown.

The GOA pages embed:
- Audio links like `[ΤΟ ΑΚΟΥΤΕ](../../music/4079.mp3)` — point to GOA's own
  /music/ path, broken from our site.
- Relative image refs `![...](../../images/...)` — same problem.
- Bullet markers (•) used as metric markers, not list bullets — ugly in Markdown.

This pass strips those artifacts and normalizes whitespace. Idempotent.

Usage:
    python cleanup_akolouthies.py             # all GOA-sourced entries
    python cleanup_akolouthies.py --slug X    # single file
    python cleanup_akolouthies.py --dry-run
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from _common import CONTENT_ROOT, log

LITURGICAL_DIR = CONTENT_ROOT / "liturgical"

# Slugs that came from the GOA scraper. Update if seed_akolouthies.py grows.
GOA_SLUGS = {
    # Ωρολόγιον
    "mikron-apodeipnon", "mega-apodeipnon", "mesonyktikon",
    "esperinos", "esperinos-kyriakis", "orthros", "orthros-kyriakis",
    "ora-prote", "ora-trite", "ora-ekte", "ora-enate",
    # Παρακλήσεις / Ακάθιστος
    "paraklesis-mikra", "paraklesis-megale",
    "akathistos-ymnos", "chairetismoi-staseis",
    # Θεῖες Λειτουργίες
    "theia-leitourgia-chrysostomou", "theia-leitourgia-vasileiou",
    "leitourgia-proegiasmenon", "theia-leitourgia-iakovou",
    # Ευχολόγιον
    "mikros-agiasmos", "vaptisma", "stefanoma-gamou",
    "nekrosimos-akolouthia", "mnimosyno-trisagion",
    # Δεσποτικαὶ Ἑορταί
    "megas-agiasmos",
}

# Audio link variants — any [text](relative/path.mp3) pattern.
AUDIO_LINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\.mp3\)")
# Relative-path image references.
REL_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\.\./[^)]*\)")
# Standalone bullet markers ('• ') that GOA uses as decorative dots.
BULLET_RE = re.compile(r"^\s*•\s+", flags=re.MULTILINE)
# Collapse 3+ blank lines.
EXTRA_BLANK_RE = re.compile(r"\n{3,}")


def clean_body(body: str) -> str:
    body = AUDIO_LINK_RE.sub("", body)
    body = REL_IMAGE_RE.sub("", body)
    body = BULLET_RE.sub("", body)
    body = EXTRA_BLANK_RE.sub("\n\n", body)
    return body.strip() + "\n"


def split_frontmatter(text: str) -> tuple[str, str] | None:
    """Return (frontmatter_inner, body) tuple, or None if not parseable."""
    if not text.startswith("---\n"):
        return None
    rest = text[4:]
    end = rest.find("\n---\n")
    if end == -1:
        return None
    fm = rest[:end + 1]  # include trailing newline
    body = rest[end + 5:]
    return fm, body


def process_file(path: Path, *, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    parsed = split_frontmatter(text)
    if parsed is None:
        log(f"  no frontmatter: {path.name}", level="warn")
        return False
    fm, body = parsed

    cleaned = clean_body(body)
    new_text = f"---\n{fm}---\n\n{cleaned}"

    if new_text == text:
        log(f"  unchanged: {path.name}")
        return False

    chars_removed = len(text) - len(new_text)
    log(f"  {'WOULD CLEAN' if dry_run else 'cleaned'} {path.name} (-{chars_removed} chars)",
        level="ok")

    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", help="Process only this slug")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    targets = [args.slug] if args.slug else sorted(GOA_SLUGS)
    log(f"Cleaning {len(targets)} file(s)")

    changed = 0
    for slug in targets:
        path = LITURGICAL_DIR / f"{slug}.md"
        if not path.exists():
            log(f"  missing: {slug}.md", level="warn")
            continue
        if process_file(path, dry_run=args.dry_run):
            changed += 1

    log(f"Done: {changed}/{len(targets)} file(s) {'would change' if args.dry_run else 'cleaned'}",
        level="ok")


if __name__ == "__main__":
    main()
