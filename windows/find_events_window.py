import sys
import threading
import tkinter as tk
import webbrowser
from calendar import monthrange
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Callable

# Ensure the parent directory is in sys.path for imports
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from components.date_picker import DatePickerEntry
from components.event_finda_calls import run_event_finda_call
from objects.data_objects import EventItem
from objects.event_finda.event_finda_objects import EventFindaEvent
from windows.selected_single_event_from_event_finda import open_selected_event_window

COLUMNS = ("name", "datetime", "location", "url")


# Return the same day next month, clamped to the month's last day (e.g. 31 Jan -> 28 Feb).
def _one_month_after(day: date) -> date:
    year = day.year + day.month // 12
    month = day.month % 12 + 1
    return date(year, month, min(day.day, monthrange(year, month)[1]))


# Replace a date entry's placeholder with a real value.
def _set_date_entry(entry: DatePickerEntry, value: date) -> None:
    entry.delete(0, tk.END)
    entry.insert(0, value.isoformat())
    entry["fg"] = entry.default_fg_color


# Append events returned from the Eventfinda API onto the existing treeview rows.
def _append_to_tree(
    tree: ttk.Treeview,
    events: list[EventFindaEvent],
    events_by_row: dict[str, EventFindaEvent],
) -> None:
    for event in events:
        row_id = tree.insert(
            "",
            tk.END,
            values=(
                event.title,
                event.datetime_summary,
                event.location,
                event.url,
            ),
        )
        events_by_row[row_id] = event


# Populate the treeview with events returned from the Eventfinda API.
def _populate_tree(
    tree: ttk.Treeview,
    events: list[EventFindaEvent],
    events_by_row: dict[str, EventFindaEvent],
) -> None:
    tree.delete(*tree.get_children())
    events_by_row.clear()
    _append_to_tree(tree, events, events_by_row)


