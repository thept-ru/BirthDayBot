from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from database import UserBirthday
from datetime import datetime
from typing import List, Optional, Tuple


class BirthdayService:
    """Service for managing birthday data"""

    @staticmethod
    def register_birthday(db: Session, user_id: int, chat_id: int, day: int, month: int, username: Optional[str] = None) -> Tuple[bool, str]:
        """
        Register or update a user's birthday for a specific chat
        
        Args:
            db: Database session
            user_id: Telegram user ID
            chat_id: Telegram chat ID
            day: Day of month
            month: Month
            username: Optional username for greeting
        
        Returns:
            Tuple of (success, message)
        """
        try:
            existing = db.query(UserBirthday).filter(
                and_(UserBirthday.user_id == user_id, UserBirthday.chat_id == chat_id)
            ).first()

            if existing:
                existing.day = day
                existing.month = month
                existing.username = username
                existing.updated_at = datetime.utcnow()
                db.commit()
                return True, f"✅ День рождения обновлен: {day:02d}.{month:02d}"
            else:
                birthday = UserBirthday(
                    user_id=user_id,
                    chat_id=chat_id,
                    day=day,
                    month=month,
                    username=username
                )
                db.add(birthday)
                db.commit()
                return True, f"✅ День рождения зарегистрирован: {day:02d}.{month:02d}"
        except Exception as e:
            db.rollback()
            return False, f"❌ Ошибка при сохранении: {str(e)}"

    @staticmethod
    def get_user_birthday(db: Session, user_id: int, chat_id: int) -> Optional[UserBirthday]:
        """Get user's birthday for a specific chat"""
        return db.query(UserBirthday).filter(
            and_(UserBirthday.user_id == user_id, UserBirthday.chat_id == chat_id)
        ).first()

    @staticmethod
    def delete_birthday(db: Session, user_id: int, chat_id: int) -> Tuple[bool, str]:
        """Delete user's birthday for a specific chat"""
        try:
            birthday = db.query(UserBirthday).filter(
                and_(UserBirthday.user_id == user_id, UserBirthday.chat_id == chat_id)
            ).first()

            if birthday:
                db.delete(birthday)
                db.commit()
                return True, "✅ Ваши данные удалены из этого чата"
            else:
                return False, "❌ Данные не найдены"
        except Exception as e:
            db.rollback()
            return False, f"❌ Ошибка при удалении: {str(e)}"

    @staticmethod
    def get_birthdays_today(db: Session) -> List[Tuple[int, List[str]]]:
        """
        Get all birthdays for today grouped by chat
        
        Returns:
            List of tuples: (chat_id, [usernames])
        """
        from utils import is_birthday_today
        
        today = datetime.now().date()
        birthdays = db.query(UserBirthday).filter(
            and_(UserBirthday.day == today.day, UserBirthday.month == today.month)
        ).all()

        # Group by chat_id
        chats_dict = {}
        for birthday in birthdays:
            if birthday.chat_id not in chats_dict:
                chats_dict[birthday.chat_id] = []
            username = birthday.username or f"User {birthday.user_id}"
            chats_dict[birthday.chat_id].append(username)

        return list(chats_dict.items())

    @staticmethod
    def get_upcoming_birthdays(db: Session, chat_id: int, days_ahead: int = 7) -> List[Tuple[str, int, int]]:
        """
        Get upcoming birthdays in a chat
        
        Args:
            db: Database session
            chat_id: Chat ID
            days_ahead: Number of days to look ahead
        
        Returns:
            List of tuples: (username, day, month, days_until)
        """
        from utils import get_days_until_birthday
        
        birthdays = db.query(UserBirthday).filter(UserBirthday.chat_id == chat_id).all()
        
        upcoming = []
        for birthday in birthdays:
            days_until = get_days_until_birthday(birthday.day, birthday.month)
            if 0 <= days_until <= days_ahead:
                username = birthday.username or f"User {birthday.user_id}"
                upcoming.append((username, birthday.day, birthday.month, days_until))
        
        # Sort by days_until
        return sorted(upcoming, key=lambda x: x[3])

    @staticmethod
    def get_all_chat_birthdays(db: Session, chat_id: int) -> List[Tuple[str, int, int]]:
        """
        Get all birthdays in a chat (for admin listing)
        
        Args:
            db: Database session
            chat_id: Chat ID
        
        Returns:
            List of tuples: (username, day, month)
        """
        birthdays = db.query(UserBirthday).filter(UserBirthday.chat_id == chat_id).all()
        
        result = []
        for birthday in birthdays:
            username = birthday.username or f"User {birthday.user_id}"
            result.append((username, birthday.day, birthday.month))
        
        return result

    @staticmethod
    def count_birthdays_in_chat(db: Session, chat_id: int) -> int:
        """Count number of registered birthdays in a chat"""
        return db.query(UserBirthday).filter(UserBirthday.chat_id == chat_id).count()
