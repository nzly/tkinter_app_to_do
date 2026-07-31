import os
import tkinter as tk
from tkinter import ttk

class FilesListboxFrame(tk.Frame):
    """Frame that contains a Listbox and its Scrollbar with helper methods."""
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(bg="lightblue")

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
            height=1,
            width=20,
            command=self.on_select_mod_change
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
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)

    def get_files_listbox(self) -> tk.Listbox:
        return self.listbox

    def _format_attachment(self, task_id: int, file_path: str) -> str:
        return f"{task_id}, {file_path}"

    # Convenience helpers
    def add_file(self, file: str) -> None:
        self.listbox.insert(tk.END, file)

    def add_attachment(self, task_id: int, file_path: str) -> None:
        self.listbox.insert(tk.END, self._format_attachment(task_id, file_path))

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

    def get_selected_files(self) -> list:
        return [self.listbox.get(int(i)) for i in self.listbox.curselection()]

    def set_files(self, items: list) -> None:
        self.listbox.delete(0, tk.END)
        for it in items:
            self.listbox.insert(tk.END, it)

    def set_attachments(self, attachments: list[dict]) -> None:
        self.listbox.delete(0, tk.END)
        for attachment in attachments:
            self.listbox.insert(
                tk.END,
                self._format_attachment(int(attachment["task_id"]), str(attachment["file_path"])),
            )

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

    def clear(self) -> None:
        self.listbox.delete(0, tk.END)

    def get_checkVar(self) -> int:
        return self.checkVar.get()

    def on_select_mod_change(self) -> None:
        if self.get_checkVar() == 1:
            self.select_mode = tk.EXTENDED
        else:
            self.select_mode = tk.SINGLE
        self.listbox.config(selectmode=self.select_mode)
