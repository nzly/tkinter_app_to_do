import sqlite3
import tomllib # Use 'import toml' if using the external toml library
import logging
from pathlib import Path
from datetime import datetime

# Get a logger instance, typically named after the current module
logger = logging.getLogger(__name__)

# Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)
logger.setLevel(logging.INFO)

def get_config(config_file="pyproject.toml"):
    """Reads configuration from pyproject.toml."""
    with open(config_file, "rb") as f:
        config = tomllib.load(f) # Use toml.load(f) if using the external toml library
    return config["tool"]["app_config"]

def init_db(db_path):
    """Initializes the SQLite database and creates the tasks table."""
    db_file = Path(db_path)
    if not db_file.parent.exists():
        db_file.parent.mkdir(parents=True, exist_ok=True)

    create_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT NOT NULL,
            creation_date TEXT NOT NULL,
            due_date TEXT,
            priority TEXT,
            is_completed INTEGER DEFAULT 0,
            notes TEXT
        )
    """
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute(create_sql)
        conn.commit()

def add_task(db_path, task_name, creation_date=None):
    """Adds a new task to the database.

    If creation_date is None, the current timestamp (ISO) is used.
    """
    if creation_date is None:
        creation_date = datetime.now().isoformat(sep=" ")

    insert_sql = "INSERT INTO tasks (task_name, creation_date) VALUES (?, ?)"
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(insert_sql, (task_name, creation_date))
        conn.commit()
    logger.debug("Task '%s' added.", task_name)

def get_tasks(db_path):
    """Retrieves all tasks from the database and returns a list of dicts."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM tasks ORDER BY id")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

if __name__ == "__main__":
    try:
        app_config = get_config()
        db_path = app_config.get("database_path", "data/tasks.db")
    except Exception as exc:
        logger.exception("Failed to load config; using default DB path.")
        db_path = "data/tasks.db"

    init_db(db_path)

    add_task(db_path, "Pay bill")
    add_task(db_path, "Go to somewhere")
    add_task(db_path, "Go to appointment")
    add_task(db_path, "Go to dentist")

    print("\nAll tasks:")
    for row in get_tasks(db_path):
        print(row)
