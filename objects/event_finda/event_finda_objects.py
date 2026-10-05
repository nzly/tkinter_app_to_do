from typing import Any

# Represents an event retrieved from the Eventfinda API.
class EventFindaEvent:
    def __init__(
        self,
        event_id: int,
        title: str,
        start_date: str = "",
        end_date: str = "",
        location: str = "",
        free: bool = False,
        *,
        description: str = "",
        datetime_summary: str = "",
        sessions: Any = None,
        location_summary: str = "",
        location_data: dict[str, Any] | None = None,
        url: str = "",
        ticket_types: Any = None,
        location_slug: str = "",
        created_at: str = "",
        updated_at: str = "",
        category: Any = None,
        tags: Any = None,
        image_url: str = "",
    ):
        self.event_id = event_id
        self.title = title
        self.start_date = start_date
        self.end_date = end_date
        self.location = location
        self.free = free
        self.description = description
        self.datetime_summary = datetime_summary
        self.sessions = sessions if sessions is not None else []
        self.location_summary = location_summary
        self.location_data = location_data if location_data is not None else {}
        self.url = url
        self.ticket_types = ticket_types if ticket_types is not None else []
        self.location_slug = location_slug
        self.created_at = created_at
        self.updated_at = updated_at
        self.category = category
        self.tags = tags if tags is not None else []
        self.image_url = image_url

    # Returns the URL of the event.
    @classmethod
    def from_api_data(cls, event_data: dict[str, Any]) -> "EventFindaEvent":
        location_data = event_data.get("location")
        if not isinstance(location_data, dict):
            location_data = {}
        location_summary = event_data.get("location_summary") or ""
        location = location_summary or location_data.get("name", "")

        return cls(
            event_id=event_data.get("id", event_data.get("event_id", 0)),
            title=event_data.get("name", event_data.get("title", "")),
            start_date=event_data.get("start_date") or event_data.get("datetime_start") or "",
            end_date=event_data.get("end_date") or event_data.get("datetime_end") or "",
            location=location,
            free=bool(event_data.get("is_free", event_data.get("free", False))),
            description=event_data.get("description", "") or "",
            datetime_summary=event_data.get("datetime_summary", "") or "",
            sessions=event_data.get("sessions"),
            location_summary=location_summary,
            location_data=location_data,
            url=event_data.get("url", "") or "",
            ticket_types=event_data.get("ticket_types"),
            location_slug=event_data.get("location_slug", "") or "",
            created_at=event_data.get("created_at", "") or "",
            updated_at=event_data.get("updated_at", "") or "",
            category=event_data.get("category"),
            tags=event_data.get("tags"),
            image_url=event_data.get("image_url", "") or "",
        )

    # Returns the event ID.
    def get_event_id(self) -> int:
        return self.event_id

    # Returns the title of the event.
    def get_title(self) -> str:
        return self.title

    # Returns the start date of the event.
    def get_start_date(self) -> str:
        return self.start_date

    # Returns the end date of the event.
    def get_end_date(self) -> str:
        return self.end_date

    # Returns the location of the event.
    def get_location(self) -> str:
        return self.location

    # Returns whether the event is free.
    def is_free(self) -> bool:
        return self.free

    # Returns the description of the event.
    def get_description(self) -> str:
        return self.description

    # Returns the date and time summary of the event.
    def get_datetime_summary(self) -> str:
        return self.datetime_summary

    # Returns the sessions of the event.
    def get_sessions(self) -> Any:
        return self.sessions

    # Returns the location summary of the event.
    def get_location_summary(self) -> str:
        return self.location_summary

    # Returns the location data of the event.
    def get_location_data(self) -> dict[str, Any]:
        return self.location_data

    # Returns the URL of the event.
    def get_url(self) -> str:
        return self.url

    # Returns the ticket types of the event.
    def get_ticket_types(self) -> Any:
        return self.ticket_types

    # Returns the location slug of the event.
    def get_location_slug(self) -> str:
        return self.location_slug

    # Returns the creation timestamp of the event.
    def get_created_at(self) -> str:
        return self.created_at

    # Returns the last updated timestamp of the event.
    def get_updated_at(self) -> str:
        return self.updated_at

    # Returns the category of the event.
    def get_category(self) -> Any:
        return self.category

    # Returns the tags associated with the event.
    def get_tags(self) -> Any:
        return self.tags

    # Returns the image URL of the event.
    def get_image_url(self) -> str:
        return self.image_url

    # Returns a string representation of the event.
    def __repr__(self) -> str:
        return (
            f"EventFindaEvent(event_id={self.event_id}, title={self.title!r}, "
            f"start_date={self.start_date!r}, end_date={self.end_date!r}, "
            f"location={self.location!r}, free={self.free}, "
            f"url={self.url!r}, location_slug={self.location_slug!r})"
        )