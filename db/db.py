import sqlite3
import tomllib # Use 'import toml' if using the external toml library
import logging
from pathlib import Path
from datetime import datetime
from objects.data_objects import TaskItem, normalize_task_type

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
            task_time TEXT,
            duration INTEGER,
            priority TEXT,
            is_completed INTEGER DEFAULT 0,
            notes TEXT,
            task_type INTEGER DEFAULT 1,
            repeat_weekdays TEXT,
            repeat_months INTEGER DEFAULT 0,
            repeat_years INTEGER DEFAULT 0
        )
    """
    create_attachments_sql = """
        CREATE TABLE IF NOT EXISTS task_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute(create_sql)
        conn.execute(create_attachments_sql)
        # Backfill new columns for existing databases created before these fields existed.
        existing_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
        }
        if "task_time" not in existing_columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN task_time TEXT")
        if "duration" not in existing_columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN duration INTEGER")
        if "task_type" not in existing_columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN task_type INTEGER DEFAULT 1")
        if "repeat_weekdays" not in existing_columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN repeat_weekdays TEXT")
        if "repeat_months" not in existing_columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN repeat_months INTEGER DEFAULT 0")
        if "repeat_years" not in existing_columns:
            conn.execute("ALTER TABLE tasks ADD COLUMN repeat_years INTEGER DEFAULT 0")
        conn.commit()


def add_task_attachment(db_path: str, task_id: int, file_path: str) -> None:
    """Stores a file path linked to a task."""
    file_name = Path(file_path).name
    created_at = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO task_attachments (task_id, file_path, file_name, created_at) VALUES (?, ?, ?, ?)",
            (int(task_id), file_path, file_name, created_at),
        )
        conn.commit()


def get_task_attachments(db_path: str, task_id: int) -> list[dict]:
    """Returns attachment rows linked to a task."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT id, task_id, file_path, file_name, created_at FROM task_attachments WHERE task_id = ? ORDER BY id ASC",
            (int(task_id),),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def get_all_task_attachments(db_path: str) -> list[dict]:
    """Returns all attachment rows across every task."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT id, task_id, file_path, file_name, created_at FROM task_attachments ORDER BY id ASC"
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


def delete_task_attachments(db_path: str, task_id: int) -> None:
    """Deletes all attachments linked to a task."""
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DELETE FROM task_attachments WHERE task_id = ?", (int(task_id),))
        conn.commit()

def _row_to_task_item(row: sqlite3.Row) -> TaskItem:
    raw_priority = row["priority"]
    try:
        priority = int(raw_priority)
    except (TypeError, ValueError):
        priority = 3
    if priority not in (1, 2, 3):
        priority = 3

    raw_duration = row["duration"]
    try:
        duration = int(float(raw_duration)) if raw_duration is not None else None
    except (TypeError, ValueError):
        duration = None

    return TaskItem(
        task_id=int(row["id"]),
        task_name=row["task_name"],
        is_completed=bool(row["is_completed"]),
        creation_date=row["creation_date"] or "",
        due_date=row["due_date"] or "",
        task_time=(row["task_time"] if "task_time" in row.keys() else None),
        duration=duration,
        priority=priority,
        notes=row["notes"] or "",
        task_type=normalize_task_type(row["task_type"] if "task_type" in row.keys() else 1),
        repeat_weekdays=(row["repeat_weekdays"] if "repeat_weekdays" in row.keys() else None),
        repeat_months=int(row["repeat_months"]) if "repeat_months" in row.keys() and row["repeat_months"] is not None else 0,
        repeat_years=int(row["repeat_years"]) if "repeat_years" in row.keys() and row["repeat_years"] is not None else 0,
    )


def insert_task(db_path: str, task_item: TaskItem) -> TaskItem:
    """Inserts a TaskItem into tasks table and returns it with generated task_id."""
    creation_date = task_item.creation_date or datetime.now().date().isoformat()
    next_id = get_next_task_id(db_path)
    priority = int(task_item.priority)
    if priority not in (1, 2, 3):
        raise ValueError("Priority must be 1 (highest), 2, or 3 (lowest).")

    insert_sql = (
        "INSERT INTO tasks (id, task_name, creation_date, due_date, task_time, duration, priority, is_completed, notes, task_type) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    with sqlite3.connect(str(db_path)) as conn:
        task_time = task_item.task_time or None
        duration = None
        if task_item.duration is not None and str(task_item.duration).strip() != "":
            try:
                duration = int(task_item.duration)
            except (TypeError, ValueError):
                duration = None

        conn.execute(
            insert_sql,
            (
                next_id,
                task_item.task_name,
                creation_date,
                task_item.due_date,
                task_time,
                duration,
                priority,
                int(task_item.is_completed),
                task_item.notes,
                normalize_task_type(task_item.task_type)
            ),
        )
        conn.commit()

    return TaskItem(
        task_id=next_id,
        task_name=task_item.task_name,
        is_completed=task_item.is_completed,
        creation_date=creation_date,
        due_date=task_item.due_date,
        task_time=task_time,
        duration=duration,
        priority=priority,
        notes=task_item.notes,
        task_type=normalize_task_type(task_item.task_type),
        repeat_weekdays=task_item.repeat_weekdays,
        repeat_months=int(task_item.repeat_months or 0),
        repeat_years=int(task_item.repeat_years or 0),
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
        conn.execute("DELETE FROM task_attachments WHERE task_id = ?", (int(task_id),))
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


def update_task(db_path: str, task_item: TaskItem) -> bool:
    """Updates all editable task fields by task id."""
    if int(task_item.task_id) <= 0:
        return False

    task_name = (task_item.task_name or "").strip()
    if not task_name:
        return False

    try:
        priority = int(task_item.priority)
    except (TypeError, ValueError):
        return False

    if priority not in (1, 2, 3):
        return False

    duration = None
    if task_item.duration is not None and str(task_item.duration).strip() != "":
        try:
            duration = int(task_item.duration)
        except (TypeError, ValueError):
            return False

    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET
                task_name = ?,
                creation_date = ?,
                due_date = ?,
                task_time = ?,
                duration = ?,
                priority = ?,
                is_completed = ?,
                notes = ?,
                task_type = ?,
                repeat_weekdays = ?,
                repeat_months = ?,
                repeat_years = ?
            WHERE id = ?
            """,
            (
                task_name,
                (task_item.creation_date or "").strip(),
                (task_item.due_date or "").strip(),
                (task_item.task_time or "").strip() or None,
                duration,
                priority,
                int(bool(task_item.is_completed)),
                (task_item.notes or "").strip(),
                normalize_task_type(task_item.task_type),
                task_item.repeat_weekdays,
                int(task_item.repeat_months or 0),
                int(task_item.repeat_years or 0),
                int(task_item.task_id),
            ),
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
