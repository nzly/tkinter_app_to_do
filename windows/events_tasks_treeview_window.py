import tkinter as tk
import sys
from pathlib import Path
from tkinter import ttk

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.db import get_events, resolve_db_path

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

    for event in get_events(resolve_db_path()):
        tree.insert(
            events,
            tk.END,
            text=event.title or "Untitled event"
        )

    tree.item(events_tasks_root, open=True)
    tree.item(events, open=True)
    root.mainloop()


if __name__ == "__main__":
    main()
