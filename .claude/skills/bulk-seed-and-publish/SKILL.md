---
name: bulk-seed-and-publish
description: One-shot mass content drop — run the daily-saints seeder for many days at once, then auto-classify and publish all the safe bot drafts in a single commit. Trigger on "γέμισε τὸ συναξάριο", "πρόσθεσε X μέρες ἁγίους", "bulk seed", "fill the calendar", "add a month of saints", "ξαναζωντάνεψε τὸ /saints", or any request that asks for a large content boost to the saints collection in one pass. Do NOT use for the daily 1–2 day cron run — that's the GitHub Actions bot's job.
---

# Bulk-seed and publish in one pass

The daily-saints bot adds ~30–60 commemorations per day. To populate the
calendar more aggressively, run the seeder for many days at once, then
publish the safe drafts immediately.

**This is the workflow that takes saints from ~93 published to 450+ in
one go.** Pre-batched with the right scripts so there's no manual triage.

## Prerequisites

- `scripts/venv/` exists with `requirements.txt` installed.
  - One-time setup: `cd scripts && python -m venv venv && ./venv/Scripts/python.exe -m pip install -r requirements.txt`
- Working tree clean (or willing to commit current state first — bulk
  edits will conflict with manual edits to `src/content/saints/`).

## Step 1 — seed N days

```bash
cd scripts
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe daily_seed.py --days 30
```

Sane defaults:
- `--days 14` for a fortnight boost
- `--days 30` for a month (~300–400 new entries)
- `--days 60+` only when starting from near-empty — the script makes one
  Wikipedia API call per saint, and 60 days = ~600 calls = ~10 min run

Output: each new entry is written with `draft: true` to
`src/content/saints/<slug>.md`, with body excerpted from the Wikipedia
"Month Day (Eastern Orthodox liturgics)" page.

## Step 2 — bulk-publish via the triage classifier

```bash
PYTHONIOENCODING=utf-8 python scripts/_triage_drafts.py --publish
```

`_triage_drafts.py` (committed in this repo) classifies every draft into:

- **bot-publishable** — auto-seeded, real-saint name → publishes (removes `draft: true`).
- **bot-suspect** — filename suggests place/date (e.g. `river-*`, `march-*`,
  `monastery-of-*`, `basilica-*`, `abbey-of-*`) → leaves as draft.
- **user-authored** — `license: original` → leaves alone (manual entries).
- **excluded duplicates** — hardcoded skips like `agathius-of-byzantium.md`
  (it's the same saint as `acacius.md`).

Run without `--publish` first to see the report; with `--publish` to apply.

## Step 3 — handle the false positives

Some real saints get caught by the `monastery-of-` heuristic — most
notably the **Kantara monk-martyrs** (Cypriot 1231 collective martyrdom).
After a bulk run, scan `bot-suspect` and manually publish real saints by
removing the `draft: true` line.

## Step 4 — verify the icon coverage

```bash
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe fetch_icon.py --update-all
```

Slow (~1s/entry, so ~10 min for 500 saints) but idempotent — only fetches
for entries that lack `iconUrl`. Each lookup hits Wikipedia langlinks →
Commons; many obscure pre-Schism Western saints have no Wikipedia image
and stay icon-less.

## Step 5 — commit + push

The bots may have pushed during your run. Always rebase first:

```bash
git pull --rebase origin main
git add -A
git commit -m "feat(saints): bulk seed N days + publish XYZ + icons"
git push
```

If push is rejected mid-flight, see `recover-from-bot-push`.

## Don'ts

- Don't run `--days 365` blindly — that's many minutes of API calls and
  produces hundreds of low-quality entries (very obscure saints from
  the long tail of the Wikipedia liturgics calendar).
- Don't bulk-publish without a quick scan of `bot-suspect` first.
  `_triage_drafts.py` flags these but doesn't auto-handle them.
- Don't commit the temporary venv. It's already in `.gitignore`.
- Don't bypass the script and `git add` everything — the duplicate
  `agathius-of-byzantium.md` and the suspect place-name files would
  go live and pollute the index.
