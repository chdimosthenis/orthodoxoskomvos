---
name: add-saint
description: Add a new saint to src/content/saints/ with original Greek hagiographic content. Trigger when the user asks to add, create, or write up an Orthodox saint — e.g. "πρόσθεσε τον Άγιο Σάββα", "γράψε για τον Όσιο Πορφύριο", "ο Άγιος Παΐσιος", "add Saint Anthony the Great", expansions of the menologion, or any request to enrich the saints calendar with a new individual entry.
---

# Add a saint

A saint entry lives in `src/content/saints/<slug>.md` and renders at
`/saints/<slug>/`. Two paths to add one — pick by scope:

- **Single ad-hoc entry** → write the file directly (faster).
- **Part of a curated batch** → append to `scripts/calendar_seed.py`'s
  `SAINTS_EL` list and re-run the seeder. Entries written this way are
  easy to regenerate with `--force` if the schema changes.

## Required information

Confirm with the user (or look up):

| Field | Notes |
|---|---|
| `name` | Full Greek form, e.g. "Άγιος Νικόλαος Μύρων της Λυκίας" |
| `feastDay` | MM-DD format. Skip movable feasts (use the `liturgical` collection instead). |
| `category` | `martyr` / `monastic` / `hierarch` / `apostle` / `prophet` / `other` |
| `wikipediaTitle` | English Wikipedia title — used by `fetch_icon.py` to find a Commons icon |
| `tropar`, `kontak` | Optional. Only include traditional centuries-old Byzantine compositions (definitely public domain). Don't include modern published translations. |
| `life` | One-sentence Greek summary (~100 chars max) for cards and the today widget |
| body | 80–120 word original Greek prose. **Do NOT copy from copyrighted sources.** |

## Path A — direct file (single saint)

```
# Pick a slug: transliterated Greek, hyphenated lowercase
# e.g. "Άγιος Σάββας ο Ηγιασμένος" → "agios-savvas-igiasmenos"
```

Write `src/content/saints/<slug>.md`:

```yaml
---
name: Άγιος ...
wikipediaTitle: ...
feastDay: MM-DD
category: ...
tropar: ...   # optional
kontak: ...   # optional
life: One-sentence Greek summary.
language: el
---

Greek body text, 80–120 words, original prose. Use polytonic where
quoting traditional texts; monotonic for modern Greek narrative.
```

Then fetch the icon and ship:

```bash
cd scripts && ./venv/Scripts/python.exe fetch_icon.py --update-all
cd .. && npm run build
git add . && git commit -m "feat: add <name> (<feast>)" && git push
```

## Path B — append to seeder (curated batch)

Edit `scripts/calendar_seed.py`, append a dict to `SAINTS_EL` matching the
existing pattern (slug, frontmatter dict, body string). Then:

```bash
cd scripts && ./venv/Scripts/python.exe calendar_seed.py --force
./venv/Scripts/python.exe fetch_icon.py --update-all
cd .. && npm run build
git add . && git commit -m "feat: seed N saints" && git push
```

## English version

If the user wants an English counterpart, see the `translate-entry` skill.

## Don'ts

- Don't make up Wikipedia titles that don't exist — verify or omit the
  field (icons can be added later via `fetch_icon.py`).
- Don't include copyrighted modern Greek translations of patristic texts.
- Don't set `iconUrl` manually as the first attempt — let `fetch_icon.py`
  resolve it from `wikipediaTitle`. Use the `fix-icon` skill if a specific
  Commons file is wanted.
- Don't commit without running `npm run build` first — schema validation
  errors only surface there.
