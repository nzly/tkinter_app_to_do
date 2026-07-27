import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from functools import partial
from datetime import date
from tasks_listbox import TasksListboxFrame
from files_listbox import FilesListboxFrame
from objects.data_objects import TaskItem

# Make ttkthemes optional
try:
    from ttkthemes import ThemedTk
    _USE_THEMED = True
except ImportError:
    ThemedTk = None
    _USE_THEMED = False

# Function to delete selected task
def delete_task(tasks_listbox: tk.Listbox) -> None:
    selected_indices = tasks_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Error", "Please select a task to delete.")
        return
    # Convert indices to ints and delete in reverse to avoid reindexing issues
    for index in reversed([int(i) for i in selected_indices]):
        tasks_listbox.delete(index)

# Function to open file dialog and select a file
def select_file(files_listbox: tk.Listbox) -> None:
    filepath = filedialog.askopenfilename(
        initialdir=os.path.expanduser("~"),
        title="Select a file",
        filetypes=(("Text files", "*.txt"), ("JPG files", "*.jpg"),
                   ("PNG files", "*.png"), ("All files", "*.*"))
    )
    if filepath:
        files_listbox.insert(tk.END, filepath)
        # Optional: show info to user instead of printing
        # messagebox.showinfo("File Selected", f"Selected: {filepath}")

# Function to handle double-click on listbox item
def on_select(event=None) -> None:
    widget = event.widget
    selection_index = widget.curselection()
    if selection_index:
        selected_item = widget.get(int(selection_index[0]))
        messagebox.showinfo("Selected Item", f"You selected: {selected_item}")


def search_task(search_entry: tk.Entry, tasks_listbox: tk.Listbox) -> None:
    query = search_entry.get().strip().lower()
    if not query:
        messagebox.showwarning("Search Error", "Please enter text to search.")
        return

    tasks = tasks_listbox.get(0, tk.END)
    for index, task in enumerate(tasks):
        if query in str(task).lower():
            tasks_listbox.selection_clear(0, tk.END)
            tasks_listbox.selection_set(index)
            tasks_listbox.activate(index)
            tasks_listbox.see(index)
            return

    messagebox.showinfo("Search", f"No task found matching: {search_entry.get().strip()}")

