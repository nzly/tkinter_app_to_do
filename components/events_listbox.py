import tkinter as tk
from datetime import datetime
from tkinter import ttk

from objects.data_objects import EventItem
from renders.renders import ListRender

# Format an event start timestamp for display in the list.
def _format_start_at_for_display(start_at: str) -> str:
    try:
        parsed_start_at = datetime.fromisoformat(start_at)
    except ValueError:
        return start_at
    return parsed_start_at.strftime("%d %b %Y, %I:%M %p")


class EventsListboxFrame(tk.Frame):
    """Frame that displays event ID, title, and start time in a scrollable list."""

    # Build the events list frame and its scrollbar.
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#f4f7fb")

        self.title_label = ttk.Label(self, text="Events", font=("Bahnschrift", 11, "bold"))
        self.title_label.pack(side=tk.TOP, anchor="w", padx=6, pady=(6, 0))

        self.helper_label = ttk.Label(
            self,
            text="Event ID, title, and start time.",
        )
        self.helper_label.pack(side=tk.TOP, anchor="w", padx=6, pady=(0, 4))

        # Pack bottom state_label FIRST to lock it to the very bottom
        self.state_label = ttk.Label(self, text="", anchor="w")
        self.state_label.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(4, 6))

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            self,
            selectmode=tk.SINGLE,
            exportselection=False,
            yscrollcommand=scrollbar.set,
            bg="#ffffff",
            fg="#1f2937",
            selectbackground="#0f766e",
            selectforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground="#d4dde8",
            highlightcolor="#0f766e",
            activestyle="none",
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.list_render = ListRender(listbox=self.listbox)
        # Set the initial empty state message.
        self.set_empty_state()

    # Return the underlying events listbox widget.
    def get_events_listbox(self) -> tk.Listbox:
        return self.listbox

    # Format one EventItem as a list row.
    def _format_event_item(self, event_item: EventItem) -> str:
        start_at = _format_start_at_for_display(event_item.start_at)
        is_all_day = "(All-day)" if event_item.is_all_day else "(Time range)"
        return f"[{start_at}] {event_item.title} {is_all_day}"

    # Append one event to the list.
    def add_item(self, event_item: EventItem) -> None:
        self.listbox.insert(tk.END, self._format_event_item(event_item))
        self.update_state_message(self.listbox.size())

    # Set the list of events to display in the listbox.
    # Assign background colors based on whether the event is passed, today, or future.
    def set_items(self, event_items: list[EventItem]) -> None:
        self.listbox.delete(0, tk.END)
        listArray_passed = []
        listArray_today = []
        listArray_future = []
        
        if not event_items:
            self.set_empty_state()
            return

        for index, item in enumerate(event_items):
            self.listbox.insert(tk.END, self._format_event_item(item))
            if item.is_passed_event():
                listArray_passed.append(index)
            elif item.is_today_event():
                listArray_today.append(index)
            elif item.is_future_event():
                listArray_future.append(index)

        if listArray_passed:
            self.list_render.assign_bg(self.listbox, listArray_passed, "lightgrey")
        if listArray_today:
            self.list_render.assign_bg(self.listbox, listArray_today, "orange")
        if listArray_future:
            self.list_render.assign_bg(self.listbox, listArray_future, "lightgreen")

        self.update_state_message(len(event_items))

    # Remove all events from the list.
    def clear(self) -> None:
        self.listbox.delete(0, tk.END)
        self.set_empty_state()

    # Display the empty-state message for the event list.
    def set_empty_state(self, message: str | None = None) -> None:
        self.state_label.config(text=message or "No events yet. Use Add Event to create your first event.")

    # Update the event count shown below the list.
    def update_state_message(self, item_count: int) -> None:
        if item_count <= 0:
            self.set_empty_state()
            return
        self.state_label.config(text=f"{item_count} event{'s' if item_count != 1 else ''} loaded")

    # Return the currently selected event rows.
    def get_selected_items(self) -> list[str]:
        return [self.listbox.get(int(index)) for index in self.listbox.curselection()]
