"""
Scraper module for WeChatRSS.
Uses Sogou for discovery and a tiered extraction model (Direct -> WeRead).
Includes URL normalization and strict deduplication.
"""

import asyncio
import os
import logging
import datetime
import uuid
import random
import hashlib
import requests
import aiofiles
from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from readability import Document
from database import get_db_async
from translator import translate_html, is_any_translator_active

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROFILE_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "data", "profiles", "wechat_rss_profile")
)
MEDIA_DIR = os.path.join(BASE_DIR, "data", "media")
DEBUG_DIR = os.path.join(BASE_DIR, "data", "debug")
SOGOU_STATE_PATH = os.path.join(BASE_DIR, "data", "sogou_state.json")

# Concurrency limit for image downloads
_IMAGE_SEMAPHORE = asyncio.Semaphore(5)

# Log retention period
_LOG_RETENTION_DAYS = 7

os.makedirs(MEDIA_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)


async def add_system_log(level, module, message):
    """Insert a system log entry and prune old entries periodically."""
    try:
        async with get_db_async() as conn:
            await conn.execute(
                "INSERT INTO system_logs (level, module, message) VALUES (?, ?, ?)",
                (level, module, message),
            )
            # Prune logs older than retention period (low overhead with index)
            cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
                days=_LOG_RETENTION_DAYS
            )
            await conn.execute(
                "DELETE FROM system_logs WHERE timestamp < ?", (cutoff.isoformat(),)
            )
            await conn.commit()
    except Exception as e:
        logger.warning(f"Failed to write system log: {e}")


async def get_settings():
    async with get_db_async() as conn:
        async with conn.execute("SELECT key, value FROM settings") as cursor:
            rows = await cursor.fetchall()
            return {row["key"]: row["value"] for row in rows}


async def _load_accounts(account_id=None):
    async with get_db_async() as conn:
        if account_id:
            async with conn.execute(
                "SELECT id, name FROM accounts WHERE id = ?", (account_id,)
            ) as cursor:
                return await cursor.fetchall()

        async with conn.execute("SELECT id, name FROM accounts") as cursor:
            return await cursor.fetchall()


def normalize_wechat_url(url):
    """
    Removes dynamic tracking parameters from WeChat URLs for reliable deduplication.
    Keeps only __biz, mid, idx, and sn.
    """
    if "/s/" in url and "?" not in url:
        return url  # Already clean format

    parsed = urlparse(url)
    if "mp.weixin.qq.com" not in parsed.netloc:
        return url

    qs = parse_qs(parsed.query)
    clean_params = {}
    for key in ["__biz", "mid", "idx", "sn"]:
        if key in qs:
            clean_params[key] = qs[key][0]

    if not clean_params:
        return url

    # Reconstruct with only essential params
    new_query = urlencode(clean_params)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", new_query, ""))


async def _download_image_safe(url):
    """Download a single image with semaphore-limited concurrency, offloaded to thread pool."""
    if not url:
        return url, None
    try:
        filename = hashlib.md5(url.encode()).hexdigest() + ".jpg"
        filepath = os.path.join(MEDIA_DIR, filename)
        if os.path.exists(filepath):
            return url, filename

        headers = {"User-Agent": "Mozilla/5.0"}
        # Offload blocking requests.get to thread pool to avoid blocking the event loop
        async with _IMAGE_SEMAPHORE:
            response = await asyncio.to_thread(
                requests.get, url, headers=headers, timeout=10
            )
        if response.status_code == 200:
            async with aiofiles.open(filepath, mode="wb") as f:
                await f.write(response.content)
            return url, filename
    except Exception as e:
        logger.debug(f"Image download failed for {url[:80]}: {e}")
    return url, None


async def download_image(url):
    """Download a single image (legacy wrapper)."""
    _, filename = await _download_image_safe(url)
    return filename


