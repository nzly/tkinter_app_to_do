import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk

# Ensure the parent directory is in sys.path for imports
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.event_finda_calls import run_event_finda_call

COLUMNS = ("name", "datetime", "location", "url")


# Pull the venue/location name out of an Eventfinda event dict.
def _extract_location(event: dict) -> str:
    location = event.get("location") or {}
    return location.get("name", "") if isinstance(location, dict) else ""


# Populate the treeview with events returned from the Eventfinda API.
def _populate_tree(tree: ttk.Treeview, events: list[dict]) -> None:
    tree.delete(*tree.get_children())
    for event in events:
        tree.insert(
            "",
            tk.END,
            values=(
                event.get("name", ""),
                event.get("datetime_summary", ""),
                _extract_location(event),
                event.get("url", ""),
            ),
        )


# Open a new window that loads and displays events from the Eventfinda API.
def open_find_events_window(parent: tk.Misc) -> None:
    window = tk.Toplevel(parent)
    window.title("Find Events")
    window.geometry("860x580")
    window.minsize(800, 460)
    window.transient(parent)

    content = ttk.Frame(window, padding=10)
    content.pack(fill=tk.BOTH, expand=True)
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(1, weight=1)

    status_var = tk.StringVar(value="Loading events from Eventfinda...")
    status_label = ttk.Label(content, textvariable=status_var)
    status_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

    tree_frame = ttk.Frame(content)
    tree_frame.grid(row=1, column=0, sticky="nsew")
    tree_frame.grid_columnconfigure(0, weight=1)
    tree_frame.grid_rowconfigure(0, weight=1)

    tree = ttk.Treeview(tree_frame, columns=COLUMNS, show="headings", selectmode="browse")
    tree.heading("name", text="Event")
    tree.heading("datetime", text="Date / Time")
    tree.heading("location", text="Location")
    tree.heading("url", text="Link")
    tree.column("name", width=260, anchor="w")
    tree.column("datetime", width=160, anchor="w")
    tree.column("location", width=160, anchor="w")
    tree.column("url", width=160, anchor="w")
    tree.grid(row=0, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    tree.configure(yscrollcommand=scrollbar.set)

    button_bar = ttk.Frame(content)
    button_bar.grid(row=2, column=0, sticky="ew", pady=(8, 0))

    # Open the selected event's Eventfinda page in the default browser.
    def open_selected_event_link(_event: tk.Event | None = None) -> None:
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Select an event first.", parent=window)
            return
        event_url = tree.set(selected[0], "url")
        if event_url:
            webbrowser.open(event_url)
        else:
            messagebox.showinfo("No Link", "This event has no link available.", parent=window)

    open_link_button = ttk.Button(button_bar, text="Open Link", command=open_selected_event_link)
    open_link_button.pack(side=tk.LEFT)

    refresh_button = ttk.Button(button_bar, text="Refresh")
    refresh_button.pack(side=tk.LEFT, padx=(8, 0))

    tree.bind("<Double-1>", open_selected_event_link)

    # Fetch events on a worker thread and hand the results back to the UI thread.
    def load_events() -> None:
        refresh_button.config(state=tk.DISABLED)
        status_var.set("Loading events from Eventfinda...")

        def worker() -> None:
            try:
                events = run_event_finda_call(num_rows=20, free_only=False, order='popularity')
            except Exception as error:  # noqa: BLE001 - surface any API/network error to the user
                window.after(0, lambda: on_error(error))
                return
            window.after(0, lambda: on_success(events))

        def on_success(events: list[dict]) -> None:
            _populate_tree(tree, events)
            status_var.set(f"{len(events)} event{'s' if len(events) != 1 else ''} loaded")
            refresh_button.config(state=tk.NORMAL)

        def on_error(error: Exception) -> None:
            status_var.set("Failed to load events.")
            refresh_button.config(state=tk.NORMAL)
            messagebox.showerror("Find Events", f"Could not retrieve events:\n{error}", parent=window)

        threading.Thread(target=worker, daemon=True).start()

    refresh_button.config(command=load_events)

    # Kick off the initial load once the window is shown.
    window.after(100, load_events)
