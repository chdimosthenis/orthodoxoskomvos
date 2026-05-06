# Orthodox Logos — project context

Bilingual (Greek/English) Orthodox Christian content site. Live at
<https://orthodox-site.pages.dev>. Repo at
<https://github.com/chdimosthenis/orthodox-site>.

## Stack

- **Astro 6** static site generator → `dist/` (requires Node ≥22.12)
- **Cloudflare Pages** hosting (free tier, auto-deploys on push to `main`)
- **Pagefind** in-build search index (`<main data-pagefind-body>` markup)
- **Python 3.13** content pipeline (in `scripts/`, with venv)
- **GitHub Actions**: daily-saints (03:00 UTC), news (every 6h)

## Communication

The user (Dimos Chatzinikolaou, GitHub: `chdimosthenis`) is Greek-speaking.
**Respond in Greek by default.** Code, commit messages, and inline comments
in English.

## Folder map

```
.github/workflows/
  daily-saints.yml                 daily Wikipedia saint-seed cron (Node 22)
  news.yml                         every-6h RSS news aggregation cron
public/                            static assets (favicon, og-default.svg, robots.txt)
scripts/                           Python content pipeline
  venv/                            Python venv (gitignored; UTF-8 stdout fix in _common.py)
  _common.py                       write_content, slug, HTML cleaning, log helpers
  daily_seed.py                    auto-seed Wikipedia EO-liturgics (with non-saint blocklist)
  calendar_seed.py                 curated saint seeder with embedded data
  fetch_ccel.py                    public-domain English patristics from ccel.org
  fetch_myriobiblos.py             Greek texts from myriobiblos.gr (verify license)
  fetch_orthodoxwiki.py            OrthodoxWiki single page via MediaWiki API
  fetch_icon.py                    Wikipedia langlinks → Commons URL (with --audit mode)
  fetch_news.py                    RSS aggregator (4 Greek Orthodox sources)
  fetch_bible.py                   Patriarchal Text 1904 NT scraper (el.wikisource.org)
  seed_fathers.py                  30 curated Church Fathers from OrthodoxWiki
  seed_akolouthies.py              full akolouthies from glt.goarch.org (Oro/Euch/Jan/...)
  seed_theology.py                 18 theology articles from OrthodoxWiki
  seed_history.py                  22 history articles from OrthodoxWiki
  cleanup_akolouthies.py           idempotent post-processor for GOA-fetched .md
src/
  i18n/{ui.ts, utils.ts}           translations + locale helpers
  content/                         Markdown content (Astro Content Layer)
    articles/  fathers/  saints/  liturgical/  bible/
  data/news.json                   live news feed (overwritten by cron)
  layouts/BaseLayout.astro         <head> SEO, JSON-LD, hreflang, RSS link, pagefind body
  components/                      Header, Footer, ArticleCard, SaintCard, TodaysSaint,
                                   ShareButtons, NewsWidget
  pages/                           Greek (default locale, no URL prefix)
  pages/en/                        English (with /en/ prefix)
  content.config.ts                Zod schemas for 5 collections
  styles/global.css                GFS Didot + Inter, byzantine-purple headings, polytonic
astro.config.mjs                   site URL, integrations (sitemap, mdx), i18n config
.claude/skills/                    project-specific skill files (see "Available skills")
```

## Content collections

`src/content.config.ts` defines 5 collections via the modern Content Layer
API. All `language` fields are the enum `'el' | 'en'`. Greek is default;
English entries render under `/en/` URLs.

| Collection | Required | Optional |
|---|---|---|
| `articles` | title, description, pubDate, author, language | sourceUrl, license, tags, draft |
| `saints` | name, feastDay (MM-DD), category, life, language | tropar, kontak, iconUrl, iconAttribution, wikipediaTitle, sourceUrl, license, draft |
| `fathers` | name, fullName, century, summary, language | feastDay, sourceUrl, license, draft |
| `liturgical` | title, type, source, language | sourceUrl, license |
| `bible` | book, order (1-27), division, language | bookEnglish, chapters, sourceUrl, license |

Enums:
- `saints.category`: martyr / monastic / hierarch / apostole / prophet / other
- `liturgical.type`: ode / tropar / kontak / prayer / hymn / apodeipno /
  paraklesis / chairetismoi / akathistos / theia-metalipsi / akolouthia
- `bible.division`: gospel / acts / paul / general / revelation
- `license`: public-domain / CC-BY / CC-BY-SA / original

## Top-level routes

```
/             home (TodaysSaint, NewsWidget, latest articles)
/news         live aggregated news (30 items, refreshed every 6h)
/bible        New Testament index (5 sections, 27 books)
/bible/[slug] per-book with chapter TOC
/articles     all articles
/theology     theology hub (11 themed sections)
/history      history hub (5 sections)
/fathers      Church Fathers index
/saints       saints index
/akolouthies  full liturgical services
/proseuxitari individual prayers
/ymnoi        hymns / tropars / kontakia
/liturgical   catchall liturgical (kept for backwards-compat)
/about        about + contact
/search       Pagefind UI
```

