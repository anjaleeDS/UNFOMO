"""
Weekly digest builder.
Synthesizes top articles into:
  1. Narrative digest (400 words)
  2. "You would have missed this" section
  3. Podcast script (800 words, two-host format, NotebookLM-compatible)
"""
import json
import anthropic

from config import ANTHROPIC_API_KEY
from db import repository as db
from processing.cost_tracker import log

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

DIGEST_MODEL = "claude-sonnet-4-6"  # better quality for weekly synthesis

WEEKLY_PROMPT = """You are writing the weekly edition of UNFOMO — a signal digest for AI power users.
Your readers are smart, experienced, and already overwhelmed. They want signal, not noise.
No filler. No "it's an exciting time in AI." Say something real.

Here are this week's top articles (sorted by significance):

{articles_json}

Write THREE sections:

## WEEKLY DIGEST
A 400-word opinionated narrative. What actually happened this week? What's the thread connecting these stories?
What does it mean for how people will use AI tools next week?

## YOU WOULD HAVE MISSED THIS
Pick 2-3 items with high significance (4-5) but that flew under the radar (low engagement score or tier 2-3 source).
Format: **[Title]** — one sentence on why this matters more than it looks.

## PODCAST SCRIPT
An 800-word two-host conversation script. Hosts: Anja (product/strategy lens) and an unnamed co-host (technical lens).
Natural, opinionated, a little irreverent. Compatible with NotebookLM Audio Overview format.
Start with: [INTRO] and mark speaker turns with [ANJA] and [HOST].
End with a concrete "so what do I do with this" takeaway for listeners."""


def build_weekly_digest() -> dict | None:
    """
    Pull this week's top articles, run through Claude, store digest.
    Returns the digest dict or None on failure.
    """
    articles = db.get_recent_articles(days=7, min_significance=3)

    if not articles:
        print("[digest_builder] No articles found for weekly digest.")
        return None

    # Format top 15 articles for the prompt
    top = sorted(articles, key=lambda a: (a.get("significance") or 0), reverse=True)[:15]
    articles_for_prompt = [
        {
            "title":        a["title"],
            "source":       a.get("source_name", ""),
            "significance": a.get("significance"),
            "engagement":   round(a.get("engagement_score") or 0, 2),
            "ai_player":    a.get("ai_player", "other"),
            "summary":      a.get("summary_text", ""),
            "now_what":     a.get("now_what", ""),
            "url":          a.get("url", ""),
        }
        for a in top
    ]

    prompt = WEEKLY_PROMPT.format(articles_json=json.dumps(articles_for_prompt, indent=2))

    try:
        response = client.messages.create(
            model=DIGEST_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text

        log(
            provider="anthropic",
            model=DIGEST_MODEL,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
        )

        # Split narrative from podcast script
        podcast_script = None
        if "## PODCAST SCRIPT" in content:
            parts = content.split("## PODCAST SCRIPT", 1)
            narrative = parts[0].strip()
            podcast_script = parts[1].strip()
        else:
            narrative = content

        digest_id = db.insert_digest(
            type_="weekly",
            content=narrative,
            podcast_script=podcast_script,
        )

        print(f"[digest_builder] Weekly digest saved (id={digest_id})")
        return {"id": digest_id, "content": narrative, "podcast_script": podcast_script}

    except Exception as e:
        print(f"[digest_builder] Error: {e}")
        return None


if __name__ == "__main__":
    result = build_weekly_digest()
    if result:
        print("\n── DIGEST PREVIEW ──\n")
        print(result["content"][:800])
        print("\n...")
