import sqlite3
import tomllib # Use 'import toml' if using the external toml library
from datetime import datetime

def get_config(config_file="pyproject.toml"):
    """Reads configuration from pyproject.toml."""
    with open(config_file, "rb") as f:
        config = tomllib.load(f) # Use toml.load(f) if using the external toml library
    return config["tool"]["app_config"]

def init_db(db_path):
    """Initializes the SQLite database and creates a table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            creation_date TEXT NOT NULL,
            due_date TEXT,
            priority TEXT,
            is_completed INTEGER DEFAULT 0,
            notes TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_task(db_path, task_name, creation_date):
    """Adds a new task to the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task_name, creation_date) VALUES (?, ?)", (task_name, creation_date))
    conn.commit()
    print(f"Task '{task_name}' added successfully.")
    conn.close()

def get_tasks(db_path):
    """Retrieves all tasks from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    return tasks

if __name__ == "__main__":
    app_config = get_config()
    db_path = app_config["database_path"]

    init_db(db_path)

    add_task(db_path, "Pay bill", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    add_task(db_path, "Go to somewhere", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    add_task(db_path, "Go to appointment", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    print("\nAll tasks:")
    for user in get_tasks(db_path):
        print(user)
