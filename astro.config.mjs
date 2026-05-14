// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

import cloudflare from '@astrojs/cloudflare';

/**
 * Build a Map<route, ISODate> from content frontmatter at config-load time.
 * Used to emit per-entry <lastmod> in the sitemap rather than defaulting to
 * build time. Reads pubDate/updatedDate via lightweight regex (no YAML lib).
 */
function buildLastmodMap() {
  const map = new Map();
  /** @type {Array<{ dir: string, urlPrefix: string }>} */
  const collections = [
    { dir: 'articles', urlPrefix: '/articles/' },
    { dir: 'erminies', urlPrefix: '/bible/erminies/' },
  ];
  for (const { dir, urlPrefix } of collections) {
    const full = join('./src/content', dir);
    let files;
    try {
      files = readdirSync(full);
    } catch {
      continue;
    }
    for (const file of files) {
      if (!file.endsWith('.md') && !file.endsWith('.mdx')) continue;
      const slug = file.replace(/\.(md|mdx)$/, '');
      let raw;
      try {
        raw = readFileSync(join(full, file), 'utf8');
      } catch {
        continue;
      }
      const fmMatch = raw.match(/^---\r?\n([\s\S]*?)\r?\n---/);
      if (!fmMatch) continue;
      const fm = fmMatch[1];
      const updated = fm.match(/^updatedDate:\s*(.+)$/m)?.[1];
      const pub = fm.match(/^pubDate:\s*(.+)$/m)?.[1];
      const raw_date = (updated ?? pub)?.trim().replace(/^['"]|['"]$/g, '');
      if (!raw_date) continue;
      const d = new Date(raw_date);
      if (Number.isNaN(d.valueOf())) continue;
      map.set(`${urlPrefix}${slug}/`, d.toISOString());
    }
  }
  return map;
}

const LASTMOD = buildLastmodMap();

// https://astro.build/config
export default defineConfig({
  site: 'https://orthodoxoskomvos.gr',
  integrations: [
    sitemap({
      serialize(item) {
        try {
          const path = new URL(item.url).pathname;
          const lm = LASTMOD.get(path);
          if (lm) {
            return { ...item, lastmod: lm };
          }
        } catch {
          // fall through — emit item unchanged
        }
        return item;
      },
    }),
    mdx(),
  ],

  i18n: {
    defaultLocale: 'el',
    locales: ['el'],
    routing: {
      prefixDefaultLocale: false,
    },
  },

  adapter: cloudflare(),
});
