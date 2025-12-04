from datetime import datetime
from typing import Tuple, Optional


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
