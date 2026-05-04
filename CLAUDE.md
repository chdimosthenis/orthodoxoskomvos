# Orthodox Logos — project context

Bilingual (Greek/English) Orthodox Christian content site. Live at
<https://orthodox-site.pages.dev>. Repo at
<https://github.com/chdimosthenis/orthodox-site>.

## Stack

- **Astro 6** static site generator → `dist/`
- **Cloudflare Pages** hosting (free tier, auto-deploys on push to `main`)
- **Pagefind** in-build search index
- **Python 3.13** content pipeline (in `scripts/`, with venv)
- **GitHub Actions** daily auto-seed at 03:00 UTC

## Communication

The user (Dimos Chatzinikolaou, GitHub: `chdimosthenis`) is Greek-speaking.
**Respond in Greek by default.** Code, commit messages, and inline comments
in English.

## Folder map

```
.github/workflows/daily-saints.yml  daily auto-seed cron
public/                             static assets (favicon, og-default.svg, robots.txt)
scripts/                            Python content pipeline
  venv/                             Python venv (gitignored)
  _common.py                        write_content, slug, HTML cleaning helpers
  fetch_ccel.py                     public-domain English patristics from ccel.org
  fetch_myriobiblos.py              Greek texts from myriobiblos.gr (verify license)
  fetch_orthodoxwiki.py             OrthodoxWiki via MediaWiki API (CC-BY-SA)
  fetch_icon.py                     Wikipedia langlinks → Commons icon URL
  daily_seed.py                     auto-seed from Wikipedia EO-liturgics calendar
  calendar_seed.py                  curated saint seeder with embedded data
src/
  i18n/{ui.ts, utils.ts}            translations + locale helpers
  content/                          Markdown content (Astro Content Layer API)
    articles/  fathers/  saints/  liturgical/
  layouts/BaseLayout.astro          head SEO, JSON-LD WebSite, hreflang, RSS link
  components/                       Header, Footer, ArticleCard, SaintCard, TodaysSaint
  pages/                            Greek (default locale, no URL prefix)
  pages/en/                         English (with /en/ prefix)
  content.config.ts                 Zod schemas for the four collections
  styles/global.css                 GFS Didot + Inter, light/dark, polytonic support
astro.config.mjs                    site URL, integrations (sitemap, mdx), i18n
```

## Content collections

`src/content.config.ts` defines four collections via the modern Content Layer
API. All `language` fields are the enum `'el' | 'en'`. Greek is default;
English entries render under `/en/` URLs.

| Collection | Required | Optional |
|---|---|---|
| `articles` | title, description, pubDate, author, language | sourceUrl, license, tags, draft |
| `saints` | name, feastDay (MM-DD), category, life, language | tropar, kontak, iconUrl, iconAttribution, wikipediaTitle, sourceUrl, license, draft |
| `fathers` | name, fullName, century, summary, language | feastDay |
| `liturgical` | title, type (ode/tropar/kontak/prayer/hymn), source, language | — |

`category` enum for saints: `martyr | monastic | hierarch | apostle | prophet | other`.
`license` enum: `public-domain | CC-BY | CC-BY-SA | original`.

## Conventions

- **Source attribution mandatory** for non-original content (`sourceUrl` + `license`)
- **Original content** tagged `license: original`
- **Polytonic Greek preserved as-is** in UTF-8 (no Unicode normalisation)
- **Auto-seeded entries** carry `draft: true` and are hidden from listings,
  the today widget, and RSS feeds until reviewed
- **Commit messages** present-tense imperative; `chore(bot):` prefix for
  the orthodox-bot's automated commits

## Running locally

```bash
# Dev server (no Pagefind index in dev mode)
npm run dev                       # http://localhost:4321

# Full production build (Astro + Pagefind crawl of dist/)
npm run build

# Python scripts (venv must exist; see Setup below)
cd scripts
./venv/Scripts/python.exe <script>.py [args]
```

Python venv setup (one-time, after fresh clone):

```bash
cd scripts
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Deploy

`git push` to `main` → Cloudflare Pages picks up the push and deploys in
~2 minutes. No manual step.

## Daily auto-seed (GitHub Actions)

`.github/workflows/daily-saints.yml` runs at 03:00 UTC daily and on manual
dispatch. It fetches Wikipedia "Eastern Orthodox liturgics" pages for the
next two days, parses the saint sections, writes draft stubs to
`src/content/saints/`, fetches Wikimedia icons for them, verifies the build,
then commits as `orthodox-bot` and pushes.

Manual trigger: <https://github.com/chdimosthenis/orthodox-site/actions> →
"Daily Saints Seed" → "Run workflow".

## Available skills

For recurring operations, prefer the project skills under `.claude/skills/`:

- **add-saint** — write a new saint entry with original Greek prose
- **review-drafts** — triage bot-seeded draft entries (publish/improve/delete)
- **fix-icon** — replace a saint's iconUrl when the auto-pick is wrong
- **add-article** — publish a long-form article (original or imported)
- **fetch-content** — drive the CCEL / OrthodoxWiki / Myriobiblos / Commons scrapers
- **translate-entry** — create an English counterpart of a Greek saint/article
