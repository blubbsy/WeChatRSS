import sqlite3
conn = sqlite3.connect('data/wechat_rss.db')
conn.row_factory = sqlite3.Row
print("Users:")
for row in conn.execute("SELECT * FROM users").fetchall():
    print(dict(row))
print("\nSessions:")
for row in conn.execute("SELECT * FROM sessions").fetchall():
    print(dict(row))
conn.close()
