import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from functools import partial
from ttkthemes import ThemedTk
from tkinter import filedialog

# Function to add task to the list
def add_task(task_entry, tasks_listbox):
    task = task_entry.get()
    if task != "":
        tasks_listbox.insert(tk.END, task)
        task_entry.delete(0, tk.END)
    else:
        messagebox.showwarning("Input Error", "Please enter a task.")

# Function to delete selected task
def delete_task(tasks_listbox):
    try:
        selected_task_index = tasks_listbox.curselection()
        tasks_listbox.delete(selected_task_index)
    except:
        messagebox.showwarning("Selection Error", "Please select a task to delete.")

# Function to open file dialog and select a file
def select_file(files_listbox):
    filepath = filedialog.askopenfilename(
        initialdir="/",
        title="Select a file",
        filetypes=(("Text files", "*.txt"), ("JPG files", "*.jpg"),
            ("PNG files", "*.png"), ("All files", "*.*"))
    )
    if filepath:
        #messagebox.showwarning("Selected File", filepath)
        print(f"Selected file: {filepath}")
        files_listbox.insert(tk.END, filepath)

def main():
    # Create main window
    #window = tk.Tk()
    window = ThemedTk(theme="scidgreen")
    window.title("To-Do List App")
    window.geometry("500x300")

    # Create and place widgets
    task_entry = ttk.Entry(window, width=40)
    task_entry.grid(row=0, column=0, padx=10, pady=10)

    # Listbox to display tasks
    tasks_listbox = tk.Listbox(window, width=30, height=10, selectmode=tk.SINGLE)
    tasks_listbox.grid(row=2, column=0, columnspan=1, padx=10, pady=10)
    # Listbox to display selected files
    selected_files_listbox = tk.Listbox(window, width=30, height=10, selectmode=tk.SINGLE)
    selected_files_listbox.grid(row=2, column=1, columnspan=1, padx=10, pady=10)

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

    # Run the app
    window.mainloop()

if __name__ == "__main__":
    main()
