import os
from dataclasses import dataclass

@dataclass
class TaskItem:
    task_id: int
    task_name: str
    is_completed: bool = False
    creation_date: str = ""
    due_date: str = ""
    priority: int = 3
    notes: str = ""

    def get_task_id(self) -> int:
        return self.task_id
    
    def get_task_name(self) -> str:
        return self.task_name

    def is_task_completed(self) -> bool:
        return self.is_completed

    def get_creation_date(self) -> str:
        return self.creation_date
    
    def get_due_date(self) -> str:
        return self.due_date

    def get_priority(self) -> int:
        return self.priority

    def get_notes(self) -> str:
        return self.notes
    
    def get_task_summary(self) -> str:
        status = "Completed" if self.is_completed else "Pending"
        return (f"Task ID: {self.task_id}, Name: {self.task_name}, Status: {status}, "
                f"Created: {self.creation_date}, Due: {self.due_date}, "
                f"Priority: {self.priority}, Notes: {self.notes}")

    def __str__(self) -> str:
        return f"[{self.task_id}] {self.task_name} ({'Done' if self.is_completed else 'Pending'})"

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "is_completed": self.is_completed,
            "creation_date": self.creation_date,
            "due_date": self.due_date,
            "priority": self.priority,
            "notes": self.notes,
        }

@dataclass
class FileItem:
    file_id: int
    filepath: str
    creation_date: str = ""
    notes: str = ""

    def get_display_name(self) -> str:
        return os.path.basename(self.filepath)

    def get_full_path(self) -> str:
        return self.filepath

    def get_file_id(self) -> int:
        return self.file_id
    
    def get_creation_date(self) -> str:
        return self.creation_date

    def get_notes(self) -> str:
        return self.notes

    def get_file_summary(self) -> str:
        return (f"File ID: {self.file_id}, Path: {self.filepath}, "
                f"Created: {self.creation_date}, Notes: {self.notes}")

    def __str__(self) -> str:
        return f"[{self.file_id}] {os.path.basename(self.filepath)}"

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "filepath": self.filepath,
            "creation_date": self.creation_date,
            "notes": self.notes,
        }
