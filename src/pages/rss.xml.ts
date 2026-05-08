import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const all = await getCollection('articles');
  const items = all
    .filter(a => !a.data.draft)
    .sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf())
    .slice(0, 50)
    .map(a => {
      const linkPath = a.data.language === 'en'
        ? `/en/articles/${a.id}/`
        : `/articles/${a.id}/`;
      return {
        title: a.data.title,
        pubDate: a.data.pubDate,
        description: a.data.description,
        link: linkPath,
        author: a.data.author,
        categories: a.data.tags ?? [],
      };
    });

  return rss({
    title: 'Ορθόδοξος Κόμβος',
    description: 'Ψηφιακή συγκέντρωση πατερικών κειμένων, βίων αγίων, ακολουθιών και νέων τῆς Ὀρθοδοξίας.',
    site: context.site!,
    items,
    customData: '<language>el</language>',
  });
}
