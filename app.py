import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from functools import partial
from datetime import date, datetime
from typing import Callable
from tasks_listbox import TasksListboxFrame
from files_listbox import FilesListboxFrame
from objects.data_objects import TaskItem
from db.db import (
    init_db,
    get_config,
    get_tasks,
    delete_task_by_id,
    update_task_priority_status,
    add_task_attachment,
    get_task_attachments,
    get_all_task_attachments,
)
from new_task_window import open_add_task_window
from task_summary_window import show_task_summary
from util import open_file

# Make ttkthemes optional
try:
    from ttkthemes import ThemedTk
    _USE_THEMED = True
except ImportError:
    ThemedTk = None
    _USE_THEMED = False


def configure_button_styles(root: tk.Misc) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("TFrame", background="#f4f7fb")
    style.configure("TLabel", background="#f4f7fb", foreground="#1f2937")

    style.configure(
        "Modern.TButton",
        font=("Segoe UI", 10),
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
        font=("Segoe UI", 10, "bold"),
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
        "Danger.TButton",
        font=("Segoe UI", 10, "bold"),
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
        font=("Segoe UI", 10, "bold"),
    )

# Function to delete selected task
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


def sync_task_selection_after_navigation(
    event,
    task_items: list[TaskItem],
    db_path: str,
    files_listbox_frame: FilesListboxFrame,
) -> None:
    widget = event.widget

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

    widget.after_idle(apply_selection)


def sync_file_selection_after_navigation(event, files_listbox_frame: FilesListboxFrame) -> None:
    widget = event.widget

    def apply_selection() -> None:
        active_index = widget.index("active")
        if active_index < 0 or active_index >= widget.size():
            return

        widget.selection_clear(0, tk.END)
        widget.selection_set(active_index)
        widget.activate(active_index)
        widget.see(active_index)

    widget.after_idle(apply_selection)


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


def _is_task_done(task_item: TaskItem) -> bool:
    return bool(task_item.is_completed)


def _is_task_overdue(task_item: TaskItem) -> bool:
    if _is_task_done(task_item):
        return False

    due_date = _parse_iso_date(task_item.due_date)
    if due_date is None:
        return False
    return due_date < date.today()


def _is_task_due_today(task_item: TaskItem) -> bool:
    if _is_task_done(task_item):
        return False

    due_date = _parse_iso_date(task_item.due_date)
    return due_date == date.today()


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


def refresh_tasks(task_items: list[TaskItem], tasks_listbox_frame: TasksListboxFrame, db_path: str) -> None:
    refreshed_items = tasks_listbox_frame.load_tasks_by_order(db_path, order_by_due_date="asc")
    task_items.clear()
    task_items.extend(refreshed_items)


def refresh_files(files_listbox_frame: FilesListboxFrame, db_path: str) -> None:
    attachments = get_all_task_attachments(db_path)
    files_listbox_frame.set_attachments(attachments)


