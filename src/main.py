import os
import sys

def load_env():
    """Loads variables from .env file into os.environ if it exists."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        os.environ[key.strip()] = val.strip().strip('"').strip("'")
        except Exception as e:
            print(f"Failed to load .env file: {e}")

load_env()

from fastapi import (
    FastAPI,
    Response,
    Request,
    Form,
    Depends,
    HTTPException,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from feedgen.feed import FeedGenerator
from database import get_db_async, init_db, pwd_context, SESSION_TTL_DAYS
from runtime import (
    restart_scraper_scheduler,
    shutdown_scraper_scheduler,
    start_scraper_scheduler,
)
from scraper import (
    get_settings,
    MEDIA_DIR,
    SOGOU_STATE_PATH,
    scrape_wechat,
    scrape_account,
    add_system_log,
)
import logging
import os
import secrets
import uuid
from typing import Optional, Dict
import datetime
import asyncio
from contextlib import asynccontextmanager

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Lifecycle (modern pattern, replaces deprecated on_event) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown hooks."""
    init_db()
    # Reset any active fetching tasks interrupted by a restart
    try:
        async with get_db_async() as conn:
            await conn.execute(
                "UPDATE accounts SET last_status = 'failed', error_msg = 'Interrupted by server restart', sync_progress_current = 0, sync_progress_total = 0 WHERE last_status = 'fetching'"
            )
            await conn.commit()
    except Exception as e:
        logger.error(f"Failed to reset fetching accounts on startup: {e}")

    await add_system_log("INFO", "System", "Server started successfully.")
    
    # Check translation providers availability
    from translator import check_all_providers
    try:
        await check_all_providers()
    except Exception as e:
        logger.error(f"Failed to check translation providers: {e}")

    start_scraper_scheduler()
    yield
    shutdown_scraper_scheduler()


