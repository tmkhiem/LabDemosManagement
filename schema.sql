-- Lab Demo Management System – Database Schema

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role         TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('admin', 'student')),
    is_active    BOOLEAN NOT NULL DEFAULT 1,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Pre-registered lab servers (name → internal IP mapping).
-- Only private RFC-1918 IPs are accepted.
CREATE TABLE IF NOT EXISTS servers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT UNIQUE NOT NULL,
    ip         TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS demos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    demo_name        TEXT NOT NULL,
    target_url       TEXT NOT NULL,
    description      TEXT,
    is_active        BOOLEAN NOT NULL DEFAULT 1,
    hit_count        INTEGER NOT NULL DEFAULT 0,
    last_accessed_at DATETIME,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner_id, demo_name)
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_servers_name   ON servers(name);
CREATE INDEX IF NOT EXISTS idx_demos_owner    ON demos(owner_id);
CREATE INDEX IF NOT EXISTS idx_demos_active   ON demos(is_active);
CREATE INDEX IF NOT EXISTS idx_demos_hits     ON demos(hit_count);
