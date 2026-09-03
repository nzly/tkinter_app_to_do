import tkinter as tk

root = tk.Tk()
root.geometry("400x200")

# Create a Text widget styled to look like a Listbox
list_view = tk.Text(root, bg="white", fg="#1f2937", relief=tk.FLAT, bd=1)
list_view.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Define custom tags for highlighting parts of the text
list_view.tag_configure("highlight", foreground="#0f766e", font=("Bahnschrift", 10, "bold"))
list_view.tag_configure("normal", foreground="#1f2937", font=("Bahnschrift", 10))

# Insert items with partial formatting
list_view.insert(tk.END, "Task 101: ", "highlight")
list_view.insert(tk.END, "Complete project report\n", "normal")

list_view.insert(tk.END, "Task 102: ", "highlight")
list_view.insert(tk.END, "Upload attachment files\n", "normal")

# Disable editing so it behaves like a read-only list
list_view.config(state=tk.NORMAL)

if __name__ == "__main__":
    root.mainloop()