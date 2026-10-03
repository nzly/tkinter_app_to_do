import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin, urlencode

# Eventfinda API credentials and call setup
USERNAME = 'easynotesdesktopapp'
PASSWORD = '95gn4kw4gwkj'
#BASE_URL = 'https://api.eventfinda.co.nz/v2/events.json'
BASE_URL = "https://api.eventfinda.co.nz/v2/"

def build_event_url(event_id: int | str | None = None, **params) -> str:
    """
    Builds the Eventfinda API URL.
    
    :param event_id: Optional ID for fetching a single event.
    :param params: Optional query string key-value pairs (e.g., rows=20, start_date='2026-10-01')
    """
    path = f"events/{event_id}.json" if event_id else "events.json"
    url = urljoin(BASE_URL, path)
    
    if params:
        # Automatically encode dictionary into a clean query string
        url = f"{url}?{urlencode(params)}"
        
    return url

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
        build_event_url(),
        # Alternatively, you could pass the parameters directly to build_event_url:
        # build_event_url(**params),
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
    #url = f"https://api.eventfinda.co.nz/v2/events/{event_id}.json"
    url = build_event_url(event_id=event_id)
    
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
    print(f"----------------------------------")
    print(f"Starting Eventfinda API calls...")
    print(f"----------------------------------")
    print(f"These are URL examples for the Eventfinda API")
    print(f"----------------------------------")
    # 1. Fetching multiple events list (events.json)
    print(build_event_url())
    # Output: https://api.eventfinda.co.nz/v2/events.json

    # 2. Fetching multiple events with query parameters
    print(build_event_url(rows=20, location_slug="auckland"))
    # Output: https://api.eventfinda.co.nz/v2/events.json?rows=20&location_slug=auckland

    # 3. Fetching a single event by ID (events/123456.json)
    print(build_event_url(event_id=123456))
    # Output: https://api.eventfinda.co.nz/v2/events/123456.json

    # 4. Single event with specific fields parameter
    print(build_event_url(event_id=123456, fields="event:(id,name,sessions)"))
    # Output: https://api.eventfinda.co.nz/v2/events/123456.json?fields=event%3A%28id%2Cname%2Csessions%29
    print(f"----------------------------------")

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
