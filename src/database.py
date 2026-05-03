"""
Database management module for WeChatRSS.
Handles SQLite schema initialization, user management, and connection pooling.
"""

import sqlite3
import aiosqlite
import os
import secrets
import hashlib
from passlib.context import CryptContext

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'wechat_rss.db')
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    """
    Initializes the database schema if it doesn't exist.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            feed_hash TEXT UNIQUE,
            role TEXT DEFAULT 'user'
        )
    ''')

    # Sessions table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Accounts table - Updated with status tracking
    c.execute('''
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
    ''')
    
    # Migration: Add new columns to accounts if they don't exist
    try:
        c.execute('ALTER TABLE accounts ADD COLUMN last_status TEXT DEFAULT "pending"')
        c.execute('ALTER TABLE accounts ADD COLUMN error_msg TEXT')
        c.execute('ALTER TABLE accounts ADD COLUMN article_count INTEGER DEFAULT 0')
    except:
        pass # Columns already exist

    # Articles table
    c.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id TEXT PRIMARY KEY,
            account_id TEXT,
            title TEXT,
            url TEXT UNIQUE,
            content HTML,
            pub_date TIMESTAMP,
            fetch_date TIMESTAMP
        )
    ''')
    
    # System Logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            module TEXT,
            message TEXT
        )
    ''')

    # Settings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Default system settings
    default_settings = {
        "fetch_interval_hours": "6",
        "fetch_random_jitter_minutes": "30",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "enable_stealth": "true"
    }
    for key, val in default_settings.items():
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, val))
    
    # Bootstrap default admin user
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        admin_id = str(secrets.token_hex(8))
        admin_pass = pwd_context.hash("admin")
        admin_feed_hash = secrets.token_hex(16)
        c.execute("INSERT INTO users (id, username, password_hash, feed_hash, role) VALUES (?, ?, ?, ?, ?)",
                  (admin_id, "admin", admin_pass, admin_feed_hash, "admin"))
        print(f"Created default admin user. RSS Hash: {admin_feed_hash}")
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

async def get_db_async():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
