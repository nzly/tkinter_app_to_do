import tkinter as tk
from tkcalendar import Calendar

def on_date_select(event):
    # Retrieve selected date string (formatted based on date_pattern)
    selected_date = cal.get_date()
    label_selected.config(text=f"Selected Date: {selected_date}")

root = tk.Tk()
root.title("Clickable Calendar")
root.geometry("350x300")

# Create Calendar Widget
cal = Calendar(
    root,
    selectmode='day',
    year=2026,
    month=9,
    day=7,
    date_pattern='yyyy-mm-dd'
)
cal.pack(pady=20)

# Bind selection event
cal.bind("<<CalendarSelected>>", on_date_select)

# Label to display selected date
label_selected = tk.Label(root, text="Selected Date: None", font=("Helvetica", 11))
label_selected.pack(pady=10)

if __name__ == "__main__":
    root.mainloop()