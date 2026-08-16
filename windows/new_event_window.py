import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Callable

from db.db import get_next_event_id, get_tasks, insert_event
from objects.data_objects import EventItem


DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"
DISPLAY_DATE_TIME_FORMAT = "%d %b %Y, %I:%M %p"


def _parse_date_time(value: str) -> datetime | None:
	try:
		return datetime.strptime(value.strip(), DATE_TIME_FORMAT)
	except ValueError:
		return None


def _format_date_time_for_display(value: str) -> str:
	parsed_value = datetime.fromisoformat(value)
	return parsed_value.strftime(DISPLAY_DATE_TIME_FORMAT)


def open_add_event_window(
	parent: tk.Tk,
	db_path: str,
	on_event_created: Callable[[EventItem], None] | None = None,
) -> None:
	add_window = tk.Toplevel(parent)
	add_window.title("Add Event")
	add_window.geometry("520x650")
	add_window.minsize(520, 650)
	add_window.transient(parent)

	container = ttk.Frame(add_window, padding=12)
	container.grid(row=0, column=0, sticky="nsew")
	container.grid_columnconfigure(1, weight=1)

	event_id_entry = ttk.Entry(container, width=36, state="readonly")
	title_entry = ttk.Entry(container, width=36)
	start_at_entry = ttk.Entry(container, width=36)
	end_at_entry = ttk.Entry(container, width=36)
	location_entry = ttk.Entry(container, width=36)
	all_day_var = tk.IntVar(value=0)
	task_items = [task_item for task_item in get_tasks(db_path) if not task_item.is_completed]

	labels_and_widgets = [
		("Event ID", event_id_entry),
		("Title *", title_entry),
		("Start (YYYY-MM-DD HH:MM) *", start_at_entry),
		("End (YYYY-MM-DD HH:MM) *", end_at_entry),
		("Location", location_entry),
	]
	for row_index, (label_text, widget) in enumerate(labels_and_widgets):
		ttk.Label(container, text=label_text).grid(
			row=row_index,
			column=0,
			padx=8,
			pady=6,
			sticky="w",
		)
		widget.grid(row=row_index, column=1, padx=8, pady=6, sticky="ew")

	ttk.Label(container, text="Linked Tasks").grid(row=5, column=0, padx=8, pady=6, sticky="nw")
	task_listbox = tk.Listbox(
		container,
		selectmode=tk.MULTIPLE,
		height=5,
		exportselection=False,
	)
	task_listbox.grid(row=5, column=1, padx=(8, 0), pady=6, sticky="ew")
	task_listbox_scrollbar = ttk.Scrollbar(
		container,
		orient="vertical",
		command=task_listbox.yview,
	)
	task_listbox_scrollbar.grid(row=5, column=2, padx=(0, 8), pady=6, sticky="ns")
	task_listbox.configure(yscrollcommand=task_listbox_scrollbar.set)
	for task_item in task_items:
		due_date = task_item.due_date or "No due date"
		task_listbox.insert(tk.END, f"{task_item.task_id}: {task_item.task_name} (Due: {due_date})")

	all_day_check = ttk.Checkbutton(container, text="All-day event", variable=all_day_var)
	all_day_check.grid(row=6, column=1, padx=8, pady=6, sticky="w")

	ttk.Label(container, text="Description").grid(row=7, column=0, padx=8, pady=6, sticky="nw")
	description_text = tk.Text(container, height=7, wrap="word", relief=tk.FLAT, borderwidth=1)
	description_text.grid(row=7, column=1, padx=8, pady=6, sticky="ew")

	def refresh_event_id() -> None:
		event_id_entry.config(state="normal")
		event_id_entry.delete(0, tk.END)
		event_id_entry.insert(0, str(get_next_event_id(db_path)))
		event_id_entry.config(state="readonly")

	def clear_fields() -> None:
		title_entry.delete(0, tk.END)
		start_at_entry.delete(0, tk.END)
		end_at_entry.delete(0, tk.END)
		location_entry.delete(0, tk.END)
		description_text.delete("1.0", tk.END)
		task_listbox.selection_clear(0, tk.END)
		all_day_var.set(0)
		refresh_event_id()
		title_entry.focus_set()

	def on_add() -> None:
		title = title_entry.get().strip()
		start_at = start_at_entry.get().strip()
		end_at = end_at_entry.get().strip()
		start_datetime = _parse_date_time(start_at)
		end_datetime = _parse_date_time(end_at)

		if not title:
			messagebox.showwarning("Input Error", "Event title is required.")
			return
		if start_datetime is None or end_datetime is None:
			messagebox.showwarning(
				"Input Error",
				"Start and end must use the format YYYY-MM-DD HH:MM.",
			)
			return
		if end_datetime <= start_datetime:
			messagebox.showwarning("Input Error", "End time must be after the start time.")
			return
		selected_task_ids = [
			task_items[index].task_id
			for index in task_listbox.curselection()
		]

		event_item = EventItem(
			id=get_next_event_id(db_path),
			title=title,
			start_at=start_datetime.isoformat(timespec="minutes"),
			end_at=end_datetime.isoformat(timespec="minutes"),
			is_all_day=bool(all_day_var.get()),
			description=description_text.get("1.0", tk.END).strip(),
			location=location_entry.get().strip(),
		)

		try:
			saved_event = insert_event(db_path, event_item, task_ids=selected_task_ids)
		except (OSError, ValueError) as exc:
			messagebox.showerror("Add Event Error", f"Could not save event: {exc}")
			return

		if on_event_created is not None:
			on_event_created(saved_event)
		messagebox.showinfo(
			"Success",
			(
				"Event added successfully.\n\n"
				f"Start: {_format_date_time_for_display(saved_event.start_at)}\n"
				f"End: {_format_date_time_for_display(saved_event.end_at)}"
			),
		)
		clear_fields()

	button_row = ttk.Frame(container)
	button_row.grid(row=8, column=0, columnspan=2, padx=8, pady=(12, 0), sticky="ew")
	button_row.grid_columnconfigure(0, weight=1)
	button_row.grid_columnconfigure(1, weight=1)

	ttk.Button(button_row, text="Cancel", command=add_window.destroy).grid(
		row=0,
		column=0,
		padx=(0, 6),
		sticky="ew",
	)
	ttk.Button(button_row, text="Add", command=on_add).grid(
		row=0,
		column=1,
		padx=(6, 0),
		sticky="ew",
	)

	add_window.grid_rowconfigure(0, weight=1)
	add_window.grid_columnconfigure(0, weight=1)
	refresh_event_id()
	title_entry.focus_set()
