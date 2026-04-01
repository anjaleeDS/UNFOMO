"""
One-time diagnostic: The Claude Code (OpenClaw) Emergence Story
December 2024 – February 2025

This validates the full pipeline using real historical data.
UNFOMO should surface Claude Code as an emerging signal in Dec 2024 —
the thing everyone missed until February.

NOT part of the daily pipeline. Run manually with:
  python scripts/validate_emergence_detection.py
"""
from db import repository as db
from ingestion import gemini_search
from processing import summarizer, emergence
from processing.costs import print_summary


def run():
    print("\n══ TEST: Claude Code Emergence (Dec 2024 – Feb 2025) ══════")
    print("Goal: UNFOMO should flag 'claude code' as emerging in Dec 2024.\n")

    # Step 1: Init schema
    print("[1/5] Initializing schema...")
    db.init_schema()

    # Step 2: Historical fetch via Gemini Search grounding
    print("\n[2/5] Fetching December 2024 AI news (Gemini search)...")
    dec_counts = gemini_search.fetch_historical_via_gemini("December 2024")
    print(f"      December: {dec_counts}")

    print("\n       Fetching January 2025 AI news...")
    jan_counts = gemini_search.fetch_historical_via_gemini("January 2025")
    print(f"      January:  {jan_counts}")

    print("\n       Fetching February 2025 AI news...")
    feb_counts = gemini_search.fetch_historical_via_gemini("February 2025")
    print(f"      February: {feb_counts}")

    # Step 3: Summarize everything
    print("\n[3/5] Summarizing articles with Claude...")
    # Use a large batch since this is a one-time backfill
    total_processed = 0
    while True:
        result = summarizer.process_unsummarized(batch_size=30)
        total_processed += result["processed"]
        print(f"      Batch: +{result['processed']} processed, {result['failed']} failed")
        if result["processed"] == 0:
            break

    print(f"      Total summarized: {total_processed}")

    # Step 4: Run emergence detection
    print("\n[4/5] Running emergence detection...")
    new_terms = emergence.run()
    print(f"      Flagged as emerging: {new_terms}")

    # Step 5: Report results
    print("\n[5/5] Results:\n")

    print("── Top articles by significance ──")
    articles = db.get_recent_articles(days=90, min_significance=4)
    for a in articles[:10]:
        print(f"  [{a['significance']}] {a['title'][:80]}")
        if a.get("now_what"):
            print(f"       → {a['now_what']}")
        print()

    print("── Emerging terms flagged ──")
    terms = db.get_emerging_terms()
    if terms:
        for t in terms:
            print(f"  🌱 '{t['term']}' — {t['count_48h']} mentions, first seen {t['first_seen_at']}")
    else:
        print("  None flagged (may need more data or lower threshold)")

    print("\n── Did UNFOMO catch Claude Code? ──")
    claude_code_found = any(
        "claude code" in (t["term"] or "").lower() or
        "claude cli" in (t["term"] or "").lower()
        for t in terms
    )
    if claude_code_found:
        print("  ✅ YES — 'claude code' flagged as emerging signal")
    else:
        print("  ⚠️  Not flagged yet — check article count and threshold")
        print("     Try lowering EMERGENCE_MIN_MENTIONS in emergence.py")

    print_summary()
    print("\n══ Test complete ════════════════════════════════════════\n")


if __name__ == "__main__":
    run()
