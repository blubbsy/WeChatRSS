"""
Database management module for WeChatRSS.
Handles SQLite schema initialization, user management, and connection lifecycle.
"""

import sqlite3
import aiosqlite
import os
import secrets
import datetime
from contextlib import asynccontextmanager
from passlib.context import CryptContext

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "wechat_rss.db")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Session expiry (30 days)
SESSION_TTL_DAYS = 30


def _configure_sqlite_connection(conn):
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")


def init_db():
    """
    Initializes the database schema if it doesn't exist.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    _configure_sqlite_connection(conn)
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            feed_hash TEXT UNIQUE,
            role TEXT DEFAULT 'user'
        )
    """)

    # Sessions table (with expiry)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Migration: Add expires_at if missing
    try:
        c.execute("ALTER TABLE sessions ADD COLUMN expires_at TIMESTAMP")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Accounts table - Updated with status tracking
    c.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT,
            user_id TEXT,
            name TEXT,
            last_sync TIMESTAMP,
            last_status TEXT DEFAULT 'pending',
            error_msg TEXT,
            article_count INTEGER DEFAULT 0,
            PRIMARY KEY (id, user_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Migration: Add new columns to accounts if they don't exist
    for col_sql in [
        'ALTER TABLE accounts ADD COLUMN last_status TEXT DEFAULT "pending"',
        "ALTER TABLE accounts ADD COLUMN error_msg TEXT",
        "ALTER TABLE accounts ADD COLUMN article_count INTEGER DEFAULT 0",
        "ALTER TABLE accounts ADD COLUMN sync_progress_current INTEGER DEFAULT 0",
        "ALTER TABLE accounts ADD COLUMN sync_progress_total INTEGER DEFAULT 0",
    ]:
        try:
            c.execute(col_sql)
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Articles table
    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            account_id TEXT,
            title TEXT,
            url TEXT UNIQUE,
            content TEXT,
            pub_date TIMESTAMP,
            fetch_date TIMESTAMP
        )
    """)

    # Migration: Add new columns to articles if they don't exist
    for col_sql in [
        "ALTER TABLE articles ADD COLUMN translated_title TEXT",
        "ALTER TABLE articles ADD COLUMN translated_content TEXT",
        "ALTER TABLE articles ADD COLUMN translation_status TEXT DEFAULT 'pending'",
        "ALTER TABLE articles ADD COLUMN translation_error TEXT",
    ]:
        try:
            c.execute(col_sql)
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Align status for previously translated articles
    try:
        c.execute("UPDATE articles SET translation_status = 'success' WHERE translated_title IS NOT NULL AND translation_status = 'pending'")
    except Exception:
        pass

    # System Logs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            module TEXT,
            message TEXT
        )
    """)

    # Settings table
    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # --- Indexes for performance ---
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_articles_account_id ON articles (account_id)"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_articles_url ON articles (url)")
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_articles_title_account ON articles (title, account_id)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_accounts_user_id ON accounts (user_id)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions (user_id)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs (timestamp)"
    )

    # Default system settings
    default_settings = {
        "fetch_interval_hours": "6",
        "fetch_random_jitter_minutes": "30",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "enable_stealth": "true",
    }
    for key, val in default_settings.items():
        c.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val)
        )

    # Bootstrap default admin user
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        admin_id = str(secrets.token_hex(8))
        admin_pass = pwd_context.hash("admin")
        admin_feed_hash = secrets.token_hex(16)
        c.execute(
            "INSERT INTO users (id, username, password_hash, feed_hash, role) VALUES (?, ?, ?, ?, ?)",
            (admin_id, "admin", admin_pass, admin_feed_hash, "admin"),
        )
        print(f"Created default admin user. RSS Hash: {admin_feed_hash}")

    # Cleanup expired sessions on startup
    c.execute("DELETE FROM sessions WHERE expires_at IS NOT NULL AND expires_at < ?",
              (datetime.datetime.now(datetime.timezone.utc).isoformat(),))

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=5)
    _configure_sqlite_connection(conn)
    conn.row_factory = sqlite3.Row
    return conn


@asynccontextmanager
async def get_db_async():
    """
    Async context manager for database connections.
    Guarantees the connection is always closed, even on exception.

    Usage:
        async with get_db_async() as conn:
            await conn.execute(...)
    """
    conn = await aiosqlite.connect(DB_PATH, timeout=5)
    try:
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute("PRAGMA busy_timeout=5000")
        conn.row_factory = aiosqlite.Row
        yield conn
    finally:
        await conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
