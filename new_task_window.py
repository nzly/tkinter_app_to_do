import tkinter as tk
from tkinter import messagebox

def open_new_window(selected_item: TaskItem) -> None:
    # Create a new window
    new_win = tk.Toplevel(root)
    new_win.title("Selected Item")
    new_win.geometry("250x100")

    # Display the selected item
    label = tk.Label(new_win, text=f"You selected: {selected_item.get_task_name()}")
    label.pack(pady=20)
