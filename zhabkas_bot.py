import os
import datetime
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from replit import db
from apscheduler.schedulers.background import BackgroundScheduler

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
                                   text="Send /zhabka and see if today is Wednesday, my dudes! "
                                        "Send /register and receive a zhabka every Wednesday")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Welcome, my dudes!")


async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.chat.id)  # Retrieve the user ID from the chat
    if user_id not in db.keys():  # Check if user_id is not in the database
        db[user_id] = "registered"  # Add user_id to the database
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You're now registered to receive a frog message every Wednesday!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You're already registered!")

async def send_wednesday_message_to_all_users():
    for user_id in db.keys():
        await send_wednesday_message(int(user_id))  # Convert user_id back to int before sending the message


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

    application.run_polling()
