import tkinter as tk

class PlaceholderEntry(tk.Entry):
    """An Entry widget that displays placeholder text when it is empty."""

    def __init__(self, master=None, placeholder="Enter text...", color="gray", **kwargs):
        """Initialize the entry and configure its placeholder behavior."""
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

        self._add_placeholder()

    def _add_placeholder(self, event=None):
        """Display the placeholder when the entry is empty."""
        if not super().get():
            self.insert(0, self.placeholder)
            self['fg'] = self.placeholder_color

    def _clear_placeholder(self, event=None):
        """Remove the placeholder when the entry receives focus."""
        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg_color

    def get(self):
        """Return an empty string when the entry contains only its placeholder."""
        current_text = super().get()
        if current_text == self.placeholder and self['fg'] == self.placeholder_color:
            return ""
        return current_text
