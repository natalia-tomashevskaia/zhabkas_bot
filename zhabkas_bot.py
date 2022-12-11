import datetime
import os
from zoneinfo import ZoneInfo

import requests
from requests import JSONDecodeError
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

NOT_WEDNESDAY_PICTURE_PATH = 'not_wednesday.jpg'
WEDNESDAY = 2
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
UNSPLASH_CLIENT_ID = os.getenv('UNSPLASH_CLIENT_ID')


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
    current_day_in_moscow = datetime.datetime.now(tz=ZoneInfo('Europe/Moscow')).today().weekday()
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
                                       text='sorry, my dudes, no zhabka for now, try later')


async def send_non_wednesday_message(update, context, current_day_in_moscow):
    days_to_wait = calc_days_to_wait_until_wednesday(current_day_in_moscow)
    day_string = calc_day_string(days_to_wait)
    await context.bot.send_photo(chat_id=update.effective_chat.id,
                                 photo=NOT_WEDNESDAY_PICTURE_PATH,
                                 caption=f'have patience for {days_to_wait} more {day_string}, my pals')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="send /zhabka and see if today is Wednesday, my dudes!")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="welcome, my dudes!")


def assert_env_vars():
    assert TELEGRAM_BOT_TOKEN
    assert UNSPLASH_CLIENT_ID


if __name__ == '__main__':
    assert_env_vars()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('zhabka', get_zhabka_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('start', start_command))

    print("Starting the zhabkas bot...")
    application.run_polling()
