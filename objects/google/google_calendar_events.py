import requests

from auth import get_credentials

CALENDAR_URL = (
    "https://www.googleapis.com/calendar/v3"
    "/calendars/primary/events"
)

START_TIME = "2026-09-01T00:00:00Z"
END_TIME = "2026-10-31T23:59:59Z"
FETCH_EVENTS_ENDPOINT = (
    f"{CALENDAR_URL}?timeMin={START_TIME}&timeMax={END_TIME}&singleEvents=true&orderBy=startTime"
)

def get_events():
    credentials = get_credentials()

    # Make sure the access token is available
    access_token = credentials.token

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        FETCH_EVENTS_ENDPOINT,
        headers=headers
    )

    print("HTTP status:", response.status_code)
    response.raise_for_status()
    return response.json()


def main():
    data = get_events()
    print(data)

if __name__ == "__main__":
    main()