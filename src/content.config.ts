import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const feastDayPattern = /^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;

const articles = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/articles' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    author: z.string(),
    language: z.enum(['el', 'en']),
    sourceUrl: z.string().url().optional(),
    license: z.enum(['public-domain', 'CC-BY', 'CC-BY-SA', 'original']).optional(),
    tags: z.array(z.string()).optional(),
    draft: z.boolean().optional().default(false),
  }),
});

const fathers = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/fathers' }),
  schema: z.object({
    name: z.string(),
    fullName: z.string(),
    century: z.number().int(),
    feastDay: z.string().regex(feastDayPattern).optional(),
    summary: z.string(),
    language: z.enum(['el', 'en']),
    /** External source URL — set by bot-seeded entries. */
    sourceUrl: z.string().url().optional(),
    /** License of imported content. */
    license: z.enum(['public-domain', 'CC-BY', 'CC-BY-SA', 'original']).optional(),
    /** `true` for auto-seeded entries that need human review. */
    draft: z.boolean().optional().default(false),
  }),
});

const saints = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/saints' }),
  schema: z.object({
    name: z.string(),
    feastDay: z.string().regex(feastDayPattern),
    category: z.enum(['martyr', 'monastic', 'hierarch', 'apostle', 'prophet', 'other']),
    tropar: z.string().optional(),
    kontak: z.string().optional(),
    life: z.string(),
    language: z.enum(['el', 'en']),
    /** Wikimedia Commons URL of a representative icon. */
    iconUrl: z.string().url().optional(),
    /** Plain-text attribution e.g. "Wikimedia Commons · Public domain". */
    iconAttribution: z.string().optional(),
    /** Wikipedia article slug used by scripts/fetch_icon.py to refresh iconUrl. */
    wikipediaTitle: z.string().optional(),
    /** External source URL — set by daily_seed.py for auto-seeded entries. */
    sourceUrl: z.string().url().optional(),
    /** License of imported content (CC-BY-SA for Wikipedia/OrthodoxWiki). */
    license: z.enum(['public-domain', 'CC-BY', 'CC-BY-SA', 'original']).optional(),
    /**
     * `true` for auto-seeded entries that need human review before being
     * published. They get a static page at their direct URL but are excluded
     * from listings, the today widget, and the RSS feed.
     */
    draft: z.boolean().optional().default(false),
  }),
});

const liturgical = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/liturgical' }),
  schema: z.object({
    title: z.string(),
    type: z.enum([
      'ode', 'tropar', 'kontak', 'prayer', 'hymn',
      'apodeipno', 'paraklesis', 'chairetismoi', 'akathistos', 'theia-metalipsi', 'akolouthia',
    ]),
    source: z.string(),
    language: z.enum(['el', 'en']),
    /** Canonical source URL (e.g. glt.goarch.org/texts/Oro/Esperinos.html). */
    sourceUrl: z.string().url().optional(),
    /** License of the underlying text. Most akolouthies are public-domain. */
    license: z.enum(['public-domain', 'CC-BY', 'CC-BY-SA', 'original']).optional(),
  }),
});

export const collections = { articles, fathers, saints, liturgical };
