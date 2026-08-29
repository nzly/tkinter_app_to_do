import os
import sqlite3
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class FilesListboxFrame(tk.Frame):
    """Frame that contains a Listbox and its Scrollbar with helper methods."""
    # Build the attachments list frame and its controls.
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="#f4f7fb")

        self.title_label = ttk.Label(self, text="Attachments", font=("Bahnschrift", 11, "bold"))
        self.title_label.pack(side=tk.TOP, anchor="w", padx=6, pady=(6, 0))

        self.helper_label = ttk.Label(
            self,
            text="Double-click a file to open it. Use multiple selection for bulk actions.",
        )
        self.helper_label.pack(side=tk.TOP, anchor="w", padx=6, pady=(0, 4))

        # Default selection mode
        self.select_mode = tk.SINGLE

        # Checkbox to toggle multiple selection
        self.checkVar = tk.IntVar()
        checkbox_multiple_selection = tk.Checkbutton(
            self,
            text="Multiple Selection",
            variable=self.checkVar,
            onvalue=1,
            offvalue=0,
            anchor="w",
            height=1,
            width=20,
            command=self.on_select_mod_change,
            bg="#f4f7fb",
            activebackground="#f4f7fb",
            fg="#1f2937",
            activeforeground="#1f2937",
            selectcolor="#ffffff",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
        )
        checkbox_multiple_selection.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)

        # Themed scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Listbox: exportselection=False keeps selection when focus changes
        self.listbox = tk.Listbox(
            self,
            selectmode=self.select_mode,
            exportselection=False,
            yscrollcommand=scrollbar.set,
            bg="#ffffff",
            fg="#1f2937",
            selectbackground="#0f766e",
            selectforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            highlightthickness=1,
            highlightbackground="#d4dde8",
            highlightcolor="#0f766e",
            activestyle="none",
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

        self.state_label = ttk.Label(self, text="", anchor="w")
        self.state_label.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=(4, 6))

        self.set_empty_state()

        # -----------------------------------------------------
        # Create Right-Click Context Menu
        # -----------------------------------------------------
        self.popup_menu = tk.Menu(self.listbox, tearoff=0)
        self.popup_menu.add_command(
            label="Unlink it from task", command=self.unlink_attachment
        )

        # -----------------------------------------------------
        # Bind Right-Click event
        # (<Button-3> on Windows/Linux)
        # -----------------------------------------------------
        self.listbox.bind("<Button-3>", self.show_context_menu)
        self.listbox.bind("<Button-2>", self.show_context_menu)

    # -----------------------------------------------------
    # Context Menu Actions
    # -----------------------------------------------------
    def show_context_menu(self, event):
        """Select item under cursor and display context menu."""
        index = self.listbox.nearest(event.y)

        # Check if click happened inside an item bounding box
        if index >= 0 and self.listbox.bbox(index):
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(index)
            self.listbox.activate(index)
            self.popup_menu.tk_popup(event.x_root, event.y_root)

    # -----------------------------------------------------
    # Unlink attachment from database and list
    # -----------------------------------------------------
    def unlink_attachment(self):
        """Unlink selected attachment from database and update list."""
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            return

        index = selected_indices[0]
        raw_value = self.listbox.get(index)

        # Parse task_id and file_path from the formatted string "task_id, file_path"
        parts = str(raw_value).split(", ", 1)
        if len(parts) < 2:
            return

        try:
            task_id = int(parts[0])
            file_path = parts[1]
        except ValueError:
            return

        # Fetch attachment_id from database using task_id and file_path
        from app import _resolve_db_path
        db_path = getattr(self, "db_path", _resolve_db_path())

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM task_attachments WHERE task_id = ? AND file_path = ?",
                (task_id, file_path)
            )
            row = cursor.fetchone()

            if row:
                attachment_id = row[0]
                # Delete record from task_attachments table
                if self.delete_from_db(task_id, attachment_id):
                    # Remove item from Listbox UI
                    self.listbox.delete(index)

                # Update count message below listbox
                remaining = self.listbox.size()
                if remaining > 0:
                    self.update_state_message(remaining)
                else:
                    self.set_empty_state()

            conn.close()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to unlink attachment:\n{e}")

    # -----------------------------------------------------
    # Database Operations
    # Delete attachment link from task_attachments table
    # -----------------------------------------------------
    def delete_from_db(self, task_id: int, attachment_id: int) -> bool:
        """Execute SQLite query to delete attachment link."""
        from app import _resolve_db_path
        
        try:
            db_path = getattr(self, "db_path", _resolve_db_path())
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM task_attachments WHERE task_id = ? AND id = ?",
                (task_id, attachment_id),
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            messagebox.showerror(
                "Database Error", f"Failed to unlink attachment:\n{e}"
            )
            return False
            
    # Return the underlying files listbox widget.
    def get_files_listbox(self) -> tk.Listbox:
        return self.listbox

    # Format an attachment as a list row.
    def _format_attachment(self, task_id: int, file_path: str) -> str:
        return f"{task_id}, {file_path}"

    # Extract a file path from a formatted attachment row.
    def extract_path_from_row(self, row_value: str) -> str:
        parts = str(row_value).split(", ", 1)
        if len(parts) == 2:
            return parts[1].strip()
        return str(row_value).strip()

    # Return the path from the selected attachment row.
    def get_selected_file_path(self) -> str | None:
        indices = self.listbox.curselection()
        if not indices:
            return None

        raw_value = self.listbox.get(int(indices[0]))
        file_path = self.extract_path_from_row(raw_value)
        return file_path or None

    # Convenience helpers
    # Append a standalone file path to the list.
    def add_file(self, file: str) -> None:
        self.listbox.insert(tk.END, file)

    # Append a task attachment to the list.
    def add_attachment(self, task_id: int, file_path: str) -> None:
        self.listbox.insert(tk.END, self._format_attachment(task_id, file_path))

    # Delete selected attachment rows.
    def delete_selected(self) -> None:
        indices = self.listbox.curselection()
        if not indices:
            return
        for idx in indices[::-1]:
            try:
                self.listbox.delete(int(idx))
            except (ValueError, tk.TclError):
                try:
                    self.listbox.delete(idx)
                except Exception:
                    pass

    # Return all selected attachment rows.
    def get_selected_files(self) -> list:
        return [self.listbox.get(int(i)) for i in self.listbox.curselection()]

    # Replace the list contents with file items.
    def set_files(self, items: list) -> None:
        self.listbox.delete(0, tk.END)
        for it in items:
            self.listbox.insert(tk.END, it)
        if items:
            self.update_state_message(len(items))
        else:
            self.set_empty_state()

    # Replace the list contents with database attachment rows.
    def set_attachments(self, attachments: list[dict]) -> None:
        self.listbox.delete(0, tk.END)
        for attachment in attachments:
            self.listbox.insert(
                tk.END,
                self._format_attachment(int(attachment["task_id"]), str(attachment["file_path"])),
            )
        if attachments:
            self.update_state_message(len(attachments))
        else:
            self.set_empty_state()

    # --------------------------------------------------
    # Highlight attachments belonging to one task
    # --------------------------------------------------
    def highlight_task_attachments(self, task_id: int) -> None:
        self.listbox.selection_clear(0, tk.END)
        match_indices: list[int] = []
        prefix = f"{int(task_id)}, "

        for index in range(self.listbox.size()):
            value = str(self.listbox.get(index))
            if value.startswith(prefix):
                match_indices.append(index)

        for index in match_indices:
            self.listbox.selection_set(index)

        if match_indices:
            self.listbox.see(match_indices[0])

    # --------------------------------------------------
    # Highlight attachments belonging to multiple tasks
    # --------------------------------------------------
    def highlight_all_tasks_attachments(self, task_ids: set[int]) -> None:
        attachments_listbox = self.get_files_listbox()
        # Clear once at the start
        attachments_listbox.selection_clear(0, tk.END)
        
        for index, file_item in enumerate(self.listbox.get(0, tk.END)):
            # Check if file belongs to any of the linked tasks
            if str(file_item).startswith(tuple(f"{int(task_id)}, " for task_id in task_ids)):
                attachments_listbox.selection_set(index)

    # Remove all attachment rows from the list.
    def clear(self) -> None:
        self.listbox.delete(0, tk.END)
        self.set_empty_state()

    # Display the empty-state message for the files list.
    def set_empty_state(self, message: str | None = None) -> None:
        self.state_label.config(
            text=message or "No attachments yet. Upload a file from a task to see it here.",
        )

    # Update the attachment count shown below the list.
    def update_state_message(self, item_count: int) -> None:
        if item_count <= 0:
            self.set_empty_state()
            return

        self.state_label.config(text=f"{item_count} attachment{'s' if item_count != 1 else ''} loaded")

    # Return the multiple-selection checkbox value.
    def get_checkVar(self) -> int:
        return self.checkVar.get()

    # Apply the selected single or multiple selection mode.
    def on_select_mod_change(self) -> None:
        if self.get_checkVar() == 1:
            self.select_mode = tk.EXTENDED
        else:
            self.select_mode = tk.SINGLE
        self.listbox.config(selectmode=self.select_mode)
