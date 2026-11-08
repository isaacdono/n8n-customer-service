-- PostgreSQL Schema for FastAPI Router and n8n Chat Memory

CREATE TABLE IF NOT EXISTS chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128),
    user_id VARCHAR(128),
    sender_name VARCHAR(255),
    prefix VARCHAR(64),
    user_message TEXT,
    agent_response TEXT,
    message JSONB,
    timestamp BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_prefix ON chat_history(prefix);

CREATE TABLE IF NOT EXISTS active_sessions (
    user_id VARCHAR(128) PRIMARY KEY,
    prefix VARCHAR(64) NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