async def mirror_assets(html_content, account_name=None):
    """Download and mirror all images in HTML content, in parallel."""
    soup = BeautifulSoup(html_content, "html.parser")
    img_tags = soup.find_all("img")

    # Collect all image URLs
    url_map = {}
    for img in img_tags:
        src = img.get("data-src") or img.get("src")
        if src:
            url_map[id(img)] = (img, src)

    if not url_map:
        return str(soup)

    if account_name:
        await add_system_log("DEBUG", "Scraper", f"[{account_name}] Found {len(url_map)} image assets in article. Downloading in parallel...")

    # Download all images in parallel (bounded by semaphore)
    tasks = [_download_image_safe(src) for _, src in url_map.values()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build result lookup: original_url -> local_filename
    downloaded = {}
    for result in results:
        if isinstance(result, Exception):
            continue
        orig_url, local_filename = result
        if local_filename:
            downloaded[orig_url] = local_filename

    if account_name:
        await add_system_log("DEBUG", "Scraper", f"[{account_name}] Cached {len(downloaded)}/{len(url_map)} images locally.")

    # Apply results to soup
    for img, src in url_map.values():
        if src in downloaded:
            img["src"] = f"/media/{downloaded[src]}"
            if img.get("data-src"):
                del img["data-src"]
            img["style"] = "max-width: 100%; height: auto;"

    return str(soup)


async def _process_account(page, account_name, account_id):
    """Process a single account: discover and fetch articles. Uses its own DB connection."""
    await add_system_log("INFO", "Scraper", f"[{account_name}] Starting sync cycle.")

    # Step 1: Update status to 'fetching' and check if initial sync
    is_initial = True
    try:
        async with get_db_async() as conn:
            async with conn.execute(
                "SELECT last_sync FROM accounts WHERE id = ?", (account_id,)
            ) as cur:
                row = await cur.fetchone()
                if row and row["last_sync"] is not None:
                    is_initial = False
            
            await conn.execute(
                "UPDATE accounts SET last_status = 'fetching', error_msg = NULL, sync_progress_current = 0, sync_progress_total = 0 WHERE id = ?",
                (account_id,),
            )
            await conn.commit()
    except Exception as db_err:
        logger.warning(f"Failed to update pre-fetch status for {account_name}: {db_err}")

    urls = []
    try:
        if is_initial:
            await add_system_log(
                "INFO", "Scraper", f"[{account_name}] Initial sync: performing multi-page historical backup..."
            )
            # Fetch up to 5 pages on Sogou search to aggregate historical articles
            for page_num in range(1, 6):
                # Check if sync has been stopped by user
                async with get_db_async() as conn:
                    async with conn.execute("SELECT last_status FROM accounts WHERE id = ?", (account_id,)) as cur:
                        row = await cur.fetchone()
                        if row and row["last_status"] != "fetching":
                            await add_system_log("WARNING", "Scraper", f"[{account_name}] Sync stopped by user request during discovery.")
                            return 0
                try:
                    await add_system_log(
                        "INFO", "Scraper", f"[{account_name}] Querying page {page_num} of Sogou search for history..."
                    )
                    await page.goto(
                        f"https://weixin.sogou.com/weixin?type=2&query={account_name}&page={page_num}",
                        wait_until="networkidle",
                    )
                    page_urls = await page.evaluate(
                        """() => Array.from(document.querySelectorAll('.news-list li h3 a')).map(a => a.href)"""
                    )
                    if not page_urls:
                        await add_system_log("DEBUG", "Scraper", f"[{account_name}] No articles returned on page {page_num}. Terminating history query.")
                        break
                    
                    await add_system_log("DEBUG", "Scraper", f"[{account_name}] Page {page_num} returned {len(page_urls)} articles.")
                    for u in page_urls:
                        if u not in urls:
                            urls.append(u)
                    
                    # Prevent rapid page hits to avoid Sogou CAPTCHAs
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                except Exception as page_err:
                    await add_system_log(
                        "WARNING", "Scraper", f"[{account_name}] Failed fetching page {page_num}: {page_err}"
                    )
                    break
        else:
            # Incremental sync: just page 1
            await page.goto(
                f"https://weixin.sogou.com/weixin?type=2&query={account_name}",
                wait_until="networkidle",
            )
            urls = await page.evaluate(
                """() => Array.from(document.querySelectorAll('.news-list li h3 a')).map(a => a.href)"""
            )

        if not urls:
            await add_system_log(
                "WARNING", "Scraper", f"[{account_name}] No articles found on discovery."
            )
            async with get_db_async() as conn:
                await conn.execute(
                    "UPDATE accounts SET last_sync = ?, last_status = 'success', error_msg = NULL, sync_progress_current = 0, sync_progress_total = 0 WHERE id = ?",
                    (datetime.datetime.now(datetime.timezone.utc).isoformat(), account_id),
                )
                await conn.commit()
            return 0

        # Process found URLs: up to 30 for initial sync (as a backup), up to 10 for incremental
        max_to_process = 30 if is_initial else 10
        urls_to_process = urls[:max_to_process]
        total_urls = len(urls_to_process)

        await add_system_log("INFO", "Scraper", f"[{account_name}] Discovered {len(urls)} total articles. Processing limit set to {total_urls} URLs.")

        # Update progress total in DB
        async with get_db_async() as conn:
            await conn.execute(
                "UPDATE accounts SET sync_progress_total = ?, sync_progress_current = 0 WHERE id = ?",
                (total_urls, account_id),
            )
            await conn.commit()

        new_count = 0
        async with get_db_async() as conn:
            for index, url in enumerate(urls_to_process):
                # Check if sync has been stopped by user
                async with conn.execute("SELECT last_status FROM accounts WHERE id = ?", (account_id,)) as cur:
                    row = await cur.fetchone()
                    if row and row["last_status"] != "fetching":
                        await add_system_log("WARNING", "Scraper", f"[{account_name}] Sync stopped by user request.")
                        # Also update the article count and commit since we fetched some new articles before stopping
                        await conn.execute(
                            "UPDATE accounts SET article_count = (SELECT COUNT(*) FROM articles WHERE account_id = ?) WHERE id = ?",
                            (account_id, account_id),
                        )
                        await conn.commit()
                        return new_count

                # Update progress current in DB
                await conn.execute(
                    "UPDATE accounts SET sync_progress_current = ? WHERE id = ?",
                    (index + 1, account_id),
                )
                await conn.commit()

                try:
                    await add_system_log("INFO", "Scraper", f"[{account_name}] Processing article {index+1}/{total_urls}: {url[:80]}...")
                    await page.goto(url, wait_until="networkidle")
                    real_url = normalize_wechat_url(page.url)

                    if "mp.weixin.qq.com" not in real_url:
                        await add_system_log("WARNING", "Scraper", f"[{account_name}] Skipping non-WeChat URL: {real_url[:100]}")
                        continue

                    async with conn.execute(
                        "SELECT 1 FROM articles WHERE url = ?", (real_url,)
                    ) as cur:
                        if await cur.fetchone():
                            await add_system_log("DEBUG", "Scraper", f"[{account_name}] Already in database (URL match). Skipping.")
                            continue

                    data, err = await fetch_full_content(page, real_url, account_name=account_name)
                    if not data:
                        await add_system_log("WARNING", "Scraper", f"[{account_name}] Failed to extract content: {err}")
                        continue

                    async with conn.execute(
                        "SELECT 1 FROM articles WHERE title = ? AND account_id = ?",
                        (data["title"], account_id),
                    ) as cur:
                        if await cur.fetchone():
                            await add_system_log("DEBUG", "Scraper", f"[{account_name}] Updating existing article URL for: '{data['title'][:60]}'")
                            await conn.execute(
                                "UPDATE articles SET url = ? WHERE title = ? AND account_id = ?",
                                (real_url, data["title"], account_id),
                            )
                            await conn.commit()
                            continue

                    # Run translation if any translator is configured and active
                    translated_title = None
                    translated_content = None
                    translation_status = 'pending'
                    translation_error = None
                    if is_any_translator_active():
                        try:
                            await add_system_log("INFO", "Translation", f"[{account_name}] Translating article: '{data['title'][:40]}'...")
                            translated_title = await translate_html(data["title"])
                            translated_content = await translate_html(data["content"])
                            translation_status = 'success'
                        except Exception as tr_err:
                            translation_status = 'failed'
                            translation_error = str(tr_err)
                            await add_system_log("WARNING", "Translation", f"[{account_name}] Translation failed: {tr_err}")
                    else:
                        translation_status = 'skipped'

                    art_id = str(uuid.uuid4())
                    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    await conn.execute(
                        """INSERT INTO articles (id, account_id, title, url, content, pub_date, fetch_date, translated_title, translated_content, translation_status, translation_error)
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            art_id,
                            account_id,
                            data["title"],
                            real_url,
                            data["content"],
                            now,
                            now,
                            translated_title,
                            translated_content,
                            translation_status,
                            translation_error,
                        ),
                    )
                    await conn.commit()
                    await add_system_log("INFO", "Scraper", f"[{account_name}] Successfully archived: '{data['title'][:60]}'")
                    new_count += 1
                except Exception as e:
                    logger.warning(f"Error processing article {url[:80]}: {e}")
                    await add_system_log("WARNING", "Scraper", f"[{account_name}] Error processing article: {e}")
                    continue

            # Commit all changes and set healthy status
            await conn.execute(
                "UPDATE accounts SET last_sync = ?, last_status = 'success', error_msg = NULL, sync_progress_current = 0, sync_progress_total = 0, article_count = (SELECT COUNT(*) FROM articles WHERE account_id = ?) WHERE id = ?",
                (datetime.datetime.now(datetime.timezone.utc).isoformat(), account_id, account_id),
            )
            await conn.commit()

        await add_system_log(
            "INFO", "Scraper", f"Synced '{account_name}' (+{new_count} articles)."
        )
        return new_count

    except Exception as e:
        logger.exception(f"Error processing account {account_name}: {e}")
        await add_system_log(
            "ERROR", "Scraper", f"Failed processing '{account_name}': {e}"
        )
        try:
            async with get_db_async() as conn:
                await conn.execute(
                    "UPDATE accounts SET last_status = 'failed', error_msg = ?, sync_progress_current = 0, sync_progress_total = 0 WHERE id = ?",
                    (str(e), account_id),
                )
                await conn.commit()
        except Exception as db_err2:
            logger.warning(f"Failed to write error status for {account_name}: {db_err2}")
        return 0


async def fetch_full_content(page, url, account_name=None):
    """Tiered Extraction: Direct -> WeRead Proxy Fallback."""
    try:
        # 1. Try Direct
        if account_name:
            await add_system_log("DEBUG", "Scraper", f"[{account_name}] Direct fetching: {url[:60]}...")
        else:
            await add_system_log("DEBUG", "Fetch", f"Trying direct: {url[:100]}...")

        await asyncio.sleep(random.uniform(1, 2))
        await page.goto(url, wait_until="networkidle", timeout=30000)

        content = await page.content()
        if "去验证" in content or "环境异常" in content or "antispider" in content:
            if account_name:
                await add_system_log("WARNING", "Scraper", f"[{account_name}] Direct access blocked by anti-bot. Retrying via WeRead proxy viewer...")
            else:
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

        mirrored_content = await mirror_assets(doc.summary(), account_name=account_name)
        return {"title": title, "content": mirrored_content}, None
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
            info = await page.evaluate("""() => {
                const biz = window.biz || (window.cgiData && window.cgiData.biz) || "";
                const nickname = window.nickname || (window.cgiData && window.cgiData.nickname) || 
                                document.querySelector('#js_name')?.innerText.trim() || "";
                return { biz, nickname };
            }""")
            if info["biz"]:
                await browser.close()
                return {"id": info["biz"], "name": info["nickname"] or "Unknown"}, None
        except Exception as e:
            logger.warning(f"Account info extraction failed for {url}: {e}")
        await browser.close()
        return None, "ID extraction failed"


async def check_session_validity():
    if not os.path.exists(PROFILE_DIR):
        return False, "No profile"
    return True, "Profile exists"


async def scrape_wechat():
    """Simplified Scraper with strict URL-based deduplication."""
    await scrape_accounts()


async def scrape_accounts(account_id=None):
    """Scrape all accounts or a single account."""
    await add_system_log("INFO", "Scraper", "Sync cycle started.")
    settings = await get_settings()

    browser_context = None
    try:
        async with async_playwright() as p:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                headless=True,
                user_agent=settings.get("user_agent"),
            )
            page = browser_context.pages[0]
            await Stealth().apply_stealth_async(page)

            accounts = await _load_accounts(account_id)
            for account in accounts:
                try:
                    await _process_account(page, account["name"], account["id"])
                except Exception as e:
                    await add_system_log(
                        "ERROR", "Scraper",
                        f"Failed processing account '{account['name']}': {e}"
                    )

            await browser_context.close()
            browser_context = None  # Prevent double-close in finally
    except Exception as e:
        await add_system_log("ERROR", "Scraper", f"Fatal error: {e}")
        logger.exception(f"Scraper fatal error: {e}")
    finally:
        if browser_context:
            try:
                await browser_context.close()
            except Exception:
                pass

    await add_system_log("INFO", "Scraper", "Sync cycle complete.")


async def scrape_account(account_id):
    """Scrape a single account by its WeChat biz id."""
    await scrape_accounts(account_id=account_id)


def start_scheduler():
    from runtime import start_scraper_scheduler

    return start_scraper_scheduler()


if __name__ == "__main__":
    asyncio.run(scrape_wechat())
