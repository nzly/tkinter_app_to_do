import tkinter as tk
from PIL import Image, ImageTk

class CanvasHoverApp:
    def __init__(self, root, image_path):
        self.root = root
        self.image_path = image_path

        # 1. Base Thumbnail Label
        pil_thumb = Image.open(image_path).resize((100, 100), Image.Resampling.LANCZOS)
        self.tk_thumb = ImageTk.PhotoImage(pil_thumb)

        self.thumb_label = tk.Label(root, image=self.tk_thumb, text=" Hover me", compound=tk.LEFT)
        self.thumb_label.pack(padx=50, pady=50)

        # 2. In-Window Overlay Container (hidden initially)
        self.overlay_frame = tk.Frame(root, bg="black", bd=2, relief=tk.SOLID)
        
        pil_large = Image.open(image_path).resize((350, 350), Image.Resampling.LANCZOS)
        self.tk_large = ImageTk.PhotoImage(pil_large)
        
        self.large_label = tk.Label(self.overlay_frame, image=self.tk_large, bg="black")
        self.large_label.pack()

        # Bind events
        self.thumb_label.bind("<Enter>", self.show_overlay)
        self.thumb_label.bind("<Leave>", self.hide_overlay)

    def show_overlay(self, event):
        # Display frame at absolute x, y position inside main window
        self.overlay_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.overlay_frame.lift()  # Raise to top layer

    def hide_overlay(self, event):
        self.overlay_frame.place_forget()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("500x500")
    app = CanvasHoverApp(root, "./resources/clip_flag_01.png")
    root.mainloop()