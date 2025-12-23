CREATE TABLE IF NOT EXISTS users (
    user_id   SERIAL PRIMARY KEY,
    username  VARCHAR(255) UNIQUE NOT NULL,
    password  VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS chats (
    chat_id   SERIAL PRIMARY KEY,
    user_id   INT NOT NULL,
    title     VARCHAR(255),
    CONSTRAINT fk_chats_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS messages (
    message_id SERIAL PRIMARY KEY,
    chat_id    INT NOT NULL,
    content    VARCHAR(255) NOT NULL,
    time       VARCHAR(255),
    is_user    BOOLEAN NOT NULL,
    CONSTRAINT fk_messages_chat
        FOREIGN KEY (chat_id) REFERENCES chats(chat_id)
        ON DELETE CASCADE
);
