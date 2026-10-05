import html
import re
import sys
import tkinter as tk
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any, Callable

# Ensure the parent directory is in sys.path for imports
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.db import insert_event
from objects.data_objects import EventItem
from objects.event_finda.event_finda_objects import EventFindaEvent


# Normalise an Eventfinda timestamp (e.g. "2026-10-05 19:30:00") to the local ISO minute format.
def _to_iso_minutes(value: str) -> str:
    raw_value = (value or "").strip()
    if not raw_value:
        return ""
    try:
        return datetime.fromisoformat(raw_value.replace("T", " ")).isoformat(timespec="minutes")
    except ValueError:
        return raw_value


# Convert an Eventfinda event into a local EventItem ready to be saved.
def _to_event_item(event: EventFindaEvent, created_by_user: int) -> EventItem:
    start_at = _to_iso_minutes(event.start_date)
    end_at = _to_iso_minutes(event.end_date)
    if start_at and not end_at:
        try:
            end_at = (datetime.fromisoformat(start_at) + timedelta(hours=1)).isoformat(timespec="minutes")
        except ValueError:
            end_at = start_at

    description = (event.description or "").strip()
    if event.url:
        description = f"{description}\n\nSource: {event.url}".strip()

    return EventItem(
        id=0,
        title=event.title,
        start_at=start_at,
        end_at=end_at,
        is_all_day=False,
        description=description,
        location=event.location,
        provider="eventfinda",
        external_event_id=str(event.event_id),
        created_by_user=created_by_user,
    )


# Format an Eventfinda timestamp as e.g. "Mon 05 Oct 2026, 07:30 PM".
def _format_date_time(value: Any) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""
    try:
        return datetime.fromisoformat(raw_value.replace("T", " ")).strftime("%a %d %b %Y, %I:%M %p")
    except ValueError:
        return raw_value


# Turn an API key such as "datetime_start" into "Datetime start".
def _humanize_key(key: Any) -> str:
    return str(key).replace("_", " ").strip().capitalize()


