"""
Polls all RSS sources, deduplicates by URL, stores new articles.
"""
import feedparser
import httpx
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from db import repository as db
from ingestion.source_registry import SOURCES
from ingestion.scorer import score


def _parse_date(entry) -> datetime | None:
    for field in ("published_parsed", "updated_parsed"):
        val = getattr(entry, field, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    # fallback: try string fields
    for field in ("published", "updated"):
        val = getattr(entry, field, None)
        if val:
            try:
                return parsedate_to_datetime(val)
            except Exception:
                pass
    return None


def _extract_content(entry) -> str:
    for field in ("summary", "content"):
        val = getattr(entry, field, None)
        if val:
            if isinstance(val, list):
                return val[0].get("value", "")
            return str(val)
    return ""


def fetch_all(cutoff_hours: int = 25) -> dict:
    """
    Fetch all active RSS sources.
    cutoff_hours: skip articles older than this (default 25h for daily job).
    Pass cutoff_hours=0 to ingest everything (used for historical test case).
    Returns counts: {new, skipped, errors}
    """
    counts = {"new": 0, "skipped": 0, "errors": 0}
    now = datetime.now(timezone.utc)

    for src in SOURCES:
        if src["type"] != "rss":
            continue

        source_id = db.upsert_source(src["name"], src["url"], src["type"], src["tier"])

        try:
            feed = feedparser.parse(src["url"])
        except Exception as e:
            print(f"[rss_fetcher] ERROR fetching {src['name']}: {e}")
            counts["errors"] += 1
            continue

        for entry in feed.entries:
            url = getattr(entry, "link", None)
            title = getattr(entry, "title", "").strip()
            if not url or not title:
                continue

            published_at = _parse_date(entry)

            # skip old articles unless cutoff disabled
            if cutoff_hours > 0 and published_at:
                age_hours = (now - published_at).total_seconds() / 3600
                if age_hours > cutoff_hours:
                    counts["skipped"] += 1
                    continue

            content = _extract_content(entry)
            eng_score = score(src["tier"], published_at)

            article_id = db.insert_article(
                source_id=source_id,
                url=url,
                title=title,
                raw_content=content,
                published_at=published_at,
                engagement_score=eng_score,
            )

            if article_id:
                counts["new"] += 1
            else:
                counts["skipped"] += 1

    return counts


if __name__ == "__main__":
    result = fetch_all()
    print(f"RSS fetch complete: {result}")
