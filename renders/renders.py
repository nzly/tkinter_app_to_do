import tkinter as tk

class ListRender:
    def __init__(self, parent_window):
        self.listbox = tk.Listbox(parent_window)
        self.default_bg = self.listbox.cget("bg")
        self.default_fg = self.listbox.cget("fg")

    def _is_valid_index(self, index) -> bool:
        try:
            return 0 <= int(index) < self.listbox.size()
        except (TypeError, ValueError):
            return False

    def render(self) -> str:
        return "\n".join(self.listbox.get(0, tk.END))
    
    def assign_bg(self, index, color) -> None:
        if not self._is_valid_index(index):
            return
        self.listbox.itemconfig(index, bg=color)
    
    def by_default(self, index) -> None:
        if not self._is_valid_index(index):
            return
        self.listbox.itemconfig(index, bg=self.default_bg, fg=self.default_fg)
    