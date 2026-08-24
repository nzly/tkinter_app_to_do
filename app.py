import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from functools import partial
from datetime import date, datetime
from typing import Callable
from components.events_listbox import EventsListboxFrame
from components.tasks_listbox import TasksListboxFrame
from components.files_listbox import FilesListboxFrame
from objects.data_objects import EventItem, TaskItem, get_task_type_label, normalize_task_type
from db.db import (
    init_db,
    get_config,
    get_tasks,
    get_events,
    get_event_task_ids,
    delete_event_by_id,
    delete_task_by_id,
    update_task,
    add_task_attachment,
    get_task_attachments,
    get_all_task_attachments,
    resolve_db_path,
)
from windows.new_event_window import open_add_event_window
from windows.event_edit_window import open_edit_event_window
from windows.event_summary_window import show_event_summary as show_event_summary_window
from windows.new_task_window import open_add_task_window
from windows.events_tasks_treeview_window import open_events_tasks_treeview_window
from windows.task_summary_window import show_task_summary
from windows.login_window import show_login_window
from util import open_file

# Make ttkthemes optional
try:
    from ttkthemes import ThemedTk
    _USE_THEMED = True
except ImportError:
    ThemedTk = None
    _USE_THEMED = False


# Configure the shared visual styles used by the application.
def configure_ui_components_styles(root: tk.Misc) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background="#f4f7fb")
    style.configure("TLabel", background="#f4f7fb", foreground="#1f2937")

    style.configure(
        "Modern.TButton",
        font=("Bahnschrift", 10),
        padding=(12, 7),
        relief="flat",
        borderwidth=0,
        foreground="#1f2937",
        background="#d6dee8",
    )
    style.map(
        "Modern.TButton",
        background=[("active", "#c8d3df"), ("pressed", "#b9c6d4"), ("disabled", "#e5ebf2")],
        foreground=[("disabled", "#94a3b8")],
    )

    style.configure(
        "Accent.TButton",
        font=("Bahnschrift", 10, "bold"),
        padding=(12, 7),
        relief="flat",
        borderwidth=0,
        foreground="#ffffff",
        background="#0f766e",
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#0d5f5a"), ("pressed", "#0a4f4b"), ("disabled", "#7aa9a5")],
    )

    style.configure(
        "Orange.TButton",
        font=("Bahnschrift", 10, "bold"),
        padding=(12, 7),
        relief="flat",
        borderwidth=0,
        foreground="#ffffff",
        background="#ea580c",
    )
    style.map(
        "Orange.TButton",
        background=[("active", "#c2410c"), ("pressed", "#9a3412"), ("disabled", "#fdba74")],
    )

    style.configure(
        "Danger.TButton",
        font=("Bahnschrift", 10, "bold"),
        padding=(12, 7),
        relief="flat",
        borderwidth=0,
        foreground="#ffffff",
        background="#dc2626",
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#b91c1c"), ("pressed", "#991b1b"), ("disabled", "#f3a5a5")],
    )

    style.configure(
        "Modern.TCombobox",
        fieldbackground="#f8fafc",
        background="#f8fafc",
        foreground="#1f2937",
        bordercolor="#cbd5e1",
        lightcolor="#cbd5e1",
        darkcolor="#cbd5e1",
        arrowcolor="#334155",
        relief="flat",
        borderwidth=1,
        padding=(8, 4),
    )
    style.map(
        "Modern.TCombobox",
        fieldbackground=[("readonly", "#f8fafc"), ("focus", "#ffffff")],
        background=[("readonly", "#f8fafc")],
        foreground=[("readonly", "#1f2937")],
        bordercolor=[("focus", "#0f766e")],
        lightcolor=[("focus", "#0f766e")],
        darkcolor=[("focus", "#0f766e")],
        arrowcolor=[("active", "#0f766e"), ("focus", "#0f766e")],
    )

    style.configure(
        "Modern.TCheckbutton",
        background="#f4f7fb",
        foreground="#1f2937",
        indicatorcolor="#ffffff",
        indicatormargin=(2, 2, 6, 2),
        padding=(2, 2),
    )
    style.map(
        "Modern.TCheckbutton",
        indicatorcolor=[("selected", "#0f766e"), ("active", "#dbe5ef")],
        foreground=[("disabled", "#94a3b8")],
        background=[("active", "#f4f7fb")],
    )

    style.configure(
        "Modern.TLabelframe",
        background="#f4f7fb",
        bordercolor="#d4dde8",
        lightcolor="#d4dde8",
        darkcolor="#d4dde8",
        relief="flat",
        borderwidth=1,
        padding=(8, 6),
    )
    style.configure(
        "Modern.TLabelframe.Label",
        background="#f4f7fb",
        foreground="#334155",
        font=("Bahnschrift", 10, "bold"),
    )

# Function to delete selected task
# Delete the selected tasks and their related attachments.
def delete_task(
    tasks_listbox: tk.Listbox,
    task_items: list[TaskItem],
    tasks_listbox_frame: TasksListboxFrame,
    files_listbox_frame: FilesListboxFrame,
    db_path: str,
) -> None:
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

    tasks_listbox_frame.update_state_message(len(task_items))
    refresh_files(files_listbox_frame, db_path)

