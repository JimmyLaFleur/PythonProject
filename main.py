from datetime import datetime
import sqlite3
import telebot
from telebot import types
import config

bot = telebot.TeleBot(config.TOKEN)
conn = sqlite3.connect('finance_bot.db', check_same_thread=False)
cursor = conn.cursor()

tmp_dict = {}

commands = types.ReplyKeyboardMarkup(resize_keyboard=True)
commands.add(types.KeyboardButton("Добавить трату"))
commands.add(types.KeyboardButton("Удалить трату"))
commands.add(types.KeyboardButton("Мои траты"))
commands.add(types.KeyboardButton("Создать мероприятие"))
commands.add(types.KeyboardButton("Удалить мероприятие"))
commands.add(types.KeyboardButton("Рассчитать долги"))


@bot.message_handler(commands=['start'])
def start(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    cursor.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (username,))
    conn.commit()

    bot.send_message(message.chat.id,
                     text=f"Привет, {message.from_user.first_name}! Я бот для учета расходов",
                     reply_markup=commands)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    username = message.from_user.username or f"id_{message.from_user.id}"

    if message.text == "/help":
        bot.send_message(message.chat.id, "Мяу")
    elif message.text == "Добавить трату":
        tmp_dict[username] = {}
        bot.send_message(message.chat.id, "Напиши название траты (не больше 50 символов)")
        bot.register_next_step_handler(message, get_title)
    elif message.text == "Удалить трату":
        bot.send_message(message.chat.id, "Напиши id траты")
        bot.register_next_step_handler(message, delete_spending)
    elif message.text == "Мои траты":
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (username,))
        result = cursor.fetchone()
        if not result:
            bot.send_message(message.chat.id, "Пользователь не найден.")
            return

        user_pk = result[0]
        cursor.execute('SELECT * FROM spendings WHERE user_id = ?', (user_pk,))
        spendings = cursor.fetchall()

        if not spendings:
            bot.send_message(message.chat.id, "У вас пока нет трат")
        else:
            for spending in spendings:
                s = (f"Трата\nid: {spending[0]},\nцена: {spending[2]},\n"
                     f"название: {spending[3]},\nдата: {spending[4]}")
                bot.send_message(message.chat.id, s)
    elif message.text == "Создать мероприятие":
        user_id = message.from_user.id
        tmp_dict[user_id] = {}
        bot.send_message(user_id, "Введите название мероприятия:")
        bot.register_next_step_handler(message, get_event_title)
    elif message.text == "Удалить мероприятие":
        bot.send_message(message.chat.id, "Введите название или ID мероприятия, которое нужно удалить:")
        bot.register_next_step_handler(message, delete_event_handler)
    elif message.text == "Рассчитать долги":
        bot.send_message(message.chat.id, "Введите ID мероприятия:")
        bot.register_next_step_handler(message, calculate_debts)
    else:
        bot.send_message(message.chat.id, "Я тебя не понимаю.")

def calculate_debts(message):
    try:
        event_id = int(message.text.strip())

        # Получаем всех участников
        cursor.execute('''
            SELECT users.id, users.telegram_id
            FROM users
            JOIN event_participants ON users.id = event_participants.user_id
            WHERE event_participants.event_id = ?
        ''', (event_id,))
        participants = cursor.fetchall()

        if not participants:
            bot.send_message(message.chat.id, "Участники мероприятия не найдены.")
            return

        user_ids = [p[0] for p in participants]
        id_to_username = {p[0]: p[1] for p in participants}

        # Получаем все траты этих участников
        cursor.execute(f'''
            SELECT user_id, SUM(price)
            FROM spendings
            WHERE user_id IN ({','.join('?' * len(user_ids))})
            GROUP BY user_id
        ''', user_ids)
        user_spendings = dict(cursor.fetchall())

        # Считаем среднюю трату
        total = sum(user_spendings.get(uid, 0) for uid in user_ids)
        avg = total / len(user_ids)

        # Считаем, кто сколько должен
        balances = {uid: user_spendings.get(uid, 0) - avg for uid in user_ids}

        # Список долгов
        debts = []

        creditors = [(uid, bal) for uid, bal in balances.items() if bal > 0]
        debtors = [(uid, -bal) for uid, bal in balances.items() if bal < 0]

        creditor_idx = 0
        for debtor_id, debt_amount in debtors:
            while debt_amount > 0 and creditor_idx < len(creditors):
                creditor_id, credit_amount = creditors[creditor_idx]
                payment = min(debt_amount, credit_amount)
                debts.append((debtor_id, creditor_id, round(payment, 2)))
                debt_amount -= payment
                credit_amount -= payment
                if credit_amount == 0:
                    creditor_idx += 1
                else:
                    creditors[creditor_idx] = (creditor_id, credit_amount)

        # Вывод
        if not debts:
            bot.send_message(message.chat.id, "Никто никому ничего не должен.")
        else:
            for debtor, creditor, amount in debts:
                bot.send_message(message.chat.id, f"@{id_to_username[debtor]} должен(а) @{id_to_username[creditor]} {amount} руб.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при расчёте долгов: {str(e)}")
def delete_event_handler(message):
    user_input = message.text.strip()

    # Пробуем как ID
    if user_input.isdigit():
        cursor.execute("SELECT id FROM events WHERE id = ?", (int(user_input),))
    else:
        cursor.execute("SELECT id FROM events WHERE title = ?", (user_input,))

    event = cursor.fetchone()
    if not event:
        bot.send_message(message.chat.id, "Мероприятие не найдено.")
        return

    event_id = event[0]

    # Удаляем участников и само мероприятие
    cursor.execute("DELETE FROM event_participants WHERE event_id = ?", (event_id,))
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()

    bot.send_message(message.chat.id, f"Мероприятие с ID {event_id} удалено.")


def delete_spending(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    spending_id = message.text
    try:
        spending_id = int(spending_id)
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (username,))
        user_pk = cursor.fetchone()[0]
        cursor.execute('DELETE FROM spendings WHERE user_id = ? AND id = ?', (user_pk, spending_id))
        conn.commit()

        if cursor.rowcount > 0:
            bot.send_message(message.chat.id, "Трата удалена.", reply_markup=commands)
        else:
            bot.send_message(message.chat.id, "Трата с таким ID не найдена.")
    except Exception as e:
        bot.send_message(message.chat.id, f"ID должно быть числом. Ошибка: {str(e)}")
        bot.register_next_step_handler(message, delete_spending)


def get_title(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    title = message.text.strip()
    if len(title) > 50:
        bot.send_message(message.chat.id, "Название траты должно быть не больше 50 символов. Попробуй снова.")
        bot.register_next_step_handler(message, get_title)
    else:
        tmp_dict[username]['title'] = title
        bot.send_message(message.chat.id, 'Напиши размер траты')
        bot.register_next_step_handler(message, get_price)


def get_price(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    try:
        price = int(message.text.strip())
        tmp_dict[username]['price'] = price
        bot.send_message(message.chat.id, 'Введи дату траты в формате ДД.ММ.ГГГГ или напиши "сегодня"')
        bot.register_next_step_handler(message, get_date)
    except:
        bot.send_message(message.chat.id, 'Размер траты должен быть числом. Попробуй еще раз')
        bot.register_next_step_handler(message, get_price)


def get_date(message):
    username = message.from_user.username or f"id_{message.from_user.id}"
    date_string = message.text.strip().lower()

    try:
        if date_string == "сегодня":
            date = datetime.now().strftime('%Y-%m-%d')
        else:
            date = datetime.strptime(date_string, '%d.%m.%Y').strftime('%Y-%m-%d')

        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (username,))
        user_pk = cursor.fetchone()[0]

        cursor.execute('''
        INSERT INTO spendings (user_id, price, title, date)
        VALUES (?, ?, ?, ?)
        ''', (user_pk, tmp_dict[username]['price'], tmp_dict[username]['title'], date))
        conn.commit()

        bot.send_message(message.chat.id, 'Трата добавлена')
        del tmp_dict[username]
    except Exception as e:
        bot.send_message(message.chat.id, 'Неверный формат даты. Попробуй снова')
        bot.register_next_step_handler(message, get_date)

def get_event_title(message):
    user_id = message.from_user.id
    title = message.text.strip()
    if not title:
        bot.send_message(user_id, "Название не может быть пустым. Введите название мероприятия:")
        bot.register_next_step_handler(message, get_event_title)
        return

    tmp_dict[user_id]['event_title'] = title

    bot.send_message(user_id, "Введите @username участников через пробел (например: @ivan @anna):\n(можно оставить пустым, чтобы добавить участников позже)")
    bot.register_next_step_handler(message, add_event_participants)

def add_event_participants(message):
    user_id = message.from_user.id
    username = message.from_user.username
    participants_text = message.text.strip()
    title = tmp_dict[user_id]['event_title']

    cursor.execute('INSERT INTO events (title) VALUES (?)', (title,))
    conn.commit()
    event_id = cursor.lastrowid

    if username:
        cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (username,))
        creator_row = cursor.fetchone()
        if creator_row:
            creator_id = creator_row[0]
            cursor.execute('INSERT OR IGNORE INTO event_participants (event_id, user_id) VALUES (?, ?)', (event_id, creator_id))

    if participants_text:
        usernames = participants_text.split()
        for uname in usernames:
            if uname.startswith('@'):
                uname = uname[1:]
            cursor.execute('SELECT id FROM users WHERE telegram_id = ?', (uname,))
            res = cursor.fetchone()
            if res:
                participant_id = res[0]
                cursor.execute('INSERT OR IGNORE INTO event_participants (event_id, user_id) VALUES (?, ?)', (event_id, participant_id))
            else:
                bot.send_message(user_id, f"Пользователь @{uname} не найден в базе и не был добавлен.")

    conn.commit()
    bot.send_message(user_id, f"Мероприятие '{title}' создано с id {event_id}")
    del tmp_dict[user_id]


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
