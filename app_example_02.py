import tkinter as tk
from tkinter import ttk

# Main window setup
root = tk.Tk()
root.title("Employee Management System")
root.geometry("620x300")

# 1. Define Columns (The backend unique identifiers)
columns = ("id", "name", "role", "salary")

# 2. Create Treeview (show="headings" hides the default blank tree column)
tree = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")

# 3. Configure Column Widths and text alignments
tree.column("id", width=60, anchor=tk.CENTER)
tree.column("name", width=150, anchor=tk.W)
tree.column("role", width=150, anchor=tk.W)
tree.column("salary", width=100, anchor=tk.E)

# 4. Define Visual Headers (What the user actually sees)
tree.heading("id", text="ID")
tree.heading("name", text="Full Name")
tree.heading("role", text="Job Position")
tree.heading("salary", text="Salary ($)")

# 5. Insert Data Rows
# Format: tree.insert(parent, index, iid, text, values)
# Use "" for parent when making a flat table row
employees = [
    (101, "Alice Smith", "Software Engineer", 95000),
    (102, "Bob Jones", "UX Designer", 82000),
    (103, "Charlie Brown", "Data Scientist", 105000)
]

for emp in employees:
    tree.insert(parent="", index=tk.END, values=emp)

# 6. Add Scrollbar for large datasets
scrollbar = ttk.Scrollbar(root, orient=tk.VERTICAL, command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)

# 7. Layout Widgets using Grid
tree.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")

# Configure window weights so it resizes beautifully
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)

def get_selected_row(event):
    selected_item = tree.selection()  # Returns a tuple of item IDs
    if selected_item:
        item_id = selected_item[0]
        row_values = tree.item(item_id, "values")  # Returns data tuple
        print(f"Clicked row data: {row_values}")

# Bind click release event to your function
tree.bind("<ButtonRelease-1>", get_selected_row)

# Create root folder node
folder_id = tree.insert(parent="", index=tk.END, text="Documents Folder")

# Nest a file inside the folder by referencing its folder_id
tree.insert(parent=folder_id, index=tk.END, values=("Resume.pdf", "PDF file"))

root.mainloop()
