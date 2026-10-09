import tkinter as tk
from tkinter import ttk
from typing import Optional


class UserProfileWindow(tk.Toplevel):
    # Layout: header (avatar + name) / account details card / optional statistics card / footer.
    def __init__(
        self,
        parent: tk.Misc,
        username: str,
        user_id: int,
        stats: Optional[dict[str, int]] = None,
    ) -> None:
        super().__init__(parent)
        self.title("User Profile")
        self.geometry("420x420")
        self.minsize(420, 360)
        self.transient(parent)
        self.grab_set()
        self.configure(bg="#f4f6f8")

        footer = ttk.Frame(self, padding=(12, 0, 12, 10))
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(footer, text="Close", command=self.destroy).pack(side=tk.RIGHT)

        outer = ttk.Frame(self, padding=(12, 10, 12, 8))
        outer.pack(fill=tk.BOTH, expand=True)

        # Header: circular avatar with the user's initial next to name and status text.
        header = ttk.Frame(outer)
        header.pack(fill=tk.X)

        avatar = tk.Canvas(header, width=64, height=64, highlightthickness=0, bg=self.cget("bg"))
        avatar.create_oval(2, 2, 62, 62, fill="#3b82f6", outline="")
        initial = (username.strip()[:1] or "?").upper()
        avatar.create_text(32, 32, text=initial, fill="white", font=("Bahnschrift", 24, "bold"))
        avatar.pack(side=tk.LEFT, padx=(0, 12))

        name_block = ttk.Frame(header)
        name_block.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(name_block, text=username, font=("Bahnschrift", 14, "bold")).pack(anchor="w")
        ttk.Label(name_block, text="Signed in", font=("Bahnschrift", 9)).pack(anchor="w", pady=(2, 0))

        ttk.Separator(outer).pack(fill=tk.X, pady=10)

        account_card = ttk.LabelFrame(outer, text="Account", padding=8)
        account_card.pack(fill=tk.X)
        self._fill_rows(account_card, [("Username", username), ("User ID", user_id)])

        if stats:
            stats_card = ttk.LabelFrame(outer, text="Statistics", padding=8)
            stats_card.pack(fill=tk.X, pady=(8, 0))
            self._fill_rows(stats_card, list(stats.items()))

        self.bind("<Escape>", lambda _event: self.destroy())

    # Fill a card with "Label: value" rows.
    @staticmethod
    def _fill_rows(card: ttk.LabelFrame, rows: list[tuple[str, object]]) -> None:
        for index, (label_text, value) in enumerate(rows):
            ttk.Label(card, text=f"{label_text}:", font=("Bahnschrift", 9, "bold")).grid(
                row=index, column=0, sticky="w", padx=(0, 8), pady=1
            )
            ttk.Label(card, text=str(value), font=("Bahnschrift", 9)).grid(
                row=index, column=1, sticky="w", pady=1
            )
        card.grid_columnconfigure(1, weight=1)


# Open the modal user profile window.
def show_user_profile(
    parent: tk.Misc,
    username: str,
    user_id: int,
    stats: Optional[dict[str, int]] = None,
) -> None:
    UserProfileWindow(parent, username, user_id, stats)
