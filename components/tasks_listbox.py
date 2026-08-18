import tkinter as tk
from tkinter import ttk
from datetime import date, datetime

from renders.renders import ListRender
from db.db import get_tasks_by_order

class TasksListboxFrame(tk.Frame):
    """Frame that contains a Listbox and its Scrollbar with helper methods."""
    # Build the task list frame and its controls.
    def __init__(self, master=None, range_count: int = 0, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#f4f7fb")

        self.title_label = ttk.Label(self, text="Tasks", font=("Bahnschrift", 11, "bold"))
        self.title_label.pack(side=tk.TOP, anchor="w", padx=6, pady=(6, 0))

        self.helper_label = ttk.Label(
            self,
            text="Double-click to open a summary. Right-click to edit.",
        )
        self.helper_label.pack(side=tk.TOP, anchor="w", padx=6, pady=(0, 4))

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
            anchor="w",
            height=1,
            width=20,
            command=self.on_select_mod_change,
            bg="#f4f7fb",
            activebackground="#f4f7fb",
            fg="#1f2937",
            activeforeground="#1f2937",
            selectcolor="#ffffff",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
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
            yscrollcommand=scrollbar.set,
            bg="#ffffff",
            fg="#1f2937",
            selectbackground="#0f766e",
            selectforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground="#d4dde8",
            highlightcolor="#0f766e",
            activestyle="none",
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        self.list_render = ListRender(listbox=self.listbox)

        self.state_label = ttk.Label(self, text="", anchor="w")
        self.state_label.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(4, 6))

        # Populate with sample items if requested
        for i in range(range_count):
            self.listbox.insert(tk.END, f"Item {i+1}")

        if range_count > 0:
            self.update_state_message(range_count)
        else:
            self.set_empty_state()

    # Return the underlying tasks listbox widget.
    def get_tasks_listbox(self) -> tk.Listbox:
        return self.listbox

    # Parse a task due-date value into a date.
    def _parse_due_date(self, due_date_value) -> date | None:
        if not due_date_value:
            return None

        value = str(due_date_value).strip()
        if not value:
            return None

        try:
            return date.fromisoformat(value)
        except ValueError:
            pass

        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            return None

    # Format a task-like object as a list row.
    def _format_task_item(self, item, index=None) -> str:
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
            if status == "" and "is_completed" in item:
                status = "Done" if bool(item.get("is_completed")) else "Pending"
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
            # For TaskItem-like objects, use their __str__ representation.
            # Important: str() is used for TaskItem instances only,
            # which have a custom __str__ method.
            return str(item)

        return f"{task_id}, {task_name}, {due_date}, {priority}, {status}"

    # Return whether a task is due today.
    def _is_due_today(self, item) -> bool:
        if isinstance(item, dict):
            due_date = item.get("due_date", "")
        elif isinstance(item, (list, tuple)):
            due_date = item[2] if len(item) > 2 else ""
        elif isinstance(item, str):
            return False
        else:
            due_date = getattr(item, "due_date", "")

        return self._parse_due_date(due_date) == date.today()

    # Return whether a task due date has passed.
    def _is_due_passed(self, item) -> bool:
        if isinstance(item, dict):
            due_date = item.get("due_date", "")
        elif isinstance(item, (list, tuple)):
            due_date = item[2] if len(item) > 2 else ""
        elif isinstance(item, str):
            return False
        else:
            due_date = getattr(item, "due_date", "")

        parsed_due_date = self._parse_due_date(due_date)
        if parsed_due_date is None:
            return False
        return parsed_due_date < date.today()

    # Return whether a task is due in the future.
    def _is_due_future(self, item) -> bool:
        if isinstance(item, dict):
            due_date = item.get("due_date", "")
        elif isinstance(item, (list, tuple)):
            due_date = item[2] if len(item) > 2 else ""
        elif isinstance(item, str):
            return False
        else:
            due_date = getattr(item, "due_date", "")

        parsed_due_date = self._parse_due_date(due_date)
        if parsed_due_date is None:
            return False
        return parsed_due_date > date.today()

    # Convenience helpers
    # Append one task and apply its due-date color.
    def add_item(self, item) -> None:
        index = self.listbox.size()
        self.listbox.insert(tk.END, self._format_task_item(item, index=index))
        if self._is_due_passed(item):
            self.list_render.assign_bg(self.listbox, [index], "lightgrey")
        elif self._is_due_today(item):
            self.list_render.assign_bg(self.listbox, [index], "orange")
        elif self._is_due_future(item):
            self.list_render.assign_bg(self.listbox, [index], "lightgreen")
        self.update_state_message(self.listbox.size())

    # Delete selected task rows.
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

    # Return all selected task rows.
    def get_selected_items(self) -> list:
        return [self.listbox.get(int(i)) for i in self.listbox.curselection()]

    # Replace the list contents and apply due-date colors.
    def set_items(self, items: list) -> None:
        self.listbox.delete(0, tk.END)
        listArray_passed = []
        listArray_today = []
        listArray_future = []
        if not items:
            self.set_empty_state()
            return

        for index, item in enumerate(items):
            self.listbox.insert(tk.END, self._format_task_item(item, index=index))
            if self._is_due_passed(item):
                listArray_passed.append(index)
            elif self._is_due_today(item):
                listArray_today.append(index)
            elif self._is_due_future(item):
                listArray_future.append(index)

        if listArray_passed:
            self.list_render.assign_bg(self.listbox, listArray_passed, "lightgrey")
        if listArray_today:
            self.list_render.assign_bg(self.listbox, listArray_today, "orange")
        if listArray_future:
            self.list_render.assign_bg(self.listbox, listArray_future, "lightgreen")
        self.update_state_message(len(items))

    # Load tasks from the database in due-date order.
    def load_tasks_by_order(self, db_path: str, order_by_due_date: str = "asc") -> list:
        task_items = get_tasks_by_order(db_path, order_by_due_date=order_by_due_date)
        self.set_items(task_items)
        return task_items

    # Remove all task rows from the list.
    def clear(self) -> None:
        self.listbox.delete(0, tk.END)
        self.set_empty_state()

    # Display the empty-state message for the task list.
    def set_empty_state(self, message: str | None = None) -> None:
        self.state_label.config(
            text=message or "No tasks yet. Use Add Task to create your first item.",
        )

    # Update the task count shown below the list.
    def update_state_message(self, item_count: int) -> None:
        if item_count <= 0:
            self.set_empty_state()
            return

        self.state_label.config(text=f"{item_count} task{'s' if item_count != 1 else ''} loaded")

    # Return the multiple-selection checkbox value.
    def get_checkVar(self) -> int:
        return self.checkVar.get()

    # Apply the selected single or multiple selection mode.
    def on_select_mod_change(self) -> None:
        if self.get_checkVar() == 1:
            self.select_mode = tk.EXTENDED
        else:
            self.select_mode = tk.SINGLE
        self.listbox.config(selectmode=self.select_mode)
