import os
import shutil
import sqlite3
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

class FileDropApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drag and Drop Saver")
        self.root.geometry("400x300")

        # 1. UI Drop Target Box
        self.drop_label = tk.Label(
            root, text="Drag & Drop Files Here", bg="#e6f4f1", fg="#0f766e", relief=tk.RIDGE, bd=2
        )
        self.drop_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 2. Register drop event
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind("<<Drop>>", self.on_file_drop)

    def on_file_drop(self, event):
        # Clean up file paths (tkinterdnd2 wraps paths with spaces in curly braces {})
        raw_paths = self.root.tk.splitlist(event.data)

        for file_path in raw_paths:
            # Option A: Save the file path to a database or list
            self.save_filepath_to_db(file_path)

            # Option B: Copy the physical file to a local project directory
            self.copy_file_to_storage(file_path)

        self.drop_label.config(text=f"Saved {len(raw_paths)} file(s) successfully!")

    def save_filepath_to_db(self, file_path):
        """Save file path reference directly into a database."""
        conn = sqlite3.connect("app_data.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS attachments (path TEXT)")
        cursor.execute("INSERT INTO attachments (path) VALUES (?)", (file_path,))
        conn.commit()
        conn.close()

    def copy_file_to_storage(self, file_path):
        """Copy the dropped file into an internal 'uploads' folder."""
        dest_dir = "uploads"
        os.makedirs(dest_dir, exist_ok=True)
        if os.path.exists(file_path):
            shutil.copy(file_path, dest_dir)

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = FileDropApp(root)
    root.mainloop()