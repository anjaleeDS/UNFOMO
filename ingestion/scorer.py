"""
Engagement scoring: tier weight × recency decay.
Twitter engagement will plug in here when added.
"""
from datetime import datetime, timezone

TIER_WEIGHTS = {1: 1.0, 2: 0.7, 3: 0.5}
RECENCY_DECAY_HOURS = 48  # articles older than this get 0 recency bonus


def score(tier: int, published_at: datetime | None) -> float:
    tier_score = TIER_WEIGHTS.get(tier, 0.3)

    if published_at is None:
        recency_score = 0.0
    else:
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
        recency_score = max(0.0, 1.0 - (age_hours / RECENCY_DECAY_HOURS))

    return round(tier_score * (0.5 + 0.5 * recency_score), 4)
