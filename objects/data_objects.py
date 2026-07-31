import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class TaskItem:
    task_id: int
    task_name: str
    is_completed: bool = False
    creation_date: str = ""
    due_date: str = ""
    task_time: Optional[str] = None
    duration: Optional[float] = None
    priority: int = 3
    notes: str = ""

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
    def get_duration(self) -> Optional[float]:
        return self.duration

    # Return the task priority value.
    def get_priority(self) -> int:
        return self.priority

    # Return the task notes.
    def get_notes(self) -> str:
        return self.notes
    
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
