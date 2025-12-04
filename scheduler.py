import logging
from telegram import Bot
from telegram.error import TelegramError
from database import SessionLocal
from services import BirthdayService
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class BirthdayScheduler:
    """Scheduler for sending daily birthday greetings"""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.running = False

    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("Birthday scheduler started")
        
        while self.running:
            try:
                await self.check_and_send_greetings()
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
            
            # Wait until next 8:00 AM
            await self.wait_until_next_check()

    async def check_and_send_greetings(self):
        """Check for birthdays and send greetings"""
        db = SessionLocal()
        try:
            birthdays = BirthdayService.get_birthdays_today(db)
            
            if not birthdays:
                logger.info("No birthdays today")
                return

            for chat_id, usernames in birthdays:
                await self.send_greeting(chat_id, usernames)
                
        except Exception as e:
            logger.error(f"Error checking birthdays: {e}")
        finally:
            db.close()

    async def send_greeting(self, chat_id: int, usernames: list):
        """Send birthday greeting to a chat"""
        try:
            if len(usernames) == 1:
                message = f"🎉 Сегодня день рождения у {usernames[0]}! 🎂\n\nПоздравляем! 🎊"
            else:
                names = ", ".join(usernames)
                message = f"🎉 Сегодня дни рождения у {names}! 🎂\n\nПоздравляем! 🎊"

            await self.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Birthday greeting sent to chat {chat_id}")
        except TelegramError as e:
            logger.error(f"Error sending message to chat {chat_id}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error sending greeting: {e}")

    async def wait_until_next_check(self):
        """Wait until next check time (8:00 AM)"""
        now = datetime.now()
        
        # Calculate next 8:00 AM
        next_check = now.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # If it's already past 8:00 AM today, schedule for tomorrow
        if now >= next_check:
            from datetime import timedelta
            next_check = next_check + timedelta(days=1)
        
        wait_seconds = (next_check - now).total_seconds()
        
        logger.info(f"Next birthday check scheduled for {next_check}")
        await asyncio.sleep(wait_seconds)

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Birthday scheduler stopped")
