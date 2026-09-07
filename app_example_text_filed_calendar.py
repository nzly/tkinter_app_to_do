import tkinter as tk
from tkcalendar import Calendar

class DatePickerEntry(tk.Entry):
    def __init__(self, master=None, date_pattern='yyyy-mm-dd', **kwargs):
        super().__init__(master, **kwargs)
        self.date_pattern = date_pattern
        self.top_cal = None

        # Bind left mouse click and focus events to show the calendar
        #self.bind("<Button-1>", self.show_calendar)
        # Bind double left mouse click to show the calendar
        self.bind("<Double-Button-1>", self.show_calendar)

    def show_calendar(self, event=None):
        # Prevent multiple calendar pop-ups if one is already open
        if self.top_cal is not None and self.top_cal.winfo_exists():
            return

        # 1. Create a borderless pop-up window
        self.top_cal = tk.Toplevel(self)
        self.top_cal.overrideredirect(True)  # Remove window title bar/borders
        self.top_cal.attributes("-topmost", True)  # Keep on top

        # 2. Position the pop-up directly underneath the Entry widget
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        self.top_cal.geometry(f"+{x}+{y}")

        # 3. Create the Calendar widget inside the pop-up
        self.cal = Calendar(
            self.top_cal,
            selectmode='day',
            date_pattern=self.date_pattern
        )
        self.cal.pack(padx=2, pady=2)

        # Bind date click selection event
        self.cal.bind("<<CalendarSelected>>", self.on_date_selected)

        # Close calendar if user clicks outside the calendar window
        self.top_cal.bind("<FocusOut>", self.close_calendar)
        self.top_cal.focus_set()

    def on_date_selected(self, event=None):
        # Retrieve selected date from calendar
        selected_date = self.cal.get_date()

        # Update the entry field content
        self.delete(0, tk.END)
        self.insert(0, selected_date)

        # Close the calendar pop-up
        self.close_calendar()

    def close_calendar(self, event=None):
        if self.top_cal is not None:
            self.top_cal.destroy()
            self.top_cal = None


# --- Demonstration Window ---
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Clickable Date Field Example")
    root.geometry("400x200")

    label = tk.Label(root, text="Select Date:", font=("Helvetica", 11))
    label.pack(pady=(30, 5))

    # Custom DatePicker Entry widget
    date_entry = DatePickerEntry(root, date_pattern='yyyy-mm-dd', font=("Helvetica", 11), width=20)
    date_entry.pack(pady=5)

    # Start the Tkinter main loop
    root.mainloop()