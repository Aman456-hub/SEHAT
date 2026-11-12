import logging
from datetime import datetime, timedelta
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.token import QueueToken
from backend.models.chemist import Chemist, ChemistStock
from backend.models.blood_bank import BloodBank, BloodStock
from backend.services.notification_service import send_whatsapp_notification

logger = logging.getLogger("cron_jobs")

async def run_midnight_queue_cleanup(db: AsyncSession) -> int:
    """
    Auto-resets any leftovers in the doctor queue at midnight by marking
    waiting/called tokens as cancelled to clean the slate.
    """
    logger.info("Starting midnight queue auto-reset task...")
    stmt = (
        update(QueueToken)
        .where(QueueToken.status.in_(["waiting", "called"]))
        .values(status="cancelled")
    )
    result = await db.execute(stmt)
    await db.commit()
    count = result.rowcount
    logger.info(f"Midnight queue auto-reset completed. {count} tokens cancelled.")
    return count

async def trigger_stale_stock_reminders(db: AsyncSession) -> int:
    """
    Identifies chemists and blood banks whose last stock update exceeds 24 hours
    and issues an automated WhatsApp reminder to prompt updates.
    """
    logger.info("Checking for stale chemist and blood bank stocks...")
    stale_limit = datetime.now() - timedelta(hours=24)
    reminders_sent = 0
    
    # 1. Check chemists
    chemists_result = await db.execute(
        select(Chemist).join(ChemistStock).where(ChemistStock.last_updated < stale_limit).distinct()
    )
    for chemist in chemists_result.scalars().all():
        msg = (
            f"Hello {chemist.name}, this is an automated reminder from SEHAT.\n\n"
            f"Your medicine stock inventory for '{chemist.shop_name}' has not been updated in the last 24 hours.\n"
            f"Please log in to your dashboard to refresh your stock status: http://localhost:5173"
        )
        logger.info(f"Sending daily update reminder to chemist {chemist.phone}")
        await send_whatsapp_notification(chemist.phone, msg)
        reminders_sent += 1

    # 2. Check blood banks
    banks_result = await db.execute(
        select(BloodBank).join(BloodStock).where(BloodStock.last_updated < stale_limit).distinct()
    )
    for bank in banks_result.scalars().all():
        msg = (
            f"Hello {bank.name}, this is an automated reminder from SEHAT.\n\n"
            f"Your blood group availability counts have not been updated in the last 24 hours.\n"
            f"Please log in to your dashboard to refresh unit counts: http://localhost:5173"
        )
        logger.info(f"Sending daily update reminder to blood bank {bank.phone}")
        await send_whatsapp_notification(bank.phone, msg)
        reminders_sent += 1
        
    return reminders_sent
