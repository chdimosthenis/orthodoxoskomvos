---
name: split-akolouthia-to-hymns
description: When the user asks for individual famous hymns of a long service (Encomia, Paschal Canon, Akathistos), fetch the full akolouthia from glt.goarch.org once and produce one full akolouthia entry plus N short standalone hymn entries with the iconic verses, all cross-linked. Trigger on "πρόσθεσε τοὺς ὕμνους τῆς Μ. Παρασκευῆς", "βάλε τὸ ζωή ἐν τάφω καὶ τὸ γενεαὶ πᾶσαι", "split <service> into individual hymns", or any request for SPECIFIC named hymns that are part of a longer service.
---

# Split a long akolouthia into iconic standalone hymn entries

This is the pattern used to add the three Encomia stations and the four
Paschal hymns. The user almost always names the iconic verses they want
("ζωή ἐν τάφῳ", "γενεαὶ πᾶσαι", "ἀναστάσεως ἡμέρα") — those become the
standalone entries; the full akolouthia is the parent.

## Step 1 — probe glt.goarch.org for the URL

```python
# Try common path patterns. Tri/ for Triodion, Pen/ for Pentekostarion,
# Oro/ for daily cycle, Euch/ for sacraments, <Mon>NN.html for fixed feasts.
candidates = [
    'https://glt.goarch.org/texts/Tri/Lamentations.html',
    'https://glt.goarch.org/texts/Pen/Pascha.html',
    'https://glt.goarch.org/texts/Oro/Akathistos.html',
    # add likely variants
]
for url in candidates:
    r = requests.head(url, timeout=10, headers={'User-Agent':'orthodox-site/1.0'})
    print(r.status_code, url)
```

Many candidates will 404 — GOA's URL convention is inconsistent. Common
hits: `Tri/Lamentations.html`, `Pen/Pascha.html`. Note that GOA serves
404 pages with HTTP 200 sometimes — check status 200 AND page length > a
few KB.

## Step 2 — extend `seed_akolouthies.py` with the new entry

```python
# In ENTRIES list, add the slug → path mapping:
{"slug": "epitafios-thrinos", "title": "Τὰ Ἐγκώμια — Ἐπιτάφιος Θρῆνος",
 "type": "akolouthia", "path": "Tri/Lamentations.html"},
```

Then run:

```bash
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe seed_akolouthies.py --slug epitafios-thrinos
```

This writes the full text to `src/content/liturgical/<slug>.md` with
`type: akolouthia`, `language: el`, `license: public-domain`,
`sourceUrl: <GOA URL>`.

## Step 3 — extract iconic verses from the fetched file

Read the saved file and locate the named hymn(s) the user mentioned.
The GOA pages structure each station with `ΣΤΑΣΙΣ ΠΡΩΤΗ`/`ΔΕΥΤΕΡΑ`/`ΤΡΙΤΗ`
markers. Use grep for the iconic opening phrase to find the start of
each hymn block; copy the first 4–6 verses (the well-known ones).

## Step 4 — write standalone hymn entries

Each gets its own file at `src/content/liturgical/<slug>.md`:

```yaml
---
title: "<Greek title>"
type: hymn
source: "<which station>, <which service>, <which mode>. Παραδοσιακό· Public domain."
language: el
sourceUrl: https://glt.goarch.org/texts/<...>.html
license: public-domain
---

> **<Iconic opening verse, polytonic, blockquoted, bold for the famous line>**

> <Second iconic verse>

> <Third iconic verse>

> <Final iconic verse, bolded>

<2–3 paragraphs of original Greek prose explaining:
 - which station/place in the service
 - the theological move the hymn makes
 - the liturgical context (when sung, by whom)>

Δεῖτε τὸ πλῆρες κείμενο στὸν
[<parent akolouthia title>](/liturgical/<parent-slug>/).
```

Naming convention for slugs: short Latin transliteration of the iconic
incipit (e.g. `zoi-en-tafo.md`, `axion-esti-megalynein.md`,
`anastaseos-imera.md`). Avoid clashing with existing slugs — the
Liturgy "Ἄξιον ἐστὶν" Theotokion already lives at `axion-estin.md`, so
the Holy Saturday "Ἄξιον ἐστὶ μεγαλύνειν" needs a distinct slug.

## Step 5 — commit + push

One commit for the whole set is fine (the akolouthia + hymns are a
logical unit). Title with `feat(liturgical):` prefix per CLAUDE.md.

```bash
git pull --rebase origin main
git add scripts/seed_akolouthies.py src/content/liturgical/
git commit -m "feat(liturgical): add <Service> — full text + N hymn entries"
git push
```

## Don'ts

- Don't write the full text by hand — fetch from GOA. Even if you "know"
  the verses, the polytonic accents and verse breaks must match GOA's
  authoritative digital edition.
- Don't include all 75 verses of each station in the hymn entry — pick
  the 4–6 iconic ones and link to the full akolouthia. Long hymn pages
  hurt the /ymnoi listing UX.
- Don't fabricate `source` attribution — copy the conventional credit
  block from `seed_akolouthies.py` SOURCE_CREDIT or use `Public domain`
  with a short historical note.
