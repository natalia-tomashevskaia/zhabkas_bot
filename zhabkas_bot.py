import sqlite3
import datetime
import os
import requests
from aiohttp import web
from zoneinfo import ZoneInfo
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from requests import JSONDecodeError

# Set up database connection
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create table if not exists
c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)") 

# Save (commit) the changes
conn.commit()

# Set up global variables
WEDNESDAY = 2
NOT_WEDNESDAY_PICTURE_PATH = 'not_wednesday.jpg'
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
UNSPLASH_CLIENT_ID = os.getenv('UNSPLASH_CLIENT_ID') 
WEDNESDAY_PHOTO = None

# Set up calculations
def calc_days_to_wait_until_wednesday(current_day):
    if current_day < WEDNESDAY:
        return WEDNESDAY - current_day
    if current_day > WEDNESDAY:
        number_of_weekdays = 7
        return number_of_weekdays + WEDNESDAY - current_day
    if current_day == WEDNESDAY: 
        return 0

def calc_day_string(days_to_wait):
    if days_to_wait != 1:
        day_string = 'days'
    else:
        day_string = 'day'
    return day_string

async def get_zhabka_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id  # Retrieve the user ID from the chat
    current_day_in_moscow = datetime.datetime.now(tz=ZoneInfo('Europe/Moscow')).weekday()
    if current_day_in_moscow == WEDNESDAY:
        await send_wednesday_message(user_id)
    else:
        await send_non_wednesday_message(user_id, update, context, current_day_in_moscow)


async def send_wednesday_message(user_id):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    global WEDNESDAY_PHOTO
    if WEDNESDAY_PHOTO is None:
        try:
            data = requests.get('https://api.unsplash.com/photos/random',
                                params={
                                    "query": "frog",
                                    "client_id": UNSPLASH_CLIENT_ID
                                }).json()

            WEDNESDAY_PHOTO = data['urls']['small']
        except JSONDecodeError:
            await bot.send_message(chat_id=user_id,
                                   text='Sorry, my dudes, no zhabka for now, try later')
            return

    await bot.send_photo(chat_id=user_id,
                         photo=WEDNESDAY_PHOTO,
                         caption='It is Wednesday (in UTC+3), my dudes✨')

async def send_non_wednesday_message(user_id, update, context, current_day_in_moscow):
    days_to_wait = calc_days_to_wait_until_wednesday(current_day_in_moscow)
    day_string = calc_day_string(days_to_wait)
    await context.bot.send_photo(chat_id=user_id,
                                 photo=NOT_WEDNESDAY_PICTURE_PATH,
                                 caption=f'Have patience for {days_to_wait} more {day_string}, my pals')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Send /zhabka and see if today is Wednesday, my dudes! Send /register and receive a zhabka every Wednesday")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Welcome, my dudes!")

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id  # Retrieve the user ID from the chat
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    result = c.fetchone()
    if result is None:
        c.execute("INSERT INTO users VALUES (?)", (user_id,))
        conn.commit()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You're now registered to receive a frog message every Wednesday!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You're already registered!")

async def unregister_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat.id  # Retrieve the user ID from the chat
    c.execute("SELECT id FROM users WHERE id=?", (user_id,))
    result = c.fetchone()
    if result is not None:
        c.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You're now unregistered and won't receive a frog message every Wednesday!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You're not registered yet!")

async def send_wednesday_message_to_all_users():
    global WEDNESDAY_PHOTO
    WEDNESDAY_PHOTO = None  # Reset the Wednesday photo URL at the beginning of the day
    c.execute("SELECT id FROM users")
    user_ids = [row[0] for row in c.fetchall()]
    for user_id in user_ids:
        await send_wednesday_message(user_id)

# Set up a custom filter and a custom handler to avoid package conflicts
class AllMessagesFilter(object):
    def filter(self, message):
        return True

class CustomHandler(MessageHandler):
    def check_update(self, update):
        return True  # Always handle the update

async def handle_unknown_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if the message is a command
    if update.message and not update.message.text.startswith('/'):
        frog_ascii = """
   @..@
 (-----)
( >  < )
^^    ^^
        """
        await context.bot.send_message(chat_id=update.effective_chat.id, text=frog_ascii)

# Build the app and set up a cron expression
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('zhabka', get_zhabka_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('register', register_command))
    application.add_handler(CommandHandler('unregister', unregister_command))
    application.add_handler(CustomHandler(AllMessagesFilter(), handle_unknown_commands))

    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(send_wednesday_message_to_all_users, 'cron', day_of_week='2', hour='12', minute='00')
    scheduler.start()

    # Start the HTTP server
    app = web.Application()
    app.router.add_get('/', handle_healthcheck)
    web.run_app(app, port=int(os.environ.get("PORT", 8080)))

    application.run_polling()

    application.run_polling()