# Convert any nested API value into plain, indented, human-readable text.
def _to_readable(value: Any, indent: int = 0) -> str:
    pad = "  " * indent
    if value is None or value == "" or value == [] or value == {}:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if str(key).startswith("@"):
                continue
            text = _to_readable(item, indent + 1)
            if not text:
                continue
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{_humanize_key(key)}:\n{text}")
            else:
                lines.append(f"{pad}{_humanize_key(key)}: {text}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for item in value:
            text = _to_readable(item, 0)
            if not text:
                continue
            first, *rest = text.splitlines()
            lines.append(pad + "\u2022 " + first + "".join(f"\n{pad}  {line}" for line in rest))
        return "\n".join(lines)
    return str(value)


# Remove HTML tags/entities from the description so it reads as plain text.
def _strip_html(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<\s*br\s*/?>|</\s*(p|div|li|h[1-6])\s*>", "\n", text, flags=re.IGNORECASE)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# List each session as one readable line.
def _format_sessions(sessions: Any) -> str:
    items = sessions.get("sessions") if isinstance(sessions, dict) else sessions
    if not isinstance(items, list):
        return _to_readable(sessions)
    lines = []
    for item in items:
        if not isinstance(item, dict):
            continue
        text = item.get("datetime_summary") or " - ".join(
            part for part in (_format_date_time(item.get("datetime_start")), _format_date_time(item.get("datetime_end"))) if part
        )
        if text and item.get("is_cancelled"):
            text += " (Cancelled)"
        if text:
            lines.append(f"\u2022 {text}")
    return "\n".join(lines) or _to_readable(sessions)


# List each ticket type with its price.
def _format_ticket_types(ticket_types: Any) -> str:
    items = ticket_types.get("ticket_types") if isinstance(ticket_types, dict) else ticket_types
    if not isinstance(items, list):
        return _to_readable(ticket_types)
    lines = []
    for item in items:
        if isinstance(item, dict) and item.get("name"):
            price = item.get("price")
            lines.append(f"\u2022 {item['name']}" + (f": {price}" if price not in (None, "") else ""))
    return "\n".join(lines) or _to_readable(ticket_types)


# Show the category by name.
def _format_category(category: Any) -> str:
    if isinstance(category, dict):
        return str(category.get("name") or _to_readable(category))
    return _to_readable(category)


# Show tags as a comma-separated list.
def _format_tags(tags: Any) -> str:
    if not isinstance(tags, list):
        return _to_readable(tags)
    names = [str(tag.get("name", "")) if isinstance(tag, dict) else str(tag) for tag in tags]
    return ", ".join(name for name in names if name)


# Build the (label, readable text) rows shown in the window; empty values are skipped.
def _build_display_rows(event: EventFindaEvent) -> list[tuple[str, str]]:
    address = event.location_data.get("address") if isinstance(event.location_data, dict) else ""
    rows = [
        ("When", event.datetime_summary),
        ("Starts", _format_date_time(event.start_date)),
        ("Ends", _format_date_time(event.end_date)),
        ("Location", event.location),
        ("Address", _to_readable(address)),
        ("Area", event.location_slug.replace("-", " ").title()),
        ("Free event", "Yes" if event.free else "No"),
        ("Category", _format_category(event.category)),
        ("Tags", _format_tags(event.tags)),
        ("Tickets", _format_ticket_types(event.ticket_types)),
        ("Sessions", _format_sessions(event.sessions)),
        ("Website", event.url),
        ("Image", event.image_url),
        ("Listed on", _format_date_time(event.created_at)),
        ("Last updated", _format_date_time(event.updated_at)),
        ("Eventfinda ID", str(event.event_id) if event.event_id else ""),
        ("Description", _strip_html(event.description)),
    ]
    return [(label, value) for label, value in rows if value and value.strip()]


# Open a window showing every Eventfinda field for one event, with Add Event and Close buttons.
def open_selected_event_window(
    parent: tk.Misc,
    event: EventFindaEvent,
    db_path: str,
    created_by_user: int,
    on_event_added: Callable[[EventItem], None] | None = None,
) -> None:
    window = tk.Toplevel(parent)
    window.title(f"Event - {event.title}")
    window.geometry("680x640")
    window.minsize(560, 480)
    window.transient(parent)

    container = ttk.Frame(window, padding=12)
    container.pack(fill=tk.BOTH, expand=True)
    container.grid_columnconfigure(0, weight=1)
    container.grid_rowconfigure(0, weight=1)

    canvas = tk.Canvas(container, highlightthickness=0, bg="#f4f7fb")
    scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    content = ttk.Frame(canvas, padding=(0, 0, 8, 0))
    content_id = canvas.create_window((0, 0), window=content, anchor="nw")
    content.grid_columnconfigure(1, weight=1)

    title_label = ttk.Label(content, text=event.title, font=("Bahnschrift", 14, "bold"), wraplength=560)
    title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

    # One label + read-only text field per piece of event information.
    value_boxes: list[tk.Text] = []
    for row_index, (label, value) in enumerate(_build_display_rows(event), start=1):
        ttk.Label(content, text=label, font=("Bahnschrift", 10, "bold")).grid(
            row=row_index, column=0, sticky="nw", padx=(0, 12), pady=4
        )
        value_box = tk.Text(
            content,
            width=10,
            height=1,
            wrap="word",
            font=("Bahnschrift", 10),
            bg="#ffffff",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground="#d4dde8",
            padx=6,
            pady=4,
        )
        value_box.insert("1.0", value)
        value_box.configure(state="disabled")
        value_box.grid(row=row_index, column=1, sticky="ew", pady=4)
        value_boxes.append(value_box)

    # Grow each text field to show all of its wrapped lines.
    def fit_value_boxes() -> None:
        window.update_idletasks()
        for value_box in value_boxes:
            counted = value_box.count("1.0", "end-1c", "displaylines")
            lines = counted[0] if isinstance(counted, tuple) else counted
            value_box.configure(height=max(1, int(lines or 1)))

    # Keep the content as wide as the canvas and re-fit text when the window is resized.
    def on_canvas_configure(canvas_event: tk.Event) -> None:
        canvas.itemconfigure(content_id, width=canvas_event.width)
        title_label.configure(wraplength=max(canvas_event.width - 40, 200))
        window.after_idle(fit_value_boxes)

    canvas.bind("<Configure>", on_canvas_configure)
    content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    window.bind("<MouseWheel>", lambda wheel_event: canvas.yview_scroll(int(-wheel_event.delta / 120), "units"))

    button_row = ttk.Frame(container)
    button_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
    for column_index in range(3):
        button_row.grid_columnconfigure(column_index, weight=1, uniform="buttons")

    # Save the Eventfinda event into the local events list.
    def add_event() -> None:
        event_item = _to_event_item(event, created_by_user)
        try:
            saved_event = insert_event(db_path, event_item)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Add Event Error", f"Could not add event: {exc}", parent=window)
            return

        add_button.config(state=tk.DISABLED)
        if on_event_added is not None:
            on_event_added(saved_event)
        messagebox.showinfo("Success", "Event added to your events list.", parent=window)

    add_button = ttk.Button(button_row, text="Add Event", style="Orange.TButton", command=add_event)
    add_button.grid(row=0, column=0, padx=(0, 6), sticky="nsew")
    ttk.Button(
        button_row,
        text="Open in Browser",
        style="Green.TButton",
        command=lambda: webbrowser.open(event.url),
        state=tk.NORMAL if event.url else tk.DISABLED,
    ).grid(row=0, column=1, padx=6, sticky="nsew")
    ttk.Button(button_row, text="Close", command=window.destroy).grid(row=0, column=2, padx=(6, 0), sticky="nsew")
