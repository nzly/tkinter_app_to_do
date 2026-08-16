import tkinter as tk
from tkinter import ttk

from objects.data_objects import EventItem


class EventsListboxFrame(tk.Frame):
    """Frame that displays event ID, title, and start time in a scrollable list."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#f4f7fb")

        self.title_label = ttk.Label(self, text="Events", font=("Segoe UI", 11, "bold"))
        self.title_label.pack(side=tk.TOP, anchor="w", padx=6, pady=(6, 0))

        self.helper_label = ttk.Label(
            self,
            text="Event ID, title, and start time.",
        )
        self.helper_label.pack(side=tk.TOP, anchor="w", padx=6, pady=(0, 4))

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

        self.state_label = ttk.Label(self, text="", anchor="w")
        self.state_label.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(4, 6))
        self.set_empty_state()

    def get_events_listbox(self) -> tk.Listbox:
        return self.listbox

    def _format_event_item(self, event_item: EventItem) -> str:
        return f"{event_item.id}, {event_item.title}, {event_item.start_at}"

    def add_item(self, event_item: EventItem) -> None:
        self.listbox.insert(tk.END, self._format_event_item(event_item))
        self.update_state_message(self.listbox.size())

    def set_items(self, event_items: list[EventItem]) -> None:
        self.listbox.delete(0, tk.END)
        for event_item in event_items:
            self.listbox.insert(tk.END, self._format_event_item(event_item))

        if not event_items:
            self.set_empty_state()
            return
        self.update_state_message(len(event_items))

    def clear(self) -> None:
        self.listbox.delete(0, tk.END)
        self.set_empty_state()

    def set_empty_state(self, message: str | None = None) -> None:
        self.state_label.config(text=message or "No events yet. Use Add Event to create your first event.")

    def update_state_message(self, item_count: int) -> None:
        if item_count <= 0:
            self.set_empty_state()
            return
        self.state_label.config(text=f"{item_count} event{'s' if item_count != 1 else ''} loaded")

    def get_selected_items(self) -> list[str]:
        return [self.listbox.get(int(index)) for index in self.listbox.curselection()]
