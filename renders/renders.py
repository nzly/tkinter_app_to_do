import tkinter as tk

class ListRender:
    def __init__(self, parent_window=None, listbox=None):
        self.listbox = listbox if listbox is not None else tk.Listbox(parent_window)
        self.default_bg = self.listbox.cget("bg")
        self.default_fg = self.listbox.cget("fg")

    def _is_valid_index(self, index) -> bool:
        try:
            return 0 <= int(index) < self.listbox.size()
        except (TypeError, ValueError):
            return False

    def render(self) -> str:
        return "\n".join(self.listbox.get(0, tk.END))
    
    def assign_bg(self, listbox, index, color) -> None:
        if isinstance(index, (list, tuple, set)):
            for item_index in index:
                if self._is_valid_index(item_index):
                    listbox.itemconfig(item_index, bg=color)
            return

        if not self._is_valid_index(index):
            return
        listbox.itemconfig(index, bg=color)
    
    def by_default(self, index) -> None:
        if not self._is_valid_index(index):
            return
        self.listbox.itemconfig(index, bg=self.default_bg, fg=self.default_fg)
    