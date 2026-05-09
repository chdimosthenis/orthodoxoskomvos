---
name: orthodoxoskomvos-orientation
description: Master orientation for the Ὀρθόδοξος Κόμβος site (orthodoxoskomvos.gr). Encodes repo location, content-collection map, voice/register conventions per type, deployment target (Cloudflare Pages), build/commit cadence, and which sub-skill to call for each kind of operation. Use as the FIRST skill in any session that mentions the orthodox site, ορθοδοξία content, polytonic Greek liturgical text, or any path under C:\Users\dimos\Documents\orthodox-site. Routes to add-saint / add-father / add-article / add-erminia / fix-icon / editorial-pass / subagent-permissions / fewer-permission-prompts / etc.
---

# Ὀρθόδοξος Κόμβος — operating context

## Repo

```
C:\Users\dimos\Documents\orthodox-site
```

Production: `https://orthodoxoskomvos.gr` (Cloudflare Pages,
auto-deploys from `main`). Pre-domain testbed:
`https://orthodox-site.pages.dev`.

GitHub: `chdimosthenis/orthodox-site` (private? — check).

## Stack

- Astro 6 static site generator
- TypeScript content collections with Zod schema (`src/content.config.ts`)
- Pagefind for full-text search
- Cloudflare Pages free tier (no API costs, no monthly fees)
- News auto-fetch every 6h via `.github/workflows/news.yml`
  (RSS only — NO Anthropic API)

## Content collections — the canonical map

| Collection | Path | Register | Voice exemplar |
|---|---|---|---|
| `articles`   | `src/content/articles/`   | Modern Greek **monotonic** | `articles/proseyhi-iisou.md` |
| `erminies`   | `src/content/erminies/`   | Modern Greek **monotonic** | `articles/proseyhi-iisou.md` |
| `fathers`    | `src/content/fathers/`    | **Polytonic** Greek strictly | `fathers/grigorios-palamas.md` |
| `saints`     | `src/content/saints/`     | Polytonic frontmatter, body either way | hand-curated batch |
| `liturgical` | `src/content/liturgical/` | Polytonic for prayers; intros either | `liturgical/symvolon-pisteos.md` |
| `bible`      | `src/content/bible/`      | Polytonic NT (Patriarchal Text 1904) | `bible/kata-matthaion.md` |

## Routing

```
/                                home (TodaysSaint widget + NewsWidget + recent articles)
/news                            latest news snapshot (auto-archived per day)
/news/archive                    list of all dated news archives
/news/<YYYY-MM-DD>               specific day's snapshot
/bible                           hub: 2 cards (Πλῆρες Κείμενο + Ἑρμηνεῖες)
/bible/keimeno                   27 NT books listing
/bible/<book>                    one NT book
/bible/erminies                  ermineia listing
/bible/erminies/<slug>           one ermineia
/didaskalia                      hub: Ἄρθρα + Θεολογία + Ἱστορία
/articles                        flat articles index
/theology                        + /theology/<cluster>
/history                         + /history/<cluster>
/prosopa                         hub: Ἅγιοι + Πατέρες
/saints                          chronological by reposeYear
/fathers                         chronological by century
/latreia                         hub: Ἀκολουθίες + Ἑορτολόγιον + Μοναστήρια + Ναὸς&Λατρεία + Προσευχητάριον + Ὕμνοι
/akolouthies, /ymnoi, /proseuxitari    (separate listings)
/eortologio                      static calendar of feasts
/monasteries                     static index of major monasteries
/naos-kai-latreia                + 3 sub-sections
/search                          Pagefind UI (noindex)
/about                           about page with AI-disclaimer + non-profit mission
```

## Build + commit cadence

```
npm run build          # always verify before commit
git add <specific-paths>   # NOT git add -A unless you've reviewed
git commit -m "<scope>: <imperative>

<body — list actual fixes, not prose>"
git pull --rebase origin main      # ALWAYS — bot pushes daily
git push
```

## Bot collisions

`.github/workflows/news.yml` runs every 6h and bot-pushes to `main`.
Always `git pull --rebase` before `git push`. The `recover-from-bot-push`
skill encodes the recovery if you forget.

## Sub-agent unlock

Sub-agents can't write to the project unless `.claude/settings.json`
explicitly allows it. The unlock is committed to this repo at
`.claude/settings.json`. If a fresh sub-agent reports "Write denied",
trigger the `subagent-permissions` skill.

## Routing table — which skill for which task

| User says... | Skill |
|---|---|
| "πρόσθεσε τὸν ἅγιο/ὁσίαν..." | `add-saint` |
| "πρόσθεσε Πατέρα τῆς Ἐκκλησίας" | `add-father` |
| "γράψε ἑρμηνεία τῆς παραβολῆς..." | `add-erminia` |
| "γράψε ἄρθρο γιὰ τὴ νοερὰ προσευχή..." | `add-article` |
| "ἐπιμελητικὸ πέρασμα στοὺς Πατέρες" | `editorial-pass` |
| "διόρθωσε τὶς εἰκόνες ποὺ δὲν φορτώνουν" | `fix-icon` |
| "πάρε νέες προσευχὲς ἀπὸ glt.goarch.org" | `fetch-akolouthia` |
| "ἀπόψε push δὲν περνᾶ — bot conflict" | `recover-from-bot-push` |
| "agents can't write" / "Write denied" | `subagent-permissions` |
| "διπλὰ permission prompts ἐνοχλοῦν" | `fewer-permission-prompts` |

## Domain + SEO state

The site is fully prepared for `orthodoxoskomvos.gr`. All hardcoded
URLs (astro.config, robots.txt, JSON-LD, scripts, GH Actions) point
to the production domain. SEO build-ins: Article + Person + Book
JSON-LD, BreadcrumbList on hub pages, sitemap auto-generated, robots
allows GPTBot/Google-Extended/ClaudeBot, og:image PNG (1200x630),
canonical URLs everywhere. See `DEPLOY.md` and `SEO.md` for the
post-launch checklist (Google Search Console, Bing Webmaster, etc.).

## Cost

€0/year operating cost (Cloudflare free tier). Domain renewal ~€18-25.
No Anthropic API costs — all content is hand-authored or RSS-aggregated.
