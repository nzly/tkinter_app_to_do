import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from functools import partial
from tasks_listbox import TasksListboxFrame
from files_listbox import FilesListboxFrame
from objects.data_objects import TaskItem
from db.db import init_db, get_config, get_tasks, delete_task_by_id
from new_task_window import open_add_task_window

# Make ttkthemes optional
try:
    from ttkthemes import ThemedTk
    _USE_THEMED = True
except ImportError:
    ThemedTk = None
    _USE_THEMED = False

# Function to delete selected task
def delete_task(tasks_listbox: tk.Listbox, task_items: list[TaskItem], db_path: str) -> None:
    selected_indices = tasks_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Error", "Please select a task to delete.")
        return

    indices = sorted([int(i) for i in selected_indices], reverse=True)
    failed_ids: list[int] = []

    # Convert indices to ints and delete in reverse to avoid reindexing issues
    for index in indices:
        if index < 0 or index >= len(task_items):
            continue

        task_id = task_items[index].task_id
        deleted = delete_task_by_id(db_path, task_id)
        if not deleted:
            failed_ids.append(task_id)
            continue

        task_items.pop(index)
        tasks_listbox.delete(index)

    if failed_ids:
        messagebox.showerror("Delete Error", f"Could not delete task IDs from DB: {failed_ids}")

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

# Function to handle single-click on task item
def on_select_task(event, task_items: list[TaskItem]) -> None:
    widget = event.widget
    selection_index = widget.curselection()
    if not selection_index:
        return

    index = int(selection_index[0])
    if index < 0 or index >= len(task_items):
        return

    selected_task = task_items[index]
    messagebox.showinfo("Task Summary", selected_task.get_task_summary())


def search_task(search_entry: tk.Entry, tasks_listbox: tk.Listbox) -> None:
    query = search_entry.get().strip().lower()
    if not query:
        messagebox.showwarning("Search Error", "Please enter text to search.")
        return

    tasks = tasks_listbox.get(0, tk.END)
    matched_indices: list[int] = []

    for index, task in enumerate(tasks):
        if query in str(task).lower():
            matched_indices.append(index)

    tasks_listbox.selection_clear(0, tk.END)

    if not matched_indices:
        messagebox.showinfo("Search", f"No task found matching: {search_entry.get().strip()}")
        return

    # Ensure all matches can be highlighted at once.
    tasks_listbox.config(selectmode=tk.EXTENDED)
    for index in matched_indices:
        tasks_listbox.selection_set(index)

    tasks_listbox.activate(matched_indices[0])
    tasks_listbox.see(matched_indices[0])


def _resolve_db_path() -> str:
    try:
        app_config = get_config()
        return app_config.get("database_path", "data/app.db")
    except Exception:
        return "data/app.db"


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

    db_path = _resolve_db_path()
    init_db(db_path)

    # Search input for locating tasks in the list.
    search_entry = ttk.Entry(window, width=40)
    search_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

    # Listbox to display tasks
    tasks_listbox_frame = TasksListboxFrame(window, range_count=0)
    tasks_listbox_frame.grid(row=1, column=0, columnspan=1, padx=10, pady=10, sticky="nsew")
    # Listbox to display selected files
    selected_files_listbox_frame = FilesListboxFrame(window)
    selected_files_listbox_frame.grid(row=1, column=1, columnspan=1, padx=10, pady=10, sticky="nsew")

    task_items: list[TaskItem] = get_tasks(db_path)
    for task_item in task_items:
        tasks_listbox_frame.get_tasks_listbox().insert(tk.END, str(task_item))

    menubar = tk.Menu(window)
    application_menu = tk.Menu(menubar, tearoff=0)
    application_menu.add_command(
        label="Add Task",
        command=partial(open_add_task_window, window, tasks_listbox_frame.get_tasks_listbox(), task_items, db_path),
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
    delete_task_command = partial(delete_task, tasks_listbox_frame.get_tasks_listbox(), task_items, db_path)
    
    # Bind Enter key to search (improves UX)
    search_entry.bind("<Return>", lambda e: search_task_command())
    # Bind single-click event to show selected task summary.
    tasks_listbox_frame.get_tasks_listbox().bind(
        "<ButtonRelease-1>",
        lambda e: on_select_task(e, task_items),
    )

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