app = FastAPI(
    title="WeChatRSS",
    description="A lightweight WeChat Official Account aggregator and RSS deliverer.",
    lifespan=lifespan,
)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Static and media asset serving
os.makedirs(MEDIA_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

# --- CSRF Configuration ---
CSRF_SECRET = os.getenv("CSRF_SECRET", secrets.token_hex(32))


def get_csrf_token(request: Request):
    """Retrieves or generates a CSRF token for the current session."""
    token = request.cookies.get("csrf_token")
    if not token:
        token = secrets.token_hex(32)
    return token


templates.env.globals["get_csrf_token"] = get_csrf_token

# --- Pydantic Models ---


class AccountCreate(BaseModel):
    """Model for adding a new WeChat Official Account."""

    id: str
    name: str


class UserCreate(BaseModel):
    """Model for creating a new dashboard user."""

    username: str
    password: str
    role: str = "user"


class PasswordUpdate(BaseModel):
    """Model for password changes."""

    new_password: str


class SettingsUpdate(BaseModel):
    """Model for updating system-wide scraper settings."""

    settings: Dict[str, str]


# --- Auth Dependencies ---


async def get_current_user(request: Request):
    """
    Dependency to retrieve the current user from the persistent sessions table.
    Checks session expiry.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_id = auth_header.replace("Bearer ", "")

    if not session_id:
        return None

    try:
        async with get_db_async() as conn:
            now = datetime.datetime.now(datetime.timezone.utc).isoformat()
            query = """
                SELECT users.id, users.username, users.feed_hash, users.role 
                FROM users 
                INNER JOIN sessions ON users.id = sessions.user_id
                WHERE sessions.id = ?
                  AND (sessions.expires_at IS NULL OR sessions.expires_at > ?)
            """
            async with conn.execute(query, (session_id, now)) as cursor:
                user = await cursor.fetchone()
                if user:
                    return dict(user)
                return None
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        return None


async def require_admin(user: Optional[dict] = Depends(get_current_user)):
    """
    Dependency to enforce admin role requirements.
    """
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user


async def require_user(user: Optional[dict] = Depends(get_current_user)):
    """
    Dependency to enforce basic authentication requirements.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def verify_csrf(request: Request):
    """Middleware-like dependency to verify CSRF tokens on state-changing requests."""
    if request.method in ["POST", "DELETE", "PUT"]:
        token_in_cookie = request.cookies.get("csrf_token")
        token_in_request = None

        token_in_request = request.headers.get("X-CSRF-Token")

        if not token_in_request:
            try:
                content_type = request.headers.get("Content-Type", "")
                if (
                    "application/x-www-form-urlencoded" in content_type
                    or "multipart/form-data" in content_type
                ):
                    form_data = await request.form()
                    token_in_request = form_data.get("csrf_token")
            except Exception:
                pass

        if (
            not token_in_request
            or not token_in_cookie
            or token_in_request != token_in_cookie
        ):
            raise HTTPException(
                status_code=403, detail="CSRF token mismatch or missing"
            )


# --- Dashboard & Login ---


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Renders the main dashboard or redirects to login if unauthenticated."""
    if not user:
        response = templates.TemplateResponse(request=request, name="login.html")
    else:
        response = templates.TemplateResponse(
            request=request, name="index.html", context={"user": user}
        )

    if not request.cookies.get("csrf_token"):
        token = get_csrf_token(request)
        # CSRF tokens must be readable by JS for AJAX requests, so httponly=False
        response.set_cookie(
            key="csrf_token", value=token, httponly=False, samesite="lax", path="/"
        )
    return response


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Handles user login and persistent session creation."""
    async with get_db_async() as conn:
        async with conn.execute(
            "SELECT id, username, password_hash, feed_hash, role FROM users WHERE username = ?",
            (username,),
        ) as cursor:
            user = await cursor.fetchone()

        if user and pwd_context.verify(password, user["password_hash"]):
            session_id = secrets.token_hex(32)
            expires_at = (
                datetime.datetime.now(datetime.timezone.utc)
                + datetime.timedelta(days=SESSION_TTL_DAYS)
            ).isoformat()
            await conn.execute(
                "INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)",
                (session_id, user["id"], expires_at),
            )
            await conn.commit()

            response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            response.set_cookie(
                key="session_id",
                value=session_id,
                httponly=True,
                samesite="lax",
                path="/",
                max_age=SESSION_TTL_DAYS * 86400,
            )
            return response

    return RedirectResponse(url="/?error=1", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/logout")
async def logout(request: Request):
    """Clears the user session from the database and cookies."""
    session_id = request.cookies.get("session_id")
    if session_id:
        async with get_db_async() as conn:
            await conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await conn.commit()
    response = RedirectResponse(url="/")
    response.delete_cookie("session_id", path="/")
    return response


# --- Settings Management (Admin Only) ---


@app.get("/settings")
async def list_settings(admin: dict = Depends(require_admin)):
    """Retrieves all system settings asynchronously."""
    async with get_db_async() as conn:
        async with conn.execute("SELECT key, value FROM settings") as cursor:
            rows = await cursor.fetchall()
            return {row["key"]: row["value"] for row in rows}


@app.post("/settings")
async def update_settings(
    data: SettingsUpdate,
    admin: dict = Depends(require_admin),
    _csrf=Depends(verify_csrf),
):
    """Updates settings and restarts the background scheduler to apply them."""
    try:
        async with get_db_async() as conn:
            for key, val in data.settings.items():
                await conn.execute(
                    "UPDATE settings SET value = ? WHERE key = ?", (val, key)
                )
            await conn.commit()

        restart_scraper_scheduler()

        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- User Management (Admin Only) ---


@app.get("/users")
async def list_users(admin: dict = Depends(require_admin)):
    """Lists all registered users."""
    async with get_db_async() as conn:
        async with conn.execute(
            "SELECT id, username, role, feed_hash FROM users"
        ) as cursor:
            users = await cursor.fetchall()
        return [dict(u) for u in users]


@app.post("/users")
async def create_user(
    user_data: UserCreate,
    admin: dict = Depends(require_admin),
    _csrf=Depends(verify_csrf),
):
    """Creates a new user with a unique RSS feed hash."""
    try:
        async with get_db_async() as conn:
            user_id = str(uuid.uuid4())
            pwd_hash = pwd_context.hash(user_data.password)
            feed_hash = secrets.token_hex(16)
            await conn.execute(
                "INSERT INTO users (id, username, password_hash, feed_hash, role) VALUES (?, ?, ?, ?, ?)",
                (user_id, user_data.username, pwd_hash, feed_hash, user_data.role),
            )
            await conn.commit()
            return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: str, admin: dict = Depends(require_admin), _csrf=Depends(verify_csrf)
):
    """Deletes a user and their associated subscriptions, articles, and sessions."""
    if user_id == admin["id"]:
        return {"status": "error", "message": "Cannot delete yourself"}
    async with get_db_async() as conn:
        # Delete articles first (orphan prevention)
        await conn.execute(
            "DELETE FROM articles WHERE account_id IN (SELECT id FROM accounts WHERE user_id = ?)",
            (user_id,),
        )
        await conn.execute("DELETE FROM accounts WHERE user_id = ?", (user_id,))
        await conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        await conn.commit()
    return {"status": "success"}


# --- Profile Management (All Users) ---


@app.post("/profile/password")
async def change_password(
    data: PasswordUpdate, user: dict = Depends(require_user), _csrf=Depends(verify_csrf)
):
    """Allows users to update their own password."""
    async with get_db_async() as conn:
        pwd_hash = pwd_context.hash(data.new_password)
        await conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user["id"])
        )
        await conn.commit()
    return {"status": "success"}


