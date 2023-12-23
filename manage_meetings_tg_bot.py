import telebot
from telebot import types

from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

import sqlite3

error_message = "Что-то пошло не так, пожалуйста напишите @Aris12122"


def get_file(path):
    with open(path) as f:
        return f.readline()


def add_to_file(path, message):
    with open(path, 'a') as f:
        f.write(message)

def check_identifier(identifier): 
    if identifier.count(' ')==0 and identifier.count('@')==1 and identifier.count('.com')!=0:
        return True
    else:
        return False

bot = telebot.TeleBot("6842927865:AAHf2hI-00VctL9xnrbRBChDAZ_lCI1N1tI")

def construct_event(day, description, location): #ок?
    start_date = datetime.strptime(day, '%Y-%m-%d').date()
    end_date = start_date + timedelta(days=1) 

    event = {
        'summary': 'Встреча, созданная ботом', 
        'location': location, 
        'description' : description, 
        'start': {
            'date' : start_date.isoformat(),
        },
        'end': {
            'date' : end_date.isoformat(),
        }
    }
    return event

def find_available_days(obj, message): #надо переписать 
    available_days = []
    today = datetime.now().date()
    end_date = today + timedelta(days=14)  
    current_date = today

    while current_date < end_date:

        conn_users = sqlite3.connect('users.db')
        cursor = conn_users.cursor()
        cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
        calendar_identifiers = cursor.fetchall()
        conn_users.close()
        all_free = True 

        for calendar in calendar_identifiers:
            calendar = calendar[0]
            if not obj.check_availability(calendar, current_date):
                all_free = False
                break

        if all_free:
            available_days.append(current_date.strftime('%Y-%m-%d'))

        current_date += timedelta(days=1)

    return available_days


#email meetingbot@telegrambot-408815.iam.gserviceaccount.com