def on_select_file(files_listbox_frame: FilesListboxFrame) -> None:
    file_path = files_listbox_frame.get_selected_file_path()
    if not file_path:
        return

    opened = open_file(file_path)
    if not opened:
        messagebox.showerror("Open File Error", f"Could not open file:\n{file_path}")


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
    update_window.title("Update Task")
    update_window.geometry("380x180")
    update_window.transient(parent)
    update_window.grab_set()

    priority_label = ttk.Label(update_window, text="Priority")
    priority_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

    priority_combo = ttk.Combobox(update_window, values=["1", "2", "3"], state="readonly", width=24)
    priority_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
    priority_combo.set(str(selected_task.priority))

    status_label = ttk.Label(update_window, text="Status")
    status_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

    status_combo = ttk.Combobox(update_window, values=["Pending", "Done"], state="readonly", width=24)
    status_combo.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
    status_combo.set("Done" if selected_task.is_completed else "Pending")

    def on_update() -> None:
        try:
            new_priority = int(priority_combo.get().strip())
        except ValueError:
            messagebox.showwarning("Input Error", "Priority must be 1, 2, or 3.")
            return

        if new_priority not in (1, 2, 3):
            messagebox.showwarning("Input Error", "Priority must be 1, 2, or 3.")
            return

        new_status = status_combo.get().strip()
        is_completed = new_status.lower() == "done"

        updated = update_task_priority_status(db_path, selected_task.task_id, new_priority, is_completed)
        if not updated:
            messagebox.showerror("Update Error", "Failed to update task.")
            return

        refresh_tasks(task_items, tasks_listbox_frame, db_path)
        if on_task_updated is not None:
            on_task_updated()
        messagebox.showinfo("Success", "Task updated successfully.")
        update_window.destroy()

    update_button = ttk.Button(update_window, text="Update", command=on_update)
    update_button.grid(row=2, column=0, columnspan=2, padx=10, pady=14, sticky="ew")

    update_window.grid_columnconfigure(1, weight=1)


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
def main() -> None:
    # Create main window (fall back to tk.Tk if ttkthemes not available)
    if _USE_THEMED and ThemedTk is not None:
        window = ThemedTk(theme="scidgreen")
    else:
        window = tk.Tk()
    window.title("Notes App")
    window.geometry("1040x620")
    window.minsize(880, 560)
    configure_button_styles(window)
    window.configure(bg="#f4f7fb")

    db_path = _resolve_db_path()
    init_db(db_path)

    header_frame = ttk.Frame(window, padding=(14, 12, 14, 8))
    header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

    title_label = ttk.Label(header_frame, text="Notes Application", font=("Segoe UI", 18, "bold"))
    title_label.pack(anchor="w")

    subtitle_label = ttk.Label(
        header_frame,
        text="Track tasks, attachments, and notes from one clean workspace.",
    )
    subtitle_label.pack(anchor="w", pady=(2, 0))

    toolbar_frame = ttk.Frame(window, padding=(14, 0, 14, 8))
    toolbar_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
    toolbar_frame.grid_columnconfigure(0, weight=1)

    search_group = ttk.Frame(toolbar_frame)
    search_group.grid(row=0, column=0, sticky="ew")
    search_group.grid_columnconfigure(0, weight=1)

    actions_group = ttk.LabelFrame(toolbar_frame, text="Actions", padding=(10, 8), style="Modern.TLabelframe")
    actions_group.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    for column_index in range(6):
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

    tasks_listbox_frame = TasksListboxFrame(window, range_count=0)
    tasks_listbox_frame.grid(row=2, column=0, columnspan=1, padx=(14, 8), pady=(0, 10), sticky="nsew")

    selected_files_listbox_frame = FilesListboxFrame(window)
    selected_files_listbox_frame.grid(row=2, column=1, columnspan=1, padx=(8, 14), pady=(0, 10), sticky="nsew")

    all_task_items: list[TaskItem] = get_tasks(db_path)
    task_items: list[TaskItem] = []
    task_attachment_task_ids: set[int] = set()
    refresh_files(selected_files_listbox_frame, db_path)

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

    def reset_search_filters() -> None:
        search_entry.delete(0, tk.END)
        status_filter_var.set("All")
        sort_var.set("Due Date (Earliest)")
        has_attachments_var.set(0)
        apply_task_controls()

    def reload_application() -> None:
        window.destroy()
        main()

    def refresh_navigation_state() -> None:
        tasks_listbox_frame.update_state_message(len(task_items))
        selected_files_listbox_frame.update_state_message(
            selected_files_listbox_frame.get_files_listbox().size(),
        )

    def refresh_all_views() -> None:
        all_task_items.clear()
        all_task_items.extend(get_tasks(db_path))

        refresh_files(selected_files_listbox_frame, db_path)

        attachments = get_all_task_attachments(db_path)
        task_attachment_task_ids.clear()
        task_attachment_task_ids.update(int(row["task_id"]) for row in attachments)

        apply_task_controls()
        refresh_navigation_state()

    def open_add_task_dialog() -> None:
        open_add_task_window(window, tasks_listbox_frame, task_items, db_path)
        refresh_all_views()

    def delete_current_tasks() -> None:
        delete_task(
            tasks_listbox_frame.get_tasks_listbox(),
            task_items,
            tasks_listbox_frame,
            selected_files_listbox_frame,
            db_path,
        )
        refresh_all_views()

    def upload_current_file() -> None:
        select_file(
            tasks_listbox_frame.get_tasks_listbox(),
            task_items,
            selected_files_listbox_frame,
            db_path,
        )
        refresh_all_views()

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
    window.config(menu=menubar)
    
    # Pre-defined button commands with partial
    search_task_command = apply_task_controls
    upload_task_command = upload_current_file
    delete_task_command = delete_current_tasks
    open_file_command = partial(on_select_file, selected_files_listbox_frame)
    
    # Bind Enter key to search (improves UX)
    search_entry.bind("<Return>", lambda e: search_task_command())
    # Bind single-click/selection change to highlight related files.
    tasks_listbox_frame.get_tasks_listbox().bind(
        "<<ListboxSelect>>",
        lambda e: on_select_task(e, task_items, db_path, selected_files_listbox_frame),
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

    add_button = ttk.Button(actions_group, text="Add Task", command=open_add_task_dialog, style="Accent.TButton")
    add_button.grid(row=0, column=0, padx=4, sticky="ew")

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
    edit_button.grid(row=0, column=1, padx=4, sticky="ew")

    upload_button = ttk.Button(actions_group, text="Upload File", command=upload_task_command, style="Modern.TButton")
    upload_button.grid(row=0, column=2, padx=4, sticky="ew")

    summary_button = ttk.Button(actions_group, text="Summary", command=open_selected_summary, style="Modern.TButton")
    summary_button.grid(row=0, column=3, padx=4, sticky="ew")

    delete_button = ttk.Button(actions_group, text="Delete Task", command=delete_task_command, style="Danger.TButton")
    delete_button.grid(row=0, column=4, padx=4, sticky="ew")

    refresh_button = ttk.Button(actions_group, text="Refresh", command=refresh_all_views, style="Modern.TButton")
    refresh_button.grid(row=0, column=5, padx=4, sticky="ew")

    # Keep both columns equal width so each listbox frame uses 50% of the window.
    window.grid_columnconfigure(0, weight=1, uniform="main_columns")
    window.grid_columnconfigure(1, weight=1, uniform="main_columns")
    window.grid_rowconfigure(2, weight=1)

    refresh_all_views()
    
    # Run the app
    window.mainloop()

if __name__ == "__main__":
    main()
