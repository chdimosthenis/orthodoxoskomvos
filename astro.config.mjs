// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

import cloudflare from '@astrojs/cloudflare';

// https://astro.build/config
export default defineConfig({
  site: 'https://orthodoxoskomvos.gr',
  integrations: [sitemap(), mdx()],

  i18n: {
    defaultLocale: 'el',
    locales: ['el'],
    routing: {
      prefixDefaultLocale: false,
    },
  },

  adapter: cloudflare(),
});