"""
Daily job: fetch → score → summarize → emergence check → Telegram ping.
Run manually: python scheduler/daily_job.py
Or triggered by APScheduler in scheduler/jobs.py
"""
from ingestion import rss_fetcher, gemini_search
from processing import summarizer, emergence
from processing.costs import print_summary
import asyncio


def run():
    print("\n══ UNFOMO Daily Job ══════════════════════════════")

    print("\n[1/4] Fetching RSS sources...")
    rss_counts = rss_fetcher.fetch_all(cutoff_hours=25)
    print(f"      RSS: {rss_counts}")

    print("\n[2/4] Fetching Gemini search grounding...")
    gem_counts = gemini_search.fetch_today_via_gemini()
    print(f"      Gemini: {gem_counts}")

    print("\n[3/4] Summarizing new articles...")
    sum_counts = summarizer.process_unsummarized(batch_size=50)
    print(f"      Summaries: {sum_counts}")

    print("\n[4/4] Running emergence detection...")
    new_terms = emergence.run()
    if new_terms:
        print(f"      🌱 New emerging: {new_terms}")
    else:
        print("      No new emerging terms.")

    print("\n[✓] Sending Telegram daily ping...")
    from bot.telegram import send_daily
    asyncio.run(send_daily())

    print_summary()
    print("\n══ Daily job complete ════════════════════════════\n")


if __name__ == "__main__":
    run()
