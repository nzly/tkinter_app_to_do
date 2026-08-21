import tkinter as tk
import sys
from pathlib import Path
from tkinter import ttk

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.db import get_event_task_ids, get_events, get_task_attachments, get_tasks, resolve_db_path


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
            text=attachment["file_name"] or attachment["file_path"]
        )

def main() -> None:
    root = tk.Tk()
    root.title("Events and Tasks Tree View")
    root.geometry("600x550")

    tree = ttk.Treeview(root)
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
    root.mainloop()


if __name__ == "__main__":
    main()
