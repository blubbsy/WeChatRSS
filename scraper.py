"""
Scraper module for WeChatRSS.
Uses Sogou for discovery and a tiered extraction model (Direct -> WeRead).
Includes URL normalization and strict deduplication.
"""

import asyncio
import os
import json
import logging
import datetime
import uuid
import random
import hashlib
import requests
import aiofiles
import re
from urllib.parse import urlparse, parse_qs, urlunparse
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from readability import Document
from database import get_db_async
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = os.path.dirname(__file__)
PROFILE_DIR = os.path.abspath(os.path.join(BASE_DIR, 'data', 'profiles', 'wechat_rss_profile'))
MEDIA_DIR = os.path.join(BASE_DIR, 'data', 'media')
DEBUG_DIR = os.path.join(BASE_DIR, 'data', 'debug')

os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

async def add_system_log(level, module, message):
    try:
        conn = await get_db_async()
        await conn.execute("INSERT INTO system_logs (level, module, message) VALUES (?, ?, ?)", 
                           (level, module, message))
        await conn.commit()
        await conn.close()
    except: pass

async def get_settings():
    conn = await get_db_async()
    try:
        async with conn.execute("SELECT key, value FROM settings") as cursor:
            rows = await cursor.fetchall()
            return {row['key']: row['value'] for row in rows}
    finally:
        await conn.close()

def normalize_wechat_url(url):
    """
    Removes dynamic tracking parameters from WeChat URLs for reliable deduplication.
    Keeps only __biz, mid, idx, and sn.
    """
    if "/s/" in url and "?" not in url:
        return url # Already clean format
        
    parsed = urlparse(url)
    if "mp.weixin.qq.com" not in parsed.netloc:
        return url
        
    qs = parse_qs(parsed.query)
    clean_params = {}
    for key in ['__biz', 'mid', 'idx', 'sn']:
        if key in qs:
            clean_params[key] = qs[key][0]
            
    if not clean_params:
        return url
        
    # Reconstruct with only essential params
    from urllib.parse import urlencode
    new_query = urlencode(clean_params)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', new_query, ''))

async def download_image(url):
    if not url: return None
    try:
        filename = hashlib.md5(url.encode()).hexdigest() + '.jpg'
        filepath = os.path.join(MEDIA_DIR, filename)
        if os.path.exists(filepath): return filename
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            async with aiofiles.open(filepath, mode='wb') as f:
                await f.write(response.content)
            return filename
    except: pass
    return None

