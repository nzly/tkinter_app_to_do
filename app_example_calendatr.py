import calendar
from datetime import datetime
import tkinter as tk

class CustomCalendarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Custom Interactive Calendar")
        self.root.geometry("320x340")

        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        # Header with navigation
        header_frame = tk.Frame(root)
        header_frame.pack(fill=tk.X, pady=10)

        self.btn_prev = tk.Button(header_frame, text="<", command=self.prev_month, width=3)
        self.btn_prev.pack(side=tk.LEFT, padx=10)

        self.title_label = tk.Label(header_frame, text="", font=("Helvetica", 12, "bold"))
        self.title_label.pack(side=tk.LEFT, expand=True)

        self.btn_next = tk.Button(header_frame, text=">", command=self.next_month, width=3)
        self.btn_next.pack(side=tk.RIGHT, padx=10)

        # Calendar Days Frame
        self.days_frame = tk.Frame(root)
        self.days_frame.pack(padx=10)

        # Selected Date Label
        self.info_label = tk.Label(root, text="Click a date", font=("Helvetica", 10), fg="#0f766e")
        self.info_label.pack(pady=10)

        self.render_calendar()

    def render_calendar(self):
        # Clear existing buttons
        for widget in self.days_frame.winfo_children():
            widget.destroy()

        # Set Header Text
        month_name = calendar.month_name[self.current_month]
        self.title_label.config(text=f"{month_name} {self.current_year}")

        # Day Headers (Mon, Tue, Wed...)
        day_headers = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
        for col, header in enumerate(day_headers):
            lbl = tk.Label(self.days_frame, text=header, font=("Helvetica", 9, "bold"), width=4)
            lbl.grid(row=0, column=col, pady=2)

        # Build Month Days Grid
        month_matrix = calendar.monthcalendar(self.current_year, self.current_month)

        for row_idx, week in enumerate(month_matrix, start=1):
            for col_idx, day in enumerate(week):
                if day != 0:
                    btn = tk.Button(
                        self.days_frame,
                        text=str(day),
                        width=4,
                        relief=tk.FLAT,
                        bg="#f3f4f6",
                        command=lambda d=day: self.on_day_click(d)
                    )
                    btn.grid(row=row_idx, column=col_idx, padx=2, pady=2)

    def on_day_click(self, day):
        selected_str = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
        self.info_label.config(text=f"Selected Date: {selected_str}")

    def prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.render_calendar()

    def next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.render_calendar()

if __name__ == "__main__":
    root = tk.Tk()
    app = CustomCalendarApp(root)
    root.mainloop()