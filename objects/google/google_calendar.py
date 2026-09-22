from datetime import datetime, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from auth import get_credentials

# Initialize credentials and build service
credentials = get_credentials()
service = build('calendar', 'v3', credentials=credentials)

# Define your ISO 8601 date range
start_time = datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()
end_time = datetime(2026, 10, 31, 23, 59, 59, tzinfo=timezone.utc).isoformat()

# Call the API
events_result = service.events().list(
    calendarId='primary',
    timeMin=start_time,
    timeMax=end_time,
    singleEvents=True,
    orderBy='startTime'
).execute()

events = events_result.get('items', [])

def run():
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        print(f"{start} - {end} - {event.get('htmlLink', 'No Link')}")

if __name__ == "__main__":
    run()