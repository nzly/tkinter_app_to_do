import tkinter as tk
from tkcalendar import Calendar
from place_holder import PlaceholderEntry

class DatePickerEntry(PlaceholderEntry):
    def __init__(self, master=None, placeholder="YYYY-MM-DD", date_pattern='yyyy-mm-dd', **kwargs):
        # Pass placeholder arguments up to PlaceholderEntry
        super().__init__(master, placeholder=placeholder, **kwargs)
        
        self.date_pattern = date_pattern
        self.top_cal = None

        # Bind double-click to trigger calendar pop-up
        self.bind("<Double-Button-1>", self.show_calendar)

    def show_calendar(self, event=None):
        if self.top_cal is not None and self.top_cal.winfo_exists():
            return

        # Clear placeholder text before selecting a date
        self._clear_placeholder()

        self.top_cal = tk.Toplevel(self)
        self.top_cal.overrideredirect(True)
        self.top_cal.attributes("-topmost", True)

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        self.top_cal.geometry(f"+{x}+{y}")

        self.cal = Calendar(
            self.top_cal,
            selectmode='day',
            date_pattern=self.date_pattern
        )
        self.cal.pack(padx=2, pady=2)

        self.cal.bind("<<CalendarSelected>>", self._on_date_selected)
        self.top_cal.bind("<FocusOut>", self._close_calendar)
        self.top_cal.focus_set()

    def _on_date_selected(self, event=None):
        selected_date = self.cal.get_date()
        self.delete(0, tk.END)
        self['fg'] = self.default_fg_color
        self.insert(0, selected_date)
        self._close_calendar()

    def _close_calendar(self, event=None):
        if self.top_cal is not None:
            self.top_cal.destroy()
            self.top_cal = None
        # Restore placeholder if entry is empty
        if not self.get():
            self._show_placeholder()