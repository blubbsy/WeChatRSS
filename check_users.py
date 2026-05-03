import sqlite3
import os

DB_PATH = os.path.join('data', 'wechat_rss.db')
if not os.path.exists(DB_PATH):
    print(f"Error: {DB_PATH} not found.")
else:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT id, username, role, feed_hash FROM users").fetchall()
    print("Users in database:")
    for u in users:
        print(dict(u))
    conn.close()
