import tkinter as tk
from tkinter import ttk


class DueTaskCard(ttk.Frame):
    def __init__(
        self,
        parent: tk.Misc,
        title: str = "Header Text",
        detail: str = "This is the smaller subtext directly underneath.",
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)

        self.top_label = ttk.Label(
            self,
            text=title,
            font=("Bahnschrift", 11, "bold"),
            anchor="w",
        )
        self.top_label.pack(fill=tk.X, anchor="w")

        self.bottom_label = ttk.Label(
            self,
            text=detail,
            font=("Bahnschrift", 8, "normal"),
            anchor="w",
        )
        self.bottom_label.pack(fill=tk.X, anchor="w", pady=(0, 0))

    def set_text(self, title: str, detail: str) -> None:
        self.top_label.config(text=title)
        self.bottom_label.config(text=detail)

    def create_due_task_card(self, title: str, detail: str) -> None:
        self.set_text(title, detail)

# Main block to demonstrate the DueTaskCard widget
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Due Task Card Example")
    root.geometry("300x100")

    due_task_card = DueTaskCard(
        root,
        title="Upcoming Task",
        detail="This task is due soon. Please complete it.",
        padding=11,
    )
    due_task_card.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    root.mainloop()
