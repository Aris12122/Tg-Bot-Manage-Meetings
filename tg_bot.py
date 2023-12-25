import telebot
import threading
from telebot import types
import sqlite3
from google_calendar import GoogleCalendar
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from io import BytesIO
from statistics_bot import get_picture

error_message = "Что-то пошло не так, пожалуйста напишите @Aris12122"


def get_file(path):
    with open(path) as f:
        return f.readline()

def add_to_file(path, message):
    with open(path, 'a') as f:
        f.write(message)

obj = GoogleCalendar()

bot = telebot.TeleBot("6842927865:AAHf2hI-00VctL9xnrbRBChDAZ_lCI1N1tI")

@bot.message_handler(commands=["start"]) 
def start(message):
    conn_users = sqlite3.connect('users.db')
    cursor_users = conn_users.cursor()
    cursor_users.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            chat_id INTEGER,
                            calendar_identifier TEXT
                            )''')
    conn_users.commit()
    conn_users.close()

    conn_meetings = sqlite3.connect('meetings.db')
    cursor_meetings = conn_meetings.cursor()
    cursor_meetings.execute('''CREATE TABLE IF NOT EXISTS meetings (
                                id INTEGER PRIMARY KEY,
                                chat_id TEXT,
                                date TEXT
                                )''')
    conn_meetings.commit()
    conn_meetings.close()

    bot.send_message(message.chat.id, text = 'Привет! Список всех моих комманд в /help')

@bot.message_handler(commands=["instruction"]) 
def instruction(message): 
    text = "Чтобы подключить доступ к гугл календарю, нужно зайти на сайт calendar.google.com , выбрать нужный календарь, добавить почту meetingbot@telegrambot-408815.iam.gserviceaccount.com в список пользователей, которым доступен календарь, для внесения изменений и предоставления доступа, вызвать в телеграм боте команду /access и отправить dentifier"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["access"]) 
def access(message):
    bot.send_message(message.chat.id,
                     "Отправь мне идентификатор календаря, подробнее о подключении бота в /instruction")
    bot.register_next_step_handler(message, identifier)

def check_identifier(identifier): 
    if identifier.count(' ')==0 and identifier.count('@')==1 and identifier.count('.com')!=0:
        return True
    else:
        return False
    
def identifier(message): 
    identifier = message.text.strip()

    if check_identifier(identifier=identifier):
        conn_users = sqlite3.connect('users.db')
        cursor_users = conn_users.cursor()
        cursor_users.execute("SELECT * FROM users WHERE chat_id = ? AND user_id = ?", (message.chat.id, message.from_user.id))

        result = cursor_users.fetchone()

        if result:
            cursor_users.execute("UPDATE users SET calendar_identifier = ? WHERE user_id = ? AND chat_id = ?", (identifier, message.from_user.id, message.chat.id))
            conn_users.commit()

        else:
            cursor_users.execute("INSERT INTO users (user_id, chat_id, calendar_identifier) VALUES (?, ?, ?)",
                                (message.from_user.id, message.chat.id, identifier))
            conn_users.commit()
            bot.send_message(message.chat.id, text = 'Спасибо, зарегистрировал тебя')
        conn_users.close()

    elif identifier == '/instruction':
        instruction(message)

    else:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, проверьте ввод и повторите попытку.')


@bot.message_handler(commands=["manage_meeting"]) 
def manage_meeting(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text = 'Назначить встречу', callback_data='set_meeting'))
    markup.add(types.InlineKeyboardButton(text = 'Удалить встречу', callback_data='delete_meeting'))
    markup.add(types.InlineKeyboardButton(text = 'Перенести встречу', callback_data='change_date'))
    markup.add(types.InlineKeyboardButton(text = 'Изменить описание встречи', callback_data='change_description'))
    markup.add(types.InlineKeyboardButton(text = 'Изменить место встречи', callback_data='change_location'))
    markup.add(types.InlineKeyboardButton(text = 'Показать ближайшие назначенные встречи', callback_data='show_meetings'))
    bot.send_message(message.chat.id, text = "Выбери функцию", reply_markup=markup)

@bot.callback_query_handler(func = lambda callback: True) 
def callback_messege(callback): 
    if callback.data == 'set_meeting':
        bot.send_message(callback.message.chat.id, text = "Напиши мне дату на которую хочешь назначить встречу в формате yyyy-mm-dd или напиши мне сообщение 'бот, найди свободные дни' и я подберу свободные дни в ближайшие 2 недели")
        bot.register_next_step_handler(callback.message, set_meeting)
    elif callback.data == 'delete_meeting':
        bot.send_message(callback.message.chat.id, text = "Напиши мне дату встречи, которую хочешь отменить в формате yyyy-mm-dd")
        bot.register_next_step_handler(callback.message, delete_meeting)
    elif callback.data == 'change_date':
        bot.send_message(callback.message.chat.id, text = "Напиши мне 2 даты через пробел в формате yyyy-mm-dd. Сначала дату встречи, которую хочешь перенести, затем на какую дату хочешь перенести")
        bot.register_next_step_handler(callback.message, change_date)
    elif callback.data == 'change_description':
        bot.send_message(callback.message.chat.id, text = "Напиши мне дату встречи в формате yyyy-mm-dd и через пробел новое описание(кавычки ставить не нужно)")
        bot.register_next_step_handler(callback.message, change_description)
    elif callback.data == 'change_location':
        bot.send_message(callback.message.chat.id, text = "Напиши мне дату встречи в формате yyyy-mm-dd и через пробел новое место встречи(кавычки ставить не нужно)")
        bot.register_next_step_handler(callback.message, change_location)
    else: 
        show_meetings(callback.message.chat.id)

def set_meeting(message):  

    if message.text.strip()=='бот, найди свободные дни':
        bot.send_message(message.chat.id, text = 'Ищу...\n')

        available_days = []
        today = datetime.now().date()
        end_date = today + timedelta(days=14)  
        current_date = today

        conn_users = sqlite3.connect('users.db')
        cursor = conn_users.cursor()
        cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
        calendar_identifiers = cursor.fetchall()
        conn_users.close()

        while current_date < end_date:
            all_free = True 
            for calendar in calendar_identifiers:
               calendar = calendar[0]
               date = current_date.strftime('%Y-%m-%d')
               if not obj.check_availability(calendar_id=calendar, day=date):
                   all_free = False
                   break

            if all_free:
               available_days.append(current_date.strftime('%Y-%m-%d'))

            current_date += timedelta(days=1) 

        text = "Свободные даты в ближайшие 2 недели:\n"
        for date in available_days:
            text+=date
            text+='\n'

        bot.send_message(message.chat.id, text = text)

    else:

        day = message.text.strip()
        if datetime.strptime(day, '%Y-%m-%d'):

            conn_users = sqlite3.connect('users.db')
            cursor = conn_users.cursor()
            cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
            calendar_identifiers = cursor.fetchall()
            conn_users.close()

            conn_meetings = sqlite3.connect('meetings.db')
            cursor_meetings = conn_meetings.cursor()
            cursor_meetings.execute("INSERT INTO meetings (chat_id, date) VALUES (?, ?)",
                                (str(message.chat.id), day))
            conn_meetings.commit()

            for calendar in calendar_identifiers:
                calendar = calendar[0]
                obj.add_event(calendar_id=calendar, date = day)

            bot.send_message(message.chat.id, text = 'Встреча была добавлена')
        else:
            bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, проверьте ввод и повторите попытку.')


def delete_meeting(message):

    conn_users = sqlite3.connect('users.db')
    cursor = conn_users.cursor()
    cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
    calendar_identifiers = cursor.fetchall()
    conn_users.close()

    conn_meetings = sqlite3.connect('meetings.db')
    cursor_meetings = conn_meetings.cursor()
    cursor_meetings.execute("DELETE FROM meetings WHERE chat_id = ? AND date = ?", (message.chat.id, message.text.strip()))
    conn_meetings.commit()
    conn_meetings.close()

    for calendar in calendar_identifiers:
        calendar = calendar[0]
        obj.delete_event(calendar_id=calendar, date=message.text.strip())

    bot.send_message(message.chat.id, text='Встреча была удалена')

def change_date(message): 
    m = message.text.strip()
    date1, date2 = m.split(' ')[0], m.split(' ')[-1]

    conn_users = sqlite3.connect('users.db')
    cursor = conn_users.cursor()
    cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
    calendar_identifiers = cursor.fetchall()
    conn_users.close()

    conn_meetings = sqlite3.connect('meetings.db')
    cursor_meetings = conn_meetings.cursor()
    cursor_meetings.execute("UPDATE meetings SET date = ? WHERE chat_id = ? AND date = ?", (date2, message.chat.id, date1))
    conn_meetings.commit()
    conn_meetings.close()

    for calendar in calendar_identifiers:
        calendar = calendar[0]
        obj.change_date(calendar_id=calendar, old_start_date=date1, new_start_date=date2)

    bot.send_message(message.chat.id, text='Встреча была перенесена')



def change_description(message): 
    m = message.text.strip()
    date, desc = m[:m.find(' ')], m[m.find(' ')+1:]

    conn_users = sqlite3.connect('users.db')
    cursor = conn_users.cursor()
    cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
    calendar_identifiers = cursor.fetchall()
    conn_users.close()

    for calendar in calendar_identifiers:
        calendar = calendar[0]
        obj.change_description(calendar_id=calendar, date=date, new_description=desc)

    bot.send_message(message.chat.id, text = 'Новое описание было добавлено')

def change_location(message): 
    m = message.text.strip()
    date, loc = m[:m.find(' ')], m[m.find(' ')+1:]

    conn_users = sqlite3.connect('users.db')
    cursor = conn_users.cursor()
    cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
    calendar_identifiers = cursor.fetchall()
    conn_users.close()

    for calendar in calendar_identifiers:
        calendar = calendar[0]
        obj.change_location(calendar_id=calendar, date=date, new_location=loc)

    bot.send_message(message.chat.id, text = 'Новое место встречи было добавлено')

def show_meetings(chat_id): 
    current_date = datetime.now().date()

    conn_meetings = sqlite3.connect('meetings.db')
    cursor_meetings = conn_meetings.cursor()
    cursor_meetings.execute("SELECT * FROM meetings WHERE chat_id = ? AND date >= ? ORDER BY date LIMIT 3", (chat_id, current_date))
    rows = cursor_meetings.fetchall()
    conn_meetings.close()

    if rows:
        content = "Предстоящие встречи:\n"
        for row in rows:
            content += row[2]
            content += '\n'
        bot.send_message(chat_id=chat_id, text=content)
    else:
        bot.send_message(chat_id=chat_id, text="Список предстоящих встреч пуст.")

def count_total_meetings(chat_id):
    conn = sqlite3.connect('meetings.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM meetings WHERE chat_id=?", (chat_id,))
    count_total = cursor.fetchone()[0]

    conn.close()
    return count_total

def count_m_by_weeks(chat_id):

    conn = sqlite3.connect('meetings.db')
    cursor = conn.cursor()
    y = []
    cursor.execute("SELECT MIN(date) FROM meetings WHERE chat_id=?", (chat_id,))

    first_meeting_date = cursor.fetchone()[0]
    first_meeting_date = datetime.strptime(first_meeting_date, '%Y-%m-%d')

    start_of_week = first_meeting_date - timedelta(days=first_meeting_date.weekday())
    end_of_week = start_of_week +  timedelta(days=6, hours=23, minutes=59)

    today = datetime.today()
    while end_of_week < today:
        start_of_week = end_of_week + timedelta(minutes=1)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59)
        cursor.execute("SELECT COUNT(*) FROM meetings WHERE chat_id=? AND date BETWEEN ? AND ?",
                       (chat_id, start_of_week, end_of_week))
        num_meetings = cursor.fetchone()[0]
        y.append(num_meetings)
    
    conn.close()
    return y
    

@bot.message_handler(commands=["statistics"]) 
def instruction(message): 
    y = count_m_by_weeks(message.chat.id)

    if y[-1]==0:
        bot.send_message(message.chat.id, text = 'На этой неделе пока не запланировано встреч')

    else:
        mean = sum(y)/len(y)
        percent_last =  int(y[-1]/mean*100//1)
        text = 'Количество встреч на неделе: ' + str(y[-1]) +'\n'
        if percent_last < 100:
            text+="Это на " + str(100-percent_last) + "% меньше чем обычно" + '\n'
        else:
            text+="Это на " + str(percent_last-100) + "% больше чем обычно" + '\n'

        text+='Среднее количество встреч на неделе: ' + str(mean)
        bot.send_message(message.chat.id, text = text)
    plt.switch_backend('Agg') 
    plt.bar(range(1, len(y)+1), y)
    plt.title('Количество встреч по неделям')
    plt.xlabel('Неделя')
    plt.ylabel('Количество встреч')

    plt.savefig('meeting_chart.png')  

    # Отправка графика
    with open('meeting_chart.png', 'rb') as photo:
        bot.send_photo(message.chat.id, photo)

    plt.close()  




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
