import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title("Tree View Example")
root.geometry("500x400")

tree = ttk.Treeview(root)

tree.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

# Root node
projects = tree.insert(
    "",
    tk.END,
    text="Projects"
)

# Python folder
python_folder = tree.insert(
    projects,
    tk.END,
    text="Python"
)

tree.insert(
    python_folder,
    tk.END,
    text="main.py"
)

tree.insert(
    python_folder,
    tk.END,
    text="database.py"
)

tree.insert(
    python_folder,
    tk.END,
    text="utils.py"
)

# Java folder
java_folder = tree.insert(
    projects,
    tk.END,
    text="Java"
)

tree.insert(
    java_folder,
    tk.END,
    text="Main.java"
)

tree.insert(
    java_folder,
    tk.END,
    text="Database.java"
)

# Documents folder
documents = tree.insert(
    projects,
    tk.END,
    text="Documents"
)

tree.insert(
    documents,
    tk.END,
    text="Report.pdf"
)

tree.insert(
    documents,
    tk.END,
    text="Notes.txt"
)

root.mainloop()
