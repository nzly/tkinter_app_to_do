import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

from objects.data_objects import EventItem, TaskItem


DISPLAY_DATE_TIME_FORMAT = "%d %b %Y, %I:%M %p"
DISPLAY_DATE_FORMAT = "%d %b %Y"


# Format an event date or datetime for display in the summary window.
def _format_event_value(value: str, is_all_day: bool) -> str:
    try:
        if is_all_day:
            return date.fromisoformat(value).strftime(DISPLAY_DATE_FORMAT)
        return datetime.fromisoformat(value).strftime(DISPLAY_DATE_TIME_FORMAT)
    except ValueError:
        return value or "-"


class EventSummaryWindow(tk.Toplevel):
    # Build the structured event summary window.
    def __init__(
        self,
        parent: tk.Misc,
        event: EventItem,
        linked_tasks: list[TaskItem] | None = None,
        linked_task_ids: list[int] | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Event Summary")
        self.geometry("700x600")
        self.minsize(700, 600)
        self.transient(parent)
        self.grab_set()
        self.configure(bg="#f4f6f8")

        linked_tasks = linked_tasks or []
        linked_task_ids = linked_task_ids or []
        task_by_id = {task.task_id: task for task in linked_tasks}

        footer = ttk.Frame(self, padding=(12, 0, 12, 10))
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(footer, text="Close", command=self.destroy).pack(side=tk.RIGHT)

        outer = ttk.Frame(self, padding=(12, 10, 12, 8))
        outer.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(outer)
        header.pack(fill=tk.X)
        ttk.Label(header, text=event.title, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        status = "All-day" if event.is_all_day else "Timed event"
        ttk.Label(
            header,
            text=f"Event #{event.id}  |  {status}",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(2, 0))

        ttk.Separator(outer).pack(fill=tk.X, pady=10)

        details_card = ttk.LabelFrame(outer, text="Event Details", padding=8)
        details_card.pack(fill=tk.X)
        details = [
            ("Event ID", event.id),
            ("Title", event.title),
            ("Start", _format_event_value(event.start_at, event.is_all_day)),
            ("End", _format_event_value(event.end_at, event.is_all_day)),
            ("Location", event.location or "-"),
            ("Provider", event.provider or "Local"),
            ("Sync Status", event.sync_status or "Local"),
        ]
        for row_index, (label_text, value) in enumerate(details):
            ttk.Label(
                details_card,
                text=f"{label_text}:",
                font=("Segoe UI", 9, "bold"),
            ).grid(row=row_index, column=0, sticky="w", padx=(0, 8), pady=1)
            ttk.Label(
                details_card,
                text=str(value),
                font=("Segoe UI", 9),
            ).grid(row=row_index, column=1, sticky="w", pady=1)
        details_card.grid_columnconfigure(1, weight=1)

        notes_card = ttk.LabelFrame(outer, text="Description", padding=8)
        notes_card.pack(fill=tk.X, pady=(8, 0))
        notes_text = tk.Text(notes_card, height=3, wrap="word", borderwidth=0, background="#ffffff")
        notes_text.insert("1.0", event.description or "No description provided.")
        notes_text.configure(state="disabled")
        notes_text.pack(fill=tk.BOTH, expand=True)

        tasks_card = ttk.LabelFrame(outer, text="Linked Tasks", padding=8)
        tasks_card.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        if linked_task_ids:
            task_list = tk.Listbox(tasks_card, height=7, activestyle="none")
            task_scrollbar = ttk.Scrollbar(tasks_card, orient=tk.VERTICAL, command=task_list.yview)
            task_list.configure(yscrollcommand=task_scrollbar.set)
            task_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            for task_id in linked_task_ids:
                task = task_by_id.get(task_id)
                if task is None:
                    task_list.insert(tk.END, f"Task #{task_id}")
                else:
                    due_date = task.due_date or "No due date"
                    task_list.insert(tk.END, f"Task #{task.task_id}: {task.task_name}  |  Due: {due_date}")
        else:
            ttk.Label(tasks_card, text="No tasks linked to this event.").pack(anchor="w")


# Open a structured summary window for an event.
def show_event_summary(
    parent: tk.Misc,
    event: EventItem,
    linked_tasks: list[TaskItem] | None = None,
    linked_task_ids: list[int] | None = None,
) -> EventSummaryWindow:
    return EventSummaryWindow(parent, event, linked_tasks, linked_task_ids)
