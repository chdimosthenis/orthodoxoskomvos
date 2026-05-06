---
name: probe-orthodoxwiki
description: When a seed_*.py script tries to fetch a page that doesn't exist on OrthodoxWiki (the canonical title is missing — common for "Pneumatology", "Eschatology", "Last Judgment", "Mystery (sacrament)"), probe alternate titles via the MediaWiki API to find pages that DO exist and cover the same theological territory. Trigger on "ξαναδοκίμασε X μὲ ἐναλλακτικοὺς τίτλους", "find OrthodoxWiki page for X", "API error: page doesn't exist" from a seeder run.
---

# Probe OrthodoxWiki for alternate titles

OrthodoxWiki has uneven coverage. Some canonical theological topics
(Pneumatology, Eschatology, Last Judgment, Mystery/sacrament) lack
dedicated pages but are covered under different titles (Holy Spirit,
Heaven, Filioque, Mystery (something-else)). The seeder's `API error:
page doesn't exist` is the trigger to switch titles.

## Step 1 — batch-query candidate titles

Use a single MediaWiki API call to test many candidates at once:

```python
import requests
titles = ['Pneumatology', 'Holy Spirit', 'Filioque',  # for Pneumatology
          'Eschatology', 'Heaven', 'Death', 'Last Judgment',  # for Eschatology
          'Christology', 'Incarnation', 'Theotokos', 'Resurrection']  # Christology
r = requests.get('https://orthodoxwiki.org/api.php', params={
    'action': 'query', 'titles': '|'.join(titles), 'format': 'json',
    'redirects': 1,
}, timeout=20)
pages = r.json()['query']['pages']
existing = [p['title'] for p in pages.values() if 'pageid' in p]
missing = [p['title'] for p in pages.values() if 'missing' in p]
print('EXISTING:', existing)
print('MISSING:', missing)
```

The API takes pipe-separated titles in one request — fast and rate-limit
friendly. A `pageid` in the response means the page exists; `missing`
key means it doesn't.

## Step 2 — substitute in the seeder

For each missing canonical title, pick 1–3 adjacent existing pages that
together cover the territory:

```
Pneumatology → Holy Spirit, Filioque
Christology  → Incarnation, Theotokos, Resurrection (Christology page is a stub)
Eschatology  → Heaven, Death
```

Add to the seeder's ENTRIES list with appropriate tags. Example
`seed_theology.py` extension:

```python
# --- Pneumatology (substitutes — OrthodoxWiki has no "Pneumatology") ---
{"page": "Holy Spirit",  "tags": ["theology", "dogmatics"]},
{"page": "Filioque",     "tags": ["theology", "dogmatics"]},
```

Comment the substitution so the next contributor doesn't re-add the
canonical title and re-trip the same error.

## Step 3 — run the seeder

```bash
cd scripts
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe seed_theology.py
```

The script is idempotent (`check_exists` skips pre-existing entries) so
re-running after extending ENTRIES only fetches the new ones.

## Step 4 — record what's confirmed-missing in CLAUDE.md

In the "Sources used" section, add or extend the
`Confirmed-NOT-available` paragraph with the titles you ruled out, plus
the substitutions you used. Keeps the next session from repeating the
probe:

```markdown
Confirmed-NOT-available (need different source): ... the literal
`Pneumatology` / `Eschatology` / `Last Judgment` / `Mystery (sacrament)`
pages on OrthodoxWiki.

For Christology / Pneumatology / Eschatology coverage we substitute
adjacent OrthodoxWiki pages that DO exist:
- Pneumatology cluster: Holy Spirit, Filioque
- Christology cluster: Christology (stub), Incarnation, Theotokos, Resurrection
- Eschatology cluster: Heaven, Death
```

## Don'ts

- Don't translate from Wikipedia or another source as a fallback when
  OrthodoxWiki lacks the page. The whole point of OrthodoxWiki is the
  CC-BY-SA license + Orthodox editorial perspective. Substitute another
  OrthodoxWiki page or write original Greek prose; do NOT cross to a
  different licensing regime silently.
- Don't try to write the missing page on OrthodoxWiki itself. That's
  out of scope for this site.
- Don't grep the seeder source for the canonical title and edit in
  place — extend the ENTRIES list instead, with an explicit comment
  about the substitution.
