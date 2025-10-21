import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass

class TasksListboxFrame(tk.Frame):
    """Frame that contains a Listbox and its Scrollbar with helper methods."""
    def __init__(self, master=None, range_count: int = 0, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="lightblue")

        # Default selection mode
        self.select_mode = tk.SINGLE

        # Checkbox to toggle multiple selection
        self.checkVar = tk.IntVar()
        checkbox_multiple_selection = tk.Checkbutton(
            self,
            text="Multiple Selection",
            variable=self.checkVar,
            onvalue=1,
            offvalue=0,
            height=1,
            width=20,
            command=self.on_select_mod_change
        )
        checkbox_multiple_selection.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)

        # Themed scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox: exportselection=False keeps selection when focus changes
        self.listbox = tk.Listbox(
            self,
            selectmode=self.select_mode,
            exportselection=False,
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        # Populate with sample items if requested
        for i in range(range_count):
            self.listbox.insert(tk.END, f"Item {i+1}")

    def get_tasks_listbox(self) -> tk.Listbox:
        return self.listbox

    # Convenience helpers
    def add_item(self, item: str) -> None:
        self.listbox.insert(tk.END, item)

    def delete_selected(self) -> None:
        indices = self.listbox.curselection()
        if not indices:
            return
        for idx in indices[::-1]:
            try:
                # curselection() can return strings on some platforms
                self.listbox.delete(int(idx))
            except (ValueError, tk.TclError):
                try:
                    self.listbox.delete(idx)
                except Exception:
                    pass

    def get_selected_items(self) -> list:
        return [self.listbox.get(int(i)) for i in self.listbox.curselection()]

    def set_items(self, items: list) -> None:
        self.listbox.delete(0, tk.END)
        for it in items:
            self.listbox.insert(tk.END, it)

    def clear(self) -> None:
        self.listbox.delete(0, tk.END)

    def get_checkVar(self) -> int:
        return self.checkVar.get()

    def on_select_mod_change(self) -> None:
        if self.get_checkVar() == 1:
            self.select_mode = tk.EXTENDED
        else:
            self.select_mode = tk.SINGLE
        self.listbox.config(selectmode=self.select_mode)

@dataclass
class TaskItem:
    task_id: int
    task_name: str
    is_completed: bool
    creation_date: str
    due_date: str
    priority: str
    notes: str

    def get_task_id(self) -> int:
        return self.task_id
    
    def get_task_name(self) -> str:
        return self.task_name

    def is_task_completed(self) -> bool:
        return self.is_completed

    def get_creation_date(self) -> str:
        return self.creation_date
    
    def get_due_date(self) -> str:
        return self.due_date

    def get_priority(self) -> str:
        return self.priority

    def get_notes(self) -> str:
        return self.notes
    
    def get_task_summary(self) -> str:
        status = "Completed" if self.is_completed else "Pending"
        return (f"Task ID: {self.task_id}, Name: {self.task_name}, Status: {status}, "
                f"Created: {self.creation_date}, Due: {self.due_date}, "
                f"Priority: {self.priority}, Notes: {self.notes}")
