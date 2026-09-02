import tkinter as tk

root = tk.Tk()
root.geometry("400x300")

label = tk.Label(root, text="Drag Me", bg="royalblue", fg="white", padx=10, pady=10)
label.place(x=50, y=50)

def on_drag_start(event):
    widget = event.widget
    widget._drag_start_x = event.x
    widget._drag_start_y = event.y

def on_drag_motion(event):
    widget = event.widget
    x = widget.winfo_x() - widget._drag_start_x + event.x
    y = widget.winfo_y() - widget._drag_start_y + event.y
    widget.place(x=x, y=y)

label.bind("<Button-1>", on_drag_start)
label.bind("<B1-Motion>", on_drag_motion)

if __name__ == "__main__":
    root.mainloop()
