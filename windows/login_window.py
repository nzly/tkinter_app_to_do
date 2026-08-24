import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from objects.logger import get_logger

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.db import verify_login

# Make ttkthemes optional, matching app.py's fallback behavior.
try:
    from ttkthemes import ThemedTk
    _USE_THEMED = True
except ImportError:
    ThemedTk = None
    _USE_THEMED = False


# Configure the styles used by the login form.
def _configure_login_styles(root: tk.Misc) -> None:
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("Login.TFrame", background="#f4f7fb")
    style.configure("LoginCard.TFrame", background="#ffffff")

    style.configure(
        "LoginTitle.TLabel",
        background="#ffffff",
        foreground="#1f2937",
        font=("Bahnschrift", 18, "bold"),
    )
    style.configure(
        "LoginSubtitle.TLabel",
        background="#ffffff",
        foreground="#64748b",
        font=("Bahnschrift", 10),
    )
    style.configure(
        "LoginField.TLabel",
        background="#ffffff",
        foreground="#1f2937",
        font=("Bahnschrift", 10),
    )
    style.configure(
        "LoginError.TLabel",
        background="#ffffff",
        foreground="#dc2626",
        font=("Bahnschrift", 9),
    )

    style.configure(
        "Login.TEntry",
        fieldbackground="#f8fafc",
        bordercolor="#cbd5e1",
        lightcolor="#cbd5e1",
        darkcolor="#cbd5e1",
        relief="flat",
        borderwidth=1,
        padding=(8, 6),
    )
    style.map(
        "Login.TEntry",
        bordercolor=[("focus", "#0f766e")],
        lightcolor=[("focus", "#0f766e")],
        darkcolor=[("focus", "#0f766e")],
    )

    style.configure(
        "LoginAccent.TButton",
        font=("Bahnschrift", 10, "bold"),
        padding=(12, 8),
        relief="flat",
        borderwidth=0,
        foreground="#ffffff",
        background="#0f766e",
    )
    style.map(
        "LoginAccent.TButton",
        background=[("active", "#0d5f5a"), ("pressed", "#0a4f4b"), ("disabled", "#7aa9a5")],
    )

    style.configure(
        "LoginGhost.TButton",
        font=("Bahnschrift", 9),
        padding=(0, 0),
        relief="flat",
        borderwidth=0,
        foreground="#0f766e",
        background="#ffffff",
    )
    style.map(
        "LoginGhost.TButton",
        foreground=[("active", "#0d5f5a")],
        background=[("active", "#ffffff")],
    )


# Display a modern login dialog and validate credentials against the users table.
def show_login_window(db_path: str) -> int | None:
    if _USE_THEMED and ThemedTk is not None:
        root = ThemedTk(theme="scidgreen")
    else:
        root = tk.Tk()

    root.title("EasyNotes - Sign In")
    root.geometry("420x480")
    root.resizable(False, False)
    root.configure(bg="#f4f7fb")
    _configure_login_styles(root)

    authenticated_user_id: dict[str, int | None] = {"value": None}
    show_password = tk.BooleanVar(value=False)

    outer_frame = ttk.Frame(root, style="Login.TFrame", padding=24)
    outer_frame.pack(fill="both", expand=True)

    card = ttk.Frame(outer_frame, style="LoginCard.TFrame", padding=(28, 32))
    card.pack(fill="both", expand=True)

    title_label = ttk.Label(card, text="Welcome back", style="LoginTitle.TLabel")
    title_label.pack(anchor="w")

    subtitle_label = ttk.Label(
        card,
        text="Sign in to continue to EasyNotes.",
        style="LoginSubtitle.TLabel",
    )
    subtitle_label.pack(anchor="w", pady=(2, 24))

    username_label = ttk.Label(card, text="Username", style="LoginField.TLabel")
    username_label.pack(anchor="w")

    username_entry = ttk.Entry(card, style="Login.TEntry", font=("Bahnschrift", 10))
    username_entry.pack(fill="x", pady=(4, 16))
    username_entry.focus_set()

    password_label = ttk.Label(card, text="Password", style="LoginField.TLabel")
    password_label.pack(anchor="w")

    password_entry = ttk.Entry(card, style="Login.TEntry", font=("Bahnschrift", 10), show="\u2022")
    password_entry.pack(fill="x", pady=(4, 4))

    # Toggle password visibility between hidden and plain text.
    def toggle_password_visibility() -> None:
        password_entry.config(show="" if show_password.get() else "\u2022")

    show_password_check = ttk.Checkbutton(
        card,
        text="Show password",
        variable=show_password,
        command=toggle_password_visibility,
    )
    show_password_check.pack(anchor="w", pady=(0, 16))

    error_label = ttk.Label(card, text="", style="LoginError.TLabel", wraplength=320)
    error_label.pack(anchor="w", pady=(0, 8))

    # Validate the entered credentials and close the window on success.
    def attempt_login(event=None) -> None:
        username = username_entry.get().strip()
        password = password_entry.get()

        if not username or not password:
            error_label.config(text="Please enter both username and password.")
            return

        login_button.config(state="disabled")
        root.update_idletasks()
        try:
            user_id = verify_login(db_path, username, password)
        finally:
            login_button.config(state="normal")

        if user_id is None:
            error_label.config(text="Invalid username or password.")
            password_entry.delete(0, tk.END)
            get_logger().warning("Failed login attempt for username: %s", username)
            return

        authenticated_user_id["value"] = user_id
        get_logger().info("User ID %s logged in successfully.", authenticated_user_id["value"])
        root.destroy()

    # If user clicks the window 'X' button without logging in
    def on_close() -> None:
        authenticated_user_id["value"] = None
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)

    # Login button triggers the attempt_login function when clicked.
    login_button = ttk.Button(
        card,
        text="Sign In",
        style="LoginAccent.TButton",
        command=attempt_login,
    )
    login_button.pack(fill="x", pady=(8, 0))

    root.bind("<Return>", attempt_login)

    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    root.mainloop()

    return authenticated_user_id["value"]
