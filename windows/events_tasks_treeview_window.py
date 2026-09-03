import os
import tkinter as tk
import sys
from pathlib import Path
from tkinter import ttk
from PIL import Image, ImageTk

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
    remove_event_flag,
    resolve_db_path,
)
from util import get_resource_path, open_file, resize_image
from windows.event_summary_window import show_event_summary

# Define paths to resource images and their sizes
EVENT_IMAGE = get_resource_path(os.path.join("resources", "event.png"))  # Path to your event icon image
TASK_IMAGE = get_resource_path(os.path.join("resources", "task_04.png"))  # Path to your task icon image
ATTACHED_FILE_IMAGE = get_resource_path(os.path.join("resources", "file_attachment_01.png"))  # Path to your attachment icon image
FLAG_IMAGES = [
    get_resource_path(os.path.join("resources", f"clip_flag_{index:02d}.png"))
    for index in range(1, 12)
]
TREE_IMAGE_SIZE_BIGGER = (23, 23)  # Size for the images in the Treeview
TREE_IMAGE_SIZE_SMALLER = (20, 20)  # Size for the images in the Treeview
FLAG_IMAGE_SIZE = (32, 32)
EVENT_FLAG_IMAGE_SIZE = (20, 20)

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

    tree = ttk.Treeview(
        content,
        columns=("attachment_path", "flags"),
        displaycolumns=("flags",),
    )
    tree.heading("#0", text="Event / Task")
    tree.heading("flags", text="Flags")
    tree.column("#0", width=460, minwidth=280, stretch=True)
    tree.column("flags", width=210, minwidth=150, stretch=True)
    tree.bind("<Double-1>", lambda event: open_attachment(event, tree))
    tree.grid(row=1, column=0, sticky="nsew")
    tree.tag_configure("event_flagged", foreground="#0f766e")

    insert_event_image = resize_image(EVENT_IMAGE, TREE_IMAGE_SIZE_BIGGER)
    insert_task_image = resize_image(TASK_IMAGE, TREE_IMAGE_SIZE_SMALLER)
    insert_attached_file_image = resize_image(ATTACHED_FILE_IMAGE, TREE_IMAGE_SIZE_SMALLER)
    flag_images = [resize_image(image_path, FLAG_IMAGE_SIZE) for image_path in FLAG_IMAGES]
    tree.ref_images = [insert_event_image, insert_task_image, insert_attached_file_image, *flag_images]
    event_node_ids: dict[str, int] = {}
    events_by_id = {}
    dragged_flag = [None]
    drag_preview = tk.Label(root, bd=0, highlightthickness=0)
    tooltip = [None]

    def create_event_flag_image(assigned_flags) -> tk.PhotoImage:
        image_paths = [flag_image_paths_by_id.get(flag_item.id) for flag_item in assigned_flags]
        image_paths = [image_path for image_path in image_paths if image_path]
        if not image_paths:
            return insert_event_image

        with Image.open(EVENT_IMAGE) as event_source:
            event_image = event_source.convert("RGBA").resize(TREE_IMAGE_SIZE_BIGGER, Image.Resampling.LANCZOS)
        flag_bitmaps = []
        for image_path in image_paths:
            with Image.open(image_path) as flag_source:
                flag_bitmaps.append(
                    flag_source.convert("RGBA").resize(EVENT_FLAG_IMAGE_SIZE, Image.Resampling.LANCZOS)
                )

        combined = Image.new(
            "RGBA",
            (event_image.width + sum(image.width for image in flag_bitmaps), max(event_image.height, EVENT_FLAG_IMAGE_SIZE[1])),
            (0, 0, 0, 0),
        )
        combined.alpha_composite(event_image, (0, 0))
        offset = event_image.width
        for flag_image in flag_bitmaps:
            combined.alpha_composite(flag_image, (offset, 0))
            offset += flag_image.width

        combined_image = ImageTk.PhotoImage(combined)
        tree.ref_images.append(combined_image)
        return combined_image

    def show_flag_tooltip(event: tk.Event, flag_name: str) -> None:
        hide_flag_tooltip()
        tooltip_window = tk.Toplevel(root)
        tooltip_window.overrideredirect(True)
        tooltip_window.geometry(f"+{event.x_root + 12}+{event.y_root + 12}")
        ttk.Label(
            tooltip_window,
            text=f"{flag_name}\nPlease drag and drop the flag on Event (multiple flags can be added to an event)",
            padding=(8, 5),
            relief="solid",
        ).pack()
        tooltip[0] = tooltip_window

    def hide_flag_tooltip(_event: tk.Event | None = None) -> None:
        if tooltip[0] is not None:
            tooltip[0].destroy()
            tooltip[0] = None

    def load_tree() -> None:
        tree.delete(*tree.get_children())
        event_node_ids.clear()
        events_by_id.clear()
        events_tasks_root = tree.insert("", tk.END, text="Events and Tasks", tags=("root",))
        events = tree.insert(events_tasks_root, tk.END, text="Events", tags=("events_group",))
        tasks = tree.insert(events_tasks_root, tk.END, text="Tasks", tags=("tasks_group",))
        tasks_by_id = {task.task_id: task for task in get_tasks(db_path)}
        linked_task_ids: set[int] = set()

        for event_item in get_events(db_path):
            events_by_id[event_item.id] = event_item
            assigned_flags = get_event_flags(db_path, event_item.id)
            flag_names = ", ".join(flag.flag_name for flag in assigned_flags)
            event_text = event_item.title or "Untitled event"
            event_node = tree.insert(
                events,
                tk.END,
                text=event_text,
                values=("", flag_names),
                image=create_event_flag_image(assigned_flags),
                tags=("event", "event_flagged") if assigned_flags else ("event",),
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

    def view_event(event_id: int) -> None:
        event_item = events_by_id.get(event_id)
        if event_item is None:
            return
        show_event_summary(
            root,
            event_item,
            linked_tasks=list(get_tasks(db_path)),
            linked_task_ids=get_event_task_ids(db_path, event_id),
        )

    def open_remove_flags_window(event_id: int) -> None:
        assigned_flags = get_event_flags(db_path, event_id)
        if not assigned_flags:
            return

        remove_window = tk.Toplevel(root)
        remove_window.title("Remove Flags")
        remove_window.transient(root)
        remove_window.grab_set()

        content_frame = ttk.Frame(remove_window, padding=12)
        content_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(content_frame, text="Select flags to remove:").pack(anchor="w")

        selected_flags = []
        for flag_item in assigned_flags:
            selected = tk.BooleanVar(value=False)
            ttk.Checkbutton(
                content_frame,
                text=flag_item.flag_name,
                variable=selected,
            ).pack(anchor="w", pady=2)
            selected_flags.append((flag_item.id, selected))

        def remove_selected_flags() -> None:
            for flag_id, selected in selected_flags:
                if selected.get():
                    remove_event_flag(db_path, event_id, flag_id)
            remove_window.destroy()
            load_tree()

        button_row = ttk.Frame(content_frame)
        button_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(button_row, text="Cancel", command=remove_window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_row, text="Remove Selected", command=remove_selected_flags).pack(side=tk.RIGHT, padx=(0, 8))

    def open_event_context_menu(event: tk.Event) -> None:
        item_id = tree.identify_row(event.y)
        if item_id not in event_node_ids:
            return

        tree.selection_set(item_id)
        event_id = event_node_ids[item_id]
        context_menu = tk.Menu(root, tearoff=0)
        context_menu.add_command(label="View Event", command=lambda: view_event(event_id))
        context_menu.add_separator()
        context_menu.add_command(label="Remove Flag(s)", command=lambda: open_remove_flags_window(event_id))
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    tree.bind("<Button-3>", open_event_context_menu)

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
    flag_image_paths_by_id = {
        flag_item.id: image_path
        for flag_item, image_path in zip(available_flags[:11], FLAG_IMAGES)
    }
    for column, (flag_item, image) in enumerate(zip(available_flags[:11], flag_images)):
        flag_label = tk.Label(flag_toolbar, image=image, cursor="hand2", bd=0)
        flag_label.grid(row=0, column=column, padx=8, pady=2)
        flag_label.bind("<ButtonPress-1>", lambda event, item=flag_item, flag_image=image: start_drag(event, item, flag_image))
        flag_label.bind("<B1-Motion>", move_drag)
        flag_label.bind("<ButtonRelease-1>", drop_flag)
        flag_label.bind("<Enter>", lambda event, name=flag_item.flag_name: show_flag_tooltip(event, name))
        flag_label.bind("<Leave>", hide_flag_tooltip)

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