async def mirror_assets(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('data-src') or img.get('src')
        if src:
            local = await download_image(src)
            if local:
                img['src'] = f"/media/{local}"
                if img.get('data-src'): del img['data-src']
                img['style'] = "max-width: 100%; height: auto;" 
    return str(soup)

async def fetch_full_content(page, url):
    """Tiered Extraction: Direct -> WeRead Proxy Fallback."""
    try:
        # 1. Try Direct
        await add_system_log("DEBUG", "Fetch", f"Trying direct: {url[:100]}...")
        await asyncio.sleep(random.uniform(1, 2))
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        content = await page.content()
        if "去验证" in content or "环境异常" in content or "antispider" in content:
            await add_system_log("WARNING", "Fetch", "Directly blocked. Using WeRead Proxy.")
            # 2. Fallback to Proxy
            proxy_url = f"https://weread.qq.com/wrpage/mp/index.html?link={url}"
            await page.goto(proxy_url, wait_until="networkidle", timeout=30000)
            
        await page.evaluate("window.scrollBy(0, document.body.scrollHeight / 2)")
        await asyncio.sleep(0.5)
        html = await page.content()
        doc = Document(html)
        title = doc.title()
        
        if title == "搜狗搜索" or not title:
            return None, "Invalid title (extraction failed)"
            
        return {"title": title, "content": await mirror_assets(doc.summary())}, None
    except Exception as e:
        return None, str(e)

async def extract_account_info(url):
    """Simple ID extraction from a link."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        try:
            await page.goto(url, wait_until="networkidle")
            info = await page.evaluate('''() => {
                const biz = window.biz || (window.cgiData && window.cgiData.biz) || "";
                const nickname = window.nickname || (window.cgiData && window.cgiData.nickname) || 
                                document.querySelector('#js_name')?.innerText.trim() || "";
                return { biz, nickname };
            }''')
            if info['biz']:
                await browser.close()
                return {"id": info['biz'], "name": info['nickname'] or "Unknown"}, None
        except: pass
        await browser.close()
        return None, "ID extraction failed"

async def check_session_validity():
    if not os.path.exists(PROFILE_DIR): return False, "No profile"
    return True, "Profile exists"

async def scrape_wechat():
    """Simplified Scraper with strict URL-based deduplication."""
    await add_system_log("INFO", "Scraper", "Sync cycle started.")
    settings = await get_settings()
    
    async with async_playwright() as p:
        browser_context = None
        try:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                headless=True,
                user_agent=settings.get("user_agent")
            )
            page = browser_context.pages[0]
            await Stealth().apply_stealth_async(page)

            conn = await get_db_async()
            async with conn.execute("SELECT id, name FROM accounts") as cursor:
                db_accounts = await cursor.fetchall()
            
            for db_acc in db_accounts:
                name, target_biz = db_acc['name'], db_acc['id']
                await add_system_log("INFO", "Scraper", f"Targeting: {name}")
                
                # Discovery: Sogou Articles
                try:
                    await page.goto(f"https://weixin.sogou.com/weixin?type=2&query={name}", wait_until="networkidle")
                    urls = await page.evaluate('''() => Array.from(document.querySelectorAll('.news-list li h3 a')).map(a => a.href)''')
                except: urls = []

                if urls:
                    new_count = 0
                    for url in urls[:10]: # Increased to 10 for better coverage
                        # Resolve and Deduplicate
                        try:
                            await page.goto(url, wait_until="networkidle")
                            real_url = normalize_wechat_url(page.url)
                            
                            if "mp.weixin.qq.com" not in real_url: continue
                            
                            # Deduplicate by normalized URL
                            async with conn.execute("SELECT 1 FROM articles WHERE url = ?", (real_url,)) as cur:
                                if await cur.fetchone(): continue
                            
                            # Check by Title + Account ID for extra safety
                            # (Wait for fetch to get title)
                            
                            data, err = await fetch_full_content(page, real_url)
                            if data:
                                # Final duplicate check by title to handle different URL formats
                                async with conn.execute("SELECT 1 FROM articles WHERE title = ? AND account_id = ?", (data['title'], target_biz)) as cur:
                                    if await cur.fetchone():
                                        # Update URL if it's the same title but a newer link
                                        await conn.execute("UPDATE articles SET url = ? WHERE title = ? AND account_id = ?", (real_url, data['title'], target_biz))
                                        continue

                                art_id = str(uuid.uuid4())
                                await conn.execute('''INSERT INTO articles (id, account_id, title, url, content, pub_date, fetch_date)
                                                   VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                                                   (art_id, target_biz, data['title'], real_url, data['content'], datetime.datetime.now(), datetime.datetime.now()))
                                await conn.commit()
                                new_count += 1
                        except: continue
                    
                    await conn.execute("UPDATE accounts SET last_sync = ?, last_status = 'success', article_count = (SELECT COUNT(*) FROM articles WHERE account_id = ?) WHERE id = ?", (datetime.datetime.now(), target_biz, target_biz))
                    await add_system_log("INFO", "Scraper", f"Synced '{name}' (+{new_count} articles).")
                    await conn.commit()
                else:
                    await add_system_log("WARNING", "Scraper", f"[{name}] No articles found on discovery.")

            await conn.close()
        except Exception as e:
            await add_system_log("ERROR", "Scraper", f"Fatal error: {e}")
        finally:
            if browser_context: await browser_context.close()
    await add_system_log("INFO", "Scraper", "Sync cycle complete.")

def start_scheduler():
    import sqlite3
    from database import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(scrape_wechat, 'interval', hours=int(settings.get("fetch_interval_hours", 6)), 
                      jitter=int(settings.get("fetch_random_jitter_minutes", 30))*60, id='wechat_scraper', max_instances=1, coalesce=True)
    scheduler.start()
    return scheduler

if __name__ == "__main__":
    asyncio.run(scrape_wechat())
