import os
from datetime import timedelta

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = f"{os.environ.get('BASE_URL', 'http://localhost:5000')}/api/google/callback"

def get_google_auth_flow():
    return Flow.from_client_secrets_file(
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )

def create_event(user, task):
    if not user.google_calendar_integrated:
        return None

    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=os.environ.get("GOOGLE_CLIENT_ID"),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES
    )

    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': task.description,
        'start': {
            'dateTime': task.scheduled_time.isoformat(),
            'timeZone': 'America/Guayaquil',
        },
        'end': {
            'dateTime': (task.scheduled_time + timedelta(hours=1)).isoformat(),
            'timeZone': 'America/Guayaquil',
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event.get('id')

def update_event(user, task):
    if not user.google_calendar_integrated or not task.google_calendar_event_id:
        return

    creds = Credentials.from_authorized_user_info({
        "access_token": user.google_access_token,
        "refresh_token": user.google_refresh_token
    })

    service = build('calendar', 'v3', credentials=creds)

    event = {
        'summary': task.description,
        'start': {
            'dateTime': task.scheduled_time.isoformat(),
            'timeZone': 'America/Guayaquil',
        },
        'end': {
            'dateTime': (task.scheduled_time + timedelta(hours=1)).isoformat(),
            'timeZone': 'America/Guayaquil',
        },
    }

    service.events().update(calendarId='primary', eventId=task.google_calendar_event_id, body=event).execute()

def delete_event(user, task):
    if not user.google_calendar_integrated or not task.google_calendar_event_id:
        return

    creds = Credentials.from_authorized_user_info({
        "access_token": user.google_access_token,
        "refresh_token": user.google_refresh_token
    })
    service = build('calendar', 'v3', credentials=creds)
    service.events().delete(calendarId='primary', eventId=task.google_calendar_event_id).execute()