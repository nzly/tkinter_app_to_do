import tkinter as tk
import sys
from pathlib import Path
from tkinter import ttk

# Ensure the parent directory is in sys.path for imports
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import additional necessary modules from the project
from db.db import get_event_task_ids, get_events, get_task_attachments, get_tasks, resolve_db_path
from util import open_file

# Add a task node to the Treeview, including its attachments
def add_task_node(tree: ttk.Treeview, parent: str, task, db_path: str) -> None:
    task_node = tree.insert(
        parent,
        tk.END,
        text=task.task_name or "Untitled task"
    )
    for attachment in get_task_attachments(db_path, task.task_id):
        tree.insert(
            task_node,
            tk.END,
            text=attachment["file_name"] or attachment["file_path"],
            values=(attachment["file_path"],),
        )

# Handle double-click event to open the attachment
def open_attachment(event: tk.Event, tree: ttk.Treeview) -> None:
    item_id = tree.identify_row(event.y)
    if not item_id:
        return

    attachment_path = tree.item(item_id, "values")
    if attachment_path:
        open_file(str(attachment_path[0]))

# Open a new window displaying events and tasks in a Treeview
def open_events_tasks_treeview_window(parent: tk.Misc, db_path: str) -> None:
    root = tk.Toplevel(parent)
    root.title("Events and Tasks Tree View")
    root.geometry("600x550")

    tree = ttk.Treeview(root, columns=("attachment_path",), displaycolumns=())
    tree.bind("<Double-1>", lambda event: open_attachment(event, tree))
    tree.pack(
        fill="both",
        expand=True,
        padx=10,
        pady=10
    )

    events_tasks_root = tree.insert(
        "",
        tk.END,
        text="Events and Tasks"
    )

    events = tree.insert(
        events_tasks_root,
        tk.END,
        text="Events"
    )

    tasks = tree.insert(
        events_tasks_root,
        tk.END,
        text="Tasks"
    )

    db_path = resolve_db_path()
    tasks_by_id = {task.task_id: task for task in get_tasks(db_path)}
    linked_task_ids = set()

    for event in get_events(db_path):
        event_node = tree.insert(
            events,
            tk.END,
            text=event.title or "Untitled event"
        )
        for task_id in get_event_task_ids(db_path, event.id):
            linked_task_ids.add(task_id)
            task = tasks_by_id.get(task_id)
            if task is not None:
                add_task_node(tree, event_node, task, db_path)

    for task in tasks_by_id.values():
        if task.task_id not in linked_task_ids:
            add_task_node(tree, tasks, task, db_path)

    tree.item(events_tasks_root, open=True)
    tree.item(events, open=True)
    tree.item(tasks, open=True)

# Main function to run the application
def main() -> None:
    root = tk.Tk()
    root.title("Tkinter Main Window")
    root.geometry("300x200")
    my_label = tk.Label(root, text="In the real world \nthis is supposed to be \nthe main window \nof the application.")
    my_label.pack(pady=20)
    open_events_tasks_treeview_window(root, resolve_db_path())
    root.mainloop()

# Application entry point
if __name__ == "__main__":
    main()
