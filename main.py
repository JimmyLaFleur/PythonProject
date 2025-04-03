from datetime import datetime

import telebot
from telebot import types

import DBManager
import config


bot = telebot.TeleBot(config.TOKEN)
connection = DBManager.connect()
tmp_dict = {}

commands = types.ReplyKeyboardMarkup(resize_keyboard=True)
btn1 = types.KeyboardButton("Добавить трату")
btn2 = types.KeyboardButton("Мои траты")
btn3 = types.KeyboardButton("Удалить трату")
commands.add(btn1, btn3, btn2)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id, "Привет! Я помогу тебе следить за своими тратами и анализировать их!")
    print(message.from_user.id)
    DBManager.add_user(connection, message.from_user.id)

    bot.send_message(message.from_user.id, "Создал ячейку в базе")
    bot.send_message(message.chat.id, text="Привет, {0.first_name}! Я тестовый бот".format(message.from_user), reply_markup=commands)



@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    user_id = message.from_user.id
    if message.text == "/help":
        bot.send_message(user_id, "Мяу")
    elif message.text == "Добавить трату":
        tmp_dict[user_id] = {}
        tmp_dict[user_id]['user_id'] = user_id
        bot.send_message(user_id, "Напиши название траты (не больше 50 символов)")
        bot.register_next_step_handler(message, get_title)
    elif message.text == "Удалить трату":
        bot.send_message(user_id, "Напиши id траты")
        bot.register_next_step_handler(message, delete_spending)

    elif message.text == "Мои траты":
        tg_pk = DBManager.execute_query_with_return(connection, f'SELECT id FROM telegram_profiles WHERE user_id={user_id}')[0][0]
        user_pk = DBManager.execute_query_with_return(connection, f'SELECT id FROM users WHERE telegram_id={tg_pk}')[0][0]
        spendings = DBManager.execute_query_with_return(connection, f"SELECT * FROM spendings WHERE user_id = '{user_pk}'")
        print(spendings)
        for x in spendings:
            s = f"Трата\n id: {x[0]},\n цена: {x[2]},\n название: {x[3]},\n категория: {x[4]},\n дата {x[5]},\n рейтинг {x[6]}"

            bot.send_message(user_id, s)
    else:
        bot.send_message(user_id, "Я тебя не понимаю.")
# def check_cancel(message):
def delete_spending(message):
    user_id = message.from_user.id
    spending_id = message.text
    try:
        spending_id = int(spending_id)

        tg_pk = DBManager.execute_query_with_return(connection, f'SELECT id FROM telegram_profiles WHERE user_id={user_id}')[0][0]
        user_pk = DBManager.execute_query_with_return(connection, f'SELECT id FROM users WHERE telegram_id={tg_pk}')[0][0]
        DBManager.execute_query(connection,f"DELETE FROM spendings WHERE user_id = {user_pk} AND id = {spending_id}")

        bot.send_message(user_id, "Трата удалена.", reply_markup=commands)
    except Exception as e:
        bot.send_message(user_id, "id должно быть числом "+str(e))
        bot.register_next_step_handler(message, delete_spending)
def get_title(message):
    user_id = message.from_user.id
    title = message.text
    if len(title) > 50:
        bot.send_message(user_id, "Название траты должно быть *не больше 50 символов*. Напиши название траты ещё раз.")
        bot.register_next_step_handler(message, get_title)
    else:
        tmp_dict[user_id]['title'] = message.text
        bot.send_message(user_id, 'Напиши размер траты')
        bot.register_next_step_handler(message, get_price)

def get_price(message):
    user_id = message.from_user.id
    price = message.text
    try:
        price = int(price)
        tmp_dict[user_id]['price'] = price
        bot.send_message(user_id, 'Введи дату траты в формате ДД.ММ.ГГГГ или нажми кнопку "сегодня"')
        bot.register_next_step_handler(message, get_date)
    except Exception as e:
        bot.send_message(user_id, 'Напиши размер траты')
        bot.register_next_step_handler(message, get_price)

def get_date(message):
    user_id = message.from_user.id
    date_string = message.text
    try:
        date = datetime.strptime(date_string, '%d.%m.%Y')
        tmp_dict[user_id]['date'] = str(date)
        DBManager.add_spending(connection, tmp_dict[user_id])
        bot.send_message(user_id, 'Трата добавлена')
        del tmp_dict[user_id]
    except Exception as e:
        print("Format error: ", e)
        bot.send_message(user_id, 'Введи дату траты в формате ДД.ММ.ГГГГ или нажми кнопку "сегодня"')
        bot.register_next_step_handler(message, get_date)


bot.polling(none_stop=True, interval=0)