# --- Secure RSS Routes ---


async def generate_feed(feed_hash: str, request: Request, translate: bool = False):
    """
    Generates an RSS XML feed with FULL CONTENT for MS Teams.
    Supports English/target language translation if translate=True.
    """
    async with get_db_async() as conn:
        async with conn.execute(
            "SELECT id, username FROM users WHERE feed_hash = ?", (feed_hash,)
        ) as cursor:
            user = await cursor.fetchone()

        if not user:
            return None

        user_id = user["id"]
        username = user["username"]

        if translate:
            query = """
                SELECT 
                    COALESCE(a.translated_title, a.title) as title, 
                    a.url, 
                    COALESCE(a.translated_content, a.content) as content, 
                    a.pub_date, 
                    acc.name as account_name
                FROM articles a
                JOIN accounts acc ON a.account_id = acc.id
                WHERE acc.user_id = ?
                ORDER BY a.pub_date DESC 
                LIMIT 100
            """
        else:
            query = """
                SELECT a.title, a.url, a.content, a.pub_date, acc.name as account_name
                FROM articles a
                JOIN accounts acc ON a.account_id = acc.id
                WHERE acc.user_id = ?
                ORDER BY a.pub_date DESC 
                LIMIT 100
            """

        async with conn.execute(query, (user_id,)) as cursor:
            articles = await cursor.fetchall()

    fg = FeedGenerator()
    try:
        fg.load_extension("content")  # Load content namespace for content:encoded
    except ImportError as exc:
        logger.warning(
            "feedgen content extension is unavailable; RSS feeds will be generated without the "
            "content:encoded namespace for full HTML content. "
            f"Reason: {exc}"
        )
    except AttributeError as exc:
        logger.warning(
            "FeedGenerator.load_extension method not found; skipping optional content extension setup. "
            "This may indicate an incompatible feedgen version. "
            f"Reason: {exc}"
        )
    fg.id(f"wechat-rss-{feed_hash}")
    fg.title(f"WeChat Full Feed (Translated) - {username}" if translate else f"WeChat Full Feed - {username}")
    fg.link(href="https://mp.weixin.qq.com/", rel="alternate")
    fg.description(f"Full content feed for MS Teams (Translated) - {username}" if translate else f"Full content feed for MS Teams - {username}")

    base_url = str(request.base_url).rstrip("/")

    for article in articles:
        fe = fg.add_entry()
        fe.id(article["url"])
        fe.title(f"[{article['account_name']}] {article['title']}")
        fe.link(href=article["url"])

        # Ensure images have absolute URLs for external readers (Teams)
        content = (article["content"] or "").replace(
            'src="/media/', f'src="{base_url}/media/'
        )

        # Use content:encoded for full-text delivery (standard for Teams RSS connectors)
        fe.content(content, type="CDATA")

        # Also set description for fallback
        fe.description(content)

        if article["pub_date"]:
            # Handle potential timestamp formats
            try:
                dt = datetime.datetime.fromisoformat(str(article["pub_date"]))
                fe.pubDate(dt.replace(tzinfo=datetime.timezone.utc))
            except (ValueError, TypeError):
                pass

    return fg.rss_str(pretty=True)


