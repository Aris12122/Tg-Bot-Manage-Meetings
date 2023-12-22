import pprint
from datetime import datetime, timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

def construct_event(day, description, location): 
    start_date = datetime.strptime(day, '%Y-%m-%d').date()
    end_date = start_date + timedelta(days=1)  # Calculate the end date as the next day

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

#email 	meetingbot@telegrambot-408815.iam.gserviceaccount.com

class GoogleCalendar:
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    FILE_PATH = 'telegrambot-408815-e609454416ce.json'

    def __init__(self):
        credentials = service_account.Credentials.from_service_account_file(
            filename=self.FILE_PATH, scopes = self.SCOPES
        )
        self.service = build('calendar', 'v3', credentials=credentials)
    
    def get_calenardar_list(self):
        return self.service.calendarList().list().execute()
    
    def add_calendar(self, calendar_id):
        calendar_list_entry = {
            'id': calendar_id
        }
        return self.service.calendarList().insert(
            body=calendar_list_entry).execute()
    
    def add_event(self, calendar_id, body):
        return self.service.events().insert(
            calendarId = calendar_id,
            body = body).execute()
    
    def get_event_ids_by_day(self, calendar_id, day): #в нормальном случае тут одна встреча на день
        try:
            event_ids = []
            events_result = self.service.events().list(
                calendarId=calendar_id, 
                timeMin=f"{day}T00:00:01Z",
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
            event_id = self.get_event_ids_by_day(calendar_id=calendar, day=old_start_date)[0]
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
            event_id = self.get_event_ids_by_day(calendar_id=calendar, day=date)[0]
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
            time_min = f"{selected_day}T00:00:01Z"
            time_max = f"{selected_day}T23:59:58Z"
            events_result = self.service.events().list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max).execute()
            events = events_result.get('items', [])
            if not events:
                print(f"No events found on {selected_day}. You are available.")
                return True
            else:
                if len(events) == 1 and events[0]["summary"] == "Встреча, созданная ботом":
                   print('something wierd happened here', selected_day)
                   return True
                print(f"Events found on {selected_day}. You are not available.")
                return False
        except Exception as e:
            print(f"An error occurred while checking availability: {e}")
            return False




obj = GoogleCalendar()
calendar = 'botalisa3@gmail.com'
day = '2023-12-26'  # Example date
description = 'yoyoyo'
location = 'Иваново'
new_description = 'my tummy hurts!!!! aaa'

def find_available_days():
    available_days = []
    today = datetime.now().date()
    end_date = today + timedelta(days=14)  # Дата через 2 недели

    current_date = today
    while current_date < end_date:
        if obj.check_availability(calendar_id = calendar, selected_day=current_date):
            ate_str = current_date.strftime('%Y-%m-%d')
            available_days.append(ate_str)
        current_date += timedelta(days=1)

    return available_days
print(find_available_days())