Each Greek route has an `/en/` mirror.

## Conventions

- **Source attribution mandatory** for non-original content (`sourceUrl` + `license`)
- **Original content** tagged `license: original`
- **Polytonic Greek**: GOA pages use extended Greek block (U+1F77 etc.);
  regex matching needs `unicodedata.normalize("NFC", ...)`. See
  `cleanup_akolouthies.py`.
- **Auto-seeded entries** carry `draft: true` — hidden from listings,
  TodaysSaint widget, and RSS feeds until human review
- **Commit messages**: present-tense imperative; `chore(bot):` prefix for
  bot commits (orthodox-bot for saints, orthodox-news-bot for news)
- **Co-Authored-By**: include the Claude attribution line in commits
- **Windows UTF-8**: scripts that print Greek MUST `from _common import log`
  or use `PYTHONIOENCODING=utf-8` to avoid cp1253 crash

## Running locally

```bash
npm run dev                       # http://localhost:4321 (no Pagefind in dev)
npm run build                     # full prod build (Astro + Pagefind)

# Python scripts
cd scripts
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe <script>.py [args]
```

Python venv setup (one-time):

```bash
cd scripts
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Deploy

`git push` to `main` → Cloudflare Pages picks up the push and deploys in
~1-2 minutes. No manual step.

## Automated bots

Two GitHub Actions push to `main` autonomously. If your push is rejected,
see the **recover-from-bot-push** skill.

| Workflow | Schedule | Commits as | Touches |
|---|---|---|---|
| `daily-saints.yml` | 03:00 UTC daily | `orthodox-bot` | `src/content/saints/*.md` |
| `news.yml` | every 6h at :05 | `orthodox-news-bot` | `src/data/news.json` |
| `weekly-article.yml` | manual only (cron commented) | `orthodox-article-bot` | new branch `agentic-article/<date>` + PR (not `main`) |

The weekly-article workflow uses the Anthropic API. To activate:
1. Add `ANTHROPIC_API_KEY` to repo Secrets.
2. Run once via "Run workflow" to verify output quality.
3. Uncomment the schedule block in `.github/workflows/weekly-article.yml`.

Drafts go to a PR, NOT directly to `main` — review removes `draft: true`
and merges when the article is editorially ready.

Manual trigger any workflow:
<https://github.com/chdimosthenis/orthodox-site/actions>

## Sources used

| Source | License | Pipeline |
|---|---|---|
| `glt.goarch.org` (GOA Liturgical Texts) | public-domain canonical texts | `seed_akolouthies.py` + `cleanup_akolouthies.py` |
| `el.wikisource.org` | public domain | `fetch_bible.py` (Patriarchal Text 1904) |
| `orthodoxwiki.org` | CC-BY-SA | `fetch_orthodoxwiki.py`, `seed_fathers.py`, `seed_theology.py`, `seed_history.py`, `daily_seed.py` (via Wikipedia EO-liturgics) |
| Wikipedia + Commons | varies (mostly PD/CC) | `fetch_icon.py` |
| `pemptousia.com`, `vimaorthodoxias.gr`, `dogma.gr`, `orthodoxianewsagency.gr` | publisher rights / quoted | `fetch_news.py` (RSS, headline + excerpt + outbound link only) |
| `ccel.org`, `myriobiblos.gr` | varies | `fetch_ccel.py`, `fetch_myriobiblos.py` |

Confirmed-NOT-available (need different source): Holy Unction
(Εὐχέλαιον), Confession service text, Photian Schism dedicated page,
the literal `Pneumatology` / `Eschatology` / `Last Judgment` /
`Mystery (sacrament)` pages on OrthodoxWiki.

For Christology / Pneumatology / Eschatology coverage we substitute
adjacent OrthodoxWiki pages that DO exist (seeded via Phase K.2):
- Pneumatology cluster: Holy Spirit, Filioque
- Christology cluster:  Christology (stub), Incarnation, Theotokos, Resurrection
- Eschatology cluster:  Heaven, Death

## Available skills

For recurring operations, prefer the project skills under `.claude/skills/`:

| Skill | When to use |
|---|---|
| **add-saint** | write a new saint entry with original Greek prose |
| **review-drafts** | triage bot-seeded saint drafts (publish/improve/delete) |
| **fix-icon** | replace a saint's iconUrl; also `--audit` mode for bulk classification |
| **add-article** | publish a long-form article (original or imported) |
| **fetch-content** | drive single-page scrapers (CCEL / OrthodoxWiki / Myriobiblos / Commons) |
| **translate-entry** | create the English counterpart of a Greek saint/article |
| **seed-batch** | build a new themed batch seeder (`scripts/seed_X.py`) |
| **fetch-akolouthia** | add a new full liturgical service from glt.goarch.org |
| **classifier-workaround** | when long Greek text generation gets blocked — pivot to scraper |
| **recover-from-bot-push** | resolve `git push` rejection from bot collisions |
| **manage-news** | add RSS sources, tune news classifier, debug the feeder |
