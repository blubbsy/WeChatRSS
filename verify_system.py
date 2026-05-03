import asyncio
import os
from scraper import check_session_validity, scrape_wechat
from database import get_db_async

async def verify_and_test():
    print("="*50)
    print("VERIFYING WECHAT SESSION")
    print("="*50)
    
    # 1. Check validity
    is_valid, message = await check_session_validity()
    print(f"Status: {'✅ VALID' if is_valid else '❌ INVALID'}")
    print(f"Message: {message}")
    
    if not is_valid:
        print("\nAborting test scrape due to invalid session.")
        return

    # 2. Check for subscriptions
    print("\nChecking for active subscriptions...")
    conn = await get_db_async()
    async with conn.execute("SELECT id, name FROM accounts") as cursor:
        accounts = await cursor.fetchall()
    await conn.close()
    
    if not accounts:
        print("No accounts found in database. Please add one in the dashboard first.")
        print("Example account added for testing: 小木易仿真 (Mzk4ODUyMTE4Ng==)")
        conn = await get_db_async()
        # Add a test account linked to the admin user (id: 38cb0d9afa01651c)
        try:
            await conn.execute("INSERT INTO accounts (id, user_id, name) VALUES (?, ?, ?)", 
                             ('Mzk4ODUyMTE4Ng==', '38cb0d9afa01651c', '小木易仿真'))
            await conn.commit()
            print("Test account added.")
        except Exception as e:
            print(f"Could not add test account (might already exist): {e}")
        finally:
            await conn.close()

    # 3. Perform test scrape
    print("\n" + "="*50)
    print("STARTING TEST SCRAPE")
    print("="*50)
    try:
        await scrape_wechat()
        print("\nScrape cycle completed.")
        
        # 4. Verify data in DB
        conn = await get_db_async()
        async with conn.execute("SELECT title, pub_date FROM articles ORDER BY fetch_date DESC LIMIT 5") as cursor:
            articles = await cursor.fetchall()
        await conn.close()
        
        if articles:
            print(f"\nSUCCESS: Found {len(articles)} articles in database:")
            for art in articles:
                print(f"- {art['title']} ({art['pub_date']})")
        else:
            print("\nWARNING: Scrape finished but no articles were found. Check logs for details.")
            
    except Exception as e:
        print(f"\nCRITICAL ERROR during scrape: {e}")

if __name__ == "__main__":
    asyncio.run(verify_and_test())