class GoogleCalendar:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    FILE_PATH = 'telegrambot-408815-e609454416ce.json' 

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes = self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentials)
    
    def add_event(self, calendar_id, body):
        return self.service.events().insert(
            calendarId = calendar_id,
            body = body).execute()
    
    def get_event_ids_by_day(self, calendar_id, day): #ок?
        try:
            event_ids = []
            events_result = self.service.events().list(
                calendarId=calendar_id, 
                timeMin=f"{day}T00:00:00Z",
                timeMax=f"{day}T23:59:59Z"
            ).execute()
            events = events_result.get('items', [])
            if not events:
                print('No events found on this day.')
            else:
                print('Event IDs on this day:')
                for event in events:
                    event_ids.append(event['id'])
                    print(event['id'])
            return event_ids
        except Exception as e:
            print(f"An error occurred while retrieving event IDs: {e}")
            return []
        
    def delete_event(self, calendar_id, date): #ок?
        try:
            event_id = self.get_event_ids_by_day(calendar_id=calendar_id, day=date)[0]
            self.service.events().delete(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            print(f"Event with ID {event_id} has been deleted successfully.")
        except Exception as e:
            print(f"An error occurred while deleting the event: {e}")
    
    def change_date(self, calendar_id, old_start_date, new_start_date): #ок?
        try:
            event_id = self.get_event_ids_by_day(calendar_id=calendar_id, day=old_start_date)[0]
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            new_end_date = (datetime.strptime(new_start_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

            event['start'] = {'date': new_start_date}
            event['end'] = {'date': new_end_date}

            updated_event = self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
            print(f"Event with ID {event_id} has been updated to start on {new_start_date} and end on {new_end_date}.")
            return updated_event
        except Exception as e:
            print(f"An error occurred while updating the event: {e}")
            return None

    def change_description(self, calendar_id, date, new_description): #ок?
        try:
            event_id = self.get_event_ids_by_day(calendar_id=calendar_id, day=date)[0]
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            event['description'] = new_description

            updated_event = self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
            print(f"Description of event with ID {event_id} has been updated to: {new_description}.")
            return updated_event
        except Exception as e:
            print(f"An error occurred while updating the event description: {e}")
            return None

    def change_location(self, calendar_id, date, new_location): #ок?
        try:
            event_id = self.get_event_ids_by_day(calendar_id=calendar_id, day=date)[0]
            event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            event['location'] = new_location

            updated_event = self.service.events().update(calendarId=calendar_id, eventId=event_id, body=event).execute()
            print(f"Location of event with ID {event_id} has been updated to: {new_location}.")
            return updated_event
        except Exception as e:
            print(f"An error occurred while updating the event location: {e}")
            return None
        
    def check_availability(self, calendar_id, selected_day): #очень надо переписать вообще не как надо работает
        try:
            time_min = f"{selected_day}T00:00:00Z"
            time_max = f"{selected_day}T23:59:59Z"
            events_result = self.service.events().list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max).execute()
            events = events_result.get('items', [])
            if not events:
                print(f"No events found on {selected_day}. You are available.")
                return True
            else:
                if len(events) == 1 and events[0]["summary"] == "Встреча, созданная ботом":
                   return True
                print(f"Events found on {selected_day}. You are not available.")
                return False
        except Exception as e:
            print(f"An error occurred while checking availability: {e}")
            return False

obj = GoogleCalendar()




@bot.message_handler(commands=["start"]) #ок?
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

def get_users_db_content(): #вспомогательная потом удалить
    conn_users = sqlite3.connect('users.db')
    cursor_users = conn_users.cursor()

    # Получаем все записи из базы данных
    cursor_users.execute("SELECT * FROM users")
    rows = cursor_users.fetchall()

    content = "Содержимое базы данных пользователей:\n"
    for row in rows:
        content += f"ID: {row[0]}, User ID: {row[1]}, Chat ID: {row[2]}, Calendar Identifier: {row[3]}\n"

    conn_users.close()
    return content

def conn_meetings_db_content(): #вспомогательная потом удалить
    conn_meetings = sqlite3.connect('meetings.db')
    cursor_meetings = conn_meetings.cursor()
    cursor_meetings.execute("SELECT * FROM meetings")
    rows = cursor_meetings.fetchall()
    content = "Содержимое базы данных встреч:\n"
    for row in rows:
        content += f"ID: {row[0]}, Chat ID: {row[1]}, Дата: {row[2]}\n"
    conn_meetings.close()
    return content

@bot.message_handler(commands=["instruction"]) #ок?
def instruction(message): 
    text = "Чтобы подключить доступ к гугл календарю, нужно зайти на сайт calendar.google.com , выбрать нужный календарь, добавить почту meetingbot@telegrambot-408815.iam.gserviceaccount.com в список пользователей, которым доступен календарь, для внесения изменений и предоставления доступа, вызвать в телеграм боте команду /access и отправить dentifier"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["access"]) #ок?
def access(message):
    bot.send_message(message.chat.id,
                     "Отправь мне идентификатор календаря, подробнее о подключении бота в /instruction")
    bot.register_next_step_handler(message, identifier)

def identifier(message): #ок?
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
        
        bot.send_message(message.chat.id, 'База данных пользователей после изменений:\n' + get_users_db_content())
    elif identifier == '/instruction':
        instruction(message)
    else:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, проверьте ввод и повторите попытку.')




@bot.message_handler(commands=["manage_meeting"]) #ок?
def manage_meeting(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text = 'Назначить встречу', callback_data='set_meeting'))
    markup.add(types.InlineKeyboardButton(text = 'Удалить встречу', callback_data='delete_meeting'))
    markup.add(types.InlineKeyboardButton(text = 'Перенести встречу', callback_data='change_date'))
    markup.add(types.InlineKeyboardButton(text = 'Изменить описание встречи', callback_data='change_description'))
    markup.add(types.InlineKeyboardButton(text = 'Изменить место встречи', callback_data='change_location'))
    markup.add(types.InlineKeyboardButton(text = 'Показать ближайшие назначенные встречи', callback_data='show_meetings'))
    bot.send_message(message.chat.id, text = "Выбери функцию", reply_markup=markup)

@bot.callback_query_handler(func = lambda callback: True) #ок?
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

