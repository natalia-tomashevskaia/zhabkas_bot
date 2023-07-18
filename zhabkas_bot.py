import sqlite3
import datetime
import os
from zoneinfo import ZoneInfo

import requests
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from requests import JSONDecodeError
import warnings

# Set up database connection
conn = sqlite3.connect('users.db')
c = conn.cursor()

# Create table if not exists
c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY)")

# Save (commit) the changes
conn.commit()

WEDNESDAY = 2
NOT_WEDNESDAY_PICTURE_PATH = 'not_wednesday.jpg'
BOT_ROOT_URI = os.getenv('ROOT_BOT_URI')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
UNSPLASH_CLIENT_ID = os.getenv('UNSPLASH_CLIENT_ID')
PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 5000
PROFILE = os.getenv('PROFILE')

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
    try:
        data = requests.get('https://api.unsplash.com/photos/random',
                            params={
                                "query": "frog",
                                "client_id": UNSPLASH_CLIENT_ID
                            }).json()

        photo = data['urls']['small']
        await bot.send_photo(chat_id=user_id,
                             photo=photo,
                             caption='It is Wednesday (in UTC+3), my dudes✨')
    except JSONDecodeError:
        await bot.send_message(chat_id=user_id,
                               text='Sorry, my dudes, no zhabka for now, try later')

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

async def send_wednesday_message_to_all_users():
    c.execute("SELECT id FROM users")
    user_ids = [row[0] for row in c.fetchall()]
    for user_id in user_ids:
        await send_wednesday_message(user_id)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('zhabka', get_zhabka_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('register', register_command))

    print("Starting the zhabkas bot...")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_wednesday_message_to_all_users, 'cron', day_of_week='2', hour='12', minute='00')
    scheduler.start()

    if PROFILE == 'prod':
        application.run_webhook(
            listen='0.0.0.0',
            port=PORT,
            webhook_url=BOT_ROOT_URI
        )
    else:
        application.run_polling()
