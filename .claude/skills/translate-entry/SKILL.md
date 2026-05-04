---
name: translate-entry
description: Create an English version of an existing Greek saint or article (or the reverse), keeping schema fields aligned. Trigger on "μετάφρασε τον <saint> στα αγγλικά", "translate <article> to English", "create the EN version of...", "βγάλε αγγλική εκδοχή του...", or bilingual content management requests.
---

# Translate a content entry

Each language has its own file. Greek and English entries describing the
same subject live as separate `.md` files, often sharing a slug.

## Saints

Source: `src/content/saints/<slug>.md` with `language: el`.

To create the English counterpart:

1. **Copy the file**. The slug can stay the same — Astro filters by
   `language` in the dynamic route's `getStaticPaths`, so both Greek and
   English entries with the same slug render at `/saints/<slug>/` and
   `/en/saints/<slug>/` respectively. Alternatively, give the English
   version a translated slug — both work.
2. **Translate `name`** to its standard English form. "Άγιος Νικόλαος
   Μύρων της Λυκίας" → "Saint Nicholas of Myra". Use the established
   English form (consult Wikipedia/OrthodoxWiki) — don't invent.
3. **Translate `life`** to a one-sentence English summary.
4. **Translate the body**. Preserve direct Greek quotations from
   traditional troparia / kontakia inside `<blockquote lang="grc">`
   tags — these shouldn't be translated.
5. **Keep the same**: `feastDay`, `category`, `wikipediaTitle`,
   `iconUrl`, `iconAttribution`. The Wikimedia Commons file is identical
   regardless of UI language.
6. **Switch** `language: el` → `language: en`.
7. Optionally translate `tropar` / `kontak` to English — but only with
   a known public-domain English translation, cited. If unsure, leave
   the Greek; the English page renders Greek hymnography fine and the
   `lang="grc"` tag handles it for screen readers.

## Articles

Identical pattern. Write a separate file with `language: en`. Translate
`title`, `description`, body. Keep `pubDate`, `author`, `tags`.

If translating from CCEL/OrthodoxWiki content (CC-BY-SA), preserve
`sourceUrl` and the appropriate `license`. If translating original Greek
content into English, the English version is also `license: original`.

## Verification

```bash
npm run build
```

The English version should now appear at `/en/saints/<slug>/`. Confirm
both versions resolve and the language switcher in the header toggles
between them correctly.

## Commit

```bash
git add . && git commit -m "feat(i18n): English version of <name>" && git push
```

## Don'ts

- Don't translate names of well-known saints idiosyncratically; use the
  established English form (consult Wikipedia/OrthodoxWiki).
- Don't translate centuries-old liturgical hymnography (`tropar`,
  `kontak`) unless using a known public-domain English translation.
  Modern published translations are typically copyrighted.
- Don't fork the icon — keep `iconUrl` identical across language
  versions. The Commons file is the same.
- Don't translate book titles or other proper nouns that have a
  conventional English form (e.g. "Φιλοκαλία" → "Philokalia", not
  "Love of the Beautiful").
