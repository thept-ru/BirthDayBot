# Birthday Reminder Bot - Setup Guide

## Overview
Birthday Reminder Bot is a Telegram bot that automatically manages and greets users on their birthdays in group chats.

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- A Telegram bot token (get from [@BotFather](https://t.me/botfather))

## Installation & Setup

### 1. Clone or navigate to the project directory
```bash
cd /Users/alexeychekunkov/PetProjects/BirthDayBot
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure the bot
1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and add your bot token:
```
BOT_TOKEN=your_actual_bot_token_from_botfather
```

### 5. Run the bot
```bash
python main.py
```

The bot will:
- Initialize the database (SQLite by default)
- Start listening for commands
- Run the birthday scheduler at 8:00 AM daily

## Usage

### User Commands (in group chats)

| Command | Description |
|---------|-------------|
| `/start` | Welcome message |
| `/help` | Show all available commands |
| `/setbirthday` | Register your birthday for this chat |
| `/mybirthday` | View your registered birthday |
| `/updatebirthday` | Change your birthday |
| `/deletebirthday` | Remove your birthday from this chat |
| `/nextbirthdays` | Show upcoming birthdays (next 7 days) |
| `/listbirthdays` | Show all registered birthdays (admin only) |

### Workflow Example

1. **User registers their birthday:**
   - Send `/setbirthday` in a group chat
   - Select month via inline buttons
   - Enter day number (1-31)
   - Confirmation message received

2. **Daily greeting (at 8:00 AM):**
   - Bot checks database for birthdays matching today's date
   - Sends greeting message to each affected chat
   - Message format: "🎉 Сегодня день рождения у [names]! 🎂"

3. **View upcoming birthdays:**
   - Send `/nextbirthdays` to see birthdays in next 7 days

## Configuration

### Database
By default, the bot uses SQLite. To use PostgreSQL instead:

1. Install PostgreSQL support:
```bash
pip install psycopg2-binary
```

2. Update `.env`:
```
DATABASE_URL=postgresql://user:password@localhost/birthday_db
```

## Project Structure

```
BirthDayBot/
├── main.py              # Entry point, bot initialization
├── database.py          # SQLAlchemy models and database setup
├── handlers.py          # Command handlers and conversation flows
├── services.py          # Business logic for birthday operations
├── scheduler.py         # Daily greeting scheduler
├── utils.py             # Utility functions (validation, formatting)
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment configuration
└── .gitignore          # Git ignore file
```

## Features

✅ **Multi-chat support** - Each user can have different birthdays in different chats  
✅ **Privacy-focused** - Birthday data only visible to users who registered it  
✅ **Admin features** - List all birthdays (admin only)  
✅ **Automatic greetings** - Daily automatic birthday messages at 8:00 AM  
✅ **Data management** - Update/delete operations per chat  
✅ **Date validation** - Prevents invalid dates (e.g., 30.02)  
✅ **Scalable** - Handles thousands of chats and users  

## Troubleshooting

### Bot doesn't respond
1. Check that `BOT_TOKEN` is correctly set in `.env`
2. Ensure the bot is running: `python main.py`
3. Check logs for error messages

### Birthday messages not sending
1. Verify the bot has message permissions in the chat
2. Check server time is correct (messages sent at 8:00 AM server time)
3. Ensure user data is registered (use `/mybirthday` to verify)

### Database errors
1. Check that you have write permissions to the project directory
2. For SQLite: delete `birthday_bot.db` and restart to reinitialize
3. For PostgreSQL: verify connection string and database exists

## Development

To extend the bot:

1. Add new handlers in `handlers.py`
2. Add database operations in `services.py`
3. Add utilities in `utils.py`
4. Register new command handlers in `main.py`

## License
This project is open source and available under the MIT License.