@app.get("/rss/{feed_hash}")
async def get_user_rss(feed_hash: str, request: Request, lang: Optional[str] = None):
    """Secure endpoint for fetching a user's private RSS feed. Optional query parameter lang=translated."""
    translate = (lang == "translated")
    rss_xml = await generate_feed(feed_hash, request, translate=translate)
    if not rss_xml:
        raise HTTPException(status_code=404, detail="Feed not found")
    return Response(content=rss_xml, media_type="application/xml")


@app.get("/rss/{feed_hash}/translated")
async def get_user_rss_translated(feed_hash: str, request: Request):
    """Convenience endpoint specifically for the translated feed."""
    rss_xml = await generate_feed(feed_hash, request, translate=True)
    if not rss_xml:
        raise HTTPException(status_code=404, detail="Feed not found")
    return Response(content=rss_xml, media_type="application/xml")


# --- WeChat Auth Status & Actions ---


@app.get("/wechat/status")
async def get_wechat_status(user: dict = Depends(require_user)):
    """Checks if the WeChat and Sogou sessions are currently valid."""
    from scraper import check_session_validity

    wechat_valid, wechat_msg = await check_session_validity()

    sogou_exists = os.path.exists(SOGOU_STATE_PATH)
    sogou_msg = "Sogou Session captured." if sogou_exists else "Sogou Session missing."

    return {
        "wechat": {"is_valid": wechat_valid, "message": wechat_msg},
        "sogou": {"is_valid": sogou_exists, "message": sogou_msg},
    }


@app.post("/wechat/trigger-auth")
async def trigger_wechat_auth(
    user: dict = Depends(require_admin), _csrf=Depends(verify_csrf)
):
    """Triggers a new authentication flow."""
    return {
        "status": "success",
        "message": "Please run 'python auth.py' in your terminal.",
    }


@app.post("/wechat/trigger-sogou-auth")
async def trigger_sogou_auth(
    user: dict = Depends(require_admin), _csrf=Depends(verify_csrf)
):
    """Triggers a new Sogou authentication flow."""
    return {
        "status": "success",
        "message": "Please run 'python auth.py' in your terminal.",
    }


# --- Translation Endpoints ---


@app.get("/translation/status")
async def get_translation_status(user: dict = Depends(require_admin)):
    """Retrieves translation provider health status and article statistics."""
    from translator import PROVIDER_STATUS
    
    # Calculate stats for articles
    stats = {"success": 0, "failed": 0, "pending": 0, "skipped": 0, "total": 0}
    async with get_db_async() as conn:
        async with conn.execute(
            "SELECT translation_status, COUNT(*) as cnt FROM articles GROUP BY translation_status"
        ) as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                status_name = r["translation_status"] or "pending"
                stats[status_name] = r["cnt"]
                stats["total"] += r["cnt"]
                
    return {
        "providers": PROVIDER_STATUS,
        "stats": stats
    }


@app.post("/translation/test")
async def test_translation_providers(user: dict = Depends(require_admin), _csrf=Depends(verify_csrf)):
    """Manually triggers availability checks for all configured translation providers."""
    from translator import check_all_providers, PROVIDER_STATUS
    await check_all_providers()
    return {
        "status": "success",
        "message": "Translation provider availability checks completed.",
        "providers": PROVIDER_STATUS
    }


@app.post("/translation/retry")
async def trigger_translation_retry(user: dict = Depends(require_admin), _csrf=Depends(verify_csrf)):
    """Manually triggers the background worker to retry any pending/failed article translations."""
    from translator import translate_pending_articles
    asyncio.create_task(translate_pending_articles())
    return {
        "status": "success",
        "message": "Retry translation task started in the background."
    }


