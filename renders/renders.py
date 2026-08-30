import tkinter as tk
from tkinter import ttk

# This class is responsible for rendering a listbox and managing its appearance.
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

# This class is responsible for rendering a user button with an emoji label.
class UserUIComponentRender:
    def __init__(self, parent_window=None, label=None):
        self.emoji_label = label if label is not None else ttk.Label(parent_window)

    def get_user_emoji_label(self, user_badge: ttk.Frame) -> str:
        # Large emoji icon label
        emoji_label = ttk.Label(
            user_badge,
            text="🧑",
            font=("Segoe UI Emoji", 12)  # Set a larger font size for the emoji
        )
        emoji_label.pack(side=tk.LEFT, padx=(0, 2))

        return emoji_label