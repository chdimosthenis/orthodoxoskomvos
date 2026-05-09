// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import mdx from '@astrojs/mdx';

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
});
