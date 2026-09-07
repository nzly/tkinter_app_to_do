import tkinter as tk

class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="Enter text...", color="gray", **kwargs):
        super().__init__(master, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

        self._add_placeholder()

    def _add_placeholder(self, event=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self['fg'] = self.placeholder_color

    def _clear_placeholder(self, event=None):
        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg_color


# --- Usage Example ---
root = tk.Tk()
root.geometry("350x200")

tk.Label(root, text="Email:").pack(anchor="w", padx=20, pady=(20, 2))
email_entry = PlaceholderEntry(root, placeholder="e.g., user@example.com", width=30)
email_entry.pack(padx=20)

if __name__ == "__main__":
    root.mainloop()