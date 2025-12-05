import os
import logging
from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, ConversationHandler, 
    MessageHandler, CallbackQueryHandler, filters
)
from database import init_db
from handlers import BirthdayHandler, WAITING_FOR_MONTH, WAITING_FOR_DAY
from scheduler import BirthdayScheduler
import asyncio

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")


async def main():
    """Main function to start the bot"""
    
    # Initialize database
    logger.info("Initializing database...")
    init_db()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Create scheduler
    scheduler = BirthdayScheduler(application.bot)
    
    # Add handlers
    # Basic commands
    application.add_handler(CommandHandler("start", BirthdayHandler.start_command))
    application.add_handler(CommandHandler("help", BirthdayHandler.help_command))
    application.add_handler(CommandHandler("mybirthday", BirthdayHandler.my_birthday))
    application.add_handler(CommandHandler("deletebirthday", BirthdayHandler.delete_birthday))
    application.add_handler(CommandHandler("nextbirthdays", BirthdayHandler.next_birthdays))
    application.add_handler(CommandHandler("listbirthdays", BirthdayHandler.list_birthdays))

    # Conversation handler for /setbirthday
    set_birthday_conv = ConversationHandler(
        entry_points=[CommandHandler("setbirthday", BirthdayHandler.set_birthday_start)],
        states={
            WAITING_FOR_DAY: [
                CallbackQueryHandler(BirthdayHandler.set_birthday_day, pattern="^set_day_"),
            ],
            WAITING_FOR_MONTH: [
                CallbackQueryHandler(BirthdayHandler.set_birthday_month, pattern="^set_month_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", BirthdayHandler.cancel_conversation)],
    )
    application.add_handler(set_birthday_conv)

    # Conversation handler for /updatebirthday
    update_birthday_conv = ConversationHandler(
        entry_points=[CommandHandler("updatebirthday", BirthdayHandler.update_birthday_start)],
        states={
            WAITING_FOR_DAY: [
                CallbackQueryHandler(BirthdayHandler.update_birthday_day, pattern="^upd_day_"),
            ],
            WAITING_FOR_MONTH: [
                CallbackQueryHandler(BirthdayHandler.update_birthday_month, pattern="^upd_month_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", BirthdayHandler.cancel_conversation)],
    )
    application.add_handler(update_birthday_conv)

    # Conversation handler for new members
    new_member_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, BirthdayHandler.new_member_welcome)],
        states={
            WAITING_FOR_DAY: [
                CallbackQueryHandler(BirthdayHandler.new_member_day, pattern="^new_day_"),
                CallbackQueryHandler(BirthdayHandler.new_member_day, pattern="^skip_birthday"),
            ],
            WAITING_FOR_MONTH: [
                CallbackQueryHandler(BirthdayHandler.new_member_month, pattern="^new_month_"),
                CallbackQueryHandler(BirthdayHandler.new_member_month, pattern="^skip_birthday"),
            ],
        },
        fallbacks=[],
    )
    application.add_handler(new_member_conv)

    # Start the scheduler in a background task
    async def start_scheduler():
        await scheduler.start()

    # Run the bot
    logger.info("Starting bot...")
    async with application:
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Start scheduler as background task
        scheduler_task = asyncio.create_task(start_scheduler())
        
        try:
            # Keep the application running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            scheduler.stop()
            await scheduler_task
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
