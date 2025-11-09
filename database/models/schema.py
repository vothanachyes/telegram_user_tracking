"""
SQL schema creation statements.
"""

# SQL Schema Creation Statements
CREATE_TABLES_SQL = """
-- App Settings Table
CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    theme TEXT NOT NULL DEFAULT 'dark',
    language TEXT NOT NULL DEFAULT 'en',
    corner_radius INTEGER NOT NULL DEFAULT 10,
    telegram_api_id TEXT,
    telegram_api_hash TEXT,
    download_root_dir TEXT NOT NULL DEFAULT './downloads',
    download_media BOOLEAN NOT NULL DEFAULT 0,
    max_file_size_mb INTEGER NOT NULL DEFAULT 50,
    fetch_delay_seconds REAL NOT NULL DEFAULT 1.0,
    download_photos BOOLEAN NOT NULL DEFAULT 1,
    download_videos BOOLEAN NOT NULL DEFAULT 1,
    download_documents BOOLEAN NOT NULL DEFAULT 1,
    download_audio BOOLEAN NOT NULL DEFAULT 1,
    track_reactions BOOLEAN NOT NULL DEFAULT 1,
    reaction_fetch_delay REAL NOT NULL DEFAULT 0.5,
    pin_enabled BOOLEAN NOT NULL DEFAULT 0,
    encrypted_pin TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (id = 1)
);

-- Telegram Credentials Table
CREATE TABLE IF NOT EXISTS telegram_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_number TEXT NOT NULL UNIQUE,
    session_string TEXT,
    is_default BOOLEAN NOT NULL DEFAULT 0,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telegram Groups Table
CREATE TABLE IF NOT EXISTS telegram_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL UNIQUE,
    group_name TEXT NOT NULL,
    group_username TEXT,
    last_fetch_date TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Telegram Users Table
CREATE TABLE IF NOT EXISTS telegram_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    full_name TEXT NOT NULL,
    phone TEXT,
    bio TEXT,
    profile_photo_path TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT,
    caption TEXT,
    date_sent TIMESTAMP NOT NULL,
    has_media BOOLEAN NOT NULL DEFAULT 0,
    media_type TEXT,
    media_count INTEGER DEFAULT 0,
    message_link TEXT,
    message_type TEXT,
    has_sticker BOOLEAN NOT NULL DEFAULT 0,
    has_link BOOLEAN NOT NULL DEFAULT 0,
    sticker_emoji TEXT,
    is_deleted BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, group_id),
    FOREIGN KEY (group_id) REFERENCES telegram_groups(group_id),
    FOREIGN KEY (user_id) REFERENCES telegram_users(user_id)
);

-- Reactions Table
CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    emoji TEXT NOT NULL,
    message_link TEXT,
    reacted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id, group_id, user_id, emoji),
    FOREIGN KEY (message_id, group_id) REFERENCES messages(message_id, group_id),
    FOREIGN KEY (user_id) REFERENCES telegram_users(user_id)
);

-- Media Files Table
CREATE TABLE IF NOT EXISTS media_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT,
    thumbnail_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(message_id)
);

-- Deleted Messages Table (for soft delete tracking)
CREATE TABLE IF NOT EXISTS deleted_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL UNIQUE,
    group_id INTEGER NOT NULL,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deleted Users Table (for soft delete tracking)
CREATE TABLE IF NOT EXISTS deleted_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Login Credentials Table (for Firebase login)
CREATE TABLE IF NOT EXISTS login_credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    encrypted_password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User License Cache Table
CREATE TABLE IF NOT EXISTS user_license_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL UNIQUE,
    license_tier TEXT NOT NULL DEFAULT 'silver',
    expiration_date TIMESTAMP,
    max_devices INTEGER NOT NULL DEFAULT 1,
    max_groups INTEGER NOT NULL DEFAULT 3,
    max_accounts INTEGER NOT NULL DEFAULT 1,
    max_account_actions INTEGER NOT NULL DEFAULT 2,
    last_synced TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Account Activity Log Table
CREATE TABLE IF NOT EXISTS account_activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_email TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'add' or 'delete'
    phone_number TEXT,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages(group_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_date_sent ON messages(date_sent);
CREATE INDEX IF NOT EXISTS idx_messages_deleted ON messages(is_deleted);
CREATE INDEX IF NOT EXISTS idx_messages_message_type ON messages(message_type);
CREATE INDEX IF NOT EXISTS idx_media_files_message_id ON media_files(message_id);
CREATE INDEX IF NOT EXISTS idx_telegram_users_deleted ON telegram_users(is_deleted);
CREATE INDEX IF NOT EXISTS idx_deleted_messages_message_id ON deleted_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_deleted_users_user_id ON deleted_users(user_id);
CREATE INDEX IF NOT EXISTS idx_reactions_message_id ON reactions(message_id);
CREATE INDEX IF NOT EXISTS idx_reactions_user_id_group_id ON reactions(user_id, group_id);
CREATE INDEX IF NOT EXISTS idx_reactions_message_link ON reactions(message_link);
CREATE INDEX IF NOT EXISTS idx_user_license_cache_email ON user_license_cache(user_email);
CREATE INDEX IF NOT EXISTS idx_user_license_cache_active ON user_license_cache(is_active);
CREATE INDEX IF NOT EXISTS idx_account_activity_user_email ON account_activity_log(user_email);
CREATE INDEX IF NOT EXISTS idx_account_activity_timestamp ON account_activity_log(action_timestamp);
"""

