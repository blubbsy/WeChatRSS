"""
Translation module for WeChatRSS.
Supports DeepL (with HTML tag preservation) as primary, Google Translate API v2
as secondary fallback, and LibreTranslate as a last resort fallback.
Includes automated availability checks, health status updates, and
background translation tasks for failed/pending articles.
"""

import os
import logging
import asyncio
import requests
import datetime
from database import get_db_async

logger = logging.getLogger(__name__)

# Provider status/health cache.
PROVIDER_STATUS = {
    "deepl": {"configured": False, "status": "unknown", "error": None, "limit_hit": False},
    "google": {"configured": False, "status": "unknown", "error": None, "limit_hit": False},
    "libretranslate": {"configured": False, "status": "unknown", "error": None, "limit_hit": False}
}

async def log_system_message(level: str, module: str, message: str):
    """Helper to log messages to the DB system log asynchronously."""
    try:
        from scraper import add_system_log
        await add_system_log(level, module, message)
    except Exception:
        logger.info(f"[{module}] {message}")

def is_provider_configured(provider: str) -> bool:
    """Check if the credentials or URL for a provider are configured in the environment."""
    if provider == "deepl":
        return bool(os.getenv("DEEPL_API_KEY"))
    elif provider == "google":
        return bool(os.getenv("GOOGLE_TRANSLATE_API_KEY"))
    elif provider == "libretranslate":
        return bool(os.getenv("LIBRETRANSLATE_API_URL"))
    return False

def check_deepl_availability() -> bool:
    key = os.getenv("DEEPL_API_KEY")
    PROVIDER_STATUS["deepl"]["configured"] = bool(key)
    if not key:
        PROVIDER_STATUS["deepl"]["status"] = "not_configured"
        PROVIDER_STATUS["deepl"]["error"] = None
        PROVIDER_STATUS["deepl"]["limit_hit"] = False
        return False
        
    url = "https://api-free.deepl.com/v2/usage" if key.endswith(":fx") else "https://api.deepl.com/v2/usage"
    try:
        res = requests.get(url, headers={"Authorization": f"DeepL-Auth-Key {key}"}, timeout=5)
        if res.status_code == 200:
            PROVIDER_STATUS["deepl"]["status"] = "healthy"
            PROVIDER_STATUS["deepl"]["error"] = None
            PROVIDER_STATUS["deepl"]["limit_hit"] = False
            return True
        elif res.status_code == 456:
            PROVIDER_STATUS["deepl"]["status"] = "error"
            PROVIDER_STATUS["deepl"]["error"] = "Quota limit exceeded (HTTP 456)"
            PROVIDER_STATUS["deepl"]["limit_hit"] = True
            return False
        else:
            PROVIDER_STATUS["deepl"]["status"] = "error"
            PROVIDER_STATUS["deepl"]["error"] = f"HTTP Error {res.status_code}: {res.text[:150]}"
            PROVIDER_STATUS["deepl"]["limit_hit"] = False
            return False
    except Exception as e:
        PROVIDER_STATUS["deepl"]["status"] = "error"
        PROVIDER_STATUS["deepl"]["error"] = str(e)
        PROVIDER_STATUS["deepl"]["limit_hit"] = False
        return False

def check_google_availability() -> bool:
    key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    PROVIDER_STATUS["google"]["configured"] = bool(key)
    if not key:
        PROVIDER_STATUS["google"]["status"] = "not_configured"
        PROVIDER_STATUS["google"]["error"] = None
        PROVIDER_STATUS["google"]["limit_hit"] = False
        return False
        
    url = f"https://translation.googleapis.com/language/translate/v2/languages?key={key}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            PROVIDER_STATUS["google"]["status"] = "healthy"
            PROVIDER_STATUS["google"]["error"] = None
            PROVIDER_STATUS["google"]["limit_hit"] = False
            return True
        elif res.status_code in [403, 429] and ("limit" in res.text.lower() or "quota" in res.text.lower()):
            PROVIDER_STATUS["google"]["status"] = "error"
            PROVIDER_STATUS["google"]["error"] = f"Quota limit hit (HTTP {res.status_code})"
            PROVIDER_STATUS["google"]["limit_hit"] = True
            return False
        else:
            PROVIDER_STATUS["google"]["status"] = "error"
            PROVIDER_STATUS["google"]["error"] = f"HTTP Error {res.status_code}: {res.text[:150]}"
            PROVIDER_STATUS["google"]["limit_hit"] = False
            return False
    except Exception as e:
        PROVIDER_STATUS["google"]["status"] = "error"
        PROVIDER_STATUS["google"]["error"] = str(e)
        PROVIDER_STATUS["google"]["limit_hit"] = False
        return False

