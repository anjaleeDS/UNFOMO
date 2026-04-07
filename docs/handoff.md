# UNFOMO — Handoff

**Date**: March 31, 2026
**Status**: MVP built, running locally, pushed to GitHub

---

## What's Done

| Area | Status | Notes |
|------|--------|-------|
| Project structure + GitHub | ✅ | `github.com/anjaleeDS/UNFOMO` — 3 commits on main |
| Postgres on Railway | ✅ | Schema initialized, connected locally via public URL |
| RSS ingestion | ✅ | 8 sources across 2 tiers, deduplication working |
| Claude summarizer | ✅ | Haiku model, JSON fix applied, cost tracking live |
| Web dashboard | ✅ | Dark theme, 5 tabs, serving at `localhost:8080` |
| Telegram bot | ✅ | `@unfomo_bot` — daily ping + `/today`, `/week`, `/player`, `/emerging`, `/cost` |
| Gemini Search grounding | ✅ | Migrated to `google.genai`, billing enabled on Google Cloud |
| Emergence detector | ✅ | Flags new terms appearing 3+ times in 48h |
| Weekly digest builder | ✅ | Claude Sonnet, narrative + "you would have missed this" + podcast script |
| Charts | ✅ | Topic trends + player velocity (Plotly → PNG for Telegram) |
| Podcast TTS | ✅ | Google Cloud TTS (Journey voices), two-host split — needs `GOOGLE_CLOUD_TTS_KEY` |
| Schedulers | ✅ | Daily 7am UTC, Weekly Sunday 8am UTC (APScheduler) |
| Article selection docs | ✅ | `docs/how-articles-are-selected.md` |

---

## What's Tabled for Tomorrow

| Task | Priority | Notes |
|------|----------|-------|
| **Cleanup + rename pass** | High | Plan written — see `~/.claude/plans/immutable-exploring-elephant.md`. Files to rename, functions to clarify, web assets to move to `web/static/` |
| **Emergence backfill test** | Medium | `scripts/test_emergence_backfill.py` — run historical backfill to validate emergence detector catches 'claude code' as a rising signal |
| **Deploy to Railway** | High | Web server + scheduler need to run as Railway services. Add all `.env` keys to Railway variables. Bot polling needs to run 24/7 |
| **Run first full daily job** | Medium | `python3 scheduler/daily_job.py` — confirm end-to-end with Gemini now that billing is on |
| **Telegram `/today` command test** | Medium | Confirm polling responds to commands (was working at end of session) |
| **Weekly digest dry run** | Medium | Trigger `scheduler/weekly_job.py` manually to see digest + charts + podcast script |
| **D3 upgrade for charts** | Low | Replace Plotly with D3 for the web dashboard's stream/river chart and force graph. Plotly stays for Telegram PNG exports |
| **Trends + Players tabs** | Low | Need a few more days of ingestion data before these charts look meaningful |

---

## How to Pick Up Tomorrow

```bash
cd "/Users/anjalee/Library/Mobile Documents/com~apple~CloudDocs/Coding/UNFOMO"

# Start dashboard
python3 -m web.server

# Run daily job manually
python3 -m scheduler.daily_job

# Start Telegram bot polling
python3 -m bot.telegram

# Run weekly job manually (generates digest + charts + podcast script)
python3 -m scheduler.weekly_job
```

---

## Credentials Needed

All in `.env` (never committed). See `.env.example` for the full list.

| Key | Status |
|-----|--------|
| `ANTHROPIC_API_KEY` | ✅ Working |
| `GEMINI_API_KEY` | ✅ Working (billing enabled) |
| `TELEGRAM_BOT_TOKEN` | ✅ `@unfomo_bot` |
| `TELEGRAM_CHAT_ID` | ✅ Personal numeric ID set |
| `DATABASE_URL` | ✅ Railway Postgres public URL |
| `GOOGLE_CLOUD_TTS_KEY` | ⏳ Needed for podcast audio step |

---

## Cost So Far

- Claude API: ~$0.02 (20 calls summarizing today's articles)
- Gemini API: minimal (billing just enabled)
- Railway Postgres: free tier

---

## Open Questions

1. **Emergence backfill** — run `scripts/test_emergence_backfill.py` to validate the detector with Dec 2024 – Feb 2025 data.
2. **Railway deployment** — do you want the bot polling and scheduler running on Railway, or keep running locally for now?
3. **Podcast audio** — do you want to enable the Google Cloud TTS key to test podcast generation?
