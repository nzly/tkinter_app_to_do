import tkinter as tk
import math
import time
from datetime import datetime
from tkinter import ttk

from db.db import get_events, get_tasks, get_user_profile
from supabase_client.license_client import get_cached_license_info


# Build the activity statistics shown in the profile from the user's tasks and events.
def _build_stats(db_path: str, user_id: int) -> dict[str, object]:
    tasks = get_tasks(db_path, user_id=user_id)
    events = get_events(db_path, user_id=user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    completed = sum(1 for t in tasks if t.is_completed)
    overdue = sum(1 for t in tasks if not t.is_completed and t.due_date and t.due_date[:10] < today)
    due_today = sum(1 for t in tasks if not t.is_completed and t.due_date[:10] == today)
    upcoming = sum(1 for e in events if e.start_at.replace("T", " ")[:16] >= now)
    total = len(tasks)
    rate = f"{round(completed * 100 / total)}%" if total else "-"

    return {
        "Total tasks": total,
        "Completed tasks": completed,
        "Completion rate": rate,
        "Due today": due_today,
        "Overdue tasks": overdue,
        "Total events": len(events),
        "Upcoming events": upcoming,
    }


def _format_license_expiry(expires_at: int | None) -> str:
    if expires_at is None:
        return "-"

    seconds_remaining = max(0, expires_at - time.time())
    if seconds_remaining == 0:
        return "Expired"
    if seconds_remaining < 86400:
        hours_remaining = math.ceil(seconds_remaining / 3600)
        unit = "hour" if hours_remaining == 1 else "hours"
        return f"{hours_remaining} {unit} remaining"

    days_remaining = int(seconds_remaining / 86400)
    unit = "day" if days_remaining == 1 else "days"
    return f"{days_remaining} {unit} remaining"


def _is_account_enabled(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "enabled"}
    return value is True or value == 1


class UserProfileWindow(tk.Toplevel):
    # Layout: profile header / account details / activity / footer.
    def __init__(
        self,
        parent: tk.Misc,
        db_path: str,
        username: str,
        user_id: int,
    ) -> None:
        super().__init__(parent)
        profile = get_user_profile(db_path, user_id) or {}
        stats = _build_stats(db_path, user_id)
        full_name = " ".join(p for p in (profile.get("first_name"), profile.get("last_name")) if p)
        display_name = full_name or username
        email = profile.get("email") or "-"
        enabled = profile.get("enabled")
        license_info = get_cached_license_info()
        if license_info:
            product_key, expires_at = license_info
            masked_product_key = f"****{product_key[-4:]}" if len(product_key) > 4 else "****"
        else:
            masked_product_key = "-"
            expires_at = None

        self.title("User Profile")
        self.geometry("480x660")
        self.minsize(460, 620)
        self.transient(parent)
        self.grab_set()
        self.configure(bg="#f4f6f8")

        style = ttk.Style(self)
        style.configure("Profile.TFrame", background="#f4f6f8")
        style.configure("Profile.TLabel", background="#f4f6f8", foreground="#263445", font=("Segoe UI", 10))
        style.configure("ProfileHeading.TLabel", background="#f4f6f8", foreground="#182433", font=("Segoe UI", 11, "bold"))
        style.configure("ProfileName.TLabel", background="#f4f6f8", foreground="#182433", font=("Segoe UI", 16, "bold"))
        style.configure("ProfileMuted.TLabel", background="#f4f6f8", foreground="#64748b", font=("Segoe UI", 10))

        footer = ttk.Frame(self, padding=(20, 0, 20, 16), style="Profile.TFrame")
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Button(footer, text="Close", command=self.destroy).pack(side=tk.RIGHT)

        outer = ttk.Frame(self, padding=(24, 22, 24, 16), style="Profile.TFrame")
        outer.pack(fill=tk.BOTH, expand=True)

        # Header: circular avatar with the user's initial next to name and status text.
        header = ttk.Frame(outer, style="Profile.TFrame")
        header.pack(fill=tk.X)

        avatar = tk.Canvas(header, width=56, height=56, highlightthickness=0, bg="#f4f6f8")
        avatar.create_oval(2, 2, 54, 54, fill="#2563a6", outline="")
        initial = (username.strip()[:1] or "?").upper()
        avatar.create_text(28, 28, text=initial, fill="white", font=("Segoe UI", 20, "bold"))
        avatar.pack(side=tk.LEFT, padx=(0, 14))

        name_block = ttk.Frame(header, style="Profile.TFrame")
        name_block.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(name_block, text=display_name, style="ProfileName.TLabel").pack(anchor="w")
        ttk.Label(name_block, text=email, style="ProfileMuted.TLabel").pack(anchor="w", pady=(3, 0))

        ttk.Separator(outer).pack(fill=tk.X, pady=(20, 16))

        account_section = ttk.Frame(outer, style="Profile.TFrame")
        account_section.pack(fill=tk.X)
        ttk.Label(account_section, text="ACCOUNT", style="ProfileHeading.TLabel").pack(anchor="w", pady=(0, 8))
        account_rows = ttk.Frame(account_section, style="Profile.TFrame")
        account_rows.pack(fill=tk.X)
        self._fill_rows(
            account_rows,
            [
                ("Username", username),
                ("User ID", user_id),
                ("First name", profile.get("first_name") or "-"),
                ("Last name", profile.get("last_name") or "-"),
                ("Email", email),
                ("Role", profile.get("role", "-")),
                ("Status", "Active" if _is_account_enabled(enabled) else "Disabled"),
                ("Member since", profile.get("created_date") or "-"),
                ("Product key", masked_product_key),
                ("License expires", _format_license_expiry(expires_at)),
            ],
        )

        ttk.Separator(outer).pack(fill=tk.X, pady=(16, 14))

        stats_section = ttk.Frame(outer, style="Profile.TFrame")
        stats_section.pack(fill=tk.X)
        ttk.Label(stats_section, text="ACTIVITY", style="ProfileHeading.TLabel").pack(anchor="w", pady=(0, 8))
        stats_rows = ttk.Frame(stats_section, style="Profile.TFrame")
        stats_rows.pack(fill=tk.X)
        self._fill_rows(stats_rows, list(stats.items()))

        self.bind("<Escape>", lambda _event: self.destroy())

    # Fill a card with "Label: value" rows.
    @staticmethod
    def _fill_rows(card: ttk.Frame, rows: list[tuple[str, object]]) -> None:
        for index, (label_text, value) in enumerate(rows):
            ttk.Label(card, text=label_text, style="ProfileMuted.TLabel").grid(
                row=index, column=0, sticky="w", padx=(0, 16), pady=3
            )
            ttk.Label(card, text=str(value), style="Profile.TLabel").grid(
                row=index, column=1, sticky="w", pady=3
            )
        card.grid_columnconfigure(1, weight=1)


# Open the modal user profile window.
def show_user_profile(parent: tk.Misc, db_path: str, username: str, user_id: int) -> None:
    UserProfileWindow(parent, db_path, username, user_id)