def check_libretranslate_availability() -> bool:
    base_url = os.getenv("LIBRETRANSLATE_API_URL", "http://localhost:5000").rstrip("/")
    configured = bool(os.getenv("LIBRETRANSLATE_API_URL"))
    PROVIDER_STATUS["libretranslate"]["configured"] = configured
    if not configured:
        PROVIDER_STATUS["libretranslate"]["status"] = "not_configured"
        PROVIDER_STATUS["libretranslate"]["error"] = None
        PROVIDER_STATUS["libretranslate"]["limit_hit"] = False
        return False
        
    url = f"{base_url}/languages"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            PROVIDER_STATUS["libretranslate"]["status"] = "healthy"
            PROVIDER_STATUS["libretranslate"]["error"] = None
            PROVIDER_STATUS["libretranslate"]["limit_hit"] = False
            return True
        elif res.status_code == 429:
            PROVIDER_STATUS["libretranslate"]["status"] = "error"
            PROVIDER_STATUS["libretranslate"]["error"] = "Rate limit hit (HTTP 429)"
            PROVIDER_STATUS["libretranslate"]["limit_hit"] = True
            return False
        else:
            PROVIDER_STATUS["libretranslate"]["status"] = "error"
            PROVIDER_STATUS["libretranslate"]["error"] = f"HTTP Error {res.status_code}: {res.text[:150]}"
            PROVIDER_STATUS["libretranslate"]["limit_hit"] = False
            return False
    except Exception as e:
        PROVIDER_STATUS["libretranslate"]["status"] = "error"
        PROVIDER_STATUS["libretranslate"]["error"] = str(e)
        PROVIDER_STATUS["libretranslate"]["limit_hit"] = False
        return False

async def check_all_providers():
    """Verify health and credentials of all configured translation providers."""
    for provider in ["deepl", "google", "libretranslate"]:
        if is_provider_configured(provider):
            if provider == "deepl":
                await asyncio.to_thread(check_deepl_availability)
            elif provider == "google":
                await asyncio.to_thread(check_google_availability)
            elif provider == "libretranslate":
                await asyncio.to_thread(check_libretranslate_availability)
        else:
            PROVIDER_STATUS[provider]["configured"] = False
            PROVIDER_STATUS[provider]["status"] = "not_configured"
            PROVIDER_STATUS[provider]["error"] = None
            PROVIDER_STATUS[provider]["limit_hit"] = False

def _translate_deepl(text: str, target_lang: str) -> str:
    key = os.getenv("DEEPL_API_KEY")
    if not key:
        raise ValueError("DeepL API key not configured")
    url = "https://api-free.deepl.com/v2/translate" if key.endswith(":fx") else "https://api.deepl.com/v2/translate"
    
    headers = {
        "Authorization": f"DeepL-Auth-Key {key}",
        "Content-Type": "application/json"
    }
    data = {
        "text": [text],
        "target_lang": target_lang.upper(),
        "tag_handling": "html",
        "split_sentences": "nonewlines"
    }
    try:
        res = requests.post(url, json=data, headers=headers, timeout=20)
        if res.status_code == 456:
            PROVIDER_STATUS["deepl"]["status"] = "error"
            PROVIDER_STATUS["deepl"]["error"] = "Quota limit hit (HTTP 456)"
            PROVIDER_STATUS["deepl"]["limit_hit"] = True
        res.raise_for_status()
        result = res.json()
        
        # Mark healthy again if it worked
        PROVIDER_STATUS["deepl"]["status"] = "healthy"
        PROVIDER_STATUS["deepl"]["limit_hit"] = False
        PROVIDER_STATUS["deepl"]["error"] = None
        return result["translations"][0]["text"]
    except Exception as e:
        if not PROVIDER_STATUS["deepl"]["limit_hit"]:
            PROVIDER_STATUS["deepl"]["status"] = "error"
            PROVIDER_STATUS["deepl"]["error"] = str(e)
        raise e

def _translate_google(text: str, target_lang: str) -> str:
    key = os.getenv("GOOGLE_TRANSLATE_API_KEY")
    if not key:
        raise ValueError("Google Translate API key not configured")
    url = "https://translation.googleapis.com/language/translate/v2"
    
    data = {
        "q": [text],
        "target": target_lang.lower(),
        "format": "html"
    }
    try:
        res = requests.post(url, params={"key": key}, json=data, timeout=20)
        if res.status_code in [403, 429] and ("limit" in res.text.lower() or "quota" in res.text.lower()):
            PROVIDER_STATUS["google"]["status"] = "error"
            PROVIDER_STATUS["google"]["error"] = f"Quota limit hit (HTTP {res.status_code})"
            PROVIDER_STATUS["google"]["limit_hit"] = True
        res.raise_for_status()
        result = res.json()
        
        PROVIDER_STATUS["google"]["status"] = "healthy"
        PROVIDER_STATUS["google"]["limit_hit"] = False
        PROVIDER_STATUS["google"]["error"] = None
        return result["data"]["translations"][0]["translatedText"]
    except Exception as e:
        if not PROVIDER_STATUS["google"]["limit_hit"]:
            PROVIDER_STATUS["google"]["status"] = "error"
            PROVIDER_STATUS["google"]["error"] = str(e)
        raise e

