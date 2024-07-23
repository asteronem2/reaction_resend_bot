CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    chat_id BIGINT NOT NULL,
    topic INTEGER DEFAULT 0 NOT NULL,
    emoji TEXT,
    UNIQUE (chat_id, topic)
);

CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    user_id BIGINT NOT NULL,
    first_name TEXT NOT NULL,
    username TEXT,
    UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS bot_message (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    message_id INTEGER NOT NULL,
    chat_id REFERENCES chat(id) NOT NULL,
    text TEXT,
    UNIQUE (message_id)
);
