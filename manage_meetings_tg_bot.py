import telebot
from telebot import types
import sqlite3

error_message = "Что-то пошло не так, пожалуйста напишите @Aris12122"


def get_file(path):
    with open(path) as f:
        return f.readline()


def add_to_file(path, message):
    with open(path, 'a') as f:
        f.write(message)


bot = telebot.TeleBot("6842927865:AAHf2hI-00VctL9xnrbRBChDAZ_lCI1N1tI")

@bot.message_handler(commands=["start"]) # с базой данных пока разбираюсь это для примера
def start(message):
    conn = sqlite3.connect('table.sql')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users (id int auto_inrecement primary key, name vatchar(50))')
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, text = 'Привет! Список всех моих комманд в /help введи мне свое имя')
    bot.register_next_step_handler(message, user_name)

def user_name(message): # разбираюсь
    name = message.text.strip()
    conn = sqlite3.connect('table.sql')
    cur = conn.cursor ()
    cur.execute("INSERT INTO users (name) VALUES ('%s')" % (name))
    conn.commit()
    cur.close()
    conn.close()
    markup = types.InlineKeyboardMarkup ()
    markup.add(types.InLineKeyboardButton('Слисок пользователей', callback_data = 'users'))
    bot.send_message(message.chat.id, 'Пользователь зарегистрирован!', reply_markup= markup)

@bot.message_handler(commands=["instruction"])
def instruction(message):
    text = "Чтобы подключить доступ к гугл календарю, нужно зайти на сайт calendar.google.com , выбрать нужный календарь, добавить почту meetingbot@telegrambot-408815.iam.gserviceaccount.com в список пользователей, которым доступен календарь, для внесения изменений и предоставления доступа, вызвать в телеграм боте команду /access и отправить идентификатор календаря"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["access"])
def access(message):
    bot.send_message(message.chat.id,
                     "Отправь мне идентификатор календаря, подробнее о подключении бота в /instruction")

@bot.message_handler(commands=["manage_meeting"])
def manage_meeting(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text = 'Назначить встречу', callback_data='set_meeting'))
    markup.add(types.InlineKeyboardButton(text = 'Удалить встречу', callback_data='delete_meeting'))
    markup.add(types.InlineKeyboardButton(text = 'Перенести встречу', callback_data='change_date'))
    markup.add(types.InlineKeyboardButton(text = 'Изменить описание встречи', callback_data='change_description'))
    bot.send_message(message.chat.id, text = "Выбери функцию", reply_markup=markup)

@bot.callback_query_handler(func = lambda callback: True)
def callback_messege(callback): #пока не написала надо базы данных сначала
    if callback.data == 'set_meeting':
        bot.send_message(callback.message.chat.id, text = "Выберана функция set_meeting")
    else:
        bot.send_message(callback.message.chat.id, text = "Выберана другая функция")

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "Привет! Я бот, который поможет тебе планировать встречи\n"
                                      "вот список моих команд:\n"
                                      "/start - начало работы\n"
                                      "/instruction - инструкция по подключению\n"
                                      "/access - подключение гугл. календаря \n"
                                      "/manage_meeting- управление встрачами\n"
                                      "/statistics - показать статистику\n"
                                      "/help - справочник \n")


while True:
    try:
        print("BEGIN")
        bot.polling(non_stop=True)
    except Exception as e:
        print("Global fail: " + str(e))
        continue
    break