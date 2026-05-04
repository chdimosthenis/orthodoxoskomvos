---
name: add-article
description: Add a new article (essay, patristic text, theological piece, devotional reflection) to the articles content collection. Trigger on "πρόσθεσε άρθρο", "γράψε ένα κείμενο για...", "δημοσίευσε αυτό το κείμενο", "add an article", or requests to publish a piece of long-form writing on the site.
---

# Add an article

Articles live in `src/content/articles/<slug>.md`, rendered at
`/articles/<slug>/`. Schema requires: title, description, pubDate, author,
language. Optional: sourceUrl, license, tags, draft.

## Two paths

**Path A — original content**: write directly. License = `original`.

**Path B — imported from a public source**: use one of the fetchers in
`scripts/`. License is set by the fetcher (CCEL → public-domain;
OrthodoxWiki → CC-BY-SA; Myriobiblos → public-domain pending manual
verification).

## Path A — original article

Pick a slug (transliterated, hyphenated, lowercase). Write the file:

```yaml
---
title: "Title in the article's language"
description: "1–2 sentence summary for cards and SEO meta description."
pubDate: 2026-MM-DD
author: "Author name (or 'Σύνταξη' for editorial pieces)"
language: el
license: original
tags: ["tag1", "tag2"]
---

Body in Markdown. Use:
- ## headings for sections
- > blockquotes (with `<blockquote lang="grc">` if quoting polytonic
  patristic Greek)
- Inline citations for any external work referenced
```

Ship:

```bash
npm run build
git add . && git commit -m "feat: add article <title>" && git push
```

## Path B — fetched

See the `fetch-content` skill. After the fetcher writes the file,
**always review the output** before committing — boilerplate from the
source page (navigation, footnote markers, "edit" links) sometimes leaks
through despite the cleaning step.

## Bilingual

The site has separate Greek and English views. To publish an article in
both languages, write two files with different `language` values. Use
either the same slug (filtered by language at render time) or
language-suffixed slugs:

- `proseyhi-iisou.md` (`language: el`)
- `proseyhi-iisou-en.md` (`language: en`)

Greek view: `/articles/proseyhi-iisou/`. English view: `/en/articles/proseyhi-iisou-en/`.

## Don'ts

- Don't omit `pubDate` — RSS feed and listings sort by it.
- Don't commit fetched articles without reviewing the body for source
  artifacts.
- Don't lose `sourceUrl` + `license` on imported content — both render
  in the attribution box at the bottom of the article page.
- Don't set `license: original` on a derivative translation. Use
  CC-BY-SA if from a CC-BY-SA source, or public-domain if from PD.