# Open a new window that loads and displays events from the Eventfinda API.
def open_find_events_window(
    parent: tk.Misc,
    db_path: str,
    created_by_user: int,
    on_event_added: Callable[[EventItem], None] | None = None,
) -> None:
    window = tk.Toplevel(parent)
    window.title("Find Events")
    window.geometry("860x580")
    window.minsize(800, 460)
    window.transient(parent)

    content = ttk.Frame(window, padding=10)
    content.pack(fill=tk.BOTH, expand=True)
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(2, weight=1)

    filter_bar = ttk.Frame(content)
    filter_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

    # Click a date field to pick a date from the calendar pop-up.
    start_date_entry = DatePickerEntry(
        filter_bar,
        placeholder="Start Date (YYYY-MM-DD)",
        date_pattern="yyyy-mm-dd",
        font=("Helvetica", 11),
        width=24,
    )
    start_date_entry.pack(side=tk.LEFT)
    end_date_entry = DatePickerEntry(
        filter_bar,
        placeholder="End Date (YYYY-MM-DD)",
        date_pattern="yyyy-mm-dd",
        font=("Helvetica", 11),
        width=24,
    )
    end_date_entry.pack(side=tk.LEFT, padx=(8, 0))
    today = date.today()
    _set_date_entry(start_date_entry, today)
    _set_date_entry(end_date_entry, _one_month_after(today))
    for date_entry in (start_date_entry, end_date_entry):
        date_entry.bind("<Button-1>", date_entry.show_calendar, add="+")

    find_button = ttk.Button(filter_bar, text="Find", style="Accent.TButton")
    find_button.pack(side=tk.LEFT, padx=(8, 0))

    status_var = tk.StringVar(value="Loading events from Eventfinda...")
    status_label = ttk.Label(content, textvariable=status_var)
    status_label.grid(row=1, column=0, sticky="w", pady=(0, 8))

    tree_frame = ttk.Frame(content)
    tree_frame.grid(row=2, column=0, sticky="nsew")
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
    button_bar.grid(row=3, column=0, sticky="ew", pady=(8, 0))

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

    events_by_row: dict[str, EventFindaEvent] = {}

    # Open the detail window for the event on the right-clicked row.
    def view_event(row_id: str) -> None:
        event = events_by_row.get(row_id)
        if event is None:
            return
        open_selected_event_window(window, event, db_path, created_by_user, on_event_added)

    # Show the View Event / Open in Browser menu for the right-clicked row.
    def show_row_menu(mouse_event: tk.Event) -> None:
        row_id = tree.identify_row(mouse_event.y)
        if not row_id:
            return
        tree.selection_set(row_id)

        row_menu = tk.Menu(window, tearoff=0)
        row_menu.add_command(label="View Event", command=lambda: view_event(row_id))
        row_menu.add_command(label="Open in Browser", command=open_selected_event_link)
        row_menu.tk_popup(mouse_event.x_root, mouse_event.y_root)

    tree.bind("<Button-3>", show_row_menu)

    open_link_button = ttk.Button(button_bar, text="Open Link", command=open_selected_event_link)
    open_link_button.pack(side=tk.LEFT)

    load_more_button = ttk.Button(button_bar, text="Load More")
    load_more_button.pack(side=tk.LEFT, padx=(8, 0))

    tree.bind("<Double-1>", open_selected_event_link)

    ROWS_PER_PAGE = 20
    pagination_state = {"offset": 0, "total": 0}
    # Dates used by the last Find, so Load More keeps paging the same search.
    active_filters: dict[str, str | None] = {"start_date": None, "end_date": None}

    # Fetch one page of events on a worker thread and hand the results back to the UI thread.
    def fetch_page(offset: int, *, is_initial_load: bool) -> None:
        find_button.config(state=tk.DISABLED)
        load_more_button.config(state=tk.DISABLED)
        status_var.set("Loading events from Eventfinda...")
        start_date = active_filters["start_date"]
        end_date = active_filters["end_date"]

        def worker() -> None:
            try:
                events, total_count = run_event_finda_call(
                    num_rows=ROWS_PER_PAGE,
                    offset=offset,
                    free_only=False,
                    order='popularity',
                    start_date=start_date,
                    end_date=end_date,
                    location_slug="wellington",
                )
            except Exception as error:  # noqa: BLE001 - surface any API/network error to the user
                window.after(0, lambda: on_error(error))
                return
            window.after(0, lambda: on_success(events, total_count))

        def on_success(events: list[EventFindaEvent], total_count: int) -> None:
            if is_initial_load:
                _populate_tree(tree, events, events_by_row)
            else:
                _append_to_tree(tree, events, events_by_row)

            pagination_state["offset"] = offset + len(events)
            pagination_state["total"] = total_count

            loaded_count = len(tree.get_children())
            status_var.set(f"{loaded_count} of {total_count} event{'s' if total_count != 1 else ''} loaded")

            find_button.config(state=tk.NORMAL)
            load_more_button.config(state=tk.NORMAL if loaded_count < total_count else tk.DISABLED)

        def on_error(error: Exception) -> None:
            status_var.set("Failed to load events.")
            find_button.config(state=tk.NORMAL)
            load_more_button.config(state=tk.NORMAL)
            messagebox.showerror("Find Events", f"Could not retrieve events:\n{error}", parent=window)

        threading.Thread(target=worker, daemon=True).start()

    # Validate the date fields, then load the first page of matching events.
    def find_events() -> None:
        start_text = start_date_entry.get().strip()
        end_text = end_date_entry.get().strip()
        try:
            start_value = date.fromisoformat(start_text) if start_text else None
            end_value = date.fromisoformat(end_text) if end_text else None
        except ValueError:
            messagebox.showwarning("Invalid Date", "Dates must use the format YYYY-MM-DD.", parent=window)
            return
        if start_value and end_value and end_value < start_value:
            messagebox.showwarning("Invalid Dates", "End date cannot be before the start date.", parent=window)
            return

        active_filters["start_date"] = start_text or None
        active_filters["end_date"] = end_text or None
        fetch_page(0, is_initial_load=True)

    # Fetch the next page of events and append it to the list.
    def load_more_events() -> None:
        fetch_page(pagination_state["offset"], is_initial_load=False)

    find_button.config(command=find_events)
    load_more_button.config(command=load_more_events)

    # Kick off the initial load once the window is shown.
    window.after(100, find_events)
