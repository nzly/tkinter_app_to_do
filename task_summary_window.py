import tkinter as tk
from tkinter import ttk
from typing import Optional

from objects.data_objects import TaskItem, get_task_type_label


class TaskSummaryWindow(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        task: TaskItem,
        attachments: Optional[list[dict]] = None,
    ) -> None:
        super().__init__(parent)
        self.title("Task Summary")
        self.geometry("700x600")
        self.minsize(700, 600)
        self.transient(parent)
        self.grab_set()

        self.configure(bg="#f4f6f8")

        footer = ttk.Frame(self, padding=(12, 0, 12, 10))
        footer.pack(side=tk.BOTTOM, fill=tk.X)

        close_button = ttk.Button(footer, text="Close", command=self.destroy)
        close_button.pack(side=tk.RIGHT)

        outer = ttk.Frame(self, padding=(12, 10, 12, 8))
        outer.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(outer)
        header.pack(fill=tk.X)

        title_label = ttk.Label(header, text=task.task_name, font=("Segoe UI", 14, "bold"))
        title_label.pack(anchor="w")

        subtitle = f"Task #{task.task_id}  |  { 'Completed' if task.is_completed else 'Pending' }"
        subtitle_label = ttk.Label(header, text=subtitle, font=("Segoe UI", 9))
        subtitle_label.pack(anchor="w", pady=(2, 0))

        ttk.Separator(outer).pack(fill=tk.X, pady=10)

        details_card = ttk.LabelFrame(outer, text="Task Details", padding=8)
        details_card.pack(fill=tk.X)

        details = [
            ("Task ID", task.task_id),
            ("Name", task.task_name),
            ("Status", "Completed" if task.is_completed else "Pending"),
            ("Type", get_task_type_label(task.task_type)),
            ("Created", task.creation_date or "-"),
            ("Due Date", task.due_date or "-"),
            ("Task Time", task.task_time or "-"),
            ("Duration (mins)", task.duration if task.duration is not None else "-"),
            ("Priority", task.priority),
        ]

        for row_index, (label_text, value) in enumerate(details):
            label = ttk.Label(details_card, text=f"{label_text}:", font=("Segoe UI", 9, "bold"))
            label.grid(row=row_index, column=0, sticky="w", padx=(0, 8), pady=1)
            value_label = ttk.Label(details_card, text=str(value), font=("Segoe UI", 9))
            value_label.grid(row=row_index, column=1, sticky="w", pady=1)

        details_card.grid_columnconfigure(1, weight=1)

        notes_card = ttk.LabelFrame(outer, text="Notes", padding=8)
        notes_card.pack(fill=tk.BOTH, expand=False, pady=(8, 0))

        notes_text = tk.Text(notes_card, height=3, wrap="word", borderwidth=0, background="#ffffff")
        notes_text.insert("1.0", task.notes or "No notes provided.")
        notes_text.configure(state="disabled")
        notes_text.pack(fill=tk.BOTH, expand=True)

        attachments_card = ttk.LabelFrame(outer, text="Attachments", padding=8)
        attachments_card.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        if attachments:
            attachment_list = tk.Listbox(attachments_card, height=8, activestyle="none")
            attachment_scrollbar = ttk.Scrollbar(attachments_card, orient=tk.VERTICAL, command=attachment_list.yview)
            attachment_list.configure(yscrollcommand=attachment_scrollbar.set)
            attachment_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            attachment_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            for attachment in attachments:
                file_name = attachment.get("file_name", "Attachment")
                file_path = attachment.get("file_path", "")
                attachment_list.insert(tk.END, file_name)
                attachment_list.insert(tk.END, f"  {file_path}")
                attachment_list.insert(tk.END, "")
        else:
            empty_label = ttk.Label(attachments_card, text="No attachments linked to this task.")
            empty_label.pack(anchor="w")


def show_task_summary(
    parent: tk.Misc,
    task: TaskItem,
    attachments: Optional[list[dict]] = None,
) -> TaskSummaryWindow:
    return TaskSummaryWindow(parent, task, attachments)