def open_add_task_window(parent: tk.Tk, tasks_listbox: tk.Listbox, task_items: list[TaskItem]) -> None:
    add_window = tk.Toplevel(parent)
    add_window.title("Add Task")
    add_window.geometry("420x360")
    add_window.transient(parent)

    fields = [
        ("task_name", "Task Name"),
        ("due_date", "Due Date"),
        ("priority", "Priority"),
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

    def refresh_creation_date() -> None:
        today = date.today().isoformat()
        creation_date_entry.config(state="normal")
        creation_date_entry.delete(0, tk.END)
        creation_date_entry.insert(0, today)
        creation_date_entry.config(state="readonly")

    for row_index, (key, label_text) in enumerate(fields, start=1):
        if key == "due_date":
            row_index = 4
        elif key == "priority":
            row_index = 5
        elif key == "notes":
            row_index = 6
        label = ttk.Label(add_window, text=label_text)
        label.grid(row=row_index, column=0, padx=10, pady=6, sticky="w")

        entry = ttk.Entry(add_window, width=36)
        entry.grid(row=row_index, column=1, padx=10, pady=6, sticky="ew")
        entries[key] = entry

    def refresh_task_id() -> None:
        next_task_id = len(task_items) + 1
        task_id_entry.config(state="normal")
        task_id_entry.delete(0, tk.END)
        task_id_entry.insert(0, str(next_task_id))
        task_id_entry.config(state="readonly")

    def clear_fields() -> None:
        for entry in entries.values():
            entry.delete(0, tk.END)
        is_completed_combo.set("No")
        refresh_creation_date()
        refresh_task_id()

    def on_add() -> None:
        values = {field: entries[field].get().strip() for field, _ in fields}
        values["is_completed"] = is_completed_combo.get().strip()
        values["creation_date"] = creation_date_entry.get().strip()
        if any(not value for value in values.values()):
            messagebox.showwarning("Input Error", "Please fill all fields before adding the task.")
            return

        task_id = len(task_items) + 1

        is_completed = values["is_completed"].lower() == "yes"

        task_item = TaskItem(
            task_id=task_id,
            task_name=values["task_name"],
            is_completed=is_completed,
            creation_date=values["creation_date"],
            due_date=values["due_date"],
            priority=values["priority"],
            notes=values["notes"],
        )
        task_items.append(task_item)
        tasks_listbox.insert(tk.END, str(task_item))
        messagebox.showinfo("Success", "Task added successfully.")
        clear_fields()

    add_button = ttk.Button(add_window, text="Add", command=on_add)
    add_button.grid(row=7, column=0, padx=10, pady=12, sticky="ew")

    cancel_button = ttk.Button(add_window, text="Cancel", command=clear_fields)
    cancel_button.grid(row=7, column=1, padx=10, pady=12, sticky="ew")

    add_window.grid_columnconfigure(1, weight=1)
    refresh_task_id()
    refresh_creation_date()
    entries["task_name"].focus_set()


def export_tasks_to_csv(parent: tk.Tk, task_items: list[TaskItem]) -> None:
    if not task_items:
        messagebox.showwarning("Export", "No tasks available to export.")
        return

    save_path = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".csv",
        filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        title="Export Tasks to CSV",
    )
    if not save_path:
        return

    fieldnames = ["task_id", "task_name", "is_completed", "creation_date", "due_date", "priority", "notes"]
    try:
        with open(save_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for task_item in task_items:
                writer.writerow(task_item.to_dict())
    except OSError as exc:
        messagebox.showerror("Export Error", f"Failed to export CSV: {exc}")
        return

    messagebox.showinfo("Export", f"Tasks exported to:\n{save_path}")

# Main application function
def main() -> None:
    # Create main window (fall back to tk.Tk if ttkthemes not available)
    if _USE_THEMED and ThemedTk is not None:
        window = ThemedTk(theme="scidgreen")
    else:
        window = tk.Tk()
    window.title("Notes App")
    window.geometry("800x500")

    # Search input for locating tasks in the list.
    search_entry = ttk.Entry(window, width=40)
    search_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    # Listbox to display tasks
    tasks_listbox_frame = TasksListboxFrame(window, range_count=50)
    tasks_listbox_frame.grid(row=1, column=0, columnspan=1, padx=10, pady=10, sticky="nsew")
    # Listbox to display selected files
    selected_files_listbox_frame = FilesListboxFrame(window)
    selected_files_listbox_frame.grid(row=1, column=1, columnspan=1, padx=10, pady=10, sticky="nsew")

    task_items: list[TaskItem] = []

    menubar = tk.Menu(window)
    application_menu = tk.Menu(menubar, tearoff=0)
    application_menu.add_command(
        label="Add Task",
        command=partial(open_add_task_window, window, tasks_listbox_frame.get_tasks_listbox(), task_items),
    )
    application_menu.add_command(
        label="Export to CSV",
        command=partial(export_tasks_to_csv, window, task_items),
    )
    application_menu.add_separator()
    application_menu.add_command(label="Exit", command=window.destroy)
    menubar.add_cascade(label="Application", menu=application_menu)
    window.config(menu=menubar)
    
    # Pre-defined button commands with partial
    search_task_command = partial(search_task, search_entry, tasks_listbox_frame.get_tasks_listbox())
    upload_task_command = partial(select_file, selected_files_listbox_frame.get_files_listbox())
    delete_task_command = partial(delete_task, tasks_listbox_frame.get_tasks_listbox())
    
    # Bind Enter key to search (improves UX)
    search_entry.bind("<Return>", lambda e: search_task_command())
    # Bind double-click event to show selected item
    tasks_listbox_frame.get_tasks_listbox().bind("<Double-1>", on_select)

    # Search button
    search_button = ttk.Button(window, text="Search", width=20, command=search_task_command)
    search_button.grid(row=0, column=1, padx=10, pady=10)
    # Delete task button
    delete_button = ttk.Button(window, text="Delete Task", width=20, command=delete_task_command)
    delete_button.grid(row=2, column=0, pady=10)
    # Upload files button
    upload_button = ttk.Button(window, text="Upload Files", width=20, command=upload_task_command)
    upload_button.grid(row=2, column=1, pady=10)

    # Keep both columns equal width so each listbox frame uses 50% of the window.
    window.grid_columnconfigure(0, weight=1, uniform="main_columns")
    window.grid_columnconfigure(1, weight=1, uniform="main_columns")
    window.grid_rowconfigure(1, weight=1)
    
    # Run the app
    window.mainloop()

if __name__ == "__main__":
    main()
