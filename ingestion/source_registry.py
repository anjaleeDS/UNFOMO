"""
All sources in one place. Adding a new source = one entry here, nothing else changes.
"""

SOURCES = [
    # ── Tier 1: Official ──────────────────────────────────────────────────────
    {
        "name": "Anthropic Blog",
        "url": "https://www.anthropic.com/news/rss.xml",
        "type": "rss",
        "tier": 1,
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com/news/rss.xml",
        "type": "rss",
        "tier": 1,
    },
    {
        "name": "Google DeepMind Blog",
        "url": "https://deepmind.google/blog/rss.xml",
        "type": "rss",
        "tier": 1,
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "type": "rss",
        "tier": 1,
    },

    # ── Tier 2: Tech Press ────────────────────────────────────────────────────
    {
        "name": "AI Daily Brief",
        "url": "https://www.thedailyai.com/feed",
        "type": "rss",
        "tier": 2,
    },
    {
        "name": "The Verge - AI",
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "type": "rss",
        "tier": 2,
    },
    {
        "name": "TechCrunch - AI",
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "type": "rss",
        "tier": 2,
    },
    {
        "name": "a16z Blog",
        "url": "https://a16z.com/feed/",
        "type": "rss",
        "tier": 2,
    },
]
