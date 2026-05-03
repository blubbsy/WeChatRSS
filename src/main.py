"""
Main application entry point for WeChatRSS.
Provides the FastAPI backend, authentication middleware, dashboard templates, and RSS generation.
"""

from fastapi import FastAPI, Response, Request, Form, Depends, HTTPException, status, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from feedgen.feed import FeedGenerator
from database import get_db_async, init_db, pwd_context
from scraper import start_scheduler, get_settings, MEDIA_DIR, scrape_wechat, add_system_log
import logging
import os
import secrets
import uuid
from typing import Optional, List, Dict
import datetime
import asyncio

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

scheduler_instance = None

app = FastAPI(
    title="WeChatRSS",
    description="A lightweight WeChat Official Account aggregator and RSS deliverer."
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

# --- Lifecycle Hooks ---

@app.on_event("startup")
async def startup_event():
    """Runs on application startup: initializes DB and starts the background scraper scheduler."""
    global scheduler_instance
    init_db()
    await add_system_log("INFO", "System", "Server started successfully.")
    scheduler_instance = start_scheduler()

# --- Auth Dependencies ---

async def get_current_user(request: Request):
    """
    Dependency to retrieve the current user from the persistent sessions table.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_id = auth_header.replace("Bearer ", "")
            
    if not session_id:
        return None
    
    conn = await get_db_async()
    try:
        query = '''
            SELECT users.id, users.username, users.feed_hash, users.role 
            FROM users 
            INNER JOIN sessions ON users.id = sessions.user_id
            WHERE sessions.id = ?
        '''
        async with conn.execute(query, (session_id,)) as cursor:
            user = await cursor.fetchone()
            if user:
                return dict(user)
            return None
    except Exception as e:
        logger.error(f"Error in get_current_user: {e}")
        return None
    finally:
        await conn.close()

async def require_admin(user: Optional[dict] = Depends(get_current_user)):
    """
    Dependency to enforce admin role requirements.
    """
    if not user or user.get('role') != 'admin':
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
                if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
                    form_data = await request.form()
                    token_in_request = form_data.get("csrf_token")
            except Exception:
                pass

        if not token_in_request or not token_in_cookie or token_in_request != token_in_cookie:
            raise HTTPException(status_code=403, detail="CSRF token mismatch or missing")

# --- Dashboard & Login ---

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, user: Optional[dict] = Depends(get_current_user)):
    """Renders the main dashboard or redirects to login if unauthenticated."""
    if not user:
        response = templates.TemplateResponse(request=request, name="login.html")
    else:
        response = templates.TemplateResponse(request=request, name="index.html", context={"user": user})
    
    if not request.cookies.get("csrf_token"):
        token = get_csrf_token(request)
        response.set_cookie(key="csrf_token", value=token, httponly=True, samesite="lax", path="/")
    return response

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    """Handles user login and persistent session creation."""
    conn = await get_db_async()
    try:
        async with conn.execute("SELECT id, username, password_hash, feed_hash, role FROM users WHERE username = ?", (username,)) as cursor:
            user = await cursor.fetchone()
        
        if user and pwd_context.verify(password, user['password_hash']):
            session_id = secrets.token_hex(32)
            await conn.execute("INSERT INTO sessions (id, user_id) VALUES (?, ?)", (session_id, user['id']))
            await conn.commit()
            
            response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
            response.set_cookie(key="session_id", value=session_id, httponly=True, samesite="lax", path="/")
            return response
    finally:
        await conn.close()
    
    return RedirectResponse(url="/?error=1", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/logout")
async def logout(request: Request):
    """Clears the user session from the database and cookies."""
    session_id = request.cookies.get("session_id")
    if session_id:
        conn = await get_db_async()
        await conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        await conn.commit()
        await conn.close()
    response = RedirectResponse(url="/")
    response.delete_cookie("session_id", path="/")
    return response

# --- Settings Management (Admin Only) ---

@app.get("/settings")
async def list_settings(admin: dict = Depends(require_admin)):
    """Retrieves all system settings asynchronously."""
    conn = await get_db_async()
    async with conn.execute("SELECT key, value FROM settings") as cursor:
        rows = await cursor.fetchall()
        settings = {row['key']: row['value'] for row in rows}
    await conn.close()
    return settings

@app.post("/settings")
async def update_settings(data: SettingsUpdate, admin: dict = Depends(require_admin), _csrf = Depends(verify_csrf)):
    """Updates settings and restarts the background scheduler to apply them."""
    global scheduler_instance
    conn = await get_db_async()
    try:
        for key, val in data.settings.items():
            await conn.execute("UPDATE settings SET value = ? WHERE key = ?", (val, key))
        await conn.commit()
        
        if scheduler_instance:
            scheduler_instance.shutdown()
        scheduler_instance = start_scheduler()
        
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()

# --- User Management (Admin Only) ---

@app.get("/users")
async def list_users(admin: dict = Depends(require_admin)):
    """Lists all registered users."""
    conn = await get_db_async()
    async with conn.execute("SELECT id, username, role, feed_hash FROM users") as cursor:
        users = await cursor.fetchall()
    await conn.close()
    return [dict(u) for u in users]

@app.post("/users")
async def create_user(user_data: UserCreate, admin: dict = Depends(require_admin), _csrf = Depends(verify_csrf)):
    """Creates a new user with a unique RSS feed hash."""
    conn = await get_db_async()
    try:
        user_id = str(uuid.uuid4())
        pwd_hash = pwd_context.hash(user_data.password)
        feed_hash = secrets.token_hex(16)
        await conn.execute("INSERT INTO users (id, username, password_hash, feed_hash, role) VALUES (?, ?, ?, ?, ?)",
                       (user_id, user_data.username, pwd_hash, feed_hash, user_data.role))
        await conn.commit()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin), _csrf = Depends(verify_csrf)):
    """Deletes a user and their associated subscriptions."""
    if user_id == admin['id']:
        return {"status": "error", "message": "Cannot delete yourself"}
    conn = await get_db_async()
    await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    await conn.execute("DELETE FROM accounts WHERE user_id = ?", (user_id,))
    await conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    await conn.commit()
    await conn.close()
    return {"status": "success"}

# --- Profile Management (All Users) ---

@app.post("/profile/password")
async def change_password(data: PasswordUpdate, user: dict = Depends(require_user), _csrf = Depends(verify_csrf)):
    """Allows users to update their own password."""
    conn = await get_db_async()
    pwd_hash = pwd_context.hash(data.new_password)
    await conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (pwd_hash, user['id']))
    await conn.commit()
    await conn.close()
    return {"status": "success"}

# --- Secure RSS Routes ---

async def generate_feed(feed_hash: str, request: Request):
    """
    Generates an RSS XML feed with FULL CONTENT for MS Teams.
    """
    conn = await get_db_async()
    try:
        async with conn.execute("SELECT id, username FROM users WHERE feed_hash = ?", (feed_hash,)) as cursor:
            user = await cursor.fetchone()
        
        if not user:
            return None
        
        user_id = user['id']
        username = user['username']

        async with conn.execute('''
            SELECT a.title, a.url, a.content, a.pub_date, acc.name as account_name
            FROM articles a
            JOIN accounts acc ON a.account_id = acc.id
            WHERE acc.user_id = ?
            ORDER BY a.pub_date DESC 
            LIMIT 100
        ''', (user_id,)) as cursor:
            articles = await cursor.fetchall()
        
        fg = FeedGenerator()
        fg.load_extension('content') # Load content namespace for content:encoded
        fg.id(f"wechat-rss-{feed_hash}")
        fg.title(f"WeChat Full Feed - {username}")
        fg.link(href=f"https://mp.weixin.qq.com/", rel='alternate')
        fg.description(f"Full content feed for MS Teams - {username}")
        
        base_url = str(request.base_url).rstrip('/')

        for article in articles:
            fe = fg.add_entry()
            fe.id(article['url'])
            fe.title(f"[{article['account_name']}] {article['title']}")
            fe.link(href=article['url'])
            
            # Ensure images have absolute URLs for external readers (Teams)
            content = article['content'].replace('src="/media/', f'src="{base_url}/media/')
            
            # Use content:encoded for full-text delivery (standard for Teams RSS connectors)
            fe.content(content, type='CDATA')
            
            # Also set description for fallback
            fe.description(content)
            
            if article['pub_date']:
                # Handle potential timestamp formats
                try:
                    dt = datetime.datetime.fromisoformat(str(article['pub_date']))
                    fe.pubDate(dt.replace(tzinfo=datetime.timezone.utc))
                except:
                    pass
            
        return fg.rss_str(pretty=True)
    finally:
        await conn.close()

@app.get("/rss/{feed_hash}")
async def get_user_rss(feed_hash: str, request: Request):
    """Secure endpoint for fetching a user's private RSS feed."""
    rss_xml = await generate_feed(feed_hash, request)
    if not rss_xml:
        raise HTTPException(status_code=404, detail="Feed not found")
    return Response(content=rss_xml, media_type="application/xml")

# --- WeChat Auth Status & Actions ---

@app.get("/wechat/status")
async def get_wechat_status(user: dict = Depends(require_user)):
    """Checks if the WeChat and Sogou sessions are currently valid."""
    from scraper import check_session_validity, PROFILE_DIR
    from auth_sogou import STATE_PATH as SOGOU_STATE_PATH
    
    wechat_valid, wechat_msg = await check_session_validity()
    
    sogou_exists = os.path.exists(SOGOU_STATE_PATH)
    sogou_msg = "Sogou Session captured." if sogou_exists else "Sogou Session missing."
    
    return {
        "wechat": {"is_valid": wechat_valid, "message": wechat_msg},
        "sogou": {"is_valid": sogou_exists, "message": sogou_msg}
    }

@app.post("/wechat/trigger-auth")
async def trigger_wechat_auth(user: dict = Depends(require_admin), _csrf = Depends(verify_csrf)):
    """Triggers a new authentication flow."""
    return {"status": "success", "message": "Please run 'python auth_ultimate.py' in your terminal."}

@app.post("/wechat/trigger-sogou-auth")
async def trigger_sogou_auth(user: dict = Depends(require_admin), _csrf = Depends(verify_csrf)):
    """Triggers a new Sogou authentication flow."""
    return {"status": "success", "message": "Please run 'python auth_ultimate.py' in your terminal."}

# --- System Logs & Stats ---

@app.get("/system/logs")
async def get_logs(user: dict = Depends(require_admin)):
    """Retrieves the last 50 system logs."""
    conn = await get_db_async()
    async with conn.execute("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 50") as cursor:
        logs = await cursor.fetchall()
    await conn.close()
    return [dict(l) for l in logs]

@app.get("/system/stats")
async def get_stats(user: dict = Depends(require_admin)):
    """Calculates usage and storage statistics."""
    conn = await get_db_async()
    
    async with conn.execute("SELECT COUNT(*) FROM articles") as cursor:
        total_articles = (await cursor.fetchone())[0]
        
    async with conn.execute("SELECT COUNT(*) FROM accounts") as cursor:
        total_subscriptions = (await cursor.fetchone())[0]
        
    db_size = os.path.getsize(os.path.join('data', 'wechat_rss.db')) / (1024 * 1024)
    
    media_size = 0
    if os.path.exists(MEDIA_DIR):
        for f in os.listdir(MEDIA_DIR):
            media_size += os.path.getsize(os.path.join(MEDIA_DIR, f))
    media_size = media_size / (1024 * 1024)
    
    await conn.close()
    
    return {
        "total_articles": total_articles,
        "total_subscriptions": total_subscriptions,
        "db_size_mb": round(db_size, 2),
        "media_size_mb": round(media_size, 2),
        "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# --- Account Management ---

@app.get("/accounts")
async def list_accounts(user: dict = Depends(require_user)):
    """Lists subscriptions with status tracking."""
    conn = await get_db_async()
    if user['role'] == 'admin':
        async with conn.execute('''
            SELECT a.*, u.username as owner 
            FROM accounts a 
            JOIN users u ON a.user_id = u.id
        ''') as cursor:
            accounts = await cursor.fetchall()
    else:
        async with conn.execute("SELECT * FROM accounts WHERE user_id = ?", (user['id'],)) as cursor:
            accounts = await cursor.fetchall()
    await conn.close()
    return [dict(a) for a in accounts]

@app.post("/accounts/{account_id}/sync")
async def sync_account(account_id: str, user: dict = Depends(require_user), _csrf = Depends(verify_csrf)):
    """Manually triggers a scrape cycle."""
    await add_system_log("INFO", "System", f"Manual sync triggered by {user['username']}")
    asyncio.create_task(scrape_wechat())
    return {"status": "success", "message": "Scrape task started in background."}

@app.post("/accounts")
async def add_account(account: AccountCreate, user: dict = Depends(require_user), _csrf = Depends(verify_csrf)):
    """Adds a new subscription."""
    conn = await get_db_async()
    try:
        await conn.execute("INSERT INTO accounts (id, user_id, name) VALUES (?, ?, ?)", 
                       (account.id, user['id'], account.name))
        await conn.commit()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()

@app.delete("/accounts/{account_id}")
async def delete_account(account_id: str, user: dict = Depends(require_user), _csrf = Depends(verify_csrf)):
    """Removes a subscription."""
    conn = await get_db_async()
    if user['role'] == 'admin':
        await conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    else:
        await conn.execute("DELETE FROM accounts WHERE id = ? AND user_id = ?", (account_id, user['id']))
    await conn.commit()
    await conn.close()
    return {"status": "success"}

@app.post("/accounts/extract")
async def extract_and_add_account(request: Request, user: dict = Depends(require_user), _csrf = Depends(verify_csrf)):
    """Extracts account info and subscribes."""
    data = await request.json()
    url = data.get("url")
    if not url or "mp.weixin.qq.com" not in url:
        return {"status": "error", "message": "Invalid WeChat article URL"}
    
    from scraper import extract_account_info
    account_info, error = await extract_account_info(url)
    
    if error:
        return {"status": "error", "message": error}
    
    conn = await get_db_async()
    try:
        # Check if already subscribed
        async with conn.execute("SELECT id FROM accounts WHERE id = ? AND user_id = ?", 
                               (account_info['id'], user['id'])) as cursor:
            if await cursor.fetchone():
                return {"status": "error", "message": f"Already subscribed to {account_info['name']}"}
        
        await conn.execute("INSERT INTO accounts (id, user_id, name, last_status) VALUES (?, ?, ?, 'pending')", 
                       (account_info['id'], user['id'], account_info['name']))
        await conn.commit()
        return {"status": "success", "account": account_info}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        await conn.close()

# --- Debug/Preview ---

@app.get("/debug/articles")
async def debug_articles(user: dict = Depends(require_user)):
    """Lists recently fetched articles for debugging/preview purposes."""
    conn = await get_db_async()
    if user['role'] == 'admin':
        async with conn.execute('''
            SELECT a.id, a.title, a.pub_date, a.url, acc.name as account_name, u.username as owner
            FROM articles a
            JOIN accounts acc ON a.account_id = acc.id
            JOIN users u ON acc.user_id = u.id
            ORDER BY a.fetch_date DESC
            LIMIT 50
        ''') as cursor:
            articles = await cursor.fetchall()
    else:
        async with conn.execute('''
            SELECT a.id, a.title, a.pub_date, a.url, acc.name as account_name
            FROM articles a
            JOIN accounts acc ON a.account_id = acc.id
            WHERE acc.user_id = ?
            ORDER BY a.fetch_date DESC
            LIMIT 20
        ''', (user['id'],)) as cursor:
            articles = await cursor.fetchall()
    await conn.close()
    return [dict(a) for a in articles]

@app.get("/debug/article/{article_id}")
async def debug_article(article_id: str, user: dict = Depends(require_user)):
    """Retrieves the full content of a specific article for preview."""
    conn = await get_db_async()
    if user['role'] == 'admin':
        async with conn.execute("SELECT title, content FROM articles WHERE id = ?", (article_id,)) as cursor:
            article = await cursor.fetchone()
    else:
        async with conn.execute('''
            SELECT a.title, a.content FROM articles a
            JOIN accounts acc ON a.account_id = acc.id
            WHERE a.id = ? AND acc.user_id = ?
        ''', (article_id, user['id'])) as cursor:
            article = await cursor.fetchone()
    await conn.close()
    return dict(article) if article else {"error": "not found or access denied"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
