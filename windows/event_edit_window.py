import tkinter as tk
from datetime import date, datetime
from tkinter import messagebox, ttk
from typing import Callable

from components.date_picker import DatePickerEntry
from db.db import get_event_task_ids, update_event
from objects.data_objects import EventItem, TaskItem

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_FORMAT = "%Y-%m-%d"


# Parse a timed-event value entered by the user.
def _parse_date_time(value: str) -> datetime | None:
    try:
        return datetime.strptime(value.strip(), DATE_TIME_FORMAT)
    except ValueError:
        return None


# Parse a date-only event value entered by the user.
def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


# Convert a stored event value into the edit form's input format.
def _format_event_value_for_edit(value: str, is_all_day: bool) -> str:
    raw_value = (value or "").strip()
    if not raw_value:
        return ""

    normalized_value = raw_value.replace("T", " ")

    try:
        if is_all_day:
            return date.fromisoformat(normalized_value.split()[0]).strftime(DATE_FORMAT)
        return datetime.fromisoformat(normalized_value).strftime(DATE_TIME_FORMAT)
    except ValueError:
        return raw_value


# Create the dialog used to edit an existing event.
def open_edit_event_window(
    parent: tk.Misc,
    db_path: str,
    event_item: EventItem,
    task_items: list[TaskItem],
    on_event_updated: Callable[[], None] | None = None,
) -> None:
    edit_window = tk.Toplevel(parent)
    edit_window.title("Edit Event")
    edit_window.geometry("520x650")
    edit_window.minsize(520, 650)
    edit_window.transient(parent)
    edit_window.grab_set()

    container = ttk.Frame(edit_window, padding=12)
    container.grid(row=0, column=0, sticky="nsew")
    container.grid_columnconfigure(1, weight=1)

    event_id_label = ttk.Label(container, text=str(event_item.id))
    title_entry = ttk.Entry(container, width=36)
    # Double-click to pick a date from the calendar pop-up.
    start_entry = DatePickerEntry(
        container,
        placeholder="Double-click to pick a date",
        date_pattern='yyyy-mm-dd',
        font=("Helvetica", 11),
        width=30,
    )
    end_entry = DatePickerEntry(
        container,
        placeholder="Double-click to pick a date",
        date_pattern='yyyy-mm-dd',
        font=("Helvetica", 11),
        width=30,
    )
    location_entry = ttk.Entry(container, width=36)
    all_day_var = tk.IntVar(value=int(event_item.is_all_day))

    start_label = ttk.Label(container, text="Start")
    end_label = ttk.Label(container, text="End")
    fields = [
        ("Event ID", event_id_label),
        ("Title *", title_entry),
        ("", start_entry),
        ("", end_entry),
        ("Location", location_entry),
    ]
    for row_index, (label_text, widget) in enumerate(fields):
        label = start_label if row_index == 2 else end_label if row_index == 3 else ttk.Label(container, text=label_text)
        label.grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
        widget.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")

    title_entry.insert(0, event_item.title)
    # Clear the placeholder text before inserting the existing event's dates.
    for date_entry, value in (
        (start_entry, _format_event_value_for_edit(event_item.start_at, bool(event_item.is_all_day))),
        (end_entry, _format_event_value_for_edit(event_item.end_at, bool(event_item.is_all_day))),
    ):
        date_entry.delete(0, tk.END)
        date_entry.insert(0, value)
        date_entry['fg'] = date_entry.default_fg_color
    location_entry.insert(0, event_item.location)

    ttk.Label(container, text="Link Tasks").grid(row=5, column=0, padx=8, pady=6, sticky="nw")
    task_filter_frame = ttk.Frame(container)
    task_filter_frame.grid(row=5, column=1, padx=(8, 0), pady=(6, 0), sticky="w")
    show_pending_var = tk.IntVar(value=1)
    show_done_var = tk.IntVar(value=1)
    ttk.Checkbutton(task_filter_frame, text="Pending", variable=show_pending_var, command=lambda: refresh_task_list()).grid(row=0, column=0, padx=(0, 12))
    ttk.Checkbutton(task_filter_frame, text="Done", variable=show_done_var, command=lambda: refresh_task_list()).grid(row=0, column=1)

    task_listbox = tk.Listbox(container, selectmode=tk.MULTIPLE, height=5, exportselection=False)
    task_listbox.grid(row=6, column=1, padx=(8, 0), pady=6, sticky="ew")
    task_scrollbar = ttk.Scrollbar(container, orient="vertical", command=task_listbox.yview)
    task_scrollbar.grid(row=6, column=2, padx=(0, 8), pady=6, sticky="ns")
    task_listbox.configure(yscrollcommand=task_scrollbar.set)

    linked_task_ids = set(get_event_task_ids(db_path, event_item.id))
    selected_task_ids = set(linked_task_ids)
    displayed_task_items: list[TaskItem] = []

    # Keep track of selections made before the visible task list is rebuilt.
    def sync_selected_task_ids() -> None:
        if not displayed_task_items:
            return
        visible_ids = {task_item.task_id for task_item in displayed_task_items}
        selected_task_ids.difference_update(visible_ids)
        selected_task_ids.update(displayed_task_items[index].task_id for index in task_listbox.curselection())

    # Rebuild the Link Tasks list based on the Pending/Done checkbox filters.
    def refresh_task_list() -> None:
        nonlocal displayed_task_items
        sync_selected_task_ids()

        show_pending = bool(show_pending_var.get())
        show_done = bool(show_done_var.get())
        if show_pending == show_done:
            displayed_task_items = list(task_items)
        elif show_pending:
            displayed_task_items = [task_item for task_item in task_items if not task_item.is_completed]
        else:
            displayed_task_items = [task_item for task_item in task_items if task_item.is_completed]

        task_listbox.delete(0, tk.END)
        for task_item in displayed_task_items:
            due_date = task_item.due_date or "No due date"
            status = "Done" if task_item.is_completed else "Pending"
            task_listbox.insert(tk.END, f"{task_item.task_id}: {task_item.task_name} (Due: {due_date}) [{status}]")
        for index, task_item in enumerate(displayed_task_items):
            if task_item.task_id in selected_task_ids:
                task_listbox.selection_set(index)

    task_listbox.bind("<<ListboxSelect>>", lambda _event: sync_selected_task_ids())
    refresh_task_list()

    # Update date field labels for all-day or timed event mode.
    def update_labels() -> None:
        if all_day_var.get():
            start_label.config(text="Start Date (YYYY-MM-DD) *")
            end_label.config(text="End Date (YYYY-MM-DD) *")
        else:
            start_label.config(text="Start (YYYY-MM-DD HH:MM) *")
            end_label.config(text="End (YYYY-MM-DD HH:MM) *")

    ttk.Checkbutton(
        container,
        text="All-day event",
        variable=all_day_var,
        command=update_labels,
    ).grid(row=7, column=1, padx=8, pady=6, sticky="w")

    ttk.Label(container, text="Description").grid(row=8, column=0, padx=8, pady=6, sticky="nw")
    description_text = tk.Text(container, height=7, wrap="word", relief=tk.FLAT, borderwidth=1)
    description_text.insert("1.0", event_item.description)
    description_text.grid(row=8, column=1, padx=8, pady=6, sticky="ew")

    # Validate and persist the edited event and task links.
    def save_changes() -> None:
        title = title_entry.get().strip()
        start_raw = start_entry.get().strip()
        end_raw = end_entry.get().strip()
        if not title:
            messagebox.showwarning("Input Error", "Event title is required.")
            return

        if all_day_var.get():
            start_date = _parse_date(start_raw)
            end_date = _parse_date(end_raw)
            if start_date is None or end_date is None:
                messagebox.showwarning("Input Error", "All-day dates must use YYYY-MM-DD.")
                return
            if end_date < start_date:
                messagebox.showwarning("Input Error", "End date cannot be before the start date.")
                return
            start_at = start_date.isoformat()
            end_at = end_date.isoformat()
        else:
            start_datetime = _parse_date_time(start_raw)
            end_datetime = _parse_date_time(end_raw)
            if start_datetime is None or end_datetime is None:
                messagebox.showwarning("Input Error", "Start and end must use YYYY-MM-DD HH:MM.")
                return
            if end_datetime <= start_datetime:
                messagebox.showwarning("Input Error", "End time must be after the start time.")
                return
            start_at = start_datetime.isoformat(timespec="minutes")
            end_at = end_datetime.isoformat(timespec="minutes")

        updated_event = EventItem(
            id=event_item.id,
            title=title,
            start_at=start_at,
            end_at=end_at,
            is_all_day=bool(all_day_var.get()),
            description=description_text.get("1.0", tk.END).strip(),
            location=location_entry.get().strip(),
            provider=event_item.provider,
            calendar_id=event_item.calendar_id,
            external_event_id=event_item.external_event_id,
            sync_status=event_item.sync_status,
            created_at=event_item.created_at,
            last_synced_at=event_item.last_synced_at,
        )
        sync_selected_task_ids()
        if not update_event(db_path, updated_event, task_ids=list(selected_task_ids)):
            messagebox.showerror("Update Error", "Could not update the event.")
            return

        if on_event_updated is not None:
            on_event_updated()
        messagebox.showinfo("Success", "Event updated successfully.")
        edit_window.destroy()

    button_row = ttk.Frame(container)
    button_row.grid(row=9, column=0, columnspan=2, padx=8, pady=(12, 0), sticky="ew")
    button_row.grid_columnconfigure(0, weight=1)
    button_row.grid_columnconfigure(1, weight=1)
    ttk.Button(button_row, text="Cancel", command=edit_window.destroy).grid(row=0, column=0, padx=(0, 6), sticky="ew")
    ttk.Button(button_row, text="Save Changes", command=save_changes).grid(row=0, column=1, padx=(6, 0), sticky="ew")

    update_labels()
    edit_window.grid_rowconfigure(0, weight=1)
    edit_window.grid_columnconfigure(0, weight=1)
    title_entry.focus_set()
