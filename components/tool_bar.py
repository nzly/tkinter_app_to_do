import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


class ToolBar(ttk.Frame):
	"""Action toolbar for creating, saving, and flagging notes items."""

	def __init__(
		self,
		parent: tk.Misc,
		on_new_event: Callable[[], None],
		on_new_task: Callable[[], None],
		on_export: Callable[[], None],
		on_refresh: Callable[[], None],
		**kwargs,
	) -> None:
		super().__init__(parent, **kwargs)

		actions = (
			("\u002b New Event", on_new_event),
			("\u002b New Task", on_new_task),
			("\U0001f4be Export CSV", on_export),
			("\u21bb Refresh", on_refresh),
		)

		for column, (label, command) in enumerate(actions):
			self.grid_columnconfigure(column, weight=1)
			ttk.Button(
				self,
				text=label,
				command=command,
				style="Modern.TButton",
			).grid(row=0, column=column, padx=(0, 8) if column < len(actions) - 1 else 0, sticky="ew")
