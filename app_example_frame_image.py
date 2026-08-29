import tkinter as tk
from tkinter import ttk

root = tk.Tk()

IMAGE = "./resources/file_attachment_01.png"  # Path to your image file

# Load original image
original_photo = tk.PhotoImage(file=IMAGE)

# Scale down by factor of 4 (e.g., a 64x64 image becomes 16x16)
small_photo = original_photo.subsample(16, 16)

tree = ttk.Treeview(root, show="tree", selectmode="extended")
tree.pack(fill="both", expand=True)

tree.photo_ref = small_photo
tree.insert("", "end", text=" Document.pdf", image=small_photo)

if __name__ == "__main__":
    root.mainloop()