import requests
from requests.auth import HTTPBasicAuth

# Eventfinda API credentials and call setup
USERNAME = 'easynotesdesktopapp'
PASSWORD = '95gn4kw4gwkj'

# Decorator for the main function (if needed, otherwise can be removed)
url = 'https://api.eventfinda.co.nz/v2/events.json'
params = {
    'rows': 10,
    'order': 'popularity',
    'free': 1  # Filter for free events
}


# Run the Eventfinda API call and return the list of event dicts (empty list on failure).
def run_event_finda_call() -> list[dict]:
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
    for event in events:
        print(f"{event['name']} - {event.get('datetime_summary', '')}")
    return events


if __name__ == "__main__":
    run_event_finda_call()
