import tkinter as tk

def createTasksListbox(root, range_count: int) -> tk.Frame:
    # Create a Frame widget
    listbox_frame = tk.Frame(root, bg="lightblue", padx=10, pady=10)

    # Create the Scrollbar
    scrollbar = tk.Scrollbar(listbox_frame, orient=tk.VERTICAL)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create the Listbox
    tasks_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
    tasks_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Link the Scrollbar to the Listbox
    scrollbar.config(command=tasks_listbox.yview)

    # Add some items to the Listbox
    for i in range(range_count):
        tasks_listbox.insert(tk.END, f"Item {i+1}")

    return listbox_frame