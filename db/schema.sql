-- UNFOMO database schema

-- Sources: where articles come from
CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    url         TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL,        -- 'rss' | 'gemini-search'
    tier        INTEGER NOT NULL,     -- 1=official, 2=press, 3=gemini-search
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Articles: raw ingested content
CREATE TABLE IF NOT EXISTS articles (
    id               SERIAL PRIMARY KEY,
    source_id        INTEGER REFERENCES sources(id),
    url              TEXT NOT NULL UNIQUE,
    title            TEXT NOT NULL,
    raw_content      TEXT,
    published_at     TIMESTAMPTZ,
    fetched_at       TIMESTAMPTZ DEFAULT NOW(),
    engagement_score FLOAT DEFAULT 0.0
);

-- Entities: companies, products, people extracted from articles
CREATE TABLE IF NOT EXISTS entities (
    id    SERIAL PRIMARY KEY,
    name  TEXT NOT NULL UNIQUE,
    type  TEXT NOT NULL   -- 'company' | 'product' | 'person'
);

CREATE TABLE IF NOT EXISTS article_entities (
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    entity_id  INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, entity_id)
);

-- Tags: topics extracted from articles
CREATE TABLE IF NOT EXISTS tags (
    id       SERIAL PRIMARY KEY,
    name     TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL  -- 'topic' | 'feature' | 'sentiment'
);

CREATE TABLE IF NOT EXISTS article_tags (
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    tag_id     INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

-- Summaries: Claude-processed output per article
CREATE TABLE IF NOT EXISTS summaries (
    id               SERIAL PRIMARY KEY,
    article_id       INTEGER REFERENCES articles(id) ON DELETE CASCADE UNIQUE,
    summary_text     TEXT NOT NULL,
    now_what         TEXT NOT NULL,
    significance     INTEGER NOT NULL CHECK (significance BETWEEN 1 AND 5),
    ai_player        TEXT NOT NULL,  -- 'anthropic' | 'openai' | 'google' | 'other'
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Topic counts: for trend charts (populated daily)
CREATE TABLE IF NOT EXISTS topic_counts (
    id       SERIAL PRIMARY KEY,
    tag_id   INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    date     DATE NOT NULL,
    count    INTEGER DEFAULT 0,
    UNIQUE (tag_id, date)
);

-- Digests: daily and weekly narrative outputs
CREATE TABLE IF NOT EXISTS digests (
    id                 SERIAL PRIMARY KEY,
    type               TEXT NOT NULL,  -- 'daily' | 'weekly'
    content            TEXT NOT NULL,
    podcast_script     TEXT,
    podcast_audio_url  TEXT,
    created_at         TIMESTAMPTZ DEFAULT NOW()
);

-- Emergence tracking: new terms appearing for the first time
CREATE TABLE IF NOT EXISTS term_appearances (
    id                  SERIAL PRIMARY KEY,
    term                TEXT NOT NULL,
    first_seen_at       TIMESTAMPTZ DEFAULT NOW(),
    count_48h           INTEGER DEFAULT 1,
    flagged_as_emerging BOOLEAN DEFAULT FALSE,
    UNIQUE (term)
);

-- API cost tracking
CREATE TABLE IF NOT EXISTS api_calls (
    id         SERIAL PRIMARY KEY,
    provider   TEXT NOT NULL,   -- 'anthropic' | 'google'
    model      TEXT NOT NULL,
    tokens_in  INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost_usd   FLOAT DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_articles_published  ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_source     ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_summaries_player    ON summaries(ai_player);
CREATE INDEX IF NOT EXISTS idx_summaries_sig       ON summaries(significance DESC);
CREATE INDEX IF NOT EXISTS idx_topic_counts_date   ON topic_counts(date DESC);
CREATE INDEX IF NOT EXISTS idx_term_emerging       ON term_appearances(flagged_as_emerging);
CREATE INDEX IF NOT EXISTS idx_api_calls_date      ON api_calls(created_at DESC);
