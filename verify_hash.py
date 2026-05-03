import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
conn = sqlite3.connect('data/wechat_rss.db')
conn.row_factory = sqlite3.Row
user = conn.execute("SELECT * FROM users WHERE username='admin'").fetchone()
if user:
    print(f"Hash in DB: {user['password_hash']}")
    is_valid = pwd_context.verify("admin", user['password_hash'])
    print(f"Is 'admin' valid? {is_valid}")
else:
    print("User not found")
conn.close()
