import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

root = tk.Tk()

IMAGE = "./resources/file_attachment_01.png"  # Path to your image file

# 1. Load and resize the image using Pillow
original_img = Image.open(IMAGE)
resized_img = original_img.resize((16, 16), Image.Resampling.LANCZOS) # 16x16 icon
image = ImageTk.PhotoImage(resized_img)

# 2. Add to Treeview
tree = ttk.Treeview(root, show="tree", selectmode="extended")
tree.pack(fill="both", expand=True)

# Keep a reference to the image so Python doesn't garbage collect it
tree.photo_ref = image

tree.insert("", "end", text=" Document.pdf", image=image)
tree.insert("", "end", text=" Image.png", image=image)

if __name__ == "__main__":
    root.mainloop()