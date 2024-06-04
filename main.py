import telebot
from telebot import types

import DBManager
import config

'''
bot = telebot.TeleBot(token='7469709374:AAHtJR9Jsw359d_7TuMGSsT2AFzJrd7CtI0')

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id, "привет пришли мне файл и я распечатаю его")
@bot.message_handler(content_types=['document'])
def handle_docs_photo(message):
    try:
        chat_id = message.chat.id
        printer.delete_files_in_folder('files')
        file_info = bot.get_file(message.document.file_id)
        print(file_info)
        downloaded_file = bot.download_file(file_info.file_path)
        print(downloaded_file)
        src = 'files/' + message.document.file_name
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, "Пожалуй, я распечатаю это")
        print(src)
        printer.print_file(src)
        bot.reply_to(message, "Распечатал")
    except Exception as e:
        bot.reply_to(message, e)

'''

bot = telebot.TeleBot(config.TOKEN)
connection = DBManager.connect()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id, "Привет! Я помогу тебе следить за своими тратами и анализировать их!")
    DBManager.add_user(connection, message.from_user.id)
    bot.send_message(message.from_user.id, "Создал ячейку в базе")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Добавить трату")
    btn2 = types.KeyboardButton("Мои траты")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, text="Привет, {0.first_name}! Я тестовый бот для твоей статьи для habr.com".format(message.from_user), reply_markup=markup)



@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "/help":
        bot.send_message(message.from_user.id, "Мяу")
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю.")


bot.polling(none_stop=True, interval=0)
