import requests
from requests.auth import HTTPBasicAuth

# Eventfinda API credentials and call setup
USERNAME = 'easynotesdesktopapp'
PASSWORD = '95gn4kw4gwkj'

url = 'https://api.eventfinda.co.nz/v2/events.json'


# Run the Eventfinda API call and return the list of event dicts (empty list on failure).
def run_event_finda_call(num_rows: int = 20, free_only: bool = False, order: str = 'popularity') -> list[dict]:
    params = {
        'rows': num_rows,
        'order': order,
        'free': 1 if free_only else 0,
    }
    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={'Accept': 'application/json'}
    )

    if response.status_code != 200:
        print(f"Failed to retrieve events: {response.status_code}")
        return []

    data = response.json()
    events = data.get('events', [])
    print(f"[Starting retrieval of events from Eventfinda API]:")
    print(f"[Retrieved {len(events)} events]")
    for event in events:
        print(f"{event['name']} - {event.get('datetime_summary', '')}")
    return events


if __name__ == "__main__":
    run_event_finda_call(num_rows=20, free_only=False, order='popularity')
