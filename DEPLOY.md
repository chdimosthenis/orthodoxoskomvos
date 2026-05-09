# Deployment guide — orthodoxoskomvos.gr

This file documents the steps required to bring the site live on the
custom domain. The codebase is fully prepared — `astro.config.mjs`,
`robots.txt`, JSON-LD canonicals, RSS feed, sitemap, share-button URLs
and Open Graph metadata all use `https://orthodoxoskomvos.gr`.

## What's done in code

- `astro.config.mjs` — `site: 'https://orthodoxoskomvos.gr'`
- `public/robots.txt` — `Sitemap:` line points to the new domain
- All Python scripts — User-Agent strings updated
- `.github/workflows/news.yml` — bot commit email updated
- All meta tags (canonical, og:url, twitter:image, hreflang) — derive
  from the `site:` config, so they're correct automatically

## What you must do in Cloudflare

### 1. Connect the custom domain to Cloudflare Pages

Open the Pages dashboard:

```
https://dash.cloudflare.com → Workers & Pages → orthodox-site → Custom domains
```

Click **Set up a custom domain**, type `orthodoxoskomvos.gr`, then click
**Continue**. Cloudflare will tell you which DNS records to add at
your registrar.

Repeat for `www.orthodoxoskomvos.gr` if you also want the www variant
(recommended — Cloudflare auto-redirects one to the other once both
are added).

### 2. Add the DNS records at your .gr registrar

Two paths — pick whichever your registrar supports:

#### Path A — keep DNS at the .gr registrar (simplest)

At your registrar's DNS panel, add two CNAME records:

```
Name           Type    Value
@              CNAME   orthodox-site.pages.dev   (apex)
www            CNAME   orthodox-site.pages.dev
```

Some Greek registrars block CNAME at the apex (`@`). If so, use:

```
@              ALIAS   orthodox-site.pages.dev   (or A 192.0.2.1, will be replaced)
www            CNAME   orthodox-site.pages.dev
```

#### Path B — transfer DNS to Cloudflare (recommended, free)

1. At Cloudflare → **Add a site** → enter `orthodoxoskomvos.gr` → free plan.
2. Cloudflare will show you 2 nameservers (e.g. `ns1.cloudflare.com`).
3. At your .gr registrar, replace the existing nameservers with those.
4. Wait 1-2 hours for propagation.
5. Once Cloudflare detects the change, the Pages custom-domain step
   becomes 1-click.

Path B gives you Cloudflare's CDN + DDoS protection + analytics for free.

### 3. SSL certificate

Cloudflare auto-issues a Let's Encrypt certificate the moment DNS
resolves correctly. No action needed — typically takes 2-15 minutes.

### 4. Verify

Once propagation completes:

```
https://orthodoxoskomvos.gr      → site loads, valid SSL
https://www.orthodoxoskomvos.gr  → redirects to apex (or vice versa)
https://orthodox-site.pages.dev  → still works (Cloudflare keeps both)
```

The pages.dev URL stays live. Cloudflare doesn't auto-redirect from
.pages.dev → custom domain, but search engines will pick up the
canonical URL via the `<link rel="canonical">` meta we already emit.

## Post-launch SEO

Once the domain resolves and the SSL cert is issued, do these once:

### Google Search Console
1. https://search.google.com/search-console → Add property
2. Pick **URL prefix** → `https://orthodoxoskomvos.gr`
3. Verify via Cloudflare DNS TXT record (1-click if DNS is on Cloudflare)
4. Submit sitemap: `https://orthodoxoskomvos.gr/sitemap-index.xml`

### Bing Webmaster Tools
1. https://www.bing.com/webmasters → Add site → same flow as Google.
2. Bing also feeds DuckDuckGo, Ecosia, and others.

### Test rich-snippet eligibility
Use Google's Rich Results Test:
- https://search.google.com/test/rich-results?url=https://orthodoxoskomvos.gr/saints/agios-nektarios-pentapoleos
- Should show "Person" schema (for saints/fathers), "Article" (for
  articles/erminies), "Book" (for bible/), "WebSite" + SearchAction
  (homepage).

## Cost summary

| Item | Annual cost |
|---|---|
| Domain `orthodoxoskomvos.gr` (already paid) | ~€18-25 |
| Cloudflare Pages | **€0** (free tier, unlimited requests/bandwidth) |
| Cloudflare DNS | **€0** (free) |
| SSL certificate | **€0** (Let's Encrypt via Cloudflare) |
| **Total ongoing** | **€0/year + domain renewal** |

No other monthly costs. The site is fully self-contained.

## Optional next steps

- **Email forwarding** — if you want `info@orthodoxoskomvos.gr` to forward
  to your Gmail, set it up at your .gr registrar's email-forwarding
  panel (most Greek registrars include this for free).
- **Analytics** — Cloudflare Web Analytics is privacy-friendly and free
  (no cookies). Pages dashboard → Analytics → enable.
- **Manual news refresh** — the news cron runs every 6h via
  `.github/workflows/news.yml`. To trigger manually: GitHub → Actions →
  News Aggregator → Run workflow.
