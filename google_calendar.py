import sqlite3
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

#email meetingbot@telegrambot-408815.iam.gserviceaccount.com

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

conn_events = sqlite3.connect('events.db')
cursor_events = conn_events.cursor()
cursor_events.execute('''CREATE TABLE IF NOT EXISTS events (
                                id INTEGER PRIMARY KEY,
                                calendar_identifier TEXT,
                                event_id TEXT,
                                date TEXT
                                )''')
conn_events.commit()
conn_events.close()

class GoogleCalendar:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    FILE_PATH = 'telegrambot-408815-e609454416ce.json' 

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes = self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentials)
    
    def add_event(self, calendar_id, date):
        body = construct_event(day=date, description='', location='')
        event = self.service.events().insert(
            calendarId=calendar_id, 
            body=body).execute()

        conn_events = sqlite3.connect('events.db')
        cursor_events = conn_events.cursor()
        cursor_events.execute("INSERT INTO events (calendar_identifier, event_id, date) VALUES (?, ?, ?)",
                              (calendar_id, event['id'], date))
        conn_events.commit()
        conn_events.close()

        return event
       
    def get_event_id_by_day(self, calendar_id, day):
        conn_events = sqlite3.connect('events.db')
        cursor_events = conn_events.cursor()
        cursor_events.execute("SELECT event_id FROM events WHERE calendar_identifier = ? AND date = ?", (calendar_id, day))
        event_ids = cursor_events.fetchall()
        conn_events.close()

        return event_ids[0][0]


    def delete_event(self, calendar_id, date):
        event_id = self.get_event_id_by_day(calendar_id=calendar_id, day=date)

        self.service.events().delete(
            calendarId=calendar_id, 
            eventId=event_id).execute()

        conn_events = sqlite3.connect('events.db')
        cursor_events = conn_events.cursor()
        cursor_events.execute("DELETE FROM events WHERE calendar_identifier = ? AND date = ?", (calendar_id, date))
        conn_events.commit()
        conn_events.close()
    
    def change_date(self, calendar_id, old_start_date, new_start_date):
        event_id = self.get_event_id_by_day(calendar_id=calendar_id, day=old_start_date)

        event = self.service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        new_end_date = (datetime.strptime(new_start_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')

        event['start'] = {'date': new_start_date}
        event['end'] = {'date': new_end_date}

        updated_event = self.service.events().update(
            calendarId=calendar_id, 
            eventId=event_id, 
            body=event).execute()

        conn_events = sqlite3.connect('events.db')
        cursor_events = conn_events.cursor()
        cursor_events.execute("UPDATE events SET date = ? WHERE calendar_identifier = ? AND event_id = ?", (new_start_date, calendar_id, event_id))
        conn_events.commit()
        conn_events.close()

        return updated_event


    def change_description(self, calendar_id, date, new_description): 
        event_id = self.get_event_id_by_day(calendar_id=calendar_id, day=date)

        event = self.service.events().get(
            calendarId=calendar_id, 
            eventId=event_id).execute()
        
        event['description'] = new_description
        updated_event = self.service.events().update(
            calendarId=calendar_id, 
            eventId=event_id, 
            body=event).execute()

        return updated_event

    def change_location(self, calendar_id, date, new_location): #ок?
        event_id = self.get_event_id_by_day(calendar_id=calendar_id, day=date)

        event = self.service.events().get(
            calendarId=calendar_id, 
            eventId=event_id).execute()
        
        event['location'] = new_location
        updated_event = self.service.events().update(
            calendarId=calendar_id, 
            eventId=event_id, 
            body=event).execute()

        return updated_event
        
    def check_availability(self, calendar_id, day): 
        start_date = datetime.strptime(day, '%Y-%m-%d').date()
    
        time_min = start_date.isoformat()+ 'T00:00:00Z'
        time_max = start_date.isoformat() + 'T23:59:59Z'
        events_result = self.service.events().list(
            calendarId=calendar_id, 
            timeMin=time_min, 
            timeMax=time_max
        ).execute()

        events = events_result.get('items', [])
        cnt = 0
        for event in events:
            try:
                if event['start']['date'] + 'T00:00:00Z' > time_max:
                   cnt+=1
            except:
                pass
        if cnt == len(events):
            return True
        else:
            return False

