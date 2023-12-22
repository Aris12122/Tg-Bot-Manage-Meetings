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

def construct_event(day, description, location): 
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

def find_available_days(obj, message): 
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
    
    def get_event_ids_by_day(self, calendar_id, day): 
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
    def delete_event(self, calendar_id, event_id):
        try:
            self.service.events().delete(
                calendarId=calendar_id, 
                eventId=event_id
            ).execute()
            print(f"Event with ID {event_id} has been deleted successfully.")
        except Exception as e:
            print(f"An error occurred while deleting the event: {e}")
    
    def change_date(self, calendar_id, old_start_date, new_start_date):
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

    def change_description(self, calendar_id, date, new_description):
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
        
    def check_availability(self, calendar_id, selected_day):
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
                                meeting_id TEXT,
                                chat_id TEXT,
                                date TEXT,
                                participants TEXT
                                )''')
    conn_meetings.commit()
    conn_meetings.close()

    bot.send_message(message.chat.id, text = 'Привет! Список всех моих комманд в /help')

def get_users_db_content(): 
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

@bot.message_handler(commands=["instruction"])
def instruction(message): 
    text = "Чтобы подключить доступ к гугл календарю, нужно зайти на сайт calendar.google.com , выбрать нужный календарь, добавить почту meetingbot@telegrambot-408815.iam.gserviceaccount.com в список пользователей, которым доступен календарь, для внесения изменений и предоставления доступа, вызвать в телеграм боте команду /access и отправить dentifier"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["access"])
def access(message):
    bot.send_message(message.chat.id,
                     "Отправь мне идентификатор календаря, подробнее о подключении бота в /instruction")
    bot.register_next_step_handler(message, identifier)

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
        
        # вместо печати всей базы данных печатай только то что 
        bot.send_message(message.chat.id, 'База данных пользователей после изменений:\n' + get_users_db_content())
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
    elif callback.data == 'change_date':
        bot.send_message(callback.message.chat.id, text = "Напиши мне 2 даты через пробел в формате yyyy-mm-dd. Сначала дату встречи, которую хочешь перенести, затем на какую дату хочешь перенести")
    elif callback.data == 'change_description':
        bot.send_message(callback.message.chat.id, text = "Напиши мне дату встречи в формате yyyy-mm-dd и через пробел новое описание(кавычки ставить не нужно)")
    elif callback.data == 'change_location':
        bot.send_message(callback.message.chat.id, text = "Напиши мне дату встречи в формате yyyy-mm-dd и через пробел новое место встречи(кавычки ставить не нужно)")
    else:
        bot.send_message(callback.message.chat.id, text = '')

def set_meeting(message):

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

        for calendar in calendar_identifiers:
            calendar = calendar[0]
            obj.add_event(calendar_id=calendar, body=event)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text = 'Да', callback_data='add'))
        markup.add(types.InlineKeyboardButton(text = 'Нет', callback_data='no'))
        bot.send_message(message.chat.id, text = 'Добавили встречу, хотите добавить ей описание?', reply_markup=markup)


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