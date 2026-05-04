---
name: fetch-content
description: Drive the existing Python scrapers to import content from CCEL (public-domain English patristics), OrthodoxWiki (CC-BY-SA encyclopedia), Myriobiblos (Greek texts, mixed licenses), or Wikimedia Commons (icons). Trigger on "τράβα από CCEL/OrthodoxWiki/Myriobiblos", "import this article", "fetch the icon for...", or scraping/importing tasks against those sources.
---

# Fetch content via Python scrapers

All scrapers live in `scripts/` and run via the project's Python venv.

## Setup (once after fresh clone)

```bash
cd scripts
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

## CCEL — public domain English patristics

```bash
./venv/Scripts/python.exe fetch_ccel.py "https://ccel.org/ccel/<...>" \
  --author "Author Name" \
  --collection articles
```

Flags: `--force` overwrites; `--dry-run` previews without writing.
License auto-set to `public-domain`.

## OrthodoxWiki — CC-BY-SA encyclopedia

```bash
./venv/Scripts/python.exe fetch_orthodoxwiki.py "Page Title" \
  --collection articles    # or saints, fathers
```

License auto-set to `CC-BY-SA`. Attribution to "OrthodoxWiki contributors".
For `--collection saints`, the fetcher writes placeholder `feastDay`
(`01-01`) and `category` (`other`) — fix these manually before publishing.

## Myriobiblos — Greek texts, mixed licenses

```bash
./venv/Scripts/python.exe fetch_myriobiblos.py "https://myriobiblos.gr/..." \
  --author "Author Name"
```

**License is assumed `public-domain` and a warning is printed.** Always
verify the source page's specific copyright notice before publishing —
some Myriobiblos texts are modern translations under restrictive license.

## Wikimedia Commons — saint icons

```bash
# Single lookup (prints, doesn't write)
./venv/Scripts/python.exe fetch_icon.py --title "Wikipedia Article Title"

# Update all saints that have wikipediaTitle but no iconUrl
./venv/Scripts/python.exe fetch_icon.py --update-all

# Refresh icons even where they already exist
./venv/Scripts/python.exe fetch_icon.py --update-all --force
```

The fetcher follows EN → EL Wikipedia interlanguage links and prefers
the Greek-Wikipedia infobox image (typically an Orthodox icon over a
Western painting).

## Daily auto-seed (already running on cron)

`scripts/daily_seed.py` is invoked by `.github/workflows/daily-saints.yml`
at 03:00 UTC. **Don't run it locally without `--dry-run`** unless you
intend to add stubs to the working tree.

```bash
# Preview tomorrow's commemorations without writing
./venv/Scripts/python.exe daily_seed.py --dry-run --days 1
```

## After any fetch

1. Review the resulting Markdown — boilerplate sometimes leaks through
2. Verify schema with a build: `cd .. && npm run build`
3. Commit with a descriptive message naming the source

## Encoding gotcha (Windows)

The scripts reconfigure `sys.stdout`/`sys.stderr` to UTF-8 at startup so
`log()` works on Windows cp1253 consoles. If you add a new script,
import from `_common.py` to inherit the same preamble — don't roll your
own logging that writes Greek or `✓`/`⚠` glyphs to a default-encoding stream.
