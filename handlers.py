import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import SessionLocal
from services import BirthdayService
from utils import validate_date, parse_date_string, format_date

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_DATE = 1
WAITING_FOR_CONFIRMATION = 2

# Month names in Russian
MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}


class BirthdayHandler:
    """Handler for birthday-related commands"""

    @staticmethod
    async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        await update.message.reply_text(
            "🎂 Добро пожаловать в Birthday Reminder Bot!\n\n"
            "Я помогу вам организовать поздравления дней рождения в вашем чате.\n\n"
            "Используйте /help для списка команд."
        )

    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_text = (
            "📋 Доступные команды:\n\n"
            "/setbirthday - Зарегистрировать свой день рождения\n"
            "/mybirthday - Показать свой день рождения в этом чате\n"
            "/updatebirthday - Обновить день рождения\n"
            "/deletebirthday - Удалить день рождения\n"
            "/nextbirthdays - Ближайшие дни рождения (на неделю)\n"
            "/listbirthdays - Все дни рождения в чате (только для администраторов)\n"
            "/help - Эта справка\n\n"
            "💡 Формат даты: ДД.ММ (например, 25.12)"
        )
        await update.message.reply_text(help_text)

    @staticmethod
    async def set_birthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start birthday registration process"""
        keyboard = []
        
        # Create date picker keyboard (simplified: day and month buttons)
        for month in range(1, 13):
            keyboard.append([InlineKeyboardButton(MONTH_NAMES[month], callback_data=f"month_{month}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📅 Выберите месяц вашего дня рождения:",
            reply_markup=reply_markup
        )
        
        context.user_data['chat_id'] = update.message.chat_id
        return WAITING_FOR_DATE

    @staticmethod
    async def set_birthday_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle month selection"""
        query = update.callback_query
        await query.answer()

        month = int(query.data.split('_')[1])
        context.user_data['month'] = month

        # Ask for day
        await query.edit_message_text(
            text=f"📅 Выберите день (1-31) для {MONTH_NAMES[month]}:\n\n"
                 "Введите число:"
        )
        
        return WAITING_FOR_CONFIRMATION

    @staticmethod
    async def set_birthday_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle day input and save birthday"""
        try:
            day = int(update.message.text.strip())
            month = context.user_data.get('month')
            chat_id = context.user_data.get('chat_id')
            user_id = update.message.from_user.id
            username = update.message.from_user.username

            # Validate date
            is_valid, error_msg = validate_date(day, month)
            if not is_valid:
                await update.message.reply_text(error_msg)
                return WAITING_FOR_CONFIRMATION

            # Save to database
            db = SessionLocal()
            try:
                success, message = BirthdayService.register_birthday(
                    db, user_id, chat_id, day, month, username
                )
                await update.message.reply_text(message)
            finally:
                db.close()

            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите число.")
            return WAITING_FOR_CONFIRMATION

    @staticmethod
    async def my_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user's birthday in current chat"""
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id

        db = SessionLocal()
        try:
            birthday = BirthdayService.get_user_birthday(db, user_id, chat_id)
            if birthday:
                date_str = format_date(birthday.day, birthday.month)
                await update.message.reply_text(f"🎂 Ваш день рождения: {date_str}")
            else:
                await update.message.reply_text(
                    "❌ Вы еще не зарегистрировали свой день рождения в этом чате.\n"
                    "Используйте /setbirthday для регистрации."
                )
        finally:
            db.close()

    @staticmethod
    async def update_birthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start birthday update process"""
        keyboard = []
        
        for month in range(1, 13):
            keyboard.append([InlineKeyboardButton(MONTH_NAMES[month], callback_data=f"upd_month_{month}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📅 Выберите новый месяц вашего дня рождения:",
            reply_markup=reply_markup
        )
        
        context.user_data['chat_id'] = update.message.chat_id
        return WAITING_FOR_DATE

    @staticmethod
    async def update_birthday_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle month selection for update"""
        query = update.callback_query
        await query.answer()

        month = int(query.data.split('_')[2])
        context.user_data['month'] = month

        await query.edit_message_text(
            text=f"📅 Выберите день (1-31) для {MONTH_NAMES[month]}:\n\n"
                 "Введите число:"
        )
        
        return WAITING_FOR_CONFIRMATION

    @staticmethod
    async def update_birthday_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle day input and update birthday"""
        try:
            day = int(update.message.text.strip())
            month = context.user_data.get('month')
            chat_id = context.user_data.get('chat_id')
            user_id = update.message.from_user.id
            username = update.message.from_user.username

            # Validate date
            is_valid, error_msg = validate_date(day, month)
            if not is_valid:
                await update.message.reply_text(error_msg)
                return WAITING_FOR_CONFIRMATION

            # Update in database
            db = SessionLocal()
            try:
                success, message = BirthdayService.register_birthday(
                    db, user_id, chat_id, day, month, username
                )
                await update.message.reply_text(message)
            finally:
                db.close()

            return ConversationHandler.END

        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите число.")
            return WAITING_FOR_CONFIRMATION

    @staticmethod
    async def delete_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Delete user's birthday from current chat"""
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id

        db = SessionLocal()
        try:
            success, message = BirthdayService.delete_birthday(db, user_id, chat_id)
            await update.message.reply_text(message)
        finally:
            db.close()

    @staticmethod
    async def next_birthdays(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show upcoming birthdays in chat (next 7 days)"""
        chat_id = update.message.chat_id

        db = SessionLocal()
        try:
            upcoming = BirthdayService.get_upcoming_birthdays(db, chat_id, days_ahead=7)
            
            if not upcoming:
                await update.message.reply_text("📭 Нет предстоящих дней рождения на неделю.")
                return

            message = "🎂 Ближайшие дни рождения (на неделю):\n\n"
            for username, day, month, days_until in upcoming:
                date_str = format_date(day, month)
                if days_until == 0:
                    message += f"🎉 {username} - сегодня! ({date_str})\n"
                else:
                    message += f"📅 {username} - {date_str} (через {days_until} дн.)\n"

            await update.message.reply_text(message)
        finally:
            db.close()

    @staticmethod
    async def list_birthdays(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """List all birthdays in chat (admin only)"""
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id

        # Check if user is admin
        try:
            chat_member = await context.bot.get_chat_member(chat_id, user_id)
            if chat_member.status not in ['administrator', 'creator']:
                await update.message.reply_text("❌ Эта команда доступна только администраторам чата.")
                return
        except Exception as e:
            logger.error(f"Error checking admin status: {e}")
            await update.message.reply_text("❌ Ошибка при проверке прав доступа.")
            return

        db = SessionLocal()
        try:
            birthdays = BirthdayService.get_all_chat_birthdays(db, chat_id)
            
            if not birthdays:
                await update.message.reply_text("📭 В этом чате еще никто не зарегистрировал свой день рождения.")
                return

            message = "📋 Дни рождения в этом чате:\n\n"
            for username, day, month in sorted(birthdays, key=lambda x: (x[2], x[1])):
                date_str = format_date(day, month)
                message += f"• {username} - {date_str}\n"

            await update.message.reply_text(message)
        finally:
            db.close()

    @staticmethod
    async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel conversation"""
        await update.message.reply_text("❌ Операция отменена.")
        return ConversationHandler.END
