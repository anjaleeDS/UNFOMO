"""
All database access lives here. No raw SQL anywhere else in the app.
"""
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from datetime import date, datetime
from typing import Optional
from config import DATABASE_URL


@contextmanager
def get_conn():
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema():
    """Run schema.sql to create all tables."""
    import os
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)


# ── Sources ──────────────────────────────────────────────────────────────────

def upsert_source(name: str, url: str, type_: str, tier: int) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO sources (name, url, type, tier)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET active = TRUE
                RETURNING id
            """, (name, url, type_, tier))
            return cur.fetchone()[0]


def get_active_sources():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM sources WHERE active = TRUE ORDER BY tier, name")
            return cur.fetchall()


# ── Articles ─────────────────────────────────────────────────────────────────

def insert_article(source_id: int, url: str, title: str,
                   raw_content: str, published_at: Optional[datetime],
                   engagement_score: float = 0.0) -> Optional[int]:
    """Returns article id, or None if URL already exists (duplicate)."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO articles (source_id, url, title, raw_content, published_at, engagement_score)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                RETURNING id
            """, (source_id, url, title, raw_content, published_at, engagement_score))
            row = cur.fetchone()
            return row[0] if row else None


def get_unsummarized_articles(limit: int = 50):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT a.*, s.name AS source_name, s.tier
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                LEFT JOIN summaries sm ON a.id = sm.article_id
                WHERE sm.id IS NULL
                ORDER BY a.published_at DESC NULLS LAST
                LIMIT %s
            """, (limit,))
            return cur.fetchall()


def get_recent_articles(days: int = 1, min_significance: int = 1):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT a.id, a.url, a.title, a.published_at, a.engagement_score,
                       s.name AS source_name, s.tier,
                       sm.summary_text, sm.now_what, sm.significance, sm.ai_player
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                LEFT JOIN summaries sm ON a.id = sm.article_id
                WHERE a.fetched_at >= NOW() - INTERVAL '%s days'
                  AND (sm.significance IS NULL OR sm.significance >= %s)
                ORDER BY sm.significance DESC NULLS LAST, a.engagement_score DESC
            """, (days, min_significance))
            return cur.fetchall()


# ── Tags & Entities ───────────────────────────────────────────────────────────

def upsert_tag(name: str, category: str) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO tags (name, category) VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category
                RETURNING id
            """, (name.lower().strip(), category))
            return cur.fetchone()[0]


def link_article_tag(article_id: int, tag_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO article_tags (article_id, tag_id) VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (article_id, tag_id))


def upsert_entity(name: str, type_: str) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO entities (name, type) VALUES (%s, %s)
                ON CONFLICT (name) DO UPDATE SET type = EXCLUDED.type
                RETURNING id
            """, (name.strip(), type_))
            return cur.fetchone()[0]


def link_article_entity(article_id: int, entity_id: int):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO article_entities (article_id, entity_id) VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (article_id, entity_id))


# ── Summaries ─────────────────────────────────────────────────────────────────

def insert_summary(article_id: int, summary_text: str, now_what: str,
                   significance: int, ai_player: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO summaries (article_id, summary_text, now_what, significance, ai_player)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (article_id) DO NOTHING
            """, (article_id, summary_text, now_what, significance, ai_player))


# ── Topic counts ──────────────────────────────────────────────────────────────

def increment_topic_count(tag_id: int, for_date: date):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO topic_counts (tag_id, date, count) VALUES (%s, %s, 1)
                ON CONFLICT (tag_id, date) DO UPDATE SET count = topic_counts.count + 1
            """, (tag_id, for_date))


def get_topic_trends(days: int = 7):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT t.name, tc.date, tc.count
                FROM topic_counts tc
                JOIN tags t ON tc.tag_id = t.id
                WHERE tc.date >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY tc.date DESC, tc.count DESC
            """, (days,))
            return cur.fetchall()


def get_player_velocity(weeks: int = 2):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT sm.ai_player,
                       COUNT(*) FILTER (WHERE a.fetched_at >= NOW() - INTERVAL '7 days') AS this_week,
                       COUNT(*) FILTER (WHERE a.fetched_at BETWEEN NOW() - INTERVAL '14 days'
                                                              AND NOW() - INTERVAL '7 days') AS last_week
                FROM summaries sm
                JOIN articles a ON sm.article_id = a.id
                GROUP BY sm.ai_player
            """, ())
            return cur.fetchall()


# ── Digests ───────────────────────────────────────────────────────────────────

def insert_digest(type_: str, content: str,
                  podcast_script: Optional[str] = None,
                  podcast_audio_url: Optional[str] = None) -> int:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO digests (type, content, podcast_script, podcast_audio_url)
                VALUES (%s, %s, %s, %s) RETURNING id
            """, (type_, content, podcast_script, podcast_audio_url))
            return cur.fetchone()[0]


def get_latest_digest(type_: str):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM digests WHERE type = %s ORDER BY created_at DESC LIMIT 1
            """, (type_,))
            return cur.fetchone()


# ── Emergence ─────────────────────────────────────────────────────────────────

def upsert_term(term: str) -> dict:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                INSERT INTO term_appearances (term, count_48h)
                VALUES (%s, 1)
                ON CONFLICT (term) DO UPDATE
                    SET count_48h = term_appearances.count_48h + 1
                RETURNING *
            """, (term.lower().strip(),))
            return cur.fetchone()


def flag_emerging(term: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE term_appearances SET flagged_as_emerging = TRUE WHERE term = %s
            """, (term.lower().strip(),))


def get_emerging_terms():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM term_appearances
                WHERE flagged_as_emerging = TRUE
                ORDER BY first_seen_at DESC
            """)
            return cur.fetchall()


# ── Cost tracking ─────────────────────────────────────────────────────────────

def log_api_call(provider: str, model: str,
                 tokens_in: int, tokens_out: int, cost_usd: float):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO api_calls (provider, model, tokens_in, tokens_out, cost_usd)
                VALUES (%s, %s, %s, %s, %s)
            """, (provider, model, tokens_in, tokens_out, cost_usd))


def get_cost_summary():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT provider, model,
                       SUM(tokens_in) AS total_tokens_in,
                       SUM(tokens_out) AS total_tokens_out,
                       SUM(cost_usd) AS total_cost_usd,
                       COUNT(*) AS call_count
                FROM api_calls
                WHERE created_at >= NOW() - INTERVAL '30 days'
                GROUP BY provider, model
                ORDER BY total_cost_usd DESC
            """)
            return cur.fetchall()