def set_meeting(message): #проблема из за того что find_available_days некорректно работает 

    if message.text.strip()=='бот, найди свободные дни':
        bot.send_message(message.chat.id, text = 'Ищу...\n')
        dates = find_available_days(obj, message)
        text = "Свободные даты в ближайшие 2 недели:\n"
        for date in dates:
            text+=date
            text+='\n'
        bot.send_message(message.chat.id, text = text)

    else:
        event = construct_event(day = message.text.strip(), description = '', location = '') 

        conn_users = sqlite3.connect('users.db')
        cursor = conn_users.cursor()
        cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
        calendar_identifiers = cursor.fetchall()
        conn_users.close()

        conn_meetings = sqlite3.connect('meetings.db')
        cursor_meetings = conn_meetings.cursor()
        cursor_meetings.execute("INSERT INTO meetings (chat_id, date) VALUES (?, ?)",
                                (str(message.chat.id), message.text.strip()))
        conn_meetings.commit()

        for calendar in calendar_identifiers:
            calendar = calendar[0]
            obj.add_event(calendar_id=calendar, body=event)

        bot.send_message(message.chat.id, text = 'Встреча была добавлена')

        cursor_meetings.execute("SELECT * FROM meetings")
        rows = cursor_meetings.fetchall()
        content = "Содержимое базы данных встреч:\n"
        for row in rows:
            content += f"ID: {row[0]}, Chat ID: {row[1]}, Дата: {row[2]}\n"
        conn_meetings.close()
        bot.send_message(message.chat.id, text=content)


def delete_meeting(message): #ок?

    bot.send_message(message.chat.id, text="Начинаю работу")

    conn_users = sqlite3.connect('users.db')
    cursor = conn_users.cursor()
    cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
    calendar_identifiers = cursor.fetchall()
    conn_users.close()

    bot.send_message(message.chat.id, text=calendar_identifiers)

    conn_meetings = sqlite3.connect('meetings.db')
    cursor_meetings = conn_meetings.cursor()
    cursor_meetings.execute("DELETE FROM meetings WHERE chat_id = ? AND date = ?", (message.chat.id, message.text.strip()))
    conn_meetings.commit()
    conn_meetings.close()
    for calendar in calendar_identifiers:
        calendar = calendar[0]
        obj.delete_event(calendar_id=calendar, date=message.text.strip())

    bot.send_message(message.chat.id, text='Встреча была удалена')

    content = conn_meetings_db_content()
    bot.send_message(message.chat.id, text=content)
    


def change_date(message): #ок?
    m = message.text.strip()
    date1, date2 = m.split(' ')[0], m.split(' ')[-1]

    conn_users = sqlite3.connect('users.db')
    cursor = conn_users.cursor()
    cursor.execute("SELECT calendar_identifier FROM users WHERE chat_id = ?", (message.chat.id,))
    calendar_identifiers = cursor.fetchall()
    conn_users.close()

    # Изменяем дату в базе данных 'meetings.db'
    conn_meetings = sqlite3.connect('meetings.db')
    cursor_meetings = conn_meetings.cursor()
    cursor_meetings.execute("UPDATE meetings SET date = ? WHERE chat_id = ? AND date = ?", (date2, message.chat.id, date1))
    conn_meetings.commit()
    conn_meetings.close()

    for calendar in calendar_identifiers:
        calendar = calendar[0]
        obj.change_date(calendar_id=calendar, old_start_date=date1, new_start_date=date2)

    bot.send_message(message.chat.id, text='Встреча была перенесена')

    content = conn_meetings_db_content()
    bot.send_message(message.chat.id, text=content)


def change_description(message): #ок?
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

def change_location(message): #ок?
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

    bot.send_message(message.chat.id, text = 'Новое описание было добавлено')

def show_meetings(chat_id): #ок?
    conn_meetings = sqlite3.connect('meetings.db')
    cursor_meetings = conn_meetings.cursor()
    cursor_meetings.execute("SELECT * FROM meetings WHERE chat_id = ? ORDER BY date LIMIT 3", (chat_id,))
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


@bot.message_handler(commands=['help']) #ок?
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