import asyncio
import aiosqlite
from database import DB_PATH

async def test_query():
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    session_id = '8778e306d76e492a662d3004b6690a1fb3c9b5ce554574936958a192db393edd'
    query = '''
            SELECT u.id, u.username, u.feed_hash, u.role 
            FROM users u
            JOIN sessions s ON u.id = s.user_id
            WHERE s.id = ?
        '''
    async with conn.execute(query, (session_id,)) as cursor:
        user = await cursor.fetchone()
        print(f"Result for {session_id}: {dict(user) if user else 'None'}")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(test_query())
