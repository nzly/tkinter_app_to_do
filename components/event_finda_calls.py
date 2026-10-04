import json
import os
import sys
import requests

from pathlib import Path
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin, urlencode

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from objects.logger import get_logger

BASE_URL = "https://api.eventfinda.co.nz/v2/"
_CREDENTIALS_FILE = Path(__file__).resolve().parents[1] / "security" / "eventfinda_credentials.json"


def _get_auth() -> HTTPBasicAuth:
    if os.getenv("EVENTFINDA_USERNAME") and os.getenv("EVENTFINDA_PASSWORD"):
        return HTTPBasicAuth(os.environ["EVENTFINDA_USERNAME"], os.environ["EVENTFINDA_PASSWORD"])

    try:
        with _CREDENTIALS_FILE.open(encoding="utf-8") as credentials_file:
            credentials = json.load(credentials_file)
    except FileNotFoundError as error:
        raise RuntimeError(
            f"Eventfinda credentials not found. Create {_CREDENTIALS_FILE} "
            "or set EVENTFINDA_USERNAME and EVENTFINDA_PASSWORD."
        ) from error

    username = credentials.get("username")
    password = credentials.get("password")
    if not username or not password:
        raise ValueError(f"Eventfinda credentials file must contain username and password: {_CREDENTIALS_FILE}")
    return HTTPBasicAuth(username, password)

# Function to build Eventfinda API URLs for events (single or multiple)
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
        auth=_get_auth(),
        headers={'Accept': 'application/json'}
    )

    if response.status_code != 200:
        get_logger().info("Failed to retrieve events: %s", response.status_code)
        return [], 0

    data = response.json()
    events = data.get('events', [])
    total_count = data.get('@attributes', {}).get('count', len(events))
    get_logger().info("Starting retrieval of events from Eventfinda API")
    get_logger().info("Retrieved %s of %s events", len(events), total_count)
    for event in events:
        get_logger().info("%s - %s", event['name'], event.get('datetime_summary', ''))
    return events, total_count

# Fetch a single event by its ID from the Eventfinda API. Returns the event data as a dictionary, or None if the request fails.
def get_single_event(event_id: int):
    #url = f"https://api.eventfinda.co.nz/v2/events/{event_id}.json"
    url = build_event_url(event_id=event_id)
    
    response = requests.get(
        url,
        auth=_get_auth(),
        headers={"Accept": "application/json"}
    )
    
    if response.status_code == 200:
        # The single event object is returned directly (not inside a list)
        event_data = response.json()
        return event_data
    else:
        get_logger().info("Failed to fetch event %s. Status: %s", event_id, response.status_code)
        return None
    
if __name__ == "__main__":
    get_logger().info("----------------------------------")
    get_logger().info("Starting Eventfinda API calls...")
    get_logger().info("----------------------------------")
    get_logger().info("These are URL examples for the Eventfinda API")
    get_logger().info("----------------------------------")
    # 1. Fetching multiple events list (events.json)
    get_logger().info(build_event_url())
    # Output: https://api.eventfinda.co.nz/v2/events.json

    # 2. Fetching multiple events with query parameters
    get_logger().info(build_event_url(rows=20, location_slug="auckland"))
    # Output: https://api.eventfinda.co.nz/v2/events.json?rows=20&location_slug=auckland

    # 3. Fetching a single event by ID (events/123456.json)
    get_logger().info(build_event_url(event_id=123456))
    # Output: https://api.eventfinda.co.nz/v2/events/123456.json

    # 4. Single event with specific fields parameter
    get_logger().info(build_event_url(event_id=123456, fields="event:(id,name,sessions)"))
    # Output: https://api.eventfinda.co.nz/v2/events/123456.json?fields=event%3A%28id%2Cname%2Csessions%29
    get_logger().info("----------------------------------")

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
    get_logger().info("----------------------------------")
    get_logger().info("Fetching event with ID: %s", event_id)
    get_logger().info("----------------------------------")
    event = get_single_event(event_id)
    if event:
        get_logger().info("Name: %s", event.get('name'))
        get_logger().info("Description: %s", event.get('description'))
        get_logger().info("Sessions: %s", event.get('sessions'))
        get_logger().info("Location/Venue: %s", event.get('location_summary'))
        get_logger().info("URL: %s", event.get('url'))
        get_logger().info("Ticket Types: %s", event.get('ticket_types'))
        get_logger().info("Start Date: %s", event.get('start_date'))
        get_logger().info("End Date: %s", event.get('end_date'))
        get_logger().info("Location Slug: %s", event.get('location_slug'))
        get_logger().info("Created At: %s", event.get('created_at'))
        get_logger().info("Updated At: %s", event.get('updated_at'))
        get_logger().info("Category: %s", event.get('category'))
        get_logger().info("Tags: %s", event.get('tags'))
        get_logger().info("Image URL: %s", event.get('image_url'))
