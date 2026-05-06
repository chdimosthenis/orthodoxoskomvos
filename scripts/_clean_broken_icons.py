"""HEAD-request every saint iconUrl; remove broken ones.

Pass 1: identify any saint .md file whose iconUrl returns non-200 (404,
403 hotlink-blocked, etc.) or fails to connect.

Pass 2: remove the `iconUrl:` and `iconAttribution:` lines from those
files. The saint stays — only the broken image reference is dropped, so
the saint card just renders without a thumbnail rather than a broken-
image icon.

Run:
    python _clean_broken_icons.py            # report only
    python _clean_broken_icons.py --apply    # actually remove broken refs
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
SAINTS_DIR = ROOT / "src" / "content" / "saints"
HEADERS = {
    "User-Agent": "OrthodoxLogos/1.0 (icon-validator; +https://orthodox-site.pages.dev)",
    "Accept": "image/*,*/*;q=0.5",
}
TIMEOUT = 15


def url_of(text: str) -> str | None:
    m = re.search(r"^iconUrl:\s*\"?([^\"\n]+)\"?\s*$", text, re.MULTILINE)
    return m.group(1).strip().strip('"').strip("'") if m else None


def check(url: str) -> tuple[int | str, str]:
    """Returns (status_or_error, url). Retries on 429 with exponential backoff."""
    for attempt in range(4):
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True, allow_redirects=True)
            status = r.status_code
            r.close()
            if status == 429:
                time.sleep(2 ** attempt)  # 1, 2, 4, 8s
                continue
            return (status, url)
        except requests.RequestException as e:
            return (f"ERR {type(e).__name__}", url)
    return (429, url)


def strip_icon_lines(text: str) -> str:
    text = re.sub(r"^iconUrl:.*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"^iconAttribution:.*\n", "", text, flags=re.MULTILINE)
    return text


def try_alternative_thumb(url: str) -> str | None:
    """Some Wikimedia thumb sizes 404 because they're not pre-generated.
    Try common alternatives (800px, 480px) before giving up."""
    if "/thumb/" not in url or "px-" not in url:
        return None
    for alt in ("800px", "480px", "320px", "1024px"):
        candidate = re.sub(r"/\d+px-", f"/{alt}-", url, count=1)
        # Truncate at first '?' to drop utm params during the test
        test_url = candidate.split("?", 1)[0]
        try:
            r = requests.head(test_url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            if 200 <= r.status_code < 300:
                return candidate
        except requests.RequestException:
            continue
        time.sleep(0.5)
    return None


def replace_icon_url(text: str, new_url: str) -> str:
    return re.sub(r"^iconUrl:.*$", f"iconUrl: \"{new_url}\"", text, count=1, flags=re.MULTILINE)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true", help="Strip broken iconUrl references")
    p.add_argument("--workers", type=int, default=12)
    args = p.parse_args()

    if not SAINTS_DIR.is_dir():
        print(f"ERROR: {SAINTS_DIR} not found", file=sys.stderr)
        return 1

    targets: list[tuple[Path, str]] = []
    for f in sorted(SAINTS_DIR.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        u = url_of(text)
        if u:
            targets.append((f, u))

    print(f"Checking {len(targets)} iconUrls with {args.workers} workers...")

    broken: list[tuple[Path, str, str]] = []
    ok = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_to_path = {pool.submit(check, u): (f, u) for f, u in targets}
        for fut in as_completed(future_to_path):
            f, u = future_to_path[fut]
            status, _ = fut.result()
            if isinstance(status, int) and 200 <= status < 300:
                ok += 1
            else:
                broken.append((f, u, str(status)))

    print(f"\n  OK:     {ok}")
    print(f"  BROKEN: {len(broken)}\n")

    if broken:
        print("--- broken ---")
        for f, u, status in sorted(broken, key=lambda x: x[0].name):
            print(f"  [{status}] {f.name}")
            print(f"      {u[:120]}")
        print()

    if args.apply and broken:
        # Skip 429s (rate-limited, not actually broken) — they'll resolve on retry.
        actionable = [(f, u, s) for f, u, s in broken if str(s) != "429"]
        if not actionable:
            print(f"--apply: all {len(broken)} 'broken' are 429 rate-limits, skipping.")
            return 0

        repaired: list[Path] = []
        stripped: list[Path] = []
        for f, u, _status in actionable:
            text = f.read_text(encoding="utf-8")
            alt = try_alternative_thumb(u)
            if alt:
                f.write_text(replace_icon_url(text, alt), encoding="utf-8")
                repaired.append(f)
                print(f"  REPAIRED {f.name} → {alt[:80]}...")
            else:
                f.write_text(strip_icon_lines(text), encoding="utf-8")
                stripped.append(f)
                print(f"  STRIPPED {f.name}")

        print(f"\n--apply: repaired {len(repaired)}, stripped {len(stripped)}.")
    elif broken:
        print("Run with --apply to repair-or-strip these broken references.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
