import tkinter as tk
from PIL import Image, ImageTk

class HoverImagePreview:
    def __init__(self, widget, image_path, preview_size=(300, 300)):
        self.widget = widget
        self.image_path = image_path
        self.preview_size = preview_size
        self.top_window = None

        # Bind hover events
        self.widget.bind("<Enter>", self.show_preview)
        self.widget.bind("<Leave>", self.hide_preview)

    def show_preview(self, event):
        if self.top_window is not None:
            return

        # Create floating top-level window
        self.top_window = tk.Toplevel(self.widget)
        self.top_window.overrideredirect(True)  # Remove window borders
        self.top_window.attributes("-topmost", True)  # Keep on top

        # Position preview slightly offset from the mouse cursor
        x = self.widget.winfo_rootx() + event.x + 15
        y = self.widget.winfo_rooty() + event.y + 15
        self.top_window.geometry(f"+{x}+{y}")

        # Load and resize image using Pillow
        pil_img = Image.open(self.image_path)
        pil_img = pil_img.resize(self.preview_size, Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(pil_img)

        # Place image inside floating window
        lbl = tk.Label(self.top_window, image=self.photo, bg="black", bd=1, relief=tk.SOLID)
        lbl.pack()

    def hide_preview(self, event):
        if self.top_window:
            self.top_window.destroy()
            self.top_window = None

# --- Usage Example ---
if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x300")
    root.title("Hover Image Preview Example")

    # Load thumbnail image
    thumb_img = Image.open("./resources/clip_flag_01.png")
    thumb_img = thumb_img.resize((80, 80), Image.Resampling.LANCZOS)
    photo_thumb = ImageTk.PhotoImage(thumb_img)

    # Thumbnail label
    thumbnail_label = tk.Label(root, image=photo_thumb, bd=2, relief=tk.RAISED)
    thumbnail_label.pack(padx=20, pady=20)

    # Attach hover functionality (pass path to large image)
    HoverImagePreview(thumbnail_label, "./resources/clip_flag_01.png", preview_size=(300, 300))

    root.mainloop()