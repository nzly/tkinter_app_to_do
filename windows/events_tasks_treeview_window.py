import os
import tkinter as tk
import sys
from pathlib import Path
from tkinter import ttk

# Ensure the parent directory is in sys.path for imports
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Import additional necessary modules from the project
from db.db import (
    add_event_flag,
    get_event_flags,
    get_event_task_ids,
    get_events,
    get_flags,
    get_task_attachments,
    get_tasks,
    resolve_db_path,
)
from util import get_resource_path, open_file, resize_image

# Define paths to resource images and their sizes
EVENT_IMAGE = get_resource_path(os.path.join("resources", "event.png"))  # Path to your event icon image
TASK_IMAGE = get_resource_path(os.path.join("resources", "task_04.png"))  # Path to your task icon image
ATTACHED_FILE_IMAGE = get_resource_path(os.path.join("resources", "file_attachment_01.png"))  # Path to your attachment icon image
FLAG_IMAGES = [
    get_resource_path(os.path.join("resources", f"clip_flag_{index:02d}.png"))
    for index in range(1, 5)
]
TREE_IMAGE_SIZE_BIGGER = (23, 23)  # Size for the images in the Treeview
TREE_IMAGE_SIZE_SMALLER = (20, 20)  # Size for the images in the Treeview
FLAG_IMAGE_SIZE = (32, 32)

# Add a task node to the Treeview, including its attachments
def add_task_node(tree: ttk.Treeview, parent: str, task, db_path: str, insert_task_image: tk.PhotoImage, insert_attached_file_image: tk.PhotoImage) -> None:
    task_node = tree.insert(
        parent,
        tk.END,
        text=task.task_name or "Untitled task",
        image=insert_task_image,
        tags=("task",),
    )
    for attachment in get_task_attachments(db_path, task.task_id):
        tree.insert(
            task_node,
            tk.END,
            text=attachment["file_name"] or attachment["file_path"],
            values=(attachment["file_path"],),
            image=insert_attached_file_image,
            tags=("attachment",),
        )

# Handle double-click event to open the attachment
def open_attachment(event: tk.Event, tree: ttk.Treeview) -> None:
    item_id = tree.identify_row(event.y)
    if not item_id:
        return

    attachment_path = tree.item(item_id, "values")
    if attachment_path:
        open_file(str(attachment_path[0]))

# Open a new window displaying events and tasks in a Treeview
def open_events_tasks_treeview_window(parent: tk.Misc, db_path: str) -> None:
    root = tk.Toplevel(parent)
    root.title("Events and Tasks Tree View")
    root.geometry("760x550")

    content = ttk.Frame(root, padding=10)
    content.pack(fill="both", expand=True)
    content.grid_columnconfigure(0, weight=1)
    content.grid_rowconfigure(1, weight=1)

    flag_toolbar = ttk.LabelFrame(content, text="Drag a flag onto an event", padding=(8, 6))
    flag_toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

    tree = ttk.Treeview(content, columns=("attachment_path",), displaycolumns=())
    tree.bind("<Double-1>", lambda event: open_attachment(event, tree))
    tree.grid(row=1, column=0, sticky="nsew")

    insert_event_image = resize_image(EVENT_IMAGE, TREE_IMAGE_SIZE_BIGGER)
    insert_task_image = resize_image(TASK_IMAGE, TREE_IMAGE_SIZE_SMALLER)
    insert_attached_file_image = resize_image(ATTACHED_FILE_IMAGE, TREE_IMAGE_SIZE_SMALLER)
    flag_images = [resize_image(image_path, FLAG_IMAGE_SIZE) for image_path in FLAG_IMAGES]
    tree.ref_images = [insert_event_image, insert_task_image, insert_attached_file_image, *flag_images]
    event_node_ids: dict[str, int] = {}
    dragged_flag = [None]
    drag_preview = tk.Label(root, bd=0, highlightthickness=0)

    def load_tree() -> None:
        tree.delete(*tree.get_children())
        event_node_ids.clear()
        events_tasks_root = tree.insert("", tk.END, text="Events and Tasks", tags=("root",))
        events = tree.insert(events_tasks_root, tk.END, text="Events", tags=("events_group",))
        tasks = tree.insert(events_tasks_root, tk.END, text="Tasks", tags=("tasks_group",))
        tasks_by_id = {task.task_id: task for task in get_tasks(db_path)}
        linked_task_ids: set[int] = set()

        for event_item in get_events(db_path):
            flag_names = ", ".join(flag.flag_name for flag in get_event_flags(db_path, event_item.id))
            event_text = event_item.title or "Untitled event"
            if flag_names:
                event_text = f"{event_text} [{flag_names}]"
            event_node = tree.insert(
                events,
                tk.END,
                text=event_text,
                image=insert_event_image,
                tags=("event",),
            )
            event_node_ids[event_node] = event_item.id
            for task_id in get_event_task_ids(db_path, event_item.id):
                linked_task_ids.add(task_id)
                task = tasks_by_id.get(task_id)
                if task is not None:
                    add_task_node(tree, event_node, task, db_path, insert_task_image, insert_attached_file_image)

        for task in tasks_by_id.values():
            if task.task_id not in linked_task_ids:
                add_task_node(tree, tasks, task, db_path, insert_task_image, insert_attached_file_image)

        tree.item(events_tasks_root, open=True)
        tree.item(events, open=True)
        tree.item(tasks, open=True)

    def start_drag(event: tk.Event, flag_item, image: tk.PhotoImage) -> None:
        dragged_flag[0] = flag_item
        drag_preview.config(image=image)
        drag_preview.place(x=event.x_root - root.winfo_rootx(), y=event.y_root - root.winfo_rooty())

    def move_drag(event: tk.Event) -> None:
        if dragged_flag[0] is not None:
            drag_preview.place(x=event.x_root - root.winfo_rootx(), y=event.y_root - root.winfo_rooty())

    def drop_flag(event: tk.Event) -> None:
        flag_item = dragged_flag[0]
        dragged_flag[0] = None
        drag_preview.place_forget()
        if flag_item is None:
            return

        tree_x = event.x_root - tree.winfo_rootx()
        tree_y = event.y_root - tree.winfo_rooty()
        if not (0 <= tree_x < tree.winfo_width() and 0 <= tree_y < tree.winfo_height()):
            return
        event_node = tree.identify_row(tree_y)
        if event_node not in event_node_ids:
            return

        add_event_flag(db_path, event_node_ids[event_node], flag_item.id)
        load_tree()

    available_flags = get_flags(db_path)
    for column, (flag_item, image) in enumerate(zip(available_flags[:4], flag_images)):
        flag_label = tk.Label(flag_toolbar, image=image, cursor="hand2", bd=0)
        flag_label.grid(row=0, column=column, padx=8, pady=2)
        flag_label.bind("<ButtonPress-1>", lambda event, item=flag_item, flag_image=image: start_drag(event, item, flag_image))
        flag_label.bind("<B1-Motion>", move_drag)
        flag_label.bind("<ButtonRelease-1>", drop_flag)

    load_tree()

# Main function to run the application
def main() -> None:
    root = tk.Tk()
    root.title("Tkinter Main Window")
    root.geometry("300x200")
    my_label = tk.Label(root, text="In the real world \nthis is supposed to be \nthe main window \nof the application.")
    my_label.pack(pady=20)
    open_events_tasks_treeview_window(root, resolve_db_path())
    root.mainloop()

# Application entry point
if __name__ == "__main__":
    main()
