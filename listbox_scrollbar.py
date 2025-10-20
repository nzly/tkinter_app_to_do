import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Listbox in Frame Example")
root.geometry("400x300")

# Create a Frame widget
frame = tk.Frame(root, bg="lightblue", padx=10, pady=10)
frame.pack(pady=20)

# Create the Scrollbar
scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Create the Listbox
listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Link the Scrollbar to the Listbox
scrollbar.config(command=listbox.yview)

# Add some items to the Listbox
for i in range(50):
    listbox.insert(tk.END, f"Item {i+1}")

# Run the Tkinter event loop
root.mainloop()
