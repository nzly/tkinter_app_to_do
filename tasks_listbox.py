import tkinter as tk
class TasksListboxFrame(tk.Frame):
    def __init__(self, master=None, range_count: int = 0, **kwargs):
        super().__init__(master, **kwargs)
        # removed invalid padx/pady from configure (padding should be applied when gridding/packing)
        self.configure(bg="lightblue")

        # Create the Scrollbar
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create the Listbox
        self.listbox = tk.Listbox(self, yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Link the Scrollbar to the Listbox
        scrollbar.config(command=self.listbox.yview)

        # Add some items to the Listbox
        for i in range(range_count):
            self.listbox.insert(tk.END, f"Item {i+1}")
    
    def get_tasks_listbox(self) -> tk.Listbox:
        return self.listbox
        