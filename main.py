from datetime import datetime
import sqlite3
import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.TOKEN)
conn = sqlite3.connect('finance_bot.db', check_same_thread=False)
cursor = conn.cursor()

def init_db():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE
    )''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS spendings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        price INTEGER,
        title TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.commit()

init_db()

tmp_dict = {}
commands = types.ReplyKeyboardMarkup(resize_keyboard=True)
commands.add(types.KeyboardButton("Добавить трату"),
             types.KeyboardButton("Удалить трату"),
             types.KeyboardButton("Мои траты"))

@bot.message_handler(commands=['start'])
def start(message):
    cursor.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (message.from_user.id,))
    conn.commit()
    bot.send_message(message.chat.id,
                     text=f"Привет, {message.from_user.first_name}! Я бот для учета расходов",
                     reply_markup=commands)

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    user_id = message.from_user.id
    if message.text == "/help":
        bot.send_message(user_id, "Команды: Добавить трату, Удалить трату, Мои траты")
    elif message.text == "Добавить трату":
        tmp_dict[user_id] = {'user_id': user_id}
        bot.send_message(user_id, "Напиши название траты (не больше 50 символов)")
        bot.register_next_step_handler(message, get_title)
    elif message.text == "Удалить трату":
        bot.send_message(user_id, "Напиши id траты")
        bot.register_next_step_handler(message, delete_spending)
    elif message.text == "Мои траты":
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_id,))
        user_pk = cursor.fetchone()[0]
        cursor.execute('SELECT * FROM spendings WHERE user_id = ?', (user_pk,))
        spendings = cursor.fetchall()
        if not spendings:
            bot.send_message(user_id, "У вас пока нет трат")
        else:
            for spending in spendings:
                s = (f"Трата\nid: {spending[0]},\nцена: {spending[2]},\n"
                     f"название: {spending[3]},\nдата: {spending[4]}")
                bot.send_message(user_id, s)
    else:
        bot.send_message(user_id, "Я тебя не понимаю.")

def delete_spending(message):
    user_id = message.from_user.id
    try:
        spending_id = int(message.text)
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_id,))
        user_pk = cursor.fetchone()[0]
        cursor.execute('DELETE FROM spendings WHERE user_id = ? AND id = ?', (user_pk, spending_id))
        conn.commit()
        if cursor.rowcount > 0:
            bot.send_message(user_id, "Трата удалена.", reply_markup=commands)
        else:
            bot.send_message(user_id, "Трата с таким ID не найдена.")
    except Exception as e:
        bot.send_message(user_id, f"ID должно быть числом. Ошибка: {str(e)}")
        bot.register_next_step_handler(message, delete_spending)

def get_title(message):
    user_id = message.from_user.id
    title = message.text
    if len(title) > 50:
        bot.send_message(user_id, "Название траты слишком длинное. Введите ещё раз.")
        bot.register_next_step_handler(message, get_title)
    else:
        tmp_dict[user_id]['title'] = title
        bot.send_message(user_id, 'Напиши сумму траты')
        bot.register_next_step_handler(message, get_price)

def get_price(message):
    user_id = message.from_user.id
    try:
        tmp_dict[user_id]['price'] = int(message.text)
        bot.send_message(user_id, 'Введи дату в формате ДД.ММ.ГГГГ или "сегодня"')
        bot.register_next_step_handler(message, get_date)
    except:
        bot.send_message(user_id, 'Сумма должна быть числом. Повторите ввод.')
        bot.register_next_step_handler(message, get_price)

def get_date(message):
    user_id = message.from_user.id
    date_string = message.text.lower()
    try:
        date = datetime.now() if date_string == "сегодня" else datetime.strptime(date_string, '%d.%m.%Y')
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (user_id,))
        user_pk = cursor.fetchone()[0]
        cursor.execute('''
        INSERT INTO spendings (user_id, price, title, date)
        VALUES (?, ?, ?, ?)''', (
            user_pk,
            tmp_dict[user_id]['price'],
            tmp_dict[user_id]['title'],
            date.strftime('%Y-%m-%d')
        ))
        conn.commit()
        bot.send_message(user_id, 'Трата добавлена')
        del tmp_dict[user_id]
    except:
        bot.send_message(user_id, 'Неверный формат даты. Повторите ввод.')
        bot.register_next_step_handler(message, get_date)

if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    finally:
        conn.close()
