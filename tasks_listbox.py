import tkinter as tk
from tkinter import ttk

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

    def _format_task_item(self, item) -> str:
        """Render a task row as 'task_id, task_name, due_date, priority, status'."""
        task_id = ""
        task_name = ""
        due_date = ""
        priority = ""
        status = ""

        if isinstance(item, dict):
            task_id = item.get("task_id", "")
            task_name = item.get("task_name", item.get("name", ""))
            due_date = item.get("due_date", "")
            priority = item.get("priority", "")
            status = item.get("status", "")
        elif isinstance(item, (list, tuple)):
            if len(item) > 0:
                task_id = item[0]
            if len(item) > 1:
                task_name = item[1]
            if len(item) > 2:
                due_date = item[2]
            if len(item) > 3:
                priority = item[3]
            if len(item) > 4:
                status = item[4]
        elif isinstance(item, str):
            # Keep backward compatibility for pre-formatted text rows.
            return item
        else:
            # Support simple objects that expose task attributes.
            task_id = getattr(item, "task_id", "")
            task_name = getattr(item, "task_name", getattr(item, "name", ""))
            due_date = getattr(item, "due_date", "")
            priority = getattr(item, "priority", "")
            status = getattr(item, "status", "")

        return f"{task_id}, {task_name}, {due_date}, {priority}, {status}"

    # Convenience helpers
    def add_item(self, item) -> None:
        self.listbox.insert(tk.END, self._format_task_item(item))

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
            self.listbox.insert(tk.END, self._format_task_item(it))

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
