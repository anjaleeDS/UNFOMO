"""
Gemini Search grounding: asks Gemini what's new in AI today.
Catches things RSS misses — feeds "emerging" and "you would have missed this".
"""
import json
import re
from datetime import datetime, timezone

from google import genai
from google.genai import types

from config import GEMINI_API_KEY
from db import repository as db
from ingestion.scorer import score
from processing.cost_tracker import log

client = genai.Client(api_key=GEMINI_API_KEY)

GEMINI_MODEL = "gemini-2.0-flash"

SEARCH_SOURCE_NAME = "Gemini Search"
SEARCH_SOURCE_URL  = "gemini://search-grounding"
SEARCH_SOURCE_TIER = 3

DAILY_QUERY = (
    "List the most significant AI product announcements, model releases, "
    "and major updates from Anthropic, OpenAI, and Google in the last 24 hours. "
    "For each item return: title, url (if available), date, and a 2-sentence summary. "
    "Focus on things that would matter to AI power users."
)

HISTORICAL_QUERY_TEMPLATE = (
    "List significant AI product announcements, model releases, and major updates "
    "from Anthropic, OpenAI, and Google during {period}. "
    "Include early mentions of Claude Code (also called 'claude code cli' or 'claude cli'). "
    "For each item return: title, url (if available), date, and a 2-sentence summary. "
    "Format as JSON array: "
    '[{{"title":"...","url":"...","date":"...","summary":"..."}}]'
)

PARSE_PROMPT = """
Extract a JSON array from this text. Each item should have:
title, url, date, summary.
If a field is missing use null.
Return ONLY the JSON array, nothing else.

Text:
{text}
"""


def _parse_articles_from_response(text: str) -> list[dict]:
    """Try to parse article list from Gemini's response."""
    # Try direct JSON parse first
    json_match = re.search(r'\[[\s\S]*\]', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    # Fallback: ask Gemini to extract structured data
    try:
        r = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=PARSE_PROMPT.format(text=text[:3000]),
        )
        match = re.search(r'\[[\s\S]*\]', r.text)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return []


def fetch_today() -> dict:
    """Run today's search grounding query, store new articles."""
    return _run_query(DAILY_QUERY, cutoff_label="today")


def fetch_historical(period: str) -> dict:
    """
    Fetch historical articles for a given period string.
    period example: "December 2024 and January 2025"
    """
    query = HISTORICAL_QUERY_TEMPLATE.format(period=period)
    return _run_query(query, cutoff_label=period)


def _run_query(query: str, cutoff_label: str) -> dict:
    counts = {"new": 0, "skipped": 0, "errors": 0}

    source_id = db.upsert_source(
        SEARCH_SOURCE_NAME,
        SEARCH_SOURCE_URL,
        "gemini-search",
        SEARCH_SOURCE_TIER,
    )

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=query,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )
        raw_text = response.text

        # log token usage
        if hasattr(response, "usage_metadata"):
            um = response.usage_metadata
            log(
                provider="google",
                model=GEMINI_MODEL,
                tokens_in=getattr(um, "prompt_token_count", 0),
                tokens_out=getattr(um, "candidates_token_count", 0),
            )

    except Exception as e:
        print(f"[gemini_fetcher] Gemini API error: {e}")
        counts["errors"] += 1
        return counts

    articles = _parse_articles_from_response(raw_text)

    for item in articles:
        url   = item.get("url") or f"gemini://result/{hash(item.get('title',''))}"
        title = (item.get("title") or "").strip()
        if not title:
            continue

        # parse date
        published_at = None
        if item.get("date"):
            for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"):
                try:
                    published_at = datetime.strptime(item["date"], fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    pass

        eng_score = score(SEARCH_SOURCE_TIER, published_at)
        article_id = db.insert_article(
            source_id=source_id,
            url=url,
            title=title,
            raw_content=item.get("summary") or "",
            published_at=published_at,
            engagement_score=eng_score,
        )

        if article_id:
            counts["new"] += 1
        else:
            counts["skipped"] += 1

    print(f"[gemini_fetcher] {cutoff_label}: {counts}")
    return counts


if __name__ == "__main__":
    result = fetch_today()
    print(f"Gemini fetch complete: {result}")