def _translate_libretranslate(text: str, target_lang: str) -> str:
    base_url = os.getenv("LIBRETRANSLATE_API_URL", "http://localhost:5000").rstrip("/")
    url = f"{base_url}/translate"
    
    data = {
        "q": text,
        "source": "auto",
        "target": target_lang.lower(),
        "format": "html"
    }
    key = os.getenv("LIBRETRANSLATE_API_KEY")
    if key:
        data["api_key"] = key
        
    try:
        res = requests.post(url, json=data, timeout=20)
        if res.status_code == 429:
            PROVIDER_STATUS["libretranslate"]["status"] = "error"
            PROVIDER_STATUS["libretranslate"]["error"] = "Rate limit hit (HTTP 429)"
            PROVIDER_STATUS["libretranslate"]["limit_hit"] = True
        res.raise_for_status()
        result = res.json()
        
        PROVIDER_STATUS["libretranslate"]["status"] = "healthy"
        PROVIDER_STATUS["libretranslate"]["limit_hit"] = False
        PROVIDER_STATUS["libretranslate"]["error"] = None
        return result["translatedText"]
    except Exception as e:
        if not PROVIDER_STATUS["libretranslate"]["limit_hit"]:
            PROVIDER_STATUS["libretranslate"]["status"] = "error"
            PROVIDER_STATUS["libretranslate"]["error"] = str(e)
        raise e

async def translate_html(html_content: str, target_lang: str = None) -> str:
    """
    Translates HTML content, falling back from DeepL -> Google -> LibreTranslate.
    Only attempts translation if providers are configured and marked healthy.
    """
    if not html_content or not html_content.strip():
        return html_content

    if not target_lang:
        target_lang = os.getenv("TRANSLATION_TARGET_LANG", "en")

    providers = ["deepl", "google", "libretranslate"]
    last_err = None
    for provider in providers:
        if is_provider_configured(provider) and PROVIDER_STATUS[provider]["status"] == "healthy":
            try:
                if provider == "deepl":
                    translated = await asyncio.to_thread(_translate_deepl, html_content, target_lang)
                elif provider == "google":
                    translated = await asyncio.to_thread(_translate_google, html_content, target_lang)
                elif provider == "libretranslate":
                    translated = await asyncio.to_thread(_translate_libretranslate, html_content, target_lang)
                
                return translated
            except Exception as e:
                logger.warning(f"Translation with {provider} failed: {e}. Trying fallback...")
                last_err = e
                # Status and error are updated inside the specific provider translation method
                
    # If a translator is active but they all failed:
    if is_any_translator_active():
        raise last_err if last_err else Exception("All configured translation providers failed.")
        
    return html_content

def is_any_translator_active() -> bool:
    """Returns True if at least one translator is configured and verified healthy."""
    return any(is_provider_configured(p) and PROVIDER_STATUS[p]["status"] == "healthy" for p in ["deepl", "google", "libretranslate"])

# Background worker lock
_TRANSLATION_LOCK = asyncio.Lock()

async def translate_pending_articles():
    """
    Looks for articles where translation_status = 'failed' or 'pending',
    translates them using the active providers, and saves the translations to the database.
    """
    if _TRANSLATION_LOCK.locked():
        logger.info("Translation background job already running. Skipping trigger.")
        return
        
    async with _TRANSLATION_LOCK:
        await check_all_providers()
        if not is_any_translator_active():
            await log_system_message("WARNING", "Translation", "No translation services are currently configured or online. Skipping retry.")
            return

        # Load failed or pending articles
        async with get_db_async() as conn:
            async with conn.execute(
                """
                SELECT a.id, a.title, a.content, acc.name as account_name
                FROM articles a
                JOIN accounts acc ON a.account_id = acc.id
                WHERE a.translation_status IN ('failed', 'pending')
                ORDER BY a.pub_date DESC
                LIMIT 50
                """
            ) as cursor:
                articles = await cursor.fetchall()

            if not articles:
                logger.debug("No pending or failed translations found.")
                return

            await log_system_message("INFO", "Translation", f"Found {len(articles)} pending/failed translations. Starting background batch...")
            
            success_count = 0
            for article in articles:
                art_id = article["id"]
                title = article["title"]
                content = article["content"]
                account_name = article["account_name"]
                
                try:
                    translated_title = await translate_html(title)
                    translated_content = await translate_html(content)
                    
                    await conn.execute(
                        """
                        UPDATE articles 
                        SET translated_title = ?, 
                            translated_content = ?, 
                            translation_status = 'success', 
                            translation_error = NULL 
                        WHERE id = ?
                        """,
                        (translated_title, translated_content, art_id)
                    )
                    await conn.commit()
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to translate article '{title[:45]}' during retry: {e}")
                    await conn.execute(
                        "UPDATE articles SET translation_status = 'failed', translation_error = ? WHERE id = ?",
                        (str(e), art_id)
                    )
                    await conn.commit()
                    
            await log_system_message("INFO", "Translation", f"Background translation batch complete: successfully translated {success_count}/{len(articles)} articles.")