@app.post("/translation/retranslate-all")
async def trigger_retranslate_all(user: dict = Depends(require_admin), _csrf=Depends(verify_csrf)):
    """Sets all articles' translation status to 'pending' and starts the background translation task."""
    from translator import translate_pending_articles
    async with get_db_async() as conn:
        await conn.execute("UPDATE articles SET translation_status = 'pending'")
        await conn.commit()
    asyncio.create_task(translate_pending_articles())
    return {
        "status": "success",
        "message": "All articles marked as pending. Retranslation task started in the background."
    }


# --- System Logs & Stats ---


@app.get("/system/logs")
async def get_logs(user: dict = Depends(require_admin)):
    """Retrieves the last 50 system logs."""
    async with get_db_async() as conn:
        async with conn.execute(
            "SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 50"
        ) as cursor:
            logs = await cursor.fetchall()
        return [dict(l) for l in logs]


def _calculate_media_size():
    """Synchronous media size calculation (meant to be called in a thread)."""
    media_size = 0
    if os.path.exists(MEDIA_DIR):
        for f in os.listdir(MEDIA_DIR):
            fpath = os.path.join(MEDIA_DIR, f)
            if os.path.isfile(fpath):
                media_size += os.path.getsize(fpath)
    return media_size


@app.get("/system/stats")
async def get_stats(user: dict = Depends(require_admin)):
    """Calculates usage and storage statistics."""
    async with get_db_async() as conn:
        async with conn.execute("SELECT COUNT(*) FROM articles") as cursor:
            total_articles = (await cursor.fetchone())[0]

        async with conn.execute("SELECT COUNT(*) FROM accounts") as cursor:
            total_subscriptions = (await cursor.fetchone())[0]

    db_path = os.path.join(BASE_DIR, "data", "wechat_rss.db")
    db_size = os.path.getsize(db_path) / (1024 * 1024) if os.path.exists(db_path) else 0

    # Offload blocking filesystem walk to thread pool
    media_bytes = await asyncio.to_thread(_calculate_media_size)
    media_size = media_bytes / (1024 * 1024)

    return {
        "total_articles": total_articles,
        "total_subscriptions": total_subscriptions,
        "db_size_mb": round(db_size, 2),
        "media_size_mb": round(media_size, 2),
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# --- Account Management ---


@app.get("/accounts")
async def list_accounts(user: dict = Depends(require_user)):
    """Lists subscriptions with status tracking."""
    async with get_db_async() as conn:
        if user["role"] == "admin":
            async with conn.execute("""
                SELECT a.*, u.username as owner 
                FROM accounts a 
                JOIN users u ON a.user_id = u.id
            """) as cursor:
                accounts = await cursor.fetchall()
        else:
            async with conn.execute(
                "SELECT * FROM accounts WHERE user_id = ?", (user["id"],)
            ) as cursor:
                accounts = await cursor.fetchall()
        return [dict(a) for a in accounts]


@app.post("/accounts/{account_id}/sync")
async def sync_account(
    account_id: str, user: dict = Depends(require_user), _csrf=Depends(verify_csrf)
):
    """Manually triggers a scrape cycle."""
    await add_system_log(
        "INFO", "System", f"Manual sync triggered by {user['username']}"
    )
    asyncio.create_task(scrape_account(account_id))
    return {"status": "success", "message": "Account sync task started in background."}


@app.post("/accounts/{account_id}/stop")
async def stop_sync(
    account_id: str, user: dict = Depends(require_user), _csrf=Depends(verify_csrf)
):
    """Manually stops an active sync cycle by setting its DB state away from fetching."""
    async with get_db_async() as conn:
        # Check if currently fetching
        async with conn.execute(
            "SELECT last_status FROM accounts WHERE id = ?", (account_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row or row["last_status"] != "fetching":
                return {"status": "error", "message": "Account is not currently syncing."}

        # Set status to failed/stopped (this will trigger the scraper loop check to exit)
        await conn.execute(
            "UPDATE accounts SET last_status = 'failed', error_msg = 'Stopped by user', sync_progress_current = 0, sync_progress_total = 0 WHERE id = ?",
            (account_id,),
        )
        await conn.commit()

    await add_system_log(
        "WARNING", "System", f"Sync stop requested for account {account_id} by {user['username']}"
    )
    return {"status": "success", "message": "Account sync stop requested."}


@app.post("/accounts")
async def add_account(
    account: AccountCreate,
    user: dict = Depends(require_user),
    _csrf=Depends(verify_csrf),
):
    """Adds a new subscription."""
    try:
        async with get_db_async() as conn:
            await conn.execute(
                "INSERT INTO accounts (id, user_id, name) VALUES (?, ?, ?)",
                (account.id, user["id"], account.name),
            )
            await conn.commit()
            return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.delete("/accounts/{account_id}")
async def delete_account(
    account_id: str, user: dict = Depends(require_user), _csrf=Depends(verify_csrf)
):
    """Removes a subscription and its articles."""
    async with get_db_async() as conn:
        if user["role"] == "admin":
            await conn.execute(
                "DELETE FROM articles WHERE account_id = ?", (account_id,)
            )
            await conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        else:
            await conn.execute(
                "DELETE FROM articles WHERE account_id = ? AND account_id IN (SELECT id FROM accounts WHERE user_id = ?)",
                (account_id, user["id"]),
            )
            await conn.execute(
                "DELETE FROM accounts WHERE id = ? AND user_id = ?",
                (account_id, user["id"]),
            )
        await conn.commit()
    return {"status": "success"}


@app.post("/accounts/extract")
async def extract_and_add_account(
    request: Request, user: dict = Depends(require_user), _csrf=Depends(verify_csrf)
):
    """Extracts account info and subscribes."""
    data = await request.json()
    url = data.get("url")
    if not url or "mp.weixin.qq.com" not in url:
        return {"status": "error", "message": "Invalid WeChat article URL"}

    from scraper import extract_account_info

    account_info, error = await extract_account_info(url)

    if error:
        return {"status": "error", "message": error}

    async with get_db_async() as conn:
        try:
            # Check if already subscribed
            async with conn.execute(
                "SELECT id FROM accounts WHERE id = ? AND user_id = ?",
                (account_info["id"], user["id"]),
            ) as cursor:
                if await cursor.fetchone():
                    return {
                        "status": "error",
                        "message": f"Already subscribed to {account_info['name']}",
                    }

            await conn.execute(
                "INSERT INTO accounts (id, user_id, name, last_status) VALUES (?, ?, ?, 'pending')",
                (account_info["id"], user["id"], account_info["name"]),
            )
            await conn.commit()
            return {"status": "success", "account": account_info}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# --- Debug/Preview ---


@app.get("/debug/articles")
async def debug_articles(user: dict = Depends(require_user)):
    """Lists recently fetched articles for debugging/preview purposes."""
    async with get_db_async() as conn:
        if user["role"] == "admin":
            async with conn.execute("""
                SELECT a.id, a.title, a.pub_date, a.url, acc.name as account_name, u.username as owner
                FROM articles a
                JOIN accounts acc ON a.account_id = acc.id
                JOIN users u ON acc.user_id = u.id
                ORDER BY a.fetch_date DESC
                LIMIT 50
            """) as cursor:
                articles = await cursor.fetchall()
        else:
            async with conn.execute(
                """
                SELECT a.id, a.title, a.pub_date, a.url, acc.name as account_name
                FROM articles a
                JOIN accounts acc ON a.account_id = acc.id
                WHERE acc.user_id = ?
                ORDER BY a.fetch_date DESC
                LIMIT 20
            """,
                (user["id"],),
            ) as cursor:
                articles = await cursor.fetchall()
        return [dict(a) for a in articles]


@app.get("/debug/article/{article_id}")
async def debug_article(article_id: str, user: dict = Depends(require_user)):
    """Retrieves the full content of a specific article for preview."""
    async with get_db_async() as conn:
        if user["role"] == "admin":
            async with conn.execute(
                "SELECT title, content FROM articles WHERE id = ?", (article_id,)
            ) as cursor:
                article = await cursor.fetchone()
        else:
            async with conn.execute(
                """
                SELECT a.title, a.content FROM articles a
                JOIN accounts acc ON a.account_id = acc.id
                WHERE a.id = ? AND acc.user_id = ?
            """,
                (article_id, user["id"]),
            ) as cursor:
                article = await cursor.fetchone()
        return dict(article) if article else {"error": "not found or access denied"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
