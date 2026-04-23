from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.repository.revoked_token_repository import RevokedTokenRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

def cleanup_expired_tokens():
    db: Session = SessionLocal()
    try:
        deleted = RevokedTokenRepository(db).delete_expired()
        if deleted:
            logger.info(f"Token cleanup: {deleted} record(s) removed.")
    except Exception as e:
        logger.error(f"Error clearing tokens: {e}")
    finally:
        db.close()

def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        cleanup_expired_tokens,
        trigger=IntervalTrigger(hours=1), # interval hardcoded -> use settings.py file and env vars
        id="cleanup_expired_tokens",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — tokens cleared every 1 hour.")
    return scheduler