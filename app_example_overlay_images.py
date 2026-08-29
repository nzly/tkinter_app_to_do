import tkinter as tk

# Set up the main window
root = tk.Tk()
root.title("Image List Overlay")

IMAGE = "./resources/file_attachment_01.png"  # Path to your image file

# Create a Canvas and a Scrollbar
canvas = tk.Canvas(root, bg="white", width=250, height=200)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="white")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# Load an image (must keep a reference so it doesn't get deleted by garbage collection)
# Replace 'sample.png' with your actual image file (PhotoImage supports GIF, PGM, PPM)
try:
    img = tk.PhotoImage(file=IMAGE)
    # Reduces the size of the image. (16 divides it by 16, etc.)
    img = img.subsample(16, 16)
except:
    # Fallback if no image file is found
    img = None

# Add items with text and images to the frame
for i in range(10):
    item_frame = tk.Frame(scrollable_frame, bg="white", pady=5)
    
    # Image label
    lbl_img = tk.Label(item_frame, image=img, bg="white")
    if img:
        lbl_img.pack(side="left", padx=5)
        
    # Text label overlaid/placed next to the image
    lbl_text = tk.Label(item_frame, text=f"Item number {i}", bg="white")
    lbl_text.pack(side="left", padx=5)
    
    item_frame.pack(fill="x", anchor="w")

# Pack the canvas and scrollbar
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

root.mainloop()
