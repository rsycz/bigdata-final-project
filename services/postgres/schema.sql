CREATE EXTENSION IF NOT EXISTS pg_trgm;

-------------------------------------------------------------------------------
-- USERS
-------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    username    TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-------------------------------------------------------------------------------
-- CREDENTIALS
-------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS credentials (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    password_hash   TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_credentials_user_id ON credentials(user_id);

-------------------------------------------------------------------------------
-- TWEETS
-------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tweets (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message     TEXT NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_user_id ON tweets(user_id);
CREATE INDEX IF NOT EXISTS idx_tweets_fts ON tweets USING GIN(to_tsvector('english', message));
