"""Background scheduler.

Polls for due DCA strategies once a minute via APScheduler. Simple enough
for MVP; swap to Celery/queue if volume grows (per CLAUDE.md).
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.dca_engine import run_due_strategies

logger = logging.getLogger("cadence.scheduler")

_scheduler: BackgroundScheduler | None = None


def _tick() -> None:
    try:
        count = run_due_strategies()
        if count:
            logger.info("Executed %d due strategies", count)
    except Exception:
        logger.exception("Scheduler tick failed")


def start_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(_tick, "interval", minutes=1, id="dca_tick",
                       max_instances=1, coalesce=True)
    _scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
