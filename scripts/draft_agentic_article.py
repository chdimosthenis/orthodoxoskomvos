"""Draft a weekly Greek-language article via the Anthropic API.

Reads:
  - src/data/news.json                 (top 10 recent items)
  - src/content/saints/*.md            (entries whose feastDay matches today)
  - .claude/references/site-voice.md   (optional; injected into system prompt
                                        if present — gives the model the
                                        site's tone/conventions)

Writes:
  - src/content/articles/<slug>.md     with draft: true
                                        (so the human reviews before publish)

Convention: this is the "agentic article" pipeline. Every weekly run produces
ONE draft article connected to the current week's saints and news. The user
reviews via the review-drafts pattern before promoting to published.

Usage:
    python draft_agentic_article.py                    # write a draft
    python draft_agentic_article.py --dry-run          # print only
    python draft_agentic_article.py --model sonnet     # default
    python draft_agentic_article.py --model opus       # higher quality, costlier

Env: ANTHROPIC_API_KEY (required).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

from anthropic import Anthropic

from _common import log, make_slug, write_content

ROOT = Path(__file__).resolve().parent.parent
NEWS_FILE = ROOT / "src" / "data" / "news.json"
SAINTS_DIR = ROOT / "src" / "content" / "saints"
VOICE_FILE = ROOT / ".claude" / "references" / "site-voice.md"

MODELS = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7",
    "haiku": "claude-haiku-4-5-20251001",
}

# Static — gets prompt-cached. Edit this to tune the agentic article voice.
SYSTEM_PROMPT_BASE = """You are drafting a weekly editorial article for a
Greek-speaking Orthodox Christian content site (orthodox-site.pages.dev).
The audience is educated Greek Orthodox lay readers familiar with the
liturgical year and basic theology.

VOICE AND STYLE
- Polytonic Greek throughout. Use the extended Greek block (ᾳ ῇ ῷ ἁ ἐ etc.).
- Tone: thoughtful, devotional, never sentimental or sermonising.
- 600–1000 words. One clear thesis per article. No bullet lists.
- Section headings (##) only when the article has a natural multi-part shape.

CONTENT RULES
- Anchor the article in *concrete particulars*: a specific saint, a specific
  Gospel pericope, a specific patristic line, a specific current event.
- Do NOT fabricate quotations, dates, or biographical details. If you do not
  know a fact, write around it instead of inventing.
- When you reference a Father, name the work or letter; do not invent
  citation strings.
- Do NOT moralise or pontificate. The reader is a sibling, not a catechumen.
- It is acceptable — and good — to engage current events theologically. But
  the article must be readable in a year, not just this week. Use the news
  as occasion, not subject.

OUTPUT FORMAT
Return ONLY a single JSON object, no preamble, no code fences:
  {
    "title": "Greek title, sentence case",
    "description": "One-sentence Greek summary for SEO and listings.",
    "tags": ["tag1", "tag2"],   // 2-4 tags, lowercase, ASCII only
    "body": "Article body in Markdown..."
  }
"""


def load_today_saints() -> list[dict]:
    today = date.today().strftime("%m-%d")
    out: list[dict] = []
    for path in sorted(SAINTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if f"feastDay: {today}" not in text:
            continue
        m = re.search(r"^name:\s*(.+)$", text, re.MULTILINE)
        name = m.group(1).strip().strip('"').strip("'") if m else path.stem
        m = re.search(r"^life:\s*(.+)$", text, re.MULTILINE)
        life = m.group(1).strip().strip('"').strip("'") if m else ""
        out.append({"slug": path.stem, "name": name, "life": life})
    return out


def load_recent_news(limit: int = 10) -> list[dict]:
    if not NEWS_FILE.is_file():
        return []
    data = json.loads(NEWS_FILE.read_text(encoding="utf-8"))
    items = data.get("items", [])[:limit]
    return [
        {
            "title": i.get("title", ""),
            "source": i.get("source", ""),
            "excerpt": i.get("excerpt", "")[:300],
            "url": i.get("url", ""),
        }
        for i in items
    ]


def build_user_message(saints: list[dict], news: list[dict]) -> str:
    parts = [f"Σήμερα: {date.today().isoformat()}", ""]
    if saints:
        parts.append(f"Ἑορτάζοντες ἅγιοι σήμερα ({len(saints)}):")
        for s in saints:
            parts.append(f"- {s['name']}: {s['life']}")
        parts.append("")
    if news:
        parts.append("Πρόσφατα νέα ἀπὸ ὀρθόδοξες πηγές (μὴ ἀντιγράψεις, χρησιμοποίησε ὡς ἀφορμή):")
        for n in news:
            parts.append(f"- [{n['source']}] {n['title']}")
            if n["excerpt"]:
                parts.append(f"  {n['excerpt'][:200]}")
        parts.append("")
    parts.append("Δράψε ἕνα ἄρθρο 600–1000 λέξεων στὰ ἑλληνικὰ μὲ τὶς προδιαγραφὲς τοῦ system prompt.")
    return "\n".join(parts)


def call_claude(model: str, system: list, user_msg: str) -> str:
    client = Anthropic()  # picks up ANTHROPIC_API_KEY from env
    resp = client.messages.create(
        model=model,
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user_msg}],
    )
    return resp.content[0].text


def parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=list(MODELS), default="sonnet")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        log("ANTHROPIC_API_KEY not set", level="error")
        return 2

    saints = load_today_saints()
    news = load_recent_news(limit=10)
    log(f"context: {len(saints)} saints today, {len(news)} news items")

    system_text = SYSTEM_PROMPT_BASE
    if VOICE_FILE.is_file():
        system_text += "\n\n## SITE VOICE NOTES\n\n" + VOICE_FILE.read_text(encoding="utf-8")

    # Cache the (large, stable) system prompt.
    system = [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]

    user_msg = build_user_message(saints, news)
    log(f"calling {MODELS[args.model]}")
    raw = call_claude(MODELS[args.model], system, user_msg)

    try:
        obj = parse_json_response(raw)
    except json.JSONDecodeError as e:
        log(f"could not parse JSON from model: {e}", level="error")
        log(f"raw response:\n{raw}")
        return 3

    title = obj["title"].strip()
    description = obj["description"].strip()
    tags = obj.get("tags", [])
    body = obj["body"].strip()
    slug = make_slug(title)

    if args.dry_run:
        log(f"DRY RUN — would write articles/{slug}.md")
        log(f"  title: {title}")
        log(f"  description: {description}")
        log(f"  tags: {tags}")
        log(f"  body: {len(body):,} chars")
        return 0

    fm = {
        "title": title,
        "description": description,
        "pubDate": date.today().isoformat(),
        "author": "Σύνταξη (AI-assisted)",
        "language": "el",
        "license": "original",
        "tags": tags,
        "draft": True,  # human review required before publish
    }
    target = write_content("articles", slug, fm, body, force=False)
    log(f"wrote {target} ({len(body):,} chars) — review and remove draft: true to publish",
        level="ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
