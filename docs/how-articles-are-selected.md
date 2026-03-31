# How Articles Are Selected for the UNFOMO Daily Digest

This document explains the full pipeline — from where articles come from to what lands in your Telegram ping and what gets quietly dropped.

---

## Pipeline at a Glance

```
Sources (RSS + Gemini Search)
        |
        v
  Age filter (< 25 hours old)
        |
        v
  Deduplication (by URL)
        |
        v
  Engagement scoring (tier weight × recency)
        |
        v
  Claude summarization + significance scoring (1–5)
        |
        v
  Emergence detection (trending new terms)
        |
        v
  Telegram ping: top 5 articles (significance >= 3) + emerging signals
```

---

## 1. Sources

UNFOMO pulls from two distinct places every day.

### RSS Feeds (the reliable backbone)

Eight feeds are registered, split into two tiers:

| Tier | What it means | Sources |
|------|---------------|---------|
| Tier 1 — Official | Direct from the labs themselves | Anthropic Blog, OpenAI Blog, Google DeepMind Blog, Google AI Blog |
| Tier 2 — Tech Press | Journalists and investors covering AI | The Verge (AI), TechCrunch (AI), AI Daily Brief, a16z Blog |

Tier matters for scoring (see below). Tier 1 sources are treated as more authoritative than press coverage.

### Gemini Search Grounding (the catch-all net)

Once a day, Gemini 2.0 Flash is asked — with live web search enabled — to surface the most significant AI product announcements, model releases, and major updates from Anthropic, OpenAI, and Google in the last 24 hours. This catches things that don't appear in the eight RSS feeds: forum posts, leaked screenshots, social media announcements, and other sources that don't have a feed.

Articles discovered this way are labelled as Tier 3 (search-discovered) and scored accordingly.

---

## 2. Ingestion and Deduplication

When the daily job runs, the RSS fetcher polls all eight feeds and the Gemini fetcher fires its search query. For each article found:

- **Age check.** If the article has a publish date and it is more than 25 hours old, it is skipped. This keeps the database focused on genuinely recent news. (The 25-hour window, rather than 24, gives a small buffer for time-zone drift and slow feeds.)
- **Deduplication.** Articles are stored by URL. If the URL is already in the database, the article is silently skipped — no duplicate summaries, no double-counting.
- **Engagement score is calculated immediately** and stored alongside the article (see Section 3).

Gemini-discovered articles that have no URL get a synthetic placeholder URL based on their title, so they are still deduplicated correctly on repeat runs.

---

## 3. Engagement Scoring

Every article gets a single numeric engagement score at ingestion time. The formula has two components:

### Tier Weight

| Tier | Weight |
|------|--------|
| Tier 1 (official) | 1.0 |
| Tier 2 (tech press) | 0.7 |
| Tier 3 (search-discovered) | 0.5 |
| Unknown | 0.3 |

### Recency Decay

An article published right now scores a full recency bonus of 1.0. That bonus decays linearly to 0.0 over 48 hours. An article with no publish date gets 0 recency bonus.

### Combined Formula

```
engagement_score = tier_weight × (0.5 + 0.5 × recency_bonus)
```

The `0.5 + 0.5 × recency` term means even a brand-new article from an unknown source gets at least half its tier weight, and even a 48-hour-old article from Anthropic's blog still gets half of Tier 1's weight (0.5). Freshness matters, but source credibility is never zeroed out.

**Example scores:**

| Scenario | Score |
|----------|-------|
| Anthropic blog post, just published | 1.0 |
| Anthropic blog post, 24 hours old | 0.75 |
| Anthropic blog post, 48 hours old | 0.5 |
| TechCrunch article, just published | 0.7 |
| TechCrunch article, 24 hours old | 0.525 |
| Gemini-discovered item, just published | 0.5 |

---

## 4. Claude Summarization

After ingestion, every new article that hasn't been summarized yet is sent to Claude (claude-haiku by default — fast and cheap) one at a time, up to 50 per run.

Claude is given the article title, source name, tier label, and up to 4,000 characters of content. It returns structured JSON with six fields:

| Field | What it is |
|-------|------------|
| `summary` | 2–3 sentences describing what actually happened |
| `now_what` | 1 sentence on what this means for someone using AI tools today |
| `significance` | Integer 1–5 (see below) |
| `tags` | Up to 3 topic tags (e.g. "model release", "pricing", "safety") |
| `entities` | Named companies, products, and people mentioned |
| `ai_player` | Which lab this primarily concerns: anthropic, openai, google, or other |

Tags and entities are stored separately and used for trending detection and the `/player` command.

### Significance Scale

| Score | Meaning |
|-------|---------|
| 5 | Major industry shift — a new frontier model, a landmark policy change |
| 4 | Significant update — a notable product launch, a meaningful capability change |
| 3 | Worth knowing — useful but not paradigm-shifting |
| 2 | Minor update — incremental improvement, routine announcement |
| 1 | Noise — minor housekeeping, duplicate coverage |

Claude assigns this score based on the article content and the source tier context it is given. The tier label ("official source" vs. "tech press" vs. "search-discovered") is included in the prompt so Claude can calibrate appropriately.

---

## 5. Significance Scoring in Practice

The significance score is the primary gate for what reaches you. It is Claude's editorial judgment, not a formula. A Tier 1 article about a patch release might score 2. A Tier 3 search-discovered item about an unexpected capability breakthrough might score 5.

The engagement score (from Section 3) captures recency and source credibility. The significance score (from Section 4) captures actual news value. These are kept separate and used at different stages of the pipeline.

---

## 6. Emergence Detection

After summarization, a separate step scans the tag and entity database to spot terms that are appearing for the first time or accelerating rapidly — things like a new model name or a new concept that's being cited across multiple sources within 48 hours.

These "emerging signals" are surfaced in the daily ping as a separate section below the top articles. They are not ranked by significance; they are flagged because they are new.

---

## 7. The Daily Telegram Ping

The ping fires once per day after all of the above steps complete.

### What gets in

- **Top 5 articles** from the last 24 hours where `significance >= 3`, ordered by significance (highest first). If two articles tie on significance, the database retrieval order determines their rank.
- **Up to 3 emerging signals** — new terms with high recent mention counts.

### What gets filtered out

| Reason | What happens |
|--------|-------------|
| Significance score of 1 or 2 | Never shown in the daily ping |
| Article older than 25 hours | Never ingested, so never scored |
| Duplicate URL | Skipped at ingestion, not stored at all |
| Summarization failure | Article stays in the database unsummarized and is retried the next time `process_unsummarized` runs |
| Quiet day (nothing scores >= 3 and no emerging terms) | A single message is sent: "quiet day — no significant updates" |

### How each article appears in the ping

Each of the top 5 articles is formatted like this:

```
1. [significance emoji] [Article Title](url)
   [player emoji] `anthropic` · Source Name
   _2–3 sentence summary of what happened._
   → What this means for you today.
```

Significance emojis: red (5), orange (4), yellow (3), white (2), black (1).
Player emojis: purple = Anthropic, blue = OpenAI, green = Google, white = other.

---

## 8. On-Demand Commands

In addition to the daily ping, the Telegram bot responds to commands:

| Command | What it returns |
|---------|----------------|
| `/today` | Same as the daily ping, on demand |
| `/week` | The weekly narrative digest |
| `/emerging` | All currently tracked emerging signals with first-seen dates |
| `/player anthropic\|openai\|google\|other` | Top 5 articles for that lab in the last 7 days (significance >= 3) |
| `/cost` | API spend breakdown for the last 30 days |

---

## 9. Adding a New Source

The entire source list lives in one file: `ingestion/source_registry.py`. Adding a new RSS feed is one dictionary entry — name, URL, type, and tier. No other file needs to change. The fetcher, scorer, and summarizer all read from the registry automatically.
