"""
Runtime lifecycle helpers for WeChatRSS.

This module owns the scheduler instance so the FastAPI application does not
have to manage job state directly.
"""

from __future__ import annotations

from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import get_db
from scraper import scrape_wechat

_scheduler: Optional[AsyncIOScheduler] = None


def _load_scheduler_settings() -> tuple[int, int]:
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        settings = {row[0]: row[1] for row in cursor.fetchall()}
    finally:
        conn.close()

    interval_hours = int(settings.get("fetch_interval_hours", 6))
    jitter_minutes = int(settings.get("fetch_random_jitter_minutes", 30))
    return interval_hours, jitter_minutes


def _build_scheduler() -> AsyncIOScheduler:
    interval_hours, jitter_minutes = _load_scheduler_settings()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scrape_wechat,
        "interval",
        hours=interval_hours,
        jitter=jitter_minutes * 60,
        id="wechat_scraper",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    # Periodic check for translation provider health (every 30 minutes)
    from translator import check_all_providers
    scheduler.add_job(
        check_all_providers,
        "interval",
        minutes=30,
        id="translation_health_check",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    # Periodic retry for failed/pending translations (every 5 minutes)
    from translator import translate_pending_articles
    scheduler.add_job(
        translate_pending_articles,
        "interval",
        minutes=5,
        id="translation_pending_retry",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )

    return scheduler


def start_scraper_scheduler() -> AsyncIOScheduler:
    global _scheduler

    if _scheduler and _scheduler.running:
        return _scheduler

    _scheduler = _build_scheduler()
    _scheduler.start()
    return _scheduler


def restart_scraper_scheduler() -> AsyncIOScheduler:
    shutdown_scraper_scheduler()
    return start_scraper_scheduler()


def shutdown_scraper_scheduler() -> None:
    global _scheduler

    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
