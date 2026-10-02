import requests
from requests.auth import HTTPBasicAuth

# Eventfinda API credentials and call setup
USERNAME = 'easynotesdesktopapp'
PASSWORD = '95gn4kw4gwkj'

url = 'https://api.eventfinda.co.nz/v2/events.json'


# Run the Eventfinda API call and return the list of event dicts (empty list on failure).
def run_event_finda_call(
    num_rows: int = 20,
    free_only: bool = False,
    order: str = 'popularity',
    start_date: str | None = None,
    end_date: str | None = None,
    location_slug: str | None = None,
) -> list[dict]:
    params = {
        'rows': num_rows,
        'order': order,
        'free': 1 if free_only else 0,
        'start_date': start_date,
        'end_date': end_date,
        'location_slug': location_slug,
    }

    # Date filters
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    # Location filters (choose slug OR GPS proximity)
    if location_slug:
        params["location_slug"] = location_slug

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
    start_date = "2026-10-01"
    end_date = "2026-12-31"
    location_slug = "wellington"
    order = 'popularity'
    run_event_finda_call(num_rows=20,
                         free_only=False,
                         order=order,
                         start_date=start_date,
                         end_date=end_date,
                         location_slug=location_slug)
