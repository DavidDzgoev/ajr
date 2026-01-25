import asyncio
import logging
import os

from sqlmodel import Session

from app.core.db import engine, init_db
from app.services.sync_service import SyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)


async def sync_initial_data() -> None:
    """Sync initial data from judobase if enabled."""
    # Check if sync is enabled via environment variable
    sync_on_startup = os.getenv("SYNC_ON_STARTUP", "false").lower() == "true"
    logger.info(sync_on_startup)
    
    if not sync_on_startup:
        logger.info("SYNC_ON_STARTUP is not enabled, skipping data sync")
        return
    
    logger.info("Starting initial data sync from judobase")
    try:
            with Session(engine) as session:
                sync_service = SyncService(session=session)
                data_sync = await sync_service.sync_all(created_by=None)
            logger.info(
                f"Initial sync completed: {data_sync.records_processed} processed, "
                f"{data_sync.records_created} created, {data_sync.records_updated} updated"
            )
    except Exception as e:
        logger.error(f"Initial sync failed: {str(e)}", exc_info=True)
        raise


def main() -> None:
    logger.info("Creating initial data")
    init()
    asyncio.run(sync_initial_data())
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
