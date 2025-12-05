from datetime import datetime
from typing import Tuple, Optional
import asyncio
from telegram import Update
from telegram.error import TelegramError
import logging

logger = logging.getLogger(__name__)


def validate_date(day: int, month: int) -> Tuple[bool, str]:
    """
    Validate birthday date (day.month format)
    
    Args:
        day: Day of month (1-31)
        month: Month (1-12)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not (1 <= month <= 12):
        return False, "❌ Месяц должен быть от 1 до 12"
    
    # Days in each month (non-leap year)
    days_in_month = {
        1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30,
        7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
    }
    
    if not (1 <= day <= days_in_month[month]):
        return False, f"❌ День должен быть от 1 до {days_in_month[month]} для выбранного месяца"
    
    return True, ""


def parse_date_string(date_str: str) -> Optional[Tuple[int, int]]:
    """
    Parse date string in DD.MM format
    
    Args:
        date_str: Date string in DD.MM format
    
    Returns:
        Tuple of (day, month) or None if parsing failed
    """
    try:
        parts = date_str.strip().split('.')
        if len(parts) != 2:
            return None
        day, month = int(parts[0]), int(parts[1])
        is_valid, _ = validate_date(day, month)
        if is_valid:
            return day, month
        return None
    except (ValueError, IndexError):
        return None


def format_date(day: int, month: int) -> str:
    """Format birthday date for display"""
    return f"{day:02d}.{month:02d}"


def get_days_until_birthday(day: int, month: int) -> int:
    """
    Calculate days until next birthday
    
    Args:
        day: Day of month
        month: Month
    
    Returns:
        Number of days until next birthday (0-365)
    """
    today = datetime.now().date()
    this_year_birthday = datetime(today.year, month, day).date()
    
    if this_year_birthday >= today:
        return (this_year_birthday - today).days
    else:
        next_year_birthday = datetime(today.year + 1, month, day).date()
        return (next_year_birthday - today).days


def is_birthday_today(day: int, month: int) -> bool:
    """Check if given date is today"""
    today = datetime.now().date()
    return today.day == day and today.month == month


async def delete_message_after_delay(update: Update, delay_seconds: int = 30) -> None:
    """
    Delete user's command message after a delay
    
    Args:
        update: Telegram update object
        delay_seconds: Delay in seconds before deleting (default: 30)
    """
    try:
        # Check if bot has permission to delete messages
        chat_id = update.message.chat_id
        message_id = update.message.message_id
        
        # Try to get chat info to check if bot is admin
        if update.message.chat.type in ['group', 'supergroup']:
            await asyncio.sleep(delay_seconds)
            await update.get_bot().delete_message(chat_id=chat_id, message_id=message_id)
            logger.debug(f"Deleted command message {message_id} from chat {chat_id}")
    except TelegramError as e:
        # Bot might not have permission to delete messages
        logger.debug(f"Cannot delete message: {e}")
    except Exception as e:
        logger.error(f"Error deleting message: {e}")
