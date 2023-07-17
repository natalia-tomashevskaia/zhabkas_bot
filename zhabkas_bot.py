import datetime
import os
import requests
import argparse
from requests import JSONDecodeError
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

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
    current_day_in_moscow = datetime.datetime.now(tz=ZoneInfo('Europe/Moscow')).weekday()
    if current_day_in_moscow == WEDNESDAY:
        await send_wednesday_message(update, context)
    else:
        await send_non_wednesday_message(update, context, current_day_in_moscow)


async def send_wednesday_message(update, context):
    try:
        data = requests.get('https://api.unsplash.com/photos/random',
                            params={
                                "query": "frog",
                                "client_id": UNSPLASH_CLIENT_ID
                            }).json()

        photo = data['urls']['small']
        await context.bot.send_photo(chat_id=update.effective_chat.id,
                                     photo=photo,
                                     caption='It is Wednesday (in UTC+3), my dudes✨')
    except JSONDecodeError:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Sorry, my dudes, no zhabka for now, try later')


async def send_non_wednesday_message(update, context, current_day_in_moscow):
    days_to_wait = calc_days_to_wait_until_wednesday(current_day_in_moscow)
    day_string = calc_day_string(days_to_wait)
    await context.bot.send_photo(chat_id=update.effective_chat.id,
                                 photo=NOT_WEDNESDAY_PICTURE_PATH,
                                 caption=f'Have patience for {days_to_wait} more {day_string}, my pals')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Send /zhabka and see if today is Wednesday, my dudes!")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Welcome, my dudes!")


def assert_env_vars():
    assert TELEGRAM_BOT_TOKEN
    assert UNSPLASH_CLIENT_ID


def get_all_user_ids():
    try:
        response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates")
        data = response.json()
        user_ids = []

        for result in data['result']:
            user_id = result['message']['chat']['id']
            user_ids.append(user_id)

        return user_ids
    except requests.exceptions.RequestException as e:
        print(f"Error occurred while retrieving user IDs: {e}")
        return []


async def send_wednesday_message_to_all_users(user_ids):
    for user_id in user_ids:
        await send_wednesday_message(user_id)


if __name__ == '__main__':
    assert_env_vars()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('zhabka', get_zhabka_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('start', start_command))

    print("Starting the zhabkas bot...")

    args = argparse.ArgumentParser(description='Telegram bot script.')
    args.add_argument('--send_frog', action='store_true', help='Send a frog picture now')
    args = args.parse_args()

    if args.send_frog:
        user_ids = get_all_user_ids()
        application.run_async(send_wednesday_message_to_all_users(user_ids))
    else:
        if PROFILE == 'prod':
            application.run_webhook(
                listen='0.0.0.0',
                port=PORT,
                webhook_url=BOT_ROOT_URI
            )
        else:
            application.run_polling()

