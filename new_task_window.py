import tkinter as tk
from tkinter import ttk, messagebox
from calendar import monthrange
from datetime import date, timedelta

from objects.data_objects import TaskItem, normalize_task_type
from db.db import get_next_task_id, insert_task
from tasks_listbox import TasksListboxFrame


WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def build_repeat_occurrences(start_date: date, selected_weekdays: list[int], months: int = 0, years: int = 0) -> list[date]:
    if not selected_weekdays:
        return []

    occurrences: list[date] = []
    total_months = months + (years * 12)
    current_year = start_date.year
    current_month = start_date.month

    if total_months <= 0:
        total_months = 1

    for offset in range(total_months):
        month_index = current_month - 1 + offset
        year = current_year + (month_index // 12)
        month = ((month_index % 12) + 12) % 12 + 1
        last_day = monthrange(year, month)[1]

        for day in range(1, last_day + 1):
            candidate_date = date(year, month, day)
            if candidate_date < start_date:
                continue
            if candidate_date.weekday() in selected_weekdays:
                occurrences.append(candidate_date)

    return occurrences


def open_add_task_window(parent: tk.Tk, tasks_listbox_frame: TasksListboxFrame, task_items: list[TaskItem], db_path: str) -> None:
    add_window = tk.Toplevel(parent)
    add_window.title("Add Task")
    add_window.geometry("470x600")
    add_window.transient(parent)

    fields = [
        ("task_name", "Task Name"),
        ("due_date", "Due Date"),
        ("task_time", "Task Time"),
        ("duration", "Duration (mins)"),
        ("notes", "Notes"),
    ]

    task_id_label = ttk.Label(add_window, text="Task ID")
    task_id_label.grid(row=0, column=0, padx=10, pady=6, sticky="w")

    task_id_entry = ttk.Entry(add_window, width=36, state="readonly")
    task_id_entry.grid(row=0, column=1, padx=10, pady=6, sticky="ew")

    entries: dict[str, ttk.Entry] = {}

    is_completed_label = ttk.Label(add_window, text="Is Completed")
    is_completed_label.grid(row=2, column=0, padx=10, pady=6, sticky="w")

    is_completed_combo = ttk.Combobox(add_window, values=["Yes", "No"], state="readonly", width=33)
    is_completed_combo.grid(row=2, column=1, padx=10, pady=6, sticky="ew")
    is_completed_combo.set("No")

    creation_date_label = ttk.Label(add_window, text="Creation Date")
    creation_date_label.grid(row=3, column=0, padx=10, pady=6, sticky="w")

    creation_date_entry = ttk.Entry(add_window, width=36, state="readonly")
    creation_date_entry.grid(row=3, column=1, padx=10, pady=6, sticky="ew")

    type_label = ttk.Label(add_window, text="Type")
    type_label.grid(row=4, column=0, padx=10, pady=6, sticky="w")

    task_type_combo = ttk.Combobox(add_window, values=["Normal", "Repeat", "Special"], state="readonly", width=33)
    task_type_combo.grid(row=4, column=1, padx=10, pady=6, sticky="ew")
    task_type_combo.set("Normal")

    priority_label = ttk.Label(add_window, text="Priority (1=High, 3=Low)")
    priority_label.grid(row=5, column=0, padx=10, pady=6, sticky="w")

    priority_combo = ttk.Combobox(add_window, values=["1", "2", "3"], state="readonly", width=33)
    priority_combo.grid(row=5, column=1, padx=10, pady=6, sticky="ew")
    priority_combo.set("3")

    repeat_frame = ttk.LabelFrame(add_window, text="Repeat Settings", padding=8)
    repeat_frame.grid(row=10, column=0, columnspan=2, padx=10, pady=6, sticky="ew")

    weekday_vars: list[tk.IntVar] = []
    for index, name in enumerate(WEEKDAY_NAMES):
        var = tk.IntVar(value=0)
        ttk.Checkbutton(repeat_frame, text=name, variable=var).grid(row=0, column=index, padx=2, pady=2, sticky="w")
        weekday_vars.append(var)

    ttk.Label(repeat_frame, text="Months").grid(row=1, column=0, padx=2, pady=6, sticky="w")
    repeat_months_entry = ttk.Entry(repeat_frame, width=8)
    repeat_months_entry.grid(row=1, column=1, padx=2, pady=6, sticky="w")
    repeat_months_entry.insert(0, "0")

    ttk.Label(repeat_frame, text="Years").grid(row=1, column=2, padx=2, pady=6, sticky="w")
    repeat_years_entry = ttk.Entry(repeat_frame, width=8)
    repeat_years_entry.grid(row=1, column=3, padx=2, pady=6, sticky="w")
    repeat_years_entry.insert(0, "0")

    repeat_frame.grid_remove()

    def refresh_creation_date() -> None:
        today = date.today().isoformat()
        creation_date_entry.config(state="normal")
        creation_date_entry.delete(0, tk.END)
        creation_date_entry.insert(0, today)
        creation_date_entry.config(state="readonly")

    for row_index, (key, label_text) in enumerate(fields, start=1):
        if key == "due_date":
            row_index = 6
        elif key == "task_time":
            row_index = 7
        elif key == "duration":
            row_index = 8
        elif key == "notes":
            row_index = 9

        label = ttk.Label(add_window, text=label_text)
        label.grid(row=row_index, column=0, padx=10, pady=6, sticky="w")

        entry = ttk.Entry(add_window, width=36)
        entry.grid(row=row_index, column=1, padx=10, pady=6, sticky="ew")
        entries[key] = entry

    def refresh_task_id() -> None:
        next_task_id = get_next_task_id(db_path)
        task_id_entry.config(state="normal")
        task_id_entry.delete(0, tk.END)
        task_id_entry.insert(0, str(next_task_id))
        task_id_entry.config(state="readonly")

    def clear_fields() -> None:
        for entry in entries.values():
            entry.delete(0, tk.END)
        is_completed_combo.set("No")
        priority_combo.set("3")
        task_type_combo.set("Normal")
        repeat_frame.grid_remove()
        for var in weekday_vars:
            var.set(0)
        repeat_months_entry.delete(0, tk.END)
        repeat_years_entry.delete(0, tk.END)
        repeat_months_entry.insert(0, "0")
        repeat_years_entry.insert(0, "0")
        refresh_creation_date()
        refresh_task_id()

    def toggle_repeat_settings() -> None:
        if task_type_combo.get() == "Repeat":
            repeat_frame.grid()
        else:
            repeat_frame.grid_remove()

    task_type_combo.bind("<<ComboboxSelected>>", lambda _event: toggle_repeat_settings())

    def on_add() -> None:
        values = {field: entries[field].get().strip() for field, _ in fields}
        values["is_completed"] = is_completed_combo.get().strip()
        values["creation_date"] = creation_date_entry.get().strip()
        values["priority"] = priority_combo.get().strip()
        values["task_type"] = task_type_combo.get().strip()

        required_fields = ["task_name", "due_date", "notes", "is_completed", "creation_date", "priority"]
        if any(not values[field] for field in required_fields):
            messagebox.showwarning("Input Error", "Please fill in the required fields before adding the task.")
            return

        duration_value = None
        if values["duration"]:
            try:
                duration_value = int(values["duration"])
            except ValueError:
                messagebox.showwarning("Input Error", "Duration must be a whole number of minutes.")
                return
            if duration_value < 0:
                messagebox.showwarning("Input Error", "Duration cannot be negative.")
                return

        task_type_label = values["task_type"]
        task_type_code = normalize_task_type(task_type_label)

        repeat_weekdays = []
        if task_type_label == "Repeat":
            repeat_weekdays = [index for index, var in enumerate(weekday_vars) if var.get() == 1]
            if not repeat_weekdays:
                messagebox.showwarning("Input Error", "Select at least one weekday for repeated tasks.")
                return

            try:
                months = int(repeat_months_entry.get().strip() or "0")
                years = int(repeat_years_entry.get().strip() or "0")
            except ValueError:
                messagebox.showwarning("Input Error", "Months and years must be whole numbers.")
                return
            if months < 0 or years < 0:
                messagebox.showwarning("Input Error", "Months and years cannot be negative.")
                return
        else:
            months = 0
            years = 0

        is_completed = values["is_completed"].lower() == "yes"

        pending_task = TaskItem(
            task_id=0,
            task_name=values["task_name"],
            is_completed=is_completed,
            creation_date=values["creation_date"],
            due_date=values["due_date"],
            task_time=values["task_time"] or None,
            duration=duration_value,
            priority=int(values["priority"]),
            notes=values["notes"],
            task_type=task_type_code,
            repeat_weekdays=",".join(str(weekday) for weekday in repeat_weekdays),
            repeat_months=months,
            repeat_years=years,
        )
        task_item = insert_task(db_path, pending_task)
        task_items.append(task_item)
        tasks_listbox_frame.add_item(task_item)

        if task_type_label == "Repeat":
            try:
                start_date = date.fromisoformat(values["due_date"])
            except ValueError:
                start_date = date.today()
            occurrences = build_repeat_occurrences(start_date, repeat_weekdays, months=months, years=years)
            for occurrence in occurrences:
                if occurrence == start_date:
                    continue
                repeating_task = TaskItem(
                    task_id=0,
                    task_name=values["task_name"],
                    is_completed=False,
                    creation_date=values["creation_date"],
                    due_date=occurrence.isoformat(),
                    task_time=values["task_time"] or None,
                    duration=duration_value,
                    priority=int(values["priority"]),
                    notes=values["notes"],
                    task_type=task_type_code,
                    repeat_weekdays=",".join(str(weekday) for weekday in repeat_weekdays),
                    repeat_months=months,
                    repeat_years=years,
                )
                inserted_repeating_task = insert_task(db_path, repeating_task)
                task_items.append(inserted_repeating_task)
                tasks_listbox_frame.add_item(inserted_repeating_task)

        messagebox.showinfo("Success", "Task added successfully.")
        clear_fields()

    add_button = ttk.Button(add_window, text="Add", command=on_add)
    add_button.grid(row=11, column=0, padx=10, pady=12, sticky="ew")

    cancel_button = ttk.Button(add_window, text="Cancel", command=clear_fields)
    cancel_button.grid(row=11, column=1, padx=10, pady=12, sticky="ew")

    add_window.grid_columnconfigure(1, weight=1)
    refresh_task_id()
    refresh_creation_date()
    entries["task_name"].focus_set()
