import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from functools import partial
from ttkthemes import ThemedTk
from tkinter import filedialog
import os

# Function to add task to the list
def add_task(task_entry, tasks_listbox):
    task = task_entry.get().strip()
    if task:
        tasks_listbox.insert(tk.END, task)
        task_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Input Error", "Please enter a task.")

# Function to delete selected task
def delete_task(tasks_listbox):
    selected = tasks_listbox.curselection()
    if not selected:
        messagebox.showwarning("Selection Error", "Please select a task to delete.")
        return
    # curselection() returns a tuple of indices (strings), take the first
    tasks_listbox.delete(int(selected[0]))

# Function to open file dialog and select a file
def select_file(files_listbox):
    filepath = filedialog.askopenfilename(
        initialdir=os.path.expanduser("~"),
        title="Select a file",
        filetypes=(("Text files", "*.txt"), ("JPG files", "*.jpg"),
            ("PNG files", "*.png"), ("All files", "*.*"))
    )
    if filepath:
        print(f"Selected file: {filepath}")
        files_listbox.insert(tk.END, filepath)

def main():
    # Create main window
    #window = tk.Tk()
    window = ThemedTk(theme="scidgreen")
    window.title("To-Do List App")
    window.geometry("500x300")
    #win_frame = ttk.Frame(window, padding="10")

    # Create and place widgets
    task_entry = ttk.Entry(window, width=40)
    task_entry.grid(row=0, column=0, padx=10, pady=10)

    # Listbox to display tasks
    tasks_listbox = tk.Listbox(window, width=30, height=10, selectmode=tk.SINGLE)
    tasks_listbox.grid(row=2, column=0, columnspan=1, padx=10, pady=10)
    # Listbox to display selected files
    selected_files_listbox = tk.Listbox(window, width=30, height=10, selectmode=tk.SINGLE)
    selected_files_listbox.grid(row=2, column=2, columnspan=1, padx=10, pady=10)

    # Test scrollbar code
    tasks_listbox.insert(tk.END, *(f"Element {i}" for i in range(100)))

    # Link a scrollbar to a list
    v_scrollbar = ttk.Scrollbar(
        window,
        orient=tk.VERTICAL,
        command=tasks_listbox.yview)
    v_scrollbar.grid(row=2, column=1, sticky="ns")
    tasks_listbox.configure(yscrollcommand=v_scrollbar.set)
    #tasks_listbox['yscrollcommand'] = v_scrollbar.set

    # Pre-defined button commands with partial
    add_task_command = partial(add_task, task_entry, tasks_listbox)
    upload_task_command = partial(select_file, selected_files_listbox)
    delete_task_command = partial(delete_task, tasks_listbox)
    
    # Create buttons
    # Add task button
    #add_button = tk.Button(window, text="Add Task", width=20, command=lambda: add_task(task_entry, listbox))
    #add_button.grid(row=0, column=1, padx=10, pady=10)
    add_button = ttk.Button(window, text="Add Task", width=20, command=add_task_command)
    add_button.grid(row=0, column=1, padx=10, pady=10)
    # Upload files button
    upload_button = ttk.Button(window, text="Upload Files", width=20, command=upload_task_command)
    upload_button.grid(row=1, column=0, pady=10)
    # Delete task button
    delete_button = ttk.Button(window, text="Delete Task", width=20, command=delete_task_command)
    delete_button.grid(row=1, column=1, columnspan=2, pady=10)

    # Config column weights for responsiveness
    window.grid_columnconfigure(0, weight=1)
    window.grid_columnconfigure(1, weight=1)
    window.grid_columnconfigure(2, weight=1)
    
    # Run the app
    window.mainloop()

if __name__ == "__main__":
    main()
