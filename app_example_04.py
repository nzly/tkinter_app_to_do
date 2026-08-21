import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("File Explorer")
root.geometry("600x400")

tree = ttk.Treeview(
    root,
    show="tree"
)

tree.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# -------------------------
# Root
# -------------------------
root_node = tree.insert(
    "",
    tk.END,
    text="📁 My Project",
    open=True
)

# -------------------------
# src
# -------------------------
src = tree.insert(
    root_node,
    tk.END,
    text="📁 src",
    open=True
)

tree.insert(
    src,
    tk.END,
    text="📄 main.py"
)

tree.insert(
    src,
    tk.END,
    text="📄 database.py"
)

tree.insert(
    src,
    tk.END,
    text="📄 utils.py"
)

# -------------------------
# resources
# -------------------------
resources = tree.insert(
    root_node,
    tk.END,
    text="📁 resources"
)

tree.insert(
    resources,
    tk.END,
    text="📄 app.ico"
)

tree.insert(
    resources,
    tk.END,
    text="📄 config.json"
)

# -------------------------
# tests
# -------------------------
tests = tree.insert(
    root_node,
    tk.END,
    text="📁 tests"
)

tree.insert(
    tests,
    tk.END,
    text="📄 test_main.py"
)

# -------------------------
# Other files
# -------------------------
tree.insert(
    root_node,
    tk.END,
    text="📄 README.md"
)

tree.insert(
    root_node,
    tk.END,
    text="📄 pyproject.toml"
)

root.mainloop()