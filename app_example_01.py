import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Treeview Example")
root.geometry("700x400")

# -------------------------
# Treeview
# -------------------------
frame = ttk.Frame(root)

frame.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

tree = ttk.Treeview(
    frame,
    columns=("id", "name", "age"),
    show="headings",
    selectmode="browse"
)

tree.heading(
    "id",
    text="ID"
)

tree.heading(
    "name",
    text="Name"
)

tree.heading(
    "age",
    text="Age"
)

tree.column(
    "id",
    width=80
)

tree.column(
    "name",
    width=250
)

tree.column(
    "age",
    width=100
)

# -------------------------
# Data
# -------------------------
data = [
    (1, "John", 35),
    (2, "Mary", 28),
    (3, "Peter", 42),
    (4, "Susan", 31),
    (5, "David", 25)
]

for row in data:

    tree.insert(
        "",
        tk.END,
        values=row
    )

# -------------------------
# Scrollbar
# -------------------------
scrollbar = ttk.Scrollbar(
    frame,
    orient="vertical",
    command=tree.yview
)

tree.configure(
    yscrollcommand=scrollbar.set
)

tree.pack(
    side="left",
    fill="both",
    expand=True
)

scrollbar.pack(
    side="right",
    fill="y"
)

# -------------------------
# Row selection
# -------------------------
def on_select(event):
    selected = tree.selection()

    if not selected:
        return

    item_id = selected[0]

    values = tree.item(
        item_id,
        "values"
    )

    print("Selected row:", values)


tree.bind(
    "<<TreeviewSelect>>",
    on_select
)

# -------------------------
# Right click
# -------------------------
def on_right_click(event):
    item_id = tree.identify_row(event.y)

    if not item_id:
        return

    tree.selection_set(item_id)

    values = tree.item(
        item_id,
        "values"
    )

    print("Right clicked:", values)

    menu.post(
        event.x_root,
        event.y_root
    )


tree.bind(
    "<Button-3>",
    on_right_click
)

# -------------------------
# Context menu
# -------------------------
def delete_row():
    selected = tree.selection()

    if selected:
        tree.delete(
            selected[0]
        )

menu = tk.Menu(
    root,
    tearoff=False
)

menu.add_command(
    label="Delete",
    command=delete_row
)

root.mainloop()
