# UNFOMO — Handoff

**Date**: April 6, 2026
**Status**: MVP running, summarizer temporarily on OpenAI while Claude tokens refill

---

## What's Done

| Area | Status | Notes |
|------|--------|-------|
| Project structure + GitHub | ✅ | `github.com/anjaleeDS/UNFOMO` |
| Postgres on Railway | ✅ | Schema initialized, connected locally via public URL |
| RSS ingestion | ✅ | 8 sources across 2 tiers, deduplication working |
| Summarizer (OpenAI) | ✅ | GPT-4o-mini — temporary swap from Claude Haiku while tokens refill |
| Web dashboard | ✅ | Dark theme, 5 tabs, serving at `localhost:8080` |
| Telegram bot | ✅ | `@unfomo_bot` — daily ping + `/today`, `/week`, `/player`, `/emerging`, `/cost` |
| Gemini Search grounding | ✅ | `gemini-2.5-flash`, billing enabled on Google Cloud |
| Emergence detector | ✅ | Flags new terms appearing 3+ times in 48h |
| Weekly digest builder | ⏸️ | Claude Sonnet — blocked until Claude API tokens refill |
| Charts | ✅ | Topic trends + player velocity (Plotly → PNG for Telegram) |
| Podcast TTS | ✅ | Google Cloud TTS (Journey voices) — needs `GOOGLE_CLOUD_TTS_KEY` |
| Schedulers | ✅ | Daily 7am UTC, Weekly Sunday 8am UTC (APScheduler) |
| Cleanup + rename pass | ✅ | Done in previous session |

---

## What Changed Today (April 6)

1. **Summarizer swapped from Claude → OpenAI GPT-4o-mini**
   - `processing/summarizer.py` now uses `openai` API instead of `anthropic`
   - `processing/costs.py` updated with gpt-4o-mini pricing
   - `config.py` added `OPENAI_API_KEY`, made `ANTHROPIC_API_KEY` optional
   - `requirements.txt` added `openai>=1.0.0`
   - Same prompt, same JSON output — drop-in swap
   - **To switch back to Claude**: revert `processing/summarizer.py` to use anthropic SDK

2. **Renamed OpenClaw test → `scripts/test_emergence_backfill.py`**
   - Cleaned up all "OpenClaw" references from docs

---

## Current Provider Map

```
Search grounding  → Gemini 2.5 Flash  ✅
Article summarizer → OpenAI GPT-4o-mini ✅ (temporary)
Weekly digest     → Claude Sonnet      ⏸️ (waiting for tokens)
Podcast TTS       → Google Cloud TTS   ⏸️ (needs key)
```

---

## What's Left To Do

| Task | Priority | Notes |
|------|----------|-------|
| **Deploy to Railway** | High | Web server + scheduler + bot as Railway services. Add `.env` keys to Railway variables |
| **Run first full daily job** | High | `python3 -m scheduler.daily_job` — end-to-end test with OpenAI summarizer |
| **Swap summarizer back to Claude** | Medium | When API tokens refill — revert `processing/summarizer.py` |
| **Gmail newsletter ingestion** | Medium | New idea: read AI newsletters from Gmail as a new trusted source tier |
| **Telegram `/today` command test** | Medium | Confirm polling responds to commands |
| **Weekly digest dry run** | Medium | Blocked until Claude tokens refill |
| **Emergence backfill test** | Medium | `scripts/test_emergence_backfill.py` — validate detector with historical data |
| **D3 upgrade for charts** | Low | Replace Plotly with D3 on web dashboard |
| **Trends + Players tabs** | Low | Need more ingestion data first |

---

## How to Pick Up

```bash
cd "/Users/anjalee/Library/Mobile Documents/com~apple~CloudDocs/Coding/UNFOMO"

# Start dashboard
python3 -m web.server

# Run daily job manually
python3 -m scheduler.daily_job

# Start Telegram bot polling
python3 -m bot.telegram

# Run weekly job manually (blocked — needs Claude tokens)
python3 -m scheduler.weekly_job
```

---

## Credentials

All in `.env` (never committed).

| Key | Status |
|-----|--------|
| `ANTHROPIC_API_KEY` | ⏸️ Tokens depleted — optional for now |
| `OPENAI_API_KEY` | ✅ Working (new — powers summarizer) |
| `GEMINI_API_KEY` | ✅ Working (billing enabled) |
| `TELEGRAM_BOT_TOKEN` | ✅ `@unfomo_bot` |
| `TELEGRAM_CHAT_ID` | ✅ Personal numeric ID set |
| `DATABASE_URL` | ✅ Railway Postgres public URL |
| `GOOGLE_CLOUD_TTS_KEY` | ⏳ Needed for podcast audio step |

---

## Open Questions

1. **Railway deployment** — deploy bot + scheduler to Railway, or keep running locally?
2. **Gmail ingestion** — which newsletters? OAuth setup needed for Gmail API access
3. **Podcast audio** — enable Google Cloud TTS key to test generation?
