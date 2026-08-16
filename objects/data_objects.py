import os
from dataclasses import dataclass
from typing import Optional

TASK_TYPE_LABELS = {1: "Normal", 2: "Repeat", 3: "Special"}


def normalize_task_type(value) -> int:
    if isinstance(value, str):
        normalized = value.strip().lower()
        mapping = {"normal": 1, "repeat": 2, "special": 3, "1": 1, "2": 2, "3": 3}
        return mapping.get(normalized, 1)

    try:
        number = int(value)
    except (TypeError, ValueError):
        return 1

    return number if number in TASK_TYPE_LABELS else 1


def get_task_type_label(value) -> str:
    return TASK_TYPE_LABELS.get(normalize_task_type(value), "Normal")


@dataclass
class TaskItem:
    task_id: int
    task_name: str
    is_completed: bool = False
    creation_date: str = ""
    due_date: str = ""
    task_time: Optional[str] = None
    duration: Optional[int] = None
    priority: int = 3
    notes: str = ""
    task_type: int = 1
    repeat_weekdays: Optional[str] = None
    repeat_months: int = 0
    repeat_years: int = 0

    # Return the task identifier.
    def get_task_id(self) -> int:
        return self.task_id
    
    # Return the task name.
    def get_task_name(self) -> str:
        return self.task_name

    # Return True when the task is completed.
    def is_task_completed(self) -> bool:
        return self.is_completed

    # Return the task creation date string.
    def get_creation_date(self) -> str:
        return self.creation_date
    
    # Return the task due date string.
    def get_due_date(self) -> str:
        return self.due_date

    # Return the task time string.
    def get_task_time(self) -> Optional[str]:
        return self.task_time

    # Return the task duration string.
    def get_duration(self) -> Optional[int]:
        return self.duration

    # Return the task priority value.
    def get_priority(self) -> int:
        return self.priority

    # Return the task notes.
    def get_notes(self) -> str:
        return self.notes

    # Return the task type.
    def get_task_type(self) -> int:
        return self.task_type

    # Return a human-readable summary of the task.
    def get_task_summary(self) -> str:
        status = "Completed" if self.is_completed else "Pending"
        return (f"Task ID: {self.task_id}, Name: {self.task_name}, Status: {status}, "
                f"Created: {self.creation_date}, Due: {self.due_date}, "
            f"Time: {self.task_time}, Duration: {self.duration}, "
                f"Priority: {self.priority}, Notes: {self.notes}")

    # Custom string representation for better readability in listboxes and logs.
    def __str__(self) -> str:
        return f"[{self.due_date}] {self.task_name} ({'Done' if self.is_completed else 'Pending'})"

    # Serialize the task item to a dictionary.
    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "is_completed": self.is_completed,
            "creation_date": self.creation_date,
            "due_date": self.due_date,
            "task_time": self.task_time,
            "duration": self.duration,
            "priority": self.priority,
            "notes": self.notes,
            "task_type": normalize_task_type(self.task_type),
            "repeat_weekdays": self.repeat_weekdays,
            "repeat_months": self.repeat_months,
            "repeat_years": self.repeat_years,
        }

@dataclass
class EventItem:
    id: int
    title: str
    start_at: str
    end_at: str
    is_all_day: bool = False
    description: str = ""
    location: str = ""
    provider: str = "local"
    calendar_id: str = ""
    external_event_id: Optional[str] = None
    sync_status: str = "local"
    created_at: str = ""
    updated_at: str = ""
    last_synced_at: str = ""

    def get_id(self) -> int:
        return self.id

    def set_id(self, event_id: int) -> None:
        self.id = event_id

    def get_calendar_id(self) -> str:
        return self.calendar_id

    def set_calendar_id(self, calendar_id: str) -> None:
        self.calendar_id = calendar_id

    def get_title(self) -> str:
        return self.title

    def set_title(self, title: str) -> None:
        self.title = title

    def get_start_at(self) -> str:
        return self.start_at

    def set_start_at(self, start_at: str) -> None:
        self.start_at = start_at

    def get_end_at(self) -> str:
        return self.end_at

    def set_end_at(self, end_at: str) -> None:
        self.end_at = end_at

    def get_is_all_day(self) -> bool:
        return self.is_all_day

    def set_is_all_day(self, is_all_day: bool) -> None:
        self.is_all_day = is_all_day

    def get_description(self) -> str:
        return self.description

    def set_description(self, description: str) -> None:
        self.description = description

    def get_location(self) -> str:
        return self.location

    def set_location(self, location: str) -> None:
        self.location = location

    def get_provider(self) -> str:
        return self.provider

    def set_provider(self, provider: str) -> None:
        self.provider = provider

    def get_external_event_id(self) -> Optional[str]:
        return self.external_event_id

    def set_external_event_id(self, external_event_id: Optional[str]) -> None:
        self.external_event_id = external_event_id

    def get_sync_status(self) -> str:
        return self.sync_status

    def set_sync_status(self, sync_status: str) -> None:
        self.sync_status = sync_status

    def get_created_at(self) -> str:
        return self.created_at

    def set_created_at(self, created_at: str) -> None:
        self.created_at = created_at

    def get_updated_at(self) -> str:
        return self.updated_at

    def set_updated_at(self, updated_at: str) -> None:
        self.updated_at = updated_at

    def get_last_synced_at(self) -> str:
        return self.last_synced_at

    def set_last_synced_at(self, last_synced_at: str) -> None:
        self.last_synced_at = last_synced_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "is_all_day": self.is_all_day,
            "description": self.description,
            "location": self.location,
            "provider": self.provider,
            "calendar_id": self.calendar_id,
            "external_event_id": self.external_event_id,
            "sync_status": self.sync_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_synced_at": self.last_synced_at,
        }

@dataclass
class FileItem:
    file_id: int
    filepath: str
    creation_date: str = ""
    notes: str = ""

    # Return the filename portion of the file path.
    def get_display_name(self) -> str:
        return os.path.basename(self.filepath)

    # Return the full file path.
    def get_full_path(self) -> str:
        return self.filepath

    # Return the file identifier.
    def get_file_id(self) -> int:
        return self.file_id
    
    # Return the file record creation date string.
    def get_creation_date(self) -> str:
        return self.creation_date

    # Return notes associated with the file item.
    def get_notes(self) -> str:
        return self.notes

    # Return a human-readable summary of the file item.
    def get_file_summary(self) -> str:
        return (f"File ID: {self.file_id}, Path: {self.filepath}, "
                f"Created: {self.creation_date}, Notes: {self.notes}")

    # Return a compact display string for file lists.
    def __str__(self) -> str:
        return f"[{self.file_id}] {os.path.basename(self.filepath)}"

    # Serialize the file item to a dictionary.
    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "filepath": self.filepath,
            "creation_date": self.creation_date,
            "notes": self.notes,
        }
