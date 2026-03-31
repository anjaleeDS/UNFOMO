"""
Emergence detection: scans recent articles for terms appearing 3+ times
in 48h that have never been flagged before.

This is UNFOMO's killer feature — catching the next "Claude Code" before
it goes mainstream.
"""
import re
from collections import Counter
from datetime import datetime, timedelta, timezone

from db import repository as db

# Terms to always ignore (common words, existing major players)
STOPWORDS = {
    "ai", "the", "and", "for", "with", "that", "this", "from", "are",
    "its", "new", "has", "can", "will", "also", "use", "using", "used",
    "more", "been", "have", "their", "they", "which", "what", "when",
    "model", "models", "llm", "api", "data", "tool", "tools", "update",
    "release", "version", "feature", "features", "users", "user",
    # Known major players — these aren't "emerging"
    "openai", "anthropic", "google", "chatgpt", "claude", "gemini",
    "gpt", "gpt-4", "gpt-4o", "meta", "llama", "mistral",
}

EMERGENCE_THRESHOLD = 3   # appearances in 48h to flag as emerging
MIN_TERM_LENGTH = 4       # ignore very short terms


def _extract_terms(text: str) -> list[str]:
    """Extract meaningful multi-word and single-word terms from text."""
    text = text.lower()
    terms = []

    # Multi-word phrases (2-3 words joined by space or hyphen)
    phrase_pattern = re.compile(r'\b([a-z][a-z0-9\-]{2,}(?:\s[a-z][a-z0-9\-]{2,}){1,2})\b')
    for match in phrase_pattern.finditer(text):
        phrase = match.group(1).strip()
        words = phrase.split()
        if not any(w in STOPWORDS for w in words):
            terms.append(phrase)

    # Single meaningful words (camelCase products, version numbers, brand names)
    word_pattern = re.compile(r'\b([a-z][a-z0-9\-]{3,})\b')
    for match in word_pattern.finditer(text):
        word = match.group(1)
        if word not in STOPWORDS and len(word) >= MIN_TERM_LENGTH:
            terms.append(word)

    return terms


def run() -> list[str]:
    """
    Scan articles from the last 48h, count term frequency,
    flag any new terms hitting the threshold.
    Returns list of newly flagged emerging terms.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=48)

    # Get all known terms that are already flagged
    known_flagged = {t["term"] for t in db.get_emerging_terms()}

    # Pull recent articles
    recent = db.get_recent_articles(days=2)
    if not recent:
        return []

    # Count terms across all titles + summaries
    all_terms: list[str] = []
    for article in recent:
        text = f"{article.get('title', '')} {article.get('summary_text', '')}"
        all_terms.extend(_extract_terms(text))

    counts = Counter(all_terms)
    newly_flagged = []

    for term, count in counts.items():
        if count < EMERGENCE_THRESHOLD:
            continue
        if term in known_flagged:
            continue

        row = db.upsert_term(term)
        # Update count to current 48h count
        if row and row["count_48h"] >= EMERGENCE_THRESHOLD and not row["flagged_as_emerging"]:
            db.flag_emerging(term)
            newly_flagged.append(term)
            print(f"[emergence] 🌱 New emerging term: '{term}' ({count} mentions)")

    return newly_flagged


if __name__ == "__main__":
    flagged = run()
    print(f"Emergence check complete. Newly flagged: {flagged}")
