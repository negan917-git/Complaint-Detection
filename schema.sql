-- Complaint Detection — SQL Schema

CREATE TABLE IF NOT EXISTS bots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_bot_id BIGINT UNIQUE,
    name VARCHAR NOT NULL,
    username VARCHAR NOT NULL UNIQUE,
    token VARCHAR,
    status VARCHAR DEFAULT 'connected',
    messages_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR,
    username VARCHAR,
    text TEXT NOT NULL,
    summary TEXT,
    sentiment VARCHAR DEFAULT 'neutral',
    emotion VARCHAR DEFAULT 'neutral',
    priority VARCHAR DEFAULT 'medium',
    category VARCHAR DEFAULT 'general',
    complaint BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_messages_sentiment ON messages(sentiment);
CREATE INDEX IF NOT EXISTS idx_messages_priority ON messages(priority);
CREATE INDEX IF NOT EXISTS idx_messages_complaint ON messages(complaint);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
