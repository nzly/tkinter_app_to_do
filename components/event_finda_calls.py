import requests
from requests.auth import HTTPBasicAuth

# Eventfinda API credentials and call setup
USERNAME = 'easynotesdesktopapp'
PASSWORD = '95gn4kw4gwkj'
BASE_URL = 'https://api.eventfinda.co.nz/v2/events.json'


# Run the Eventfinda API call and return (events, total_count_available) (([], 0) on failure).
def run_event_finda_call(
    num_rows: int = 20,
    offset: int = 0,
    free_only: bool = False,
    order: str = 'popularity',
    start_date: str | None = None,
    end_date: str | None = None,
    location_slug: str | None = None,
) -> tuple[list[dict], int]:
    params = {
        'rows': num_rows,
        'offset': offset,
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
        BASE_URL,
        params=params,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={'Accept': 'application/json'}
    )

    if response.status_code != 200:
        print(f"Failed to retrieve events: {response.status_code}")
        return [], 0

    data = response.json()
    events = data.get('events', [])
    total_count = data.get('@attributes', {}).get('count', len(events))
    print(f"[Starting retrieval of events from Eventfinda API]:")
    print(f"[Retrieved {len(events)} of {total_count} events]")
    for event in events:
        print(f"{event['name']} - {event.get('datetime_summary', '')}")
    return events, total_count

# Fetch a single event by its ID from the Eventfinda API. Returns the event data as a dictionary, or None if the request fails.
def get_single_event(event_id: int):
    url = f"https://api.eventfinda.co.nz/v2/events/{event_id}.json"
    
    response = requests.get(
        url,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 200:
        # The single event object is returned directly (not inside a list)
        event_data = response.json()
        return event_data
    else:
        print(f"Failed to fetch event {event_id}. Status: {response.status_code}")
        return None
    
if __name__ == "__main__":
    start_date = "2026-10-01"
    end_date = "2026-12-31"
    location_slug = "wellington"
    order = 'popularity'
    run_event_finda_call(num_rows=20,
                         offset=0,
                         free_only=False,
                         order=order,
                         start_date=start_date,
                         end_date=end_date,
                         location_slug=location_slug)

    event_id = 123456
    print(f"----------------------------------")
    print(f"Fetching event with ID: {event_id}")
    print(f"----------------------------------")
    event = get_single_event(event_id)
    if event:
        print(f"Name:\n {event.get('name')}")
        print(f"Description:\n {event.get('description')}")
        print(f"Sessions:\n {event.get('sessions')}")
        print(f"Location/Venue:\n {event.get('location_summary')}")
        print(f"URL:\n {event.get('url')}")
        print(f"Ticket Types:\n {event.get('ticket_types')}")
        print(f"Start Date:\n {event.get('start_date')}")
        print(f"End Date:\n {event.get('end_date')}")
        print(f"Location Slug:\n {event.get('location_slug')}")
        print(f"Created At:\n {event.get('created_at')}")
        print(f"Updated At:\n {event.get('updated_at')}")
        print(f"Category:\n {event.get('category')}")
        print(f"Tags:\n {event.get('tags')}")
        print(f"Image URL:\n {event.get('image_url')}")
