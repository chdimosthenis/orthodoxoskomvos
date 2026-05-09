---
name: add-father
description: Add a new Πατέρα τῆς Ἐκκλησίας entry to src/content/fathers/ in polytonic Greek with the canonical Βίος / Διδασκαλία / Σημασία body structure. Distinct from add-saint — fathers are a separate collection (different schema, polytonic register, century field, no iconUrl). Triggers when the user asks to add, write, or include a Father — e.g. "πρόσθεσε τὸν ἅγιο Μάξιμο τὸν Ὁμολογητή ὡς Πατέρα", "γράψε γιὰ τὸν ἅγιο Φώτιο", "add Saint Athanasius the Great", "τοὺς Πατέρες τῆς Ἐκκλησίας".
---

# Add a Father of the Church

Distinct from saints. Fathers are theological-doctrinal authorities; the
collection is **polytonic Greek** strictly, with three canonical body
sections.

## Schema (`src/content.config.ts → fathers`)

```yaml
---
name: "Polytonic short name, e.g. Γρηγόριος ὁ Παλαμᾶς"
fullName: "Ὁ ἐν ἁγίοις Πατὴρ ἡμῶν Γρηγόριος ὁ Παλαμᾶς, Ἀρχιεπίσκοπος Θεσσαλονίκης"
century: 14                # int
feastDay: "11-14"          # MM-DD, optional (some Fathers don't have a fixed feast)
summary: "1-2 sentences in polytonic Greek"
language: el
license: original
draft: false
---
```

NOTE: no `iconUrl` field. Fathers don't render icons (the rationale: they
are authorities, not objects of veneration in the same iconographic
sense; their `/fathers/` listing is text-only with century badges).

## Body structure

Three sections, ALWAYS in this order:

```markdown
## Βίος

[Birth, family, education, monastic call, episcopal/abbatial career,
councils attended, exile/martyrdom, repose. ~60-100 words.]

## Διδασκαλία

[Key works (with original Greek titles), doctrinal contribution
(Trinitarian / Christological / sacramental / spiritual / canonical),
characteristic phrases or formulae. ~80-150 words.]

## Σημασία

[Why this Father matters for Orthodox tradition: which council ratified
their teaching, which later movement they shaped, where they sit
relative to the broader patristic corpus. ~40-80 words.]
```

Total body ~200-300 words.

## Voice exemplar

Always read `src/content/fathers/grigorios-palamas.md` first to absorb
the voice. It is the gold standard:
- Polytonic with full breathings + accents (smooth/rough, acute/grave/circumflex, iota subscripts on dative singulars)
- Imperfect/aorist past tenses, not modern monotonic
- Short, dense sentences. Σημασία section restrained.
- Greek titles preserved verbatim ("Πηγὴ Γνώσεως", "Ἔκδοσις ἀκριβής",
  "Λόγοι ἀπολογητικοί").

The single OUTLIER is `ioannis-damaskinos.md` which had to be
**rewritten** from monotonic + bullet-list back into polytonic +
3-sections during the editorial pass — don't follow it.

## Workflow

1. **Confirm with user**: name, century, repose year, feast day (if any),
   key works.
2. **Choose slug**: lower-case, transliterated, hyphen-separated.
   Examples in repo: `vasileios-megas`, `grigorios-theologos`,
   `ioannis-chrysostomos`, `maximos-omologitis`, `nikodimos-agioritis`.
3. **Write** `src/content/fathers/<slug>.md` directly via the Write
   tool. Frontmatter exactly as above.
4. **Don't** add `iconUrl`, `iconAttribution`, `wikipediaTitle`, or
   `tropar`/`kontak`. Those are saint fields.
5. **Verify build**: `npm run build` from repo root.
6. **Don't commit** without user approval.

## Patristic-quote rule

Inside the body, when attributing a quote to another Father, follow the
"safe attributions" list from the `editorial-pass` skill. If you can't
verify the attribution from your training, paraphrase ("ὁ Χρυσόστομος
ἑρμηνεύει αὐτὸ ὡς…") rather than direct-quoting.

## Sort order on `/fathers/`

The listing page sorts by `century` ascending (chronological), NOT
alphabetically. This was a user directive after a brief alphabetical
trial. Don't change the sort.

## Existing batch (do NOT duplicate)

The session of 2026-05 seeded 31 fathers. Check `ls src/content/fathers/`
before adding to avoid duplication. If a Father already exists there,
edit the existing file rather than creating a new one.
