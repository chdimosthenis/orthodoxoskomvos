---
name: fix-icon
description: Replace or correct the iconUrl/iconAttribution of a specific saint when the auto-fetched Wikimedia Commons icon is wrong, low-quality, Western-style rather than Orthodox, or absent. Trigger on requests like "η εικόνα του Νικολάου είναι λάθος", "βάλε άλλη εικόνα στον <saint>", "fix the icon for <saint>", "βρες καλύτερη εικόνα για...".
---

# Fix or replace a saint's icon

Each saint has optional `iconUrl` and `iconAttribution` fields populated by
`scripts/fetch_icon.py` from Wikipedia/Commons. Sometimes the auto-pick
isn't ideal — a 19th-century Western painting instead of a Byzantine icon,
a low-resolution or poorly cropped file, or no match at all.

## Option 1 — try a different Wikipedia title

Edit the saint's `wikipediaTitle` field, then re-fetch:

```bash
cd scripts && ./venv/Scripts/python.exe fetch_icon.py --update-all --force
```

Common title fixes:

- "Spyridon" → "Saint Spyridon" (disambiguation problem)
- A specific name → an article variant the user knows has a good infobox

The fetcher follows interlanguage links, preferring the Greek-Wikipedia
infobox (which usually shows the Orthodox icon) over the English one
(often a Western painting). So updating the input title can route to a
different image.

## Option 2 — pick a Commons file by hand

If `fetch_icon.py` keeps returning the wrong thing:

1. Browse <https://commons.wikimedia.org> and find the desired file. Useful categories:
   - "Category:Orthodox icons"
   - "Category:Icons of <Saint name>"
   - "Category:<Saint name> in icons"
2. Open the file's description page, copy a thumbnail URL of suitable
   size (~600–800px). The pattern is:
   `https://upload.wikimedia.org/wikipedia/commons/thumb/<hash>/<file>/<width>px-<file>`
3. Edit the saint markdown directly:

```yaml
iconUrl: https://upload.wikimedia.org/wikipedia/commons/thumb/.../800px-...jpg
iconAttribution: <Author> · Wikimedia Commons · <License>
```

4. Build and commit:

```bash
npm run build
git add . && git commit -m "fix(icon): replace <saint> icon with <description>" && git push
```

## Quick lookup without modifying anything

```bash
./venv/Scripts/python.exe fetch_icon.py --title "<Wikipedia article title>"
```

This prints filename / URL / artist / license to stdout without writing.
Useful to check if a title resolves to anything before committing to it.

## Don'ts

- Don't hotlink files outside Wikimedia Commons. We rely on Commons CDN
  and PD/CC licensing. Other hosts' images break the attribution model
  and may break (link rot).
- Don't strip the `?utm_source=...` query parameters Wikimedia adds to
  thumbnail URLs — they're harmless analytics tags. The image still loads.
- Don't set `iconUrl` to point at a low-resolution thumbnail (<300px wide).
  Saint pages render up to 280px wide; smaller sources look pixelated.
- Don't forget to update `iconAttribution` when you change `iconUrl`.
  Stale attribution is worse than no attribution.
