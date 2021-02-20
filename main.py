from configs import *
from telegram.ext import *
import pickle
from urls import *
from telegram import *
from lib import *
import time
import logging
import random
import sqlite3

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

STATE_SIGNUP, STATE_USER, STATE_CLIENTS, STATE_FEEDBACK, STATE_ABOUT, STATE_PROMO = range(6)

conn = sqlite3.connect(database_path, check_same_thread=False)
cursor = conn.cursor()

BTN_CLIENTS, BTN_ABOUT, BTN_FEEDBACK, BTN_FOR_SPONSORS, BTN_PROMO, BTN_RAMADAN = (
    "🛍 Маҳсулот ва хизматлар", "ℹ️ Биз ҳақимизда", "💬 Алоқа учун", "🤝 Ҳамкорлик учун", "💝 Промо-кодлар", "Ramazon"
)
main_buttons = ReplyKeyboardMarkup([
    [BTN_CLIENTS], [BTN_FOR_SPONSORS, BTN_PROMO], [BTN_ABOUT, BTN_FEEDBACK]
], resize_keyboard=True)

ID_1, ID_2, ID_3, BACK = (
    '🧬 Лактовита', '♻️ Массажёр', '🏥 «Real Medical» тиббиёт маркази', '⬅️ Орқага'
)
client_buttons = ReplyKeyboardMarkup([
    [ID_1, ID_2], [ID_3], [BACK]
], resize_keyboard=True)

button_back = ReplyKeyboardMarkup([
    [KeyboardButton(BACK)]
], resize_keyboard=True)


# Greet the new user. Pass to the step of registration.
def start(update, context):
    user = update.message.from_user
    telegram_id = update.message.chat_id
    update.message.reply_html(greeting_message)
    db_id = cursor.execute("""
    SELECT ID
    FROM Users 
    WHERE telegram_id = '{}'
    """.format(telegram_id)).fetchall()
    if len(db_id) == 0:
        logger.info("New user started the bot. Username: %s and F_Name: %s, L_Name: %s", user.username, user.first_name,
                    user.last_name)
        update.message.reply_html(user_name)
        return STATE_SIGNUP
    else:
        logger.info('User %s continued using bot.', telegram_id)
        main_menu(update, context)
        return STATE_USER


def register(update, context):
    user = update.message.from_user
    first_name = user.first_name
    last_name = user.last_name
    username = user.username
    telegram_id = update.message.chat_id
    users_input = update.message.text
    unique_code = random.choice(alphabet) + '-' + str(random.randint(1000, 10000))
    cursor.execute("""
    INSERT INTO Users VALUES (NULL, '{}', '{}', '{}', 0, '{}')
    """.format(telegram_id, users_input, username, unique_code))
    conn.commit()
    button = [[KeyboardButton(phone_send_btn, request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(button, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_html(request_phone, reply_markup=reply_markup)


def reg_complete(update, context):
    phone = update.message.contact['phone_number']
    user = update.message.from_user
    username = user.username
    telegram_id = update.message.chat_id
    cursor.execute("""
    UPDATE Users
    SET phone_number = '{}'
    WHERE telegram_id = '{}'
    """.format(phone, telegram_id))
    conn.commit()
    update.message.reply_html(registration_complete_msg)
    main_menu(update, context)
    logger.info("User %s has been added to database. Phone number: %s", telegram_id, phone)
    return STATE_USER


def main_menu(update, context):
    update.message.reply_html(main_menu_text, reply_markup=main_buttons)
    return STATE_USER


def clients(update, context):
    update.message.reply_html(clients_choose_text, reply_markup=client_buttons)
    return STATE_CLIENTS


def id_1(update, context):
    update.message.reply_photo(lactovita_pic)


def id_2(update, context):
    update.message.reply_html("Id_2 tanlandi")


def id_3(update, context):
    update.message.reply_html("Id_3 tanlandi")


def back_to_menu(update, context):
    main_menu(update, context)
    return STATE_USER


def about(update, context):
    update.message.reply_text("ABOUT",
                              reply_markup=button_back)
    return STATE_ABOUT


def feedback(update, context):
    try:
        update.message.reply_text("Yozing yozmachilikni bo'tam",
                                  reply_markup=button_back)
        return STATE_FEEDBACK
    except Exception as e:
        print(e)


def for_sponsors(update, context):
    update.message.reply_text("for sponsors")


def promo(update, context):
    update.message.reply_text("promo",
                              reply_markup=button_back)
    return STATE_PROMO


# Coming soon. Will be using this function during Ramadan
def ramadan(update, context):
    update.message.reply_text("ramazon tanlandi")


def help_menu(update, context):
    update.message.reply_text("Otabek, help menuga ham tekst yozvorilik")


def main():
    updater = Updater(token=API_TOKEN, workers=100)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start, run_async=True)],
        states={
            STATE_SIGNUP: [
                MessageHandler(Filters.text, register),
                MessageHandler(Filters.contact, reg_complete)
            ],
            STATE_USER: [
                MessageHandler(Filters.regex('^(' + BTN_CLIENTS + ')$'), clients),
                MessageHandler(Filters.regex('^(' + BTN_ABOUT + ')$'), about),
                MessageHandler(Filters.regex('^(' + BTN_FEEDBACK + ')$'), feedback),
                MessageHandler(Filters.regex('^(' + BTN_FOR_SPONSORS + ')$'), for_sponsors),
                MessageHandler(Filters.regex('^(' + BTN_PROMO + ')$'), promo),
                # MessageHandler(Filters.regex('^(' + BTN_RAMADAN + ')$'), ramadan)
            ],
            STATE_CLIENTS: [
                MessageHandler(Filters.regex('^(' + ID_1 + ')$'), id_1),
                MessageHandler(Filters.regex('^(' + ID_2 + ')$'), id_2),
                MessageHandler(Filters.regex('^(' + ID_3 + ')$'), id_3),
                MessageHandler(Filters.regex('^(' + BACK + ')$'), back_to_menu)
            ],
            STATE_FEEDBACK: [
                MessageHandler(Filters.regex('^(' + BACK + ')$'), back_to_menu)
            ],
            STATE_ABOUT: [
                MessageHandler(Filters.regex('^(' + BACK + ')$'), back_to_menu)
            ],
            STATE_PROMO: [
                MessageHandler(Filters.regex('^(' + BACK + ')$'), back_to_menu)
            ],
        },
        fallbacks=[CommandHandler('menu', clients),
                   CommandHandler('start', main_menu),
                   CommandHandler('help', help_menu)]
    )
    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
