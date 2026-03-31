"""
Claude API: summarize articles into structured JSON.
One call per article. Uses Haiku by default (cheap + fast).
"""
import json
import anthropic
from datetime import date

from config import ANTHROPIC_API_KEY
from db import repository as db
from processing.cost_tracker import log, DEFAULT_MODEL

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

PROMPT_TEMPLATE = """You are processing an AI industry news article for UNFOMO — a signal feed for AI power users who want to stay ahead without drowning in noise.

Article title: {title}
Source: {source_name} (tier {tier} — {tier_label})
Content:
{content}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "summary": "2-3 sentence summary of what actually happened",
  "now_what": "1 sentence: what does this mean for someone using these AI tools today?",
  "significance": <integer 1-5, where 5 = major industry shift, 1 = minor update>,
  "tags": ["topic1", "topic2", "topic3"],
  "entities": [
    {{"name": "entity name", "type": "company|product|person"}}
  ],
  "ai_player": "anthropic|openai|google|other"
}}"""

TIER_LABELS = {1: "official source", 2: "tech press", 3: "search-discovered"}


def summarize_article(article: dict, model: str = DEFAULT_MODEL) -> dict | None:
    """
    Takes a db article row, returns parsed JSON summary dict or None on failure.
    """
    content = (article.get("raw_content") or "")[:4000]  # cap to keep tokens low
    tier = article.get("tier", 2)

    prompt = PROMPT_TEMPLATE.format(
        title=article["title"],
        source_name=article.get("source_name", "unknown"),
        tier=tier,
        tier_label=TIER_LABELS.get(tier, "unknown"),
        content=content,
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # log cost
        log(
            provider="anthropic",
            model=model,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
        )

        parsed = json.loads(raw)
        return parsed

    except json.JSONDecodeError as e:
        print(f"[summarizer] JSON parse error for article {article['id']}: {e}")
        return None
    except Exception as e:
        print(f"[summarizer] API error for article {article['id']}: {e}")
        return None


def process_unsummarized(batch_size: int = 50) -> dict:
    """
    Fetch unsummarized articles, run through Claude, store results.
    Returns counts: {processed, failed, skipped}
    """
    articles = db.get_unsummarized_articles(limit=batch_size)
    counts = {"processed": 0, "failed": 0}
    today = date.today()

    for article in articles:
        result = summarize_article(article)

        if not result:
            counts["failed"] += 1
            continue

        # store summary
        db.insert_summary(
            article_id=article["id"],
            summary_text=result.get("summary", ""),
            now_what=result.get("now_what", ""),
            significance=max(1, min(5, int(result.get("significance", 3)))),
            ai_player=result.get("ai_player", "other"),
        )

        # store tags + update topic counts
        for tag_name in result.get("tags", []):
            if tag_name:
                tag_id = db.upsert_tag(tag_name, "topic")
                db.link_article_tag(article["id"], tag_id)
                db.increment_topic_count(tag_id, today)

        # store entities
        for ent in result.get("entities", []):
            if ent.get("name") and ent.get("type"):
                entity_id = db.upsert_entity(ent["name"], ent["type"])
                db.link_article_entity(article["id"], entity_id)

        counts["processed"] += 1

    return counts


if __name__ == "__main__":
    result = process_unsummarized()
    print(f"Summarization complete: {result}")
