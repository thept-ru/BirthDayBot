import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import SessionLocal
from services import BirthdayService
from utils import validate_date, parse_date_string, format_date, delete_message_after_delay
import asyncio

logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_DAY = 1
WAITING_FOR_MONTH = 2

# Month names in Russian (abbreviated)
MONTH_NAMES = {
    1: "янв.", 2: "февр.", 3: "март", 4: "апр.",
    5: "май", 6: "июнь", 7: "июль", 8: "авг.",
    9: "сент.", 10: "окт.", 11: "нояб.", 12: "дек."
}

# Full month names for messages
MONTH_NAMES_FULL = {
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
            "💡 Выбирайте дату нажатием кнопок!"
        )
        await update.message.reply_text(help_text)
        # Delete command message after 30 seconds
        asyncio.create_task(delete_message_after_delay(update, delay_seconds=30))

    @staticmethod
    async def set_birthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start birthday registration process"""
        keyboard = []
        
        # Create day buttons (7 days per row)
        for i in range(1, 32, 7):
            row = []
            for j in range(7):
                day = i + j
                if day <= 31:
                    row.append(InlineKeyboardButton(f"{day:2d}", callback_data=f"set_day_{day}"))
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📅 Выберите день вашего дня рождения:\n(1-31)",
            reply_markup=reply_markup
        )
        
        context.user_data['chat_id'] = update.message.chat_id
        return WAITING_FOR_DAY

    @staticmethod
    async def set_birthday_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle day selection"""
        query = update.callback_query
        await query.answer()

        day = int(query.data.split('_')[2])
        context.user_data['day'] = day

        # Create month buttons (3 months per row)
        keyboard = []
        for i in range(1, 13, 3):
            row = []
            for j in range(3):
                month = i + j
                if month <= 12:
                    row.append(InlineKeyboardButton(MONTH_NAMES[month], callback_data=f"set_month_{month}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"📅 Выберите месяц ({day}-го число):",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_MONTH

    @staticmethod
    async def set_birthday_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle month selection and save birthday"""
        query = update.callback_query
        await query.answer()
        
        month = int(query.data.split('_')[2])
        day = context.user_data.get('day')
        chat_id = context.user_data.get('chat_id')
        user_id = query.from_user.id
        username = query.from_user.username

        # Validate date
        is_valid, error_msg = validate_date(day, month)
        if not is_valid:
            await query.answer(error_msg, show_alert=True)
            return WAITING_FOR_MONTH

        # Save to database
        db = SessionLocal()
        try:
            success, message = BirthdayService.register_birthday(
                db, user_id, chat_id, day, month, username
            )
            await query.edit_message_text(text=message)
        finally:
            db.close()

        return ConversationHandler.END

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
        # Delete command message after 30 seconds
        asyncio.create_task(delete_message_after_delay(update, delay_seconds=30))

    @staticmethod
    async def update_birthday_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Start birthday update process"""
        keyboard = []
        
        # Create day buttons (7 days per row)
        for i in range(1, 32, 7):
            row = []
            for j in range(7):
                day = i + j
                if day <= 31:
                    row.append(InlineKeyboardButton(f"{day:2d}", callback_data=f"upd_day_{day}"))
            keyboard.append(row)

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "📅 Выберите день вашего дня рождения:\n(1-31)",
            reply_markup=reply_markup
        )
        
        context.user_data['chat_id'] = update.message.chat_id
        return WAITING_FOR_DAY

    @staticmethod
    async def update_birthday_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle day selection for update"""
        query = update.callback_query
        await query.answer()

        day = int(query.data.split('_')[2])
        context.user_data['day'] = day

        # Create month buttons (3 months per row)
        keyboard = []
        for i in range(1, 13, 3):
            row = []
            for j in range(3):
                month = i + j
                if month <= 12:
                    row.append(InlineKeyboardButton(MONTH_NAMES[month], callback_data=f"upd_month_{month}"))
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"📅 Выберите месяц ({day}-го число):",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_MONTH

    @staticmethod
    async def update_birthday_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle month selection and update birthday"""
        query = update.callback_query
        await query.answer()
        
        month = int(query.data.split('_')[2])
        day = context.user_data.get('day')
        chat_id = context.user_data.get('chat_id')
        user_id = query.from_user.id
        username = query.from_user.username

        # Validate date
        is_valid, error_msg = validate_date(day, month)
        if not is_valid:
            await query.answer(error_msg, show_alert=True)
            return WAITING_FOR_MONTH

        # Update in database
        db = SessionLocal()
        try:
            success, message = BirthdayService.register_birthday(
                db, user_id, chat_id, day, month, username
            )
            await query.edit_message_text(text=message)
        finally:
            db.close()

        return ConversationHandler.END

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
        # Delete command message after 30 seconds
        asyncio.create_task(delete_message_after_delay(update, delay_seconds=30))

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
        # Delete command message after 30 seconds
        asyncio.create_task(delete_message_after_delay(update, delay_seconds=30))

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
        # Delete command message after 30 seconds
        asyncio.create_task(delete_message_after_delay(update, delay_seconds=30))

    @staticmethod
    async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancel conversation"""
        await update.message.reply_text("❌ Операция отменена.")
        return ConversationHandler.END

    @staticmethod
    async def new_member_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Welcome new members and ask for birthday registration"""
        for member in update.message.new_chat_members:
            # Skip if it's a bot
            if member.is_bot:
                continue
            
            # Check if user already has birthday registered
            db = SessionLocal()
            try:
                existing_birthday = BirthdayService.get_user_birthday(
                    db, member.id, update.message.chat_id
                )
                if existing_birthday:
                    # User already has birthday registered
                    continue
            finally:
                db.close()
            
            welcome_text = (
                f"👋 Добро пожаловать в чат, {member.first_name}!\n\n"
                f"🎂 Хотели бы вы зарегистрировать свой день рождения?\n"
                f"Тогда все смогут поздравить вас в этот день!\n\n"
                f"Выберите день вашего дня рождения:"
            )
            
            # Create day buttons for new members (7 days per row)
            keyboard = []
            for i in range(1, 32, 7):
                row = []
                for j in range(7):
                    day = i + j
                    if day <= 31:
                        row.append(InlineKeyboardButton(f"{day:2d}", callback_data=f"new_day_{day}"))
                keyboard.append(row)
            
            # Add skip button
            keyboard.append([InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_birthday")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await update.message.reply_text(
                    welcome_text,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Error welcoming new member: {e}")

    @staticmethod
    async def new_member_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle day selection for new members"""
        query = update.callback_query
        await query.answer()
        
        # Skip button handler
        if query.data == "skip_birthday":
            await query.edit_message_text("✅ Вы всегда можете зарегистрировать день рождения позже с помощью /setbirthday")
            return ConversationHandler.END
        
        day = int(query.data.split('_')[2])
        context.user_data['day'] = day
        context.user_data['chat_id'] = query.message.chat_id
        context.user_data['is_new_member'] = True

        # Create month buttons (3 months per row)
        keyboard = []
        for i in range(1, 13, 3):
            row = []
            for j in range(3):
                month = i + j
                if month <= 12:
                    row.append(InlineKeyboardButton(MONTH_NAMES[month], callback_data=f"new_month_{month}"))
            keyboard.append(row)
        
        # Add skip button
        keyboard.append([InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_birthday")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"📅 Выберите месяц ({day}-го число):",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_MONTH

    @staticmethod
    async def new_member_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle month selection for new members and save birthday"""
        query = update.callback_query
        await query.answer()
        
        # Skip button handler
        if query.data == "skip_birthday":
            await query.edit_message_text("✅ Вы всегда можете зарегистрировать день рождения позже с помощью /setbirthday")
            return ConversationHandler.END
        
        month = int(query.data.split('_')[2])
        day = context.user_data.get('day')
        chat_id = context.user_data.get('chat_id')
        user_id = query.from_user.id
        username = query.from_user.username

        # Validate date
        is_valid, error_msg = validate_date(day, month)
        if not is_valid:
            await query.answer(error_msg, show_alert=True)
            return WAITING_FOR_MONTH

        # Save to database
        db = SessionLocal()
        try:
            success, message = BirthdayService.register_birthday(
                db, user_id, chat_id, day, month, username
            )
            await query.edit_message_text(text=message)
        finally:
            db.close()

        return ConversationHandler.END
