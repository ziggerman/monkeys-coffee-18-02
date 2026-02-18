"""Scheduler for automated tasks and notifications."""
import logging
from datetime import time
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot

from src.database.session import async_session
from src.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Scheduler for automated background tasks."""
    
    def __init__(self, bot: Bot):
        """Initialize scheduler with bot instance.
        
        Args:
            bot: Telegram bot instance
        """
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.notification_service = NotificationService(bot)
    
    def start(self):
        """Start the scheduler and register all jobs."""
        logger.info("Starting task scheduler...")
        
        # Daily replenishment reminders - 10:00 AM
        self.scheduler.add_job(
            self._send_replenishment_reminders,
            trigger=CronTrigger(hour=10, minute=0),
            id="replenishment_reminders",
            name="Send coffee replenishment reminders",
            replace_existing=True
        )
        
        # Volume discount suggestions - 3:00 PM
        self.scheduler.add_job(
            self._send_volume_suggestions,
            trigger=CronTrigger(hour=15, minute=0),
            id="volume_suggestions",
            name="Send volume discount suggestions",
            replace_existing=True
        )
        
        # Abandoned cart reminders - 6:00 PM
        self.scheduler.add_job(
            self._send_abandoned_cart_reminders,
            trigger=CronTrigger(hour=18, minute=0),
            id="abandoned_cart_reminders",
            name="Send abandoned cart reminders",
            replace_existing=True
        )
        
        # Fresh roast announcements - Monday & Thursday at 11:00 AM
        self.scheduler.add_job(
            self._send_fresh_roast_announcements,
            trigger=CronTrigger(day_of_week='mon,thu', hour=11, minute=0),
            id="fresh_roast_announcements",
            name="Send fresh roast announcements",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Task scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping task scheduler...")
        self.scheduler.shutdown()
        logger.info("Task scheduler stopped")
    
    async def _send_replenishment_reminders(self):
        """Job to send replenishment reminders."""
        try:
            async with async_session() as session:
                count = await self.notification_service.send_replenishment_reminders(session)
                logger.info(f"Sent {count} replenishment reminders")
        except Exception as e:
            logger.error(f"Error sending replenishment reminders: {e}")
    
    async def _send_volume_suggestions(self):
        """Job to send volume discount suggestions."""
        try:
            async with async_session() as session:
                count = await self.notification_service.send_volume_discount_suggestions(session)
                logger.info(f"Sent {count} volume discount suggestions")
        except Exception as e:
            logger.error(f"Error sending volume suggestions: {e}")
    
    async def _send_abandoned_cart_reminders(self):
        """Job to send abandoned cart reminders."""
        try:
            async with async_session() as session:
                count = await self.notification_service.send_abandoned_cart_reminder(session)
                logger.info(f"Sent {count} abandoned cart reminders")
        except Exception as e:
            logger.error(f"Error sending abandoned cart reminders: {e}")
    
    async def _send_fresh_roast_announcements(self):
        """Job to send fresh roast announcements."""
        try:
            async with async_session() as session:
                count = await self.notification_service.send_fresh_roast_announcements(session)
                logger.info(f"Sent {count} fresh roast announcements")
        except Exception as e:
            logger.error(f"Error sending fresh roast announcements: {e}")
    
    # Manual trigger methods for admin use
    
    async def trigger_replenishment_reminders(self):
        """Manually trigger replenishment reminders."""
        await self._send_replenishment_reminders()
    
    async def trigger_volume_suggestions(self):
        """Manually trigger volume suggestions."""
        await self._send_volume_suggestions()
    
    async def trigger_fresh_roast_announcements(self, product_ids=None):
        """Manually trigger fresh roast announcements.
        
        Args:
            product_ids: Optional list of product IDs to announce
        """
        try:
            async with async_session() as session:
                count = await self.notification_service.send_fresh_roast_announcements(
                    session, 
                    product_ids
                )
                logger.info(f"Manually sent {count} fresh roast announcements")
                return count
        except Exception as e:
            logger.error(f"Error manually sending announcements: {e}")
            return 0
