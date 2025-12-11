"""
Background scheduler for periodic sync operations.

Uses APScheduler to run sync tasks in the background.
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
from threading import Lock

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Add backend path to sys.path
BACKEND_PATH = Path(__file__).parent.parent.parent.parent / "ferramentas/stj-dados-abertos"
sys.path.insert(0, str(BACKEND_PATH))

from src.database import STJDatabase
from src.downloader import STJDownloader
from src.processor import STJProcessor
from config import DATABASE_PATH, STAGING_DIR, ORGAOS_JULGADORES, get_date_range_urls
from api.dependencies import invalidate_cache

logger = logging.getLogger(__name__)

# Global sync status
_sync_status = {
    "status": "idle",
    "started_at": None,
    "completed_at": None,
    "downloaded": 0,
    "processed": 0,
    "inserted": 0,
    "duplicates": 0,
    "errors": 0,
    "message": None
}
_sync_lock = Lock()


def get_sync_status() -> dict:
    """
    Get current sync status.

    Returns:
        Dict with sync status information
    """
    with _sync_lock:
        return _sync_status.copy()


def _update_sync_status(**kwargs):
    """
    Update sync status (thread-safe).

    Args:
        **kwargs: Fields to update in sync status
    """
    with _sync_lock:
        _sync_status.update(kwargs)


async def run_sync_task(
    orgaos: Optional[List[str]] = None,
    dias: int = 30,
    force: bool = False
) -> dict:
    """
    Run sync task to download and process STJ data.

    Args:
        orgaos: List of órgãos to sync (None = all)
        dias: Number of days to sync (default: 30)
        force: Force redownload of existing files

    Returns:
        Dict with sync results
    """
    logger.info(f"Starting sync task: orgaos={orgaos}, dias={dias}, force={force}")

    try:
        # Update status to running
        _update_sync_status(
            status="running",
            started_at=datetime.now(),
            completed_at=None,
            downloaded=0,
            processed=0,
            inserted=0,
            duplicates=0,
            errors=0,
            message="Sync iniciado"
        )

        # Determine which órgãos to sync
        if orgaos is None:
            orgaos_to_sync = list(ORGAOS_JULGADORES.keys())
        else:
            # Validate órgãos
            invalid = [o for o in orgaos if o not in ORGAOS_JULGADORES]
            if invalid:
                error_msg = f"Órgãos inválidos: {invalid}"
                logger.error(error_msg)
                _update_sync_status(
                    status="failed",
                    completed_at=datetime.now(),
                    message=error_msg
                )
                return get_sync_status()

            orgaos_to_sync = orgaos

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=dias)

        # Generate URLs for download
        all_urls = []
        for orgao in orgaos_to_sync:
            urls = get_date_range_urls(start_date, end_date, orgao)
            all_urls.extend(urls)

        logger.info(f"Generated {len(all_urls)} URLs for download")

        # Download files
        downloader = STJDownloader(staging_dir=STAGING_DIR)
        try:
            url_configs = [
                {"url": u["url"], "filename": u["filename"], "force": force}
                for u in all_urls
            ]

            # Run download in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            downloaded_files = await loop.run_in_executor(
                None,
                downloader.download_batch,
                url_configs,
                False  # show_progress=False (API mode)
            )

            _update_sync_status(
                downloaded=downloader.stats.downloaded,
                message=f"Downloaded {downloader.stats.downloaded} files"
            )

        finally:
            downloader.client.close()

        # Process downloaded files
        processor = STJProcessor()
        all_records = processor.processar_batch(downloaded_files)

        _update_sync_status(
            processed=processor.stats.processados,
            message=f"Processed {processor.stats.processados} records"
        )

        # Insert into database
        with STJDatabase(db_path=DATABASE_PATH) as db:
            inseridos, duplicados, erros = db.inserir_batch(all_records)

            _update_sync_status(
                inserted=inseridos,
                duplicates=duplicados,
                errors=erros,
                status="completed",
                completed_at=datetime.now(),
                message=f"Sync completed: {inseridos} inserted, {duplicados} duplicates, {erros} errors"
            )

        # Invalidate cache after successful sync
        invalidate_cache()

        logger.info(f"Sync completed: {inseridos} inserted, {duplicados} duplicates")
        return get_sync_status()

    except Exception as e:
        logger.error(f"Sync task failed: {e}", exc_info=True)
        _update_sync_status(
            status="failed",
            completed_at=datetime.now(),
            message=f"Sync failed: {str(e)}"
        )
        return get_sync_status()


# APScheduler instance
scheduler: Optional[AsyncIOScheduler] = None


def start_scheduler():
    """
    Start background scheduler for periodic sync.

    Runs daily at 3 AM to sync last 7 days of data.
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    logger.info("Starting background scheduler")

    scheduler = AsyncIOScheduler()

    # Schedule daily sync at 3 AM
    scheduler.add_job(
        run_sync_task,
        trigger=CronTrigger(hour=3, minute=0),
        kwargs={"dias": 7, "force": False},
        id="daily_sync",
        name="Daily STJ sync (last 7 days)",
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started: daily sync at 3 AM")


def stop_scheduler():
    """Stop background scheduler."""
    global scheduler

    if scheduler is not None:
        logger.info("Stopping scheduler")
        scheduler.shutdown(wait=True)
        scheduler = None
