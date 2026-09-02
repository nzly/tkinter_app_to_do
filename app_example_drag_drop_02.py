from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk

# Initialize TkinterDnD root instead of tk.Tk()
root = TkinterDnD.Tk()
root.geometry("400x200")

label = tk.Label(root, text="Drop files here", bg="lightgrey", width=40, height=10)
label.pack(padx=20, pady=20)

# Register drop target
label.drop_target_register(DND_FILES)

def on_drop(event):
    label.config(text=f"Dropped file:\n{event.data}")

label.dnd_bind('<<Drop>>', on_drop)

if __name__ == "__main__":
    root.mainloop()
