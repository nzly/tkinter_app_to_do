import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from objects.data_objects import TaskItem
from db.db import get_next_task_id, insert_task
from tasks_listbox import TasksListboxFrame


def open_add_task_window(parent: tk.Tk, tasks_listbox_frame: TasksListboxFrame, task_items: list[TaskItem], db_path: str) -> None:
    add_window = tk.Toplevel(parent)
    add_window.title("Add Task")
    add_window.geometry("420x450")
    add_window.transient(parent)

    fields = [
        ("task_name", "Task Name"),
        ("due_date", "Due Date"),
        ("task_time", "Task Time"),
        ("duration", "Duration"),
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

    priority_label = ttk.Label(add_window, text="Priority (1=High, 3=Low)")
    priority_label.grid(row=5, column=0, padx=10, pady=6, sticky="w")

    priority_combo = ttk.Combobox(add_window, values=["1", "2", "3"], state="readonly", width=33)
    priority_combo.grid(row=5, column=1, padx=10, pady=6, sticky="ew")
    priority_combo.set("3")

    def refresh_creation_date() -> None:
        today = date.today().isoformat()
        creation_date_entry.config(state="normal")
        creation_date_entry.delete(0, tk.END)
        creation_date_entry.insert(0, today)
        creation_date_entry.config(state="readonly")

    for row_index, (key, label_text) in enumerate(fields, start=1):
        if key == "due_date":
            row_index = 4
        elif key == "task_time":
            row_index = 6
        elif key == "duration":
            row_index = 7
        elif key == "notes":
            row_index = 8

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
        refresh_creation_date()
        refresh_task_id()

    def on_add() -> None:
        values = {field: entries[field].get().strip() for field, _ in fields}
        values["is_completed"] = is_completed_combo.get().strip()
        values["creation_date"] = creation_date_entry.get().strip()
        values["priority"] = priority_combo.get().strip()

        if any(not value for value in values.values()):
            messagebox.showwarning("Input Error", "Please fill all fields before adding the task.")
            return

        is_completed = values["is_completed"].lower() == "yes"

        pending_task = TaskItem(
            task_id=0,
            task_name=values["task_name"],
            is_completed=is_completed,
            creation_date=values["creation_date"],
            due_date=values["due_date"],
            task_time=values["task_time"],
            duration=values["duration"],
            priority=int(values["priority"]),
            notes=values["notes"],
        )
        task_item = insert_task(db_path, pending_task)
        task_items.append(task_item)
        tasks_listbox_frame.add_item(task_item)
        messagebox.showinfo("Success", "Task added successfully.")
        clear_fields()

    add_button = ttk.Button(add_window, text="Add", command=on_add)
    add_button.grid(row=9, column=0, padx=10, pady=12, sticky="ew")

    cancel_button = ttk.Button(add_window, text="Cancel", command=clear_fields)
    cancel_button.grid(row=9, column=1, padx=10, pady=12, sticky="ew")

    add_window.grid_columnconfigure(1, weight=1)
    refresh_task_id()
    refresh_creation_date()
    entries["task_name"].focus_set()
