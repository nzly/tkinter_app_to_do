import tkinter as tk
from tkcalendar import Calendar

class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="Enter text...", color="gray", date_pattern=None, **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self.date_pattern = date_pattern
        self.top_cal = None

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)
        if self.date_pattern is not None:
            self.bind("<Double-Button-1>", self.show_calendar)

        self._add_placeholder()

    def _add_placeholder(self, event=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self['fg'] = self.placeholder_color

    def _clear_placeholder(self, event=None):
        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg_color

    def get(self):
        current_text = super().get()
        if current_text == self.placeholder and self['fg'] == self.placeholder_color:
            return ""
        return current_text

    def show_calendar(self, event=None):
        # Prevent multiple calendar pop-ups if one is already open
        if self.top_cal is not None and self.top_cal.winfo_exists():
            return

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
        #self.top_cal.bind("<FocusOut>", self._close_calendar)
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