# Function to open file dialog and select a file
# Attach a user-selected file to the selected task.
def select_file(
    tasks_listbox: tk.Listbox,
    task_items: list[TaskItem],
    files_listbox_frame: FilesListboxFrame,
    db_path: str,
) -> None:
    selected_indices = tasks_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("Selection Error", "Please select a task before uploading a file.")
        return

    index = int(selected_indices[0])
    if index < 0 or index >= len(task_items):
        messagebox.showwarning("Selection Error", "Selected task is not available.")
        return

    selected_task = task_items[index]

    filepath = filedialog.askopenfilename(
        initialdir=os.path.expanduser("~"),
        title="Select a file",
        filetypes=(("Text files", "*.txt"), ("JPG files", "*.jpg"),
                   ("PNG files", "*.png"), ("All files", "*.*"))
    )
    if filepath:
        add_task_attachment(db_path, selected_task.task_id, filepath)
        refresh_files(files_listbox_frame, db_path)
        files_listbox_frame.highlight_task_attachments(selected_task.task_id)
        messagebox.showinfo("Upload", f"Attached file to task {selected_task.task_id}.")

# Function to handle single-click on task item
# Highlight attachments associated with the selected task.
def on_select_task(
    event,
    task_items: list[TaskItem],
    db_path: str,
    files_listbox_frame: FilesListboxFrame,
) -> None:
    widget = event.widget
    selection_index = widget.curselection()
    if not selection_index:
        return

    index = int(selection_index[0])
    if index < 0 or index >= len(task_items):
        return

    selected_task = task_items[index]
    files_listbox_frame.highlight_task_attachments(selected_task.task_id)


# Highlight tasks linked to the selected event.
def on_select_event(
    event,
    event_items: list[EventItem],
    task_items: list[TaskItem],
    tasks_listbox_frame: TasksListboxFrame,
    db_path: str,
) -> None:
    events_listbox = event.widget
    selection_index = events_listbox.curselection()
    if not selection_index:
        return

    event_index = int(selection_index[0])
    if event_index < 0 or event_index >= len(event_items):
        return

    selected_event = event_items[event_index]
    linked_task_ids = set(get_event_task_ids(db_path, selected_event.id))
    tasks_listbox = tasks_listbox_frame.get_tasks_listbox()

    tasks_listbox.selection_clear(0, tk.END)
    if not linked_task_ids:
        return

    tasks_listbox_frame.checkVar.set(1)
    tasks_listbox_frame.on_select_mod_change()
    for index, task_item in enumerate(task_items):
        if task_item.task_id in linked_task_ids:
            tasks_listbox.selection_set(index)


# Show the context menu for a selected event.
def on_event_right_click(
    event,
    parent: tk.Misc,
    event_items: list[EventItem],
    task_items: list[TaskItem],
    db_path: str,
    on_event_changed: Callable[[], None] | None = None,
) -> None:
    events_listbox = event.widget
    event_index = events_listbox.nearest(event.y)
    if event_index < 0 or event_index >= len(event_items):
        return

    events_listbox.selection_clear(0, tk.END)
    events_listbox.selection_set(event_index)
    events_listbox.activate(event_index)
    selected_event = event_items[event_index]

    # Open the selected event's summary window.
    def show_event_summary() -> None:
        linked_task_ids = set(get_event_task_ids(db_path, selected_event.id))
        show_event_summary_window(
            parent,
            selected_event,
            linked_tasks=task_items,
            linked_task_ids=list(linked_task_ids),
        )

    # Open the selected event in the edit window.
    def edit_event() -> None:
        open_edit_event_window(
            parent,
            db_path,
            selected_event,
            task_items,
            on_event_updated=on_event_changed,
        )

    # Confirm and delete the selected event.
    def delete_event() -> None:
        confirmed = messagebox.askyesno(
            "Delete Event",
            f"Delete event '{selected_event.title}'?",
            parent=parent,
        )
        if not confirmed:
            return
        if not delete_event_by_id(db_path, selected_event.id):
            messagebox.showerror("Delete Event", "Could not delete the event.", parent=parent)
            return
        if on_event_changed is not None:
            on_event_changed()

    context_menu = tk.Menu(parent, tearoff=0)
    context_menu.add_command(label="Event Summary", command=show_event_summary)
    context_menu.add_separator()
    context_menu.add_command(label="Edit Event", command=edit_event)
    context_menu.add_separator()
    context_menu.add_command(label="Delete Event", command=delete_event)
    context_menu.tk_popup(event.x_root, event.y_root)


# Open the summary window for the selected task.
def on_open_task_summary(
    event,
    task_items: list[TaskItem],
    db_path: str,
) -> None:
    widget = event.widget
    selection_index = widget.curselection()
    if not selection_index:
        return

    index = int(selection_index[0])
    if index < 0 or index >= len(task_items):
        return

    selected_task = task_items[index]
    attachments = get_task_attachments(db_path, selected_task.task_id)
    show_task_summary(widget.winfo_toplevel(), selected_task, attachments)


# Keep task selection and attachment highlighting synchronized during navigation.
def sync_task_selection_after_navigation(
    event,
    task_items: list[TaskItem],
    db_path: str,
    files_listbox_frame: FilesListboxFrame,
) -> None:
    widget = event.widget

    # Apply the active listbox row after keyboard navigation settles.
    def apply_selection() -> None:
        active_index = widget.index("active")
        if active_index < 0 or active_index >= len(task_items):
            return

        widget.selection_clear(0, tk.END)
        widget.selection_set(active_index)
        widget.activate(active_index)
        widget.see(active_index)

        selected_task = task_items[active_index]
        attachments = get_task_attachments(db_path, selected_task.task_id)
        files_listbox_frame.highlight_task_attachments(selected_task.task_id)
        update_action_buttons_state(action_buttons, widget)

    widget.after_idle(apply_selection)


# Keep the active file row selected during keyboard navigation.
def sync_file_selection_after_navigation(event, files_listbox_frame: FilesListboxFrame) -> None:
    widget = event.widget

    # Apply the active file row after keyboard navigation settles.
    def apply_selection() -> None:
        active_index = widget.index("active")
        if active_index < 0 or active_index >= widget.size():
            return

        widget.selection_clear(0, tk.END)
        widget.selection_set(active_index)
        widget.activate(active_index)
        widget.see(active_index)

    widget.after_idle(apply_selection)


# Highlight tasks matching the search text.
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


# Resolve the database path with a fallback for unavailable configuration.
def _resolve_db_path() -> str:
    try:
        return resolve_db_path()
    except Exception:
        return "data/app.db"


# Parse an ISO date or datetime value into a date.
def _parse_iso_date(date_value: str | None) -> date | None:
    if not date_value:
        return None

    raw_value = str(date_value).strip()
    if not raw_value:
        return None

    try:
        return date.fromisoformat(raw_value)
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


# Check whether a value is an accepted date string.
def _is_valid_date_string(date_value: str, allow_empty: bool = True) -> bool:
    text = (date_value or "").strip()
    if not text:
        return allow_empty
    return _parse_iso_date(text) is not None


# Return whether a task has been completed.
def _is_task_done(task_item: TaskItem) -> bool:
    return bool(task_item.is_completed)


# Return whether an incomplete task is past its due date.
def _is_task_overdue(task_item: TaskItem) -> bool:
    if _is_task_done(task_item):
        return False

    due_date = _parse_iso_date(task_item.due_date)
    if due_date is None:
        return False
    return due_date < date.today()


# Return whether an incomplete task is due today.
def _is_task_due_today(task_item: TaskItem) -> bool:
    if _is_task_done(task_item):
        return False

    due_date = _parse_iso_date(task_item.due_date)
    return due_date == date.today()


# Build the searchable text for a task.
def _task_search_blob(task_item: TaskItem) -> str:
    return " ".join(
        [
            str(task_item.task_id),
            task_item.task_name or "",
            task_item.notes or "",
            task_item.creation_date or "",
            task_item.due_date or "",
            task_item.task_time or "",
            str(task_item.priority),
            "done" if task_item.is_completed else "pending",
        ]
    ).lower()


# Check whether a task matches the selected status filter.
def _apply_status_filter(task_item: TaskItem, status_filter: str) -> bool:
    value = status_filter.strip().lower()
    if value == "all":
        return True
    if value == "pending":
        return not _is_task_done(task_item)
    if value == "done":
        return _is_task_done(task_item)
    if value == "overdue":
        return _is_task_overdue(task_item)
    if value == "due today":
        return _is_task_due_today(task_item)
    return True


# Return tasks ordered according to the selected sort mode.
def _sort_tasks(task_items: list[TaskItem], sort_mode: str) -> list[TaskItem]:
    mode = (sort_mode or "Due Date (Earliest)").strip()

    if mode == "Due Date (Earliest)":
        return sorted(
            task_items,
            key=lambda item: (
                _parse_iso_date(item.due_date) is None,
                _parse_iso_date(item.due_date) or date.max,
                item.task_id,
            ),
        )
    if mode == "Due Date (Latest)":
        return sorted(
            task_items,
            key=lambda item: (
                _parse_iso_date(item.due_date) is None,
                _parse_iso_date(item.due_date) or date.min,
                item.task_id,
            ),
            reverse=True,
        )
    if mode == "Priority (High to Low)":
        return sorted(task_items, key=lambda item: (int(item.priority), item.task_id))
    if mode == "Priority (Low to High)":
        return sorted(task_items, key=lambda item: (int(item.priority), item.task_id), reverse=True)
    if mode == "Creation Date (Newest)":
        return sorted(
            task_items,
            key=lambda item: (
                _parse_iso_date(item.creation_date) is None,
                _parse_iso_date(item.creation_date) or date.min,
                item.task_id,
            ),
            reverse=True,
        )
    if mode == "Creation Date (Oldest)":
        return sorted(
            task_items,
            key=lambda item: (
                _parse_iso_date(item.creation_date) is None,
                _parse_iso_date(item.creation_date) or date.max,
                item.task_id,
            ),
        )
    if mode == "Status (Pending First)":
        return sorted(task_items, key=lambda item: (_is_task_done(item), item.task_id))
    if mode == "Status (Done First)":
        return sorted(task_items, key=lambda item: (not _is_task_done(item), item.task_id))

    return list(task_items)


# Export the supplied tasks to a user-selected CSV file.
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

    fieldnames = [
        "task_id",
        "task_name",
        "is_completed",
        "creation_date",
        "due_date",
        "task_time",
        "duration",
        "priority",
        "notes",
    ]
    try:
        with open(save_path, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for task_item in task_items:
                writer.writerow({field: task_item.to_dict().get(field, "") for field in fieldnames})
    except (OSError, ValueError) as exc:
        messagebox.showerror("Export Error", f"Failed to export CSV: {exc}")
        return

    messagebox.showinfo("Export", f"Tasks exported to:\n{save_path}")


# Reload tasks in due-date order.
def refresh_tasks(task_items: list[TaskItem], tasks_listbox_frame: TasksListboxFrame, db_path: str) -> None:
    refreshed_items = tasks_listbox_frame.load_tasks_by_order(db_path, order_by_due_date="asc")
    task_items.clear()
    task_items.extend(refreshed_items)


# Reload all attachment rows into the files list.
def refresh_files(files_listbox_frame: FilesListboxFrame, db_path: str) -> None:
    attachments = get_all_task_attachments(db_path)
    files_listbox_frame.set_attachments(attachments)


# Open the file selected in the attachments list.
def on_select_file(files_listbox_frame: FilesListboxFrame) -> None:
    file_path = files_listbox_frame.get_selected_file_path()
    if not file_path:
        return

    opened = open_file(file_path)
    if not opened:
        messagebox.showerror("Open File Error", f"Could not open file:\n{file_path}")


# Enable or disable actions based on task selection count.
def update_action_buttons_state(buttons: dict[str, ttk.Button], tasks_listbox: tk.Listbox) -> None:
    selected_count = len(tasks_listbox.curselection())
    always_available_buttons = {"add", "add_event", "refresh", "view_structure"}

    if selected_count > 1:
        for button_name in buttons:
            if button_name == "delete" or button_name in always_available_buttons:
                buttons[button_name].state(["!disabled"])
            else:
                buttons[button_name].state(["disabled"])
        return

    if selected_count == 1:
        for button_name in buttons:
            buttons[button_name].state(["!disabled"])
        buttons["delete"].state(["!disabled"])
        return

    for button_name in always_available_buttons:
        buttons[button_name].state(["!disabled"])
    for button_name in ("edit", "upload", "summary", "delete"):
        buttons[button_name].state(["disabled"])


# Open the edit dialog for the selected task.
def open_update_task_window(
    parent: tk.Tk,
    tasks_listbox: tk.Listbox,
    task_items: list[TaskItem],
    db_path: str,
    tasks_listbox_frame: TasksListboxFrame,
    on_task_updated: Callable[[], None] | None = None,
) -> None:
    selection = tasks_listbox.curselection()
    if not selection:
        messagebox.showwarning("Selection Error", "Please select a task to update.")
        return

    index = int(selection[0])
    if index < 0 or index >= len(task_items):
        messagebox.showwarning("Selection Error", "Selected task is not available.")
        return

    selected_task = task_items[index]

    update_window = tk.Toplevel(parent)
    update_window.title("Edit Task")
    update_window.geometry("500x510")
    update_window.minsize(500, 510)
    update_window.transient(parent)
    update_window.grab_set()

    container = ttk.Frame(update_window, padding=12)
    container.grid(row=0, column=0, sticky="nsew")
    container.grid_columnconfigure(1, weight=1)

    row_index = 0

    ttk.Label(container, text="Task ID").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    ttk.Label(container, text=f"{selected_task.task_id}").grid(row=row_index, column=1, padx=8, pady=6, sticky="w")
    row_index += 1

    ttk.Label(container, text="Task Name *").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    task_name_entry = ttk.Entry(container, width=36)
    task_name_entry.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")
    task_name_entry.insert(0, selected_task.task_name or "")
    row_index += 1

    ttk.Label(container, text="Creation Date (YYYY-MM-DD)").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    creation_date_entry = ttk.Entry(container, width=36)
    creation_date_entry.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")
    creation_date_entry.insert(0, selected_task.creation_date or "")
    row_index += 1

    ttk.Label(container, text="Due Date (YYYY-MM-DD)").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    due_date_entry = ttk.Entry(container, width=36)
    due_date_entry.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")
    due_date_entry.insert(0, selected_task.due_date or "")
    row_index += 1

    ttk.Label(container, text="Task Time (e.g., 09:30)").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    task_time_entry = ttk.Entry(container, width=36)
    task_time_entry.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")
    task_time_entry.insert(0, selected_task.task_time or "")
    row_index += 1

    ttk.Label(container, text="Duration (mins)").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    duration_entry = ttk.Entry(container, width=36)
    duration_entry.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")
    duration_entry.insert(0, "" if selected_task.duration is None else str(selected_task.duration))
    row_index += 1

    ttk.Label(container, text="Priority").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    priority_combo = ttk.Combobox(container, values=["1", "2", "3"], state="readonly", width=33)
    priority_combo.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")
    priority_combo.set(str(selected_task.priority))
    row_index += 1

    ttk.Label(container, text="Task Type").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    task_type_combo = ttk.Combobox(container, values=["Normal", "Repeat", "Special"], state="readonly", width=33)
    task_type_combo.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")
    task_type_combo.set(get_task_type_label(selected_task.task_type))
    row_index += 1

    ttk.Label(container, text="Status").grid(row=row_index, column=0, padx=8, pady=6, sticky="w")
    status_combo = ttk.Combobox(container, values=["Pending", "Done"], state="readonly", width=33)
    status_combo.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")
    status_combo.set("Done" if selected_task.is_completed else "Pending")
    row_index += 1

    ttk.Label(container, text="Notes").grid(row=row_index, column=0, padx=8, pady=6, sticky="nw")
    notes_text = tk.Text(update_window, height=5, wrap="word", relief=tk.FLAT, borderwidth=0)
    notes_text.insert("1.0", selected_task.notes or "")
    notes_text.grid(in_=container, row=row_index, column=1, padx=8, pady=6, sticky="ew")
    row_index += 1

    # Validate and save the edited task.
    def on_update() -> None:
        task_name = task_name_entry.get().strip()
        creation_date = creation_date_entry.get().strip()
        due_date = due_date_entry.get().strip()
        task_time = task_time_entry.get().strip()
        duration_raw = duration_entry.get().strip()
        notes = notes_text.get("1.0", tk.END).strip()
        status_raw = status_combo.get().strip().lower()

        if not task_name:
            messagebox.showwarning("Input Error", "Task Name is required.")
            return

        if not _is_valid_date_string(creation_date, allow_empty=False):
            messagebox.showwarning("Input Error", "Creation Date must be a valid date.")
            return

        if not _is_valid_date_string(due_date, allow_empty=True):
            messagebox.showwarning("Input Error", "Due Date must be empty or a valid date.")
            return

        try:
            new_priority = int(priority_combo.get().strip())
        except ValueError:
            messagebox.showwarning("Input Error", "Priority must be 1, 2, or 3.")
            return

        if new_priority not in (1, 2, 3):
            messagebox.showwarning("Input Error", "Priority must be 1, 2, or 3.")
            return

        duration_value = None
        if duration_raw:
            try:
                duration_value = int(duration_raw)
            except ValueError:
                messagebox.showwarning("Input Error", "Duration must be a whole number of minutes.")
                return
            if duration_value < 0:
                messagebox.showwarning("Input Error", "Duration cannot be negative.")
                return

        is_completed = status_raw == "done"
        new_task_type = normalize_task_type(task_type_combo.get().strip())

        updated_task = TaskItem(
            task_id=selected_task.task_id,
            task_name=task_name,
            is_completed=is_completed,
            creation_date=creation_date,
            due_date=due_date,
            task_time=task_time or None,
            duration=duration_value,
            priority=new_priority,
            notes=notes,
            task_type=new_task_type,
        )

        updated = update_task(db_path, updated_task)
        if not updated:
            messagebox.showerror("Update Error", "Failed to update task details.")
            return

        if on_task_updated is not None:
            on_task_updated()
        messagebox.showinfo("Success", "Task updated successfully.")
        update_window.destroy()

    button_row = ttk.Frame(container)
    button_row.grid(row=row_index, column=0, columnspan=2, padx=8, pady=(10, 0), sticky="ew")
    button_row.grid_columnconfigure(0, weight=1)
    button_row.grid_columnconfigure(1, weight=1)

    cancel_button = ttk.Button(button_row, text="Cancel", command=update_window.destroy, style="Modern.TButton")
    cancel_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")

    update_button = ttk.Button(button_row, text="Save Changes", command=on_update, style="Accent.TButton")
    update_button.grid(row=0, column=1, padx=(6, 0), sticky="ew")

    update_window.grid_rowconfigure(0, weight=1)
    update_window.grid_columnconfigure(0, weight=1)
    task_name_entry.focus_set()


# Open the task edit dialog from a right-clicked task row.
def on_task_right_click(
    event,
    parent: tk.Tk,
    tasks_listbox_frame: TasksListboxFrame,
    task_items: list[TaskItem],
    db_path: str,
    on_task_updated: Callable[[], None] | None = None,
) -> None:
    tasks_listbox = tasks_listbox_frame.get_tasks_listbox()
    index = tasks_listbox.nearest(event.y)
    if index < 0:
        return

    tasks_listbox.selection_clear(0, tk.END)
    tasks_listbox.selection_set(index)
    tasks_listbox.activate(index)

    open_update_task_window(
        parent,
        tasks_listbox,
        task_items,
        db_path,
        tasks_listbox_frame,
        on_task_updated=on_task_updated,
    )

# Main application function
# Create the main window, wire its controls, and start the event loop.
def main(logged_in_user_id: int) -> None:
    # Create main window (fall back to tk.Tk if ttkthemes not available)
    if _USE_THEMED and ThemedTk is not None:
        window = ThemedTk(theme="scidgreen")
    else:
        window = tk.Tk()
    window.title("EasyNotes - Events, Tasks, and Notes Manager")
    window.geometry("1040x620")
    window.minsize(880, 560)
    configure_ui_components_styles(window)
    window.configure(bg="#f4f7fb")

    db_path = _resolve_db_path()
    init_db(db_path)

    # Track active logged-in user (None = Guest or Not Logged In)
    current_user_id: list[int | None] = [logged_in_user_id]

    header_frame = ttk.Frame(window, padding=(14, 12, 14, 8))
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

    title_label = ttk.Label(header_frame, text="EasyNotes", font=("Bahnschrift", 18, "bold"))
    title_label.pack(anchor="w")

    subtitle_label = ttk.Label(
        header_frame,
        text="Track tasks, attachments, and notes from one clean workspace.",
    )
    subtitle_label.pack(anchor="w", pady=(2, 0))

    toolbar_frame = ttk.Frame(window, padding=(14, 0, 14, 8))
    toolbar_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
    toolbar_frame.grid_columnconfigure(0, weight=1)

    search_group = ttk.Frame(toolbar_frame)
    search_group.grid(row=0, column=0, sticky="ew")
    search_group.grid_columnconfigure(0, weight=1)

    separator = ttk.Separator(toolbar_frame, orient="horizontal")
    separator.grid(
        row=1,
        column=0,
        sticky="ew",
        pady=(8, 8),
    )
    actions_group = ttk.LabelFrame(
        toolbar_frame,
        text="Actions",
        padding=(10, 8),
        style="Modern.TLabelframe"
    )
    actions_group.grid(
        row=2,
        column=0,
        sticky="ew",
        pady=(10, 0)
    )
    for column_index in range(8):
        actions_group.grid_columnconfigure(column_index, weight=1)

    search_label = ttk.Label(search_group, text="Search tasks")
    search_label.grid(row=0, column=0, sticky="w")

    search_row = ttk.Frame(search_group)
    search_row.grid(row=1, column=0, sticky="ew", pady=(2, 0))
    search_row.grid_columnconfigure(0, weight=1)

    search_entry = ttk.Entry(search_row, width=40)
    search_entry.grid(row=0, column=0, sticky="ew")

    search_button = ttk.Button(search_row, text="Search", style="Modern.TButton")
    search_button.grid(row=0, column=1, padx=(8, 0))

    reset_search_button = ttk.Button(search_row, text="Reset", style="Modern.TButton")
    reset_search_button.grid(row=0, column=2, padx=(8, 0))

    structure_tree_button = ttk.Button(
        search_row,
        text="Events & Tasks Structure",
        command=lambda: open_events_tasks_treeview_window(window, db_path),
        style="Orange.TButton",
    )
    structure_tree_button.grid(row=0, column=3, padx=(8, 0))

    controls_row = ttk.Frame(search_group)
    controls_row.grid(row=2, column=0, sticky="ew", pady=(8, 0))

    status_filter_label = ttk.Label(controls_row, text="Filter")
    status_filter_label.pack(side=tk.LEFT)

    status_filter_var = tk.StringVar(value="All")
    status_filter_combo = ttk.Combobox(
        controls_row,
        state="readonly",
        width=14,
        style="Modern.TCombobox",
        textvariable=status_filter_var,
        values=["All", "Pending", "Done", "Overdue", "Due Today"],
    )
    status_filter_combo.pack(side=tk.LEFT, padx=(6, 10))

    sort_label = ttk.Label(controls_row, text="Sort")
    sort_label.pack(side=tk.LEFT)

    sort_var = tk.StringVar(value="Due Date (Earliest)")
    sort_combo = ttk.Combobox(
        controls_row,
        state="readonly",
        width=24,
        style="Modern.TCombobox",
        textvariable=sort_var,
        values=[
            "Due Date (Earliest)",
            "Due Date (Latest)",
            "Priority (High to Low)",
            "Priority (Low to High)",
            "Creation Date (Newest)",
            "Creation Date (Oldest)",
            "Status (Pending First)",
            "Status (Done First)",
        ],
    )
    sort_combo.pack(side=tk.LEFT, padx=(6, 10))

    has_attachments_var = tk.IntVar(value=0)
    attachments_only_check = ttk.Checkbutton(
        controls_row,
        text="Has attachments",
        variable=has_attachments_var,
        style="Modern.TCheckbutton",
    )
    attachments_only_check.pack(side=tk.LEFT)

    events_listbox_frame = EventsListboxFrame(window)
    events_listbox_frame.grid(row=2, column=0, columnspan=1, padx=(14, 8), pady=(0, 10), sticky="nsew")

    tasks_listbox_frame = TasksListboxFrame(window, range_count=0)
    tasks_listbox_frame.grid(row=2, column=1, columnspan=1, padx=8, pady=(0, 10), sticky="nsew")

    selected_files_listbox_frame = FilesListboxFrame(window)
    selected_files_listbox_frame.grid(row=2, column=2, columnspan=1, padx=(8, 14), pady=(0, 10), sticky="nsew")

    all_task_items: list[TaskItem] = get_tasks(db_path)
    task_items: list[TaskItem] = []
    all_event_items: list[EventItem] = get_events(db_path)
    task_attachment_task_ids: set[int] = set()
    refresh_files(selected_files_listbox_frame, db_path)

    # Apply search, filter, attachment, and sort controls to the task list.
    def apply_task_controls() -> None:
        query = search_entry.get().strip().lower()
        selected_filter = status_filter_var.get()
        selected_sort = sort_var.get()
        attachments_only = bool(has_attachments_var.get())

        filtered_items: list[TaskItem] = []
        for task_item in all_task_items:
            if query and query not in _task_search_blob(task_item):
                continue
            if not _apply_status_filter(task_item, selected_filter):
                continue
            if attachments_only and int(task_item.task_id) not in task_attachment_task_ids:
                continue
            filtered_items.append(task_item)

        ordered_items = _sort_tasks(filtered_items, selected_sort)

        task_items.clear()
        task_items.extend(ordered_items)
        tasks_listbox_frame.set_items(task_items)

        if not task_items:
            tasks_listbox_frame.set_empty_state("No tasks match your search/filter settings.")

    # Clear the search and restore the default task controls.
    def reset_search_filters() -> None:
        search_entry.delete(0, tk.END)
        status_filter_var.set("All")
        sort_var.set("Due Date (Earliest)")
        has_attachments_var.set(0)
        apply_task_controls()

    # Restart the application window.
    def reload_application() -> None:
        window.destroy()
        main()

    # Refresh empty-state and item-count labels.
    def refresh_navigation_state() -> None:
        tasks_listbox_frame.update_state_message(len(task_items))
        events_listbox_frame.update_state_message(len(all_event_items))
        selected_files_listbox_frame.update_state_message(
            selected_files_listbox_frame.get_files_listbox().size(),
        )

    # Reload database data and refresh every visible component.
    def refresh_all_views() -> None:
        all_task_items.clear()
        # Pass current_user_id[0] to filter user-specific tasks
        all_task_items.extend(get_tasks(db_path, user_id=current_user_id[0])) 

        all_event_items.clear()
        # Pass current_user_id[0] to filter user-specific events
        all_event_items.extend(get_events(db_path, user_id=current_user_id[0]))

        events_listbox_frame.set_items(all_event_items)
        refresh_files(selected_files_listbox_frame, db_path)

        attachments = get_all_task_attachments(db_path)
        task_attachment_task_ids.clear()
        task_attachment_task_ids.update(int(row["task_id"]) for row in attachments)

        apply_task_controls()
        refresh_navigation_state()
        update_action_buttons_state(action_buttons, tasks_listbox_frame.get_tasks_listbox())

    # Open the Add Task dialog and refresh the task views.
    def open_add_task_dialog() -> None:
        open_add_task_window(window, tasks_listbox_frame, task_items, db_path)
        refresh_all_views()

    # Open the Add Event dialog and refresh the event views.
    def open_add_event_dialog() -> None:
        open_add_event_window(
            window,
            db_path,
            on_event_created=lambda _event: refresh_all_views(),
        )
        refresh_all_views()

    # Delete the currently selected tasks and refresh the views.
    def delete_current_tasks() -> None:
        delete_task(
            tasks_listbox_frame.get_tasks_listbox(),
            task_items,
            tasks_listbox_frame,
            selected_files_listbox_frame,
            db_path,
        )
        refresh_all_views()

    # Upload an attachment for the selected task and refresh the views.
    def upload_current_file() -> None:
        select_file(
            tasks_listbox_frame.get_tasks_listbox(),
            task_items,
            selected_files_listbox_frame,
            db_path,
        )
        refresh_all_views()

    # Open the summary for the currently selected task.
    def open_selected_summary() -> None:
        selected_indices = tasks_listbox_frame.get_tasks_listbox().curselection()
        if not selected_indices:
            messagebox.showwarning("Selection Error", "Please select a task to view its summary.")
            return

        index = int(selected_indices[0])
        if index < 0 or index >= len(task_items):
            messagebox.showwarning("Selection Error", "Selected task is not available.")
            return

        selected_task = task_items[index]
        attachments = get_task_attachments(db_path, selected_task.task_id)
        show_task_summary(window, selected_task, attachments)

    menubar = tk.Menu(window)
    application_menu = tk.Menu(menubar, tearoff=0)
    application_menu.add_command(
        label="View Structure Tree",
        command=lambda: open_events_tasks_treeview_window(window, db_path),
    )
    application_menu.add_command(
        label="Add Event",
        command=open_add_event_dialog,
    )
    application_menu.add_command(
        label="Add Task",
        command=open_add_task_dialog,
    )
    application_menu.add_command(
        label="Export to CSV",
        command=partial(export_tasks_to_csv, window, task_items),
    )
    application_menu.add_separator()
    application_menu.add_command(
        label="Reload Application",
        command=reload_application,
    )
    application_menu.add_separator()
    application_menu.add_command(label="Exit", command=window.destroy)
    menubar.add_cascade(label="Application", menu=application_menu)

    def handle_user_login() -> None:
        # Pass 'window' as the parent so show_login_window opens modally
        user_id = show_login_window(db_path, parent=window)
        if user_id is not None:
            current_user_id[0] = user_id
            messagebox.showinfo("Login Success", f"Welcome! Logged in as User ID: {user_id}")
            refresh_all_views()  # Reload all tasks & events for this user.

    user_menu = tk.Menu(menubar, tearoff=0)
    user_menu.add_command(
        label="Login",
        command=handle_user_login,
    )
    menubar.add_cascade(label="User", menu=user_menu)

    window.config(menu=menubar)
    
    # Pre-defined button commands with partial
    search_task_command = apply_task_controls
    upload_task_command = upload_current_file
    delete_task_command = delete_current_tasks
    open_file_command = partial(on_select_file, selected_files_listbox_frame)
    
    # Bind Enter key to search (improves UX)
    search_entry.bind("<Return>", lambda e: search_task_command())
    search_entry.bind("<KeyRelease>", lambda e: search_task_command())
    # Bind single-click/selection change to highlight related files.
    tasks_listbox_frame.get_tasks_listbox().bind(
        "<<ListboxSelect>>",
        lambda e: (
            on_select_task(e, task_items, db_path, selected_files_listbox_frame),
            update_action_buttons_state(action_buttons, tasks_listbox_frame.get_tasks_listbox()),
        ),
    )
    events_listbox_frame.get_events_listbox().bind(
        "<<ListboxSelect>>",
        lambda e: (
            on_select_event(e, all_event_items, task_items, tasks_listbox_frame, db_path),
            update_action_buttons_state(action_buttons, tasks_listbox_frame.get_tasks_listbox()),
        ),
    )
    events_listbox_frame.get_events_listbox().bind(
        "<Button-3>",
        lambda e: on_event_right_click(
            e,
            window,
            all_event_items,
            task_items,
            db_path,
            on_event_changed=refresh_all_views,
        ),
    )
    # Keep selection/highlight in sync when the user moves with the keyboard.
    tasks_listbox_frame.get_tasks_listbox().bind(
        "<KeyRelease-Up>",
        lambda e: sync_task_selection_after_navigation(e, task_items, db_path, selected_files_listbox_frame),
    )
    tasks_listbox_frame.get_tasks_listbox().bind(
        "<KeyRelease-Down>",
        lambda e: sync_task_selection_after_navigation(e, task_items, db_path, selected_files_listbox_frame),
    )
    # Bind double-click event to show selected task summary.
    tasks_listbox_frame.get_tasks_listbox().bind(
        "<Double-1>",
        lambda e: on_open_task_summary(e, task_items, db_path),
    )
    # Bind right-click event to open task update popup.
    tasks_listbox_frame.get_tasks_listbox().bind(
        "<Button-3>",
        lambda e: on_task_right_click(
            e,
            window,
            tasks_listbox_frame,
            task_items,
            db_path,
            on_task_updated=refresh_all_views,
        ),
    )
    # Bind file list interactions to open selected file paths.
    selected_files_listbox_frame.get_files_listbox().bind("<Double-1>", lambda e: open_file_command())
    selected_files_listbox_frame.get_files_listbox().bind("<Return>", lambda e: open_file_command())
    selected_files_listbox_frame.get_files_listbox().bind(
        "<KeyRelease-Up>",
        lambda e: sync_file_selection_after_navigation(e, selected_files_listbox_frame),
    )
    selected_files_listbox_frame.get_files_listbox().bind(
        "<KeyRelease-Down>",
        lambda e: sync_file_selection_after_navigation(e, selected_files_listbox_frame),
    )

    search_button.config(command=search_task_command)
    reset_search_button.config(command=reset_search_filters)

    status_filter_combo.bind("<<ComboboxSelected>>", lambda e: apply_task_controls())
    sort_combo.bind("<<ComboboxSelected>>", lambda e: apply_task_controls())
    attachments_only_check.config(command=apply_task_controls)

    add_event_button = ttk.Button(
        actions_group,
        text="Add Event",
        command=open_add_event_dialog,
        style="Accent.TButton",
    )
    add_event_button.grid(row=0, column=0, padx=4, sticky="ew")

    add_task_button = ttk.Button(actions_group, text="Add Task", command=open_add_task_dialog, style="Accent.TButton")
    add_task_button.grid(row=0, column=1, padx=4, sticky="ew")

    edit_button = ttk.Button(
        actions_group,
        text="Edit Task",
        style="Modern.TButton",
        command=lambda: open_update_task_window(
            window,
            tasks_listbox_frame.get_tasks_listbox(),
            task_items,
            db_path,
            tasks_listbox_frame,
            on_task_updated=refresh_all_views,
        ),
    )
    edit_button.grid(row=0, column=2, padx=4, sticky="ew")

    upload_button = ttk.Button(actions_group, text="Upload File", command=upload_task_command, style="Accent.TButton")
    upload_button.grid(row=0, column=3, padx=4, sticky="ew")

    summary_button = ttk.Button(actions_group, text="Summary", command=open_selected_summary, style="Modern.TButton")
    summary_button.grid(row=0, column=4, padx=4, sticky="ew")

    delete_button = ttk.Button(actions_group, text="Delete Task", command=delete_task_command, style="Danger.TButton")
    delete_button.grid(row=0, column=5, padx=4, sticky="ew")

    refresh_button = ttk.Button(actions_group, text="Refresh", command=refresh_all_views, style="Modern.TButton")
    refresh_button.grid(row=0, column=6, padx=4, sticky="ew")

    action_buttons = {
        "add": add_task_button,
        "add_event": add_event_button,
        "edit": edit_button,
        "upload": upload_button,
        "summary": summary_button,
        "delete": delete_button,
        "refresh": refresh_button,
        "view_structure": structure_tree_button,
    }

    # Keep both columns equal width so each listbox frame uses 50% of the window.
    window.grid_columnconfigure(0, weight=1, uniform="main_columns")
    window.grid_columnconfigure(1, weight=1, uniform="main_columns")
    window.grid_columnconfigure(2, weight=1, uniform="main_columns")
    window.grid_rowconfigure(2, weight=1)

    refresh_all_views()
    
    # Run the app
    window.mainloop()

if __name__ == "__main__":
    db_path = _resolve_db_path()
    init_db(db_path)
    
    # 1. Launch Login Window FIRST
    user_id = show_login_window(db_path)
    
    # 2. Only launch main app if login succeeded (user_id is not None)
    if user_id is not None:
        main(user_id)
