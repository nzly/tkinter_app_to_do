import sqlite3
import tomllib # Use 'import toml' if using the external toml library
import logging
from pathlib import Path
from datetime import datetime
from objects.data_objects import TaskItem

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

def _row_to_task_item(row: sqlite3.Row) -> TaskItem:
    raw_priority = row["priority"]
    try:
        priority = int(raw_priority)
    except (TypeError, ValueError):
        priority = 3
    if priority not in (1, 2, 3):
        priority = 3

    return TaskItem(
        task_id=int(row["id"]),
        task_name=row["task_name"],
        is_completed=bool(row["is_completed"]),
        creation_date=row["creation_date"] or "",
        due_date=row["due_date"] or "",
        priority=priority,
        notes=row["notes"] or "",
    )


def insert_task(db_path: str, task_item: TaskItem) -> TaskItem:
    """Inserts a TaskItem into tasks table and returns it with generated task_id."""
    creation_date = task_item.creation_date or datetime.now().date().isoformat()
    next_id = get_next_task_id(db_path)
    priority = int(task_item.priority)
    if priority not in (1, 2, 3):
        raise ValueError("Priority must be 1 (highest), 2, or 3 (lowest).")

    insert_sql = (
        "INSERT INTO tasks (id, task_name, creation_date, due_date, priority, is_completed, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            insert_sql,
            (
                next_id,
                task_item.task_name,
                creation_date,
                task_item.due_date,
                priority,
                int(task_item.is_completed),
                task_item.notes,
            ),
        )
        conn.commit()

    return TaskItem(
        task_id=next_id,
        task_name=task_item.task_name,
        is_completed=task_item.is_completed,
        creation_date=creation_date,
        due_date=task_item.due_date,
        priority=priority,
        notes=task_item.notes,
    )


def get_next_task_id(db_path: str) -> int:
    """Returns the next task ID based on current max(id) in tasks table."""
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM tasks")
        row = cursor.fetchone()
    return int(row[0]) if row else 1


def delete_task_by_id(db_path: str, task_id: int) -> bool:
    """Deletes a task by id. Returns True when a row is deleted."""
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_task_priority_status(db_path: str, task_id: int, priority: int, is_completed: bool) -> bool:
    """Updates task priority and completion status by task id."""
    try:
        normalized_priority = int(priority)
    except (TypeError, ValueError):
        return False

    if normalized_priority not in (1, 2, 3):
        return False

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute(
            "UPDATE tasks SET priority = ?, is_completed = ? WHERE id = ?",
            (normalized_priority, int(bool(is_completed)), int(task_id)),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_tasks(db_path: str) -> list[TaskItem]:
    """Retrieves all tasks from database and maps each row to TaskItem."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM tasks ORDER BY id")
        rows = cursor.fetchall()
    return [_row_to_task_item(row) for row in rows]


def get_tasks_by_order(db_path: str, order_by_due_date: str = "asc") -> list[TaskItem]:
    """Retrieves all tasks ordered by due_date in ascending or descending order."""
    order = (order_by_due_date or "asc").strip().lower()
    if order not in ("asc", "desc"):
        raise ValueError("order_by_due_date must be 'asc' or 'desc'.")

    sql = f"SELECT * FROM tasks ORDER BY due_date {order.upper()}, id ASC"
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
    return [_row_to_task_item(row) for row in rows]

if __name__ == "__main__":
    try:
        app_config = get_config()
        db_path = app_config.get("database_path", "data/app.db")
    except Exception:
        logger.exception("Failed to load config; using default DB path.")
        db_path = "data/app.db"

    init_db(db_path)
    created = insert_task(
        db_path,
        TaskItem(
            task_id=0,
            task_name="Sample task",
            is_completed=False,
            creation_date=datetime.now().date().isoformat(),
            due_date="",
            priority=2,
            notes="Created from db.py main",
        ),
    )
    print(f"Inserted task id: {created.task_id}")
    print("\nAll tasks:")
    for row in get_tasks(db_path):
        print(row)
