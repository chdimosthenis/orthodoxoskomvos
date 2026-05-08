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
    /**
     * Year of repose, used to sort the saints listing chronologically.
     * NEGATIVE for BC dates (e.g. -850 for Prophet Elijah).
     */
    reposeYear: z.number().int().optional(),
    /**
     * Human-readable display label for the repose date — e.g. "9ος αἰὼν π.Χ.",
     * "†1809", "ΙΘ΄ αἰών". Falls back to reposeYear if absent.
     */
    reposeLabel: z.string().optional(),
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

const bible = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/bible' }),
  schema: z.object({
    /** Canonical Greek title — e.g. "Κατά Ματθαίον". */
    book: z.string(),
    /** English title for the EN site — e.g. "Gospel of Matthew". */
    bookEnglish: z.string().optional(),
    /** Position in NT canon (1=Matthew … 27=Revelation). */
    order: z.number().int().min(1).max(27),
    /** Subdivision of the NT for grouping in the index page. */
    division: z.enum(['gospel', 'acts', 'paul', 'general', 'revelation']),
    /** Number of chapters (computed at scrape time, used for the per-book TOC). */
    chapters: z.number().int().min(1).max(28).optional(),
    language: z.enum(['el', 'en']),
    sourceUrl: z.string().url().optional(),
    license: z.enum(['public-domain', 'CC-BY', 'CC-BY-SA', 'original']).optional(),
  }),
});

// Interpretive essays on New-Testament passages (parables, miracles,
// discourses, narrative, epistles). Lives at /bible/erminies/<slug>.
const erminies = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/erminies' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    author: z.string(),
    /** Biblical reference, e.g. "Λουκᾶς 10, 25-37". */
    reference: z.string(),
    /** Genre of the passage being interpreted. */
    topic: z.enum(['parable', 'miracle', 'discourse', 'narrative', 'epistle']),
    language: z.enum(['el', 'en']),
    license: z.enum(['public-domain', 'CC-BY', 'CC-BY-SA', 'original']).optional(),
    tags: z.array(z.string()).optional(),
    draft: z.boolean().optional().default(false),
  }),
});

export const collections = { articles, fathers, saints, liturgical, bible, erminies };
