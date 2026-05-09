---
name: add-erminia
description: Add a New-Testament-passage interpretation article to src/content/erminies/. Distinct from add-article — erminies have their own content collection, schema (reference + topic fields), routing under /bible/erminies/<slug>, and section conventions (Τὸ νόημα + Πατερικὲς προσεγγίσεις). Triggers when the user asks for an "ἑρμηνεία" of a parable, miracle, discourse, narrative, or epistolary passage — e.g. "γράψε ἑρμηνεία γιὰ τὴν παραβολὴ τοῦ Σπορέως", "add an interpretation of the Beatitudes", "ἑρμήνευσε τὸ Ἰω. 17".
---

# Add a Bible interpretation (ermineia)

Erminies live at `src/content/erminies/<slug>.md` and render at
`/bible/erminies/<slug>/`. They are conceptually distinct from
`/articles/` — they're tied to a specific scripture passage and grouped
by `topic` (parable / miracle / discourse / narrative / epistle).

## Schema (`src/content.config.ts → erminies`)

```yaml
---
title: "Polytonic Greek title — e.g. Ἡ Παραβολὴ τοῦ Σπορέως"
description: "1 sentence, 100-160 chars (for SERP + share previews)"
pubDate: 2026-MM-DD
author: "Σύνταξη"
reference: "Λουκᾶς 10, 25-37"   # canonical biblical citation
topic: parable                  # parable | miracle | discourse | narrative | epistle
language: el
license: original
tags: ["bible", "ermineia"]
draft: false
---
```

## Voice + structure

**Modern Greek monotonic** prose (NOT polytonic — that's for fathers
and saints). Read `src/content/articles/proseyhi-iisou.md` once for
voice.

Body: 300-450 words, three sections in this order:

```markdown
[Opening paragraph: setting / context of the passage. ~50-80 words.]

## Τὸ νόημα

[Exegesis of the central message — what the passage teaches about God,
salvation, the human condition, virtue, the kingdom. ~120-180 words.]

## Πατερικὲς προσεγγίσεις

[1-2 patristic readings. Paraphrase from your training only when you
can confidently attribute. Direct-quote only with high confidence.
Safe attributions: Χρυσόστομος on Matthew/John homilies; Νύσσης on
Beatitudes; Μάξιμος Ὁμολογητής on dogmatic; Συμεὼν Νέος Θεολόγος on
inner life; Παλαμᾶς on Tabor light / energies. ~80-120 words.]

## Ἐφαρμογή        (optional)

[Modern relevance — how this lives in the practising Christian's life.
1 paragraph, ~50-80 words.]
```

## Topic decision tree

| Passage type | `topic` value |
|---|---|
| Mt 13 parables, Lk 15-18 parables | `parable` |
| Walking on water, healing miracles, Cana, raising of Lazarus | `miracle` |
| Sermon on the Mount, "I am the vine", Last Supper, Final Judgment | `discourse` |
| Transfiguration, Baptism of the Lord, Pentecost descent | `narrative` |
| 1 Cor 13, Phil 2:5-11, Rom 8, Heb 11 | `epistle` |

## Existing slate (do NOT duplicate)

The session of 2026-05 authored 30 erminies. Before adding, run:

```
ls src/content/erminies/
```

The 30 covered: 12 parables, 6 miracles, 6 discourses, 3 narratives,
3 epistles. If the passage is already covered, the user probably wants
an edit/expansion of the existing entry, not a new one.

## Listing page

`/bible/erminies/index.astro` already groups entries by `topic` and
sorts by `pubDate` desc within each group. New entries appear
automatically — no listing-page edit required.

## Don't

- Don't put erminies in `src/content/articles/`. They have their own
  collection so they DON'T appear in the flat `/articles` index (a
  filter would be needed otherwise).
- Don't omit `reference:` — it renders as a chip on the article header.
- Don't direct-quote scripture from a copyrighted modern translation;
  cite by reference and paraphrase, or use the public-domain
  Patriarchikon Keimenon (1904) which is what `/bible/keimeno` ships.
