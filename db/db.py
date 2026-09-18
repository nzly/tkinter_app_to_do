import os
import sqlite3
import sys
import tomllib # Use 'import toml' if using the external toml library
import hashlib
import hmac
from pathlib import Path
from datetime import datetime
from objects.data_objects import EventItem, FlagItem, TaskItem, normalize_task_type
from objects.logger import get_logger


# Return the project root for both source runs and packaged EXEs.
def _get_project_root() -> Path:
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


# True only for --onefile builds, whose _MEIPASS is a temp dir wiped on exit.
def _is_onefile_temp_extraction() -> bool:
    meipass = getattr(sys, "_MEIPASS", None)
    if not meipass:
        return False
    import tempfile
    return Path(meipass).parent == Path(tempfile.gettempdir())


# Reads configuration from pyproject.toml.
def get_config(config_file=None):
    root = _get_project_root()
    config_path = Path(config_file) if config_file else root / "pyproject.toml"
    if not config_path.is_absolute():
        config_path = root / config_path

    if not config_path.exists():
        return {"tool": {"app_config": {}}}

    with open(config_path, "rb") as f:
        config = tomllib.load(f) # Use toml.load(f) if using the external toml library
    return config.get("tool", {}).get("app_config", {})


# Resolve a SQLite database path that works for source runs and packaged EXEs.
def resolve_db_path() -> str:
    root = _get_project_root()
    onefile_temp = _is_onefile_temp_extraction()
    appdata_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "tkinter_notes_app"
    configured_db = get_config().get("database_path", "")

    candidates: list[Path] = []
    if configured_db:
        configured_path = Path(configured_db)
        if not configured_path.is_absolute():
            configured_path = root / configured_path
        candidates.append(configured_path)

    # --onefile extracts to a temp dir that's wiped on exit, so AppData must win there.
    # --onedir keeps root pointing at the real folder next to the exe, so it stays first.
    if onefile_temp:
        candidates.extend(
            [
                appdata_dir / "data" / "app.db",
                appdata_dir / "app.db",
            ]
        )
    candidates.extend(
        [
            root / "data" / "app.db",
            root / "app.db",
            Path.cwd() / "data" / "app.db",
            Path.cwd() / "app.db",
            appdata_dir / "data" / "app.db",
            appdata_dir / "app.db",
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    fallback_path = appdata_dir / "data" / "app.db" if onefile_temp else root / "data" / "app.db"
    if configured_db:
        configured_path = Path(configured_db)
        if not configured_path.is_absolute():
            configured_path = root / configured_path
        fallback_path = configured_path

    return str(fallback_path)

# Initializes the SQLite database and creates the tasks table.
def init_db(db_path):
    db_file = Path(db_path)
    if not db_file.parent.exists():
        db_file.parent.mkdir(parents=True, exist_ok=True)

    create_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name       TEXT    NOT NULL,
            creation_date   TEXT    NOT NULL,
            due_date        TEXT    NOT NULL,
            task_time       TEXT    DEFAULT NULL,
            duration        INTEGER DEFAULT NULL,
            priority        INTEGER NOT NULL
                                    DEFAULT (3),
            is_completed    INTEGER DEFAULT 0,
            notes           TEXT,
            task_type       INTEGER,
            repeat_weekdays TEXT,
            repeat_months   INTEGER DEFAULT 0,
            repeat_years    INTEGER DEFAULT 0,
            created_by_user BIGINT  DEFAULT (1)
                                    NOT NULL
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
    create_calendar_events_sql = """
        CREATE TABLE IF NOT EXISTS calendar_events (
            id                INTEGER PRIMARY KEY,
            title             TEXT    NOT NULL,
            start_at          TEXT    NOT NULL,
            end_at            TEXT    NOT NULL,
            is_all_day        INTEGER NOT NULL DEFAULT 0,
            description       TEXT,
            location          TEXT,
            provider          TEXT    NOT NULL DEFAULT 'local',
            calendar_id       TEXT,
            external_event_id TEXT,
            sync_status       TEXT    NOT NULL DEFAULT 'local',
            created_at        TEXT    NOT NULL,
            updated_at        TEXT,
            last_synced_at    TEXT,
            created_by_user   BIGINT  NOT NULL DEFAULT (1),
            UNIQUE (
                provider,
                calendar_id,
                external_event_id
            )
        )
    """
    create_event_task_links_sql = """
        CREATE TABLE IF NOT EXISTS event_task_links (
            event_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (event_id, task_id),
            FOREIGN KEY (event_id) REFERENCES calendar_events(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
        )
    """
    create_flags_sql = """
        CREATE TABLE IF NOT EXISTS flags (
            id        INTEGER PRIMARY KEY,
            flag_name TEXT NOT NULL UNIQUE
        )
    """
    create_event_flag_links_sql = """
        CREATE TABLE IF NOT EXISTS event_flag_links (
            event_id INTEGER NOT NULL,
            flag_id  INTEGER NOT NULL,
            PRIMARY KEY (event_id, flag_id),
            FOREIGN KEY (event_id) REFERENCES calendar_events(id) ON DELETE CASCADE,
            FOREIGN KEY (flag_id) REFERENCES flags(id) ON DELETE CASCADE
        )
    """
    create_users_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id           INTEGER PRIMARY KEY AUTOINCREMENT
                                NOT NULL UNIQUE,
            username     TEXT    NOT NULL,
            pass         TEXT    NOT NULL,
            created_date DATE    NOT NULL,
            enabled      BOOLEAN NOT NULL DEFAULT (true),
            role         INTEGER DEFAULT (1) NOT NULL
        )
    """
    with sqlite3.connect(str(db_file)) as conn:
        conn.execute(create_sql)
        conn.execute(create_attachments_sql)
        conn.execute(create_calendar_events_sql)
        conn.execute(create_event_task_links_sql)
        conn.execute(create_flags_sql)
        conn.execute(create_event_flag_links_sql)
        conn.execute(create_users_sql)
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


# Hashes a plaintext password with a random salt for storage.
def hash_password(plain_password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${digest.hex()}"


# Checks a plaintext password against a salted hash produced by hash_password.
def _verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
    except (AttributeError, ValueError):
        return False
    salt = bytes.fromhex(salt_hex)
    expected_digest = bytes.fromhex(digest_hex)
    candidate_digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(candidate_digest, expected_digest)


# Creates a user with a securely hashed password. Returns the new user id.
def create_user(db_path: str, username: str, plain_password: str, role: str = "user") -> int:
    created_date = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute(
            "INSERT INTO users (username, pass, created_date, enabled, role) VALUES (?, ?, ?, 1, ?)",
            (username.strip(), hash_password(plain_password), created_date, role),
        )
        conn.commit()
        return int(cursor.lastrowid)


# Validates login credentials against the users table. Returns the user id on success, else None.
def verify_login(db_path: str, username: str, plain_password: str) -> int | None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, pass, enabled FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()

    if row is None or not row["enabled"]:
        return None
    if not _verify_password(plain_password, row["pass"]):
        return None
    return int(row["id"])


# Stores a file path linked to a task.
def add_task_attachment(db_path: str, task_id: int, file_path: str) -> None:
    file_name = Path(file_path).name
    created_at = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT INTO task_attachments (task_id, file_path, file_name, created_at) VALUES (?, ?, ?, ?)",
            (int(task_id), file_path, file_name, created_at),
        )
        conn.commit()


# Returns attachment rows linked to a task.
def get_task_attachments(db_path: str, task_id: int) -> list[dict]:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT id, task_id, file_path, file_name, created_at FROM task_attachments WHERE task_id = ? ORDER BY id ASC",
            (int(task_id),),
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


# Returns all attachment rows across every task owned by the given user.
def get_all_task_attachments_by_user(db_path: str, userId: int | None) -> list[dict]:
    if userId is None:
        return []
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT att.id as attachment_id, att.task_id, att.file_path, att.file_name, att.created_at, tk.created_by_user "
            "FROM task_attachments att "
            "INNER JOIN tasks tk "
            "ON att.task_id = tk.id "
            "WHERE tk.created_by_user = ? "
            "ORDER BY attachment_id ASC;",
            (int(userId),)
        )
        rows = cursor.fetchall()
    return [dict(row) for row in rows]


# Deletes all attachments linked to a task.
def delete_task_attachments(db_path: str, task_id: int) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DELETE FROM task_attachments WHERE task_id = ?", (int(task_id),))
        conn.commit()

# Converts a sqlite3.Row from the tasks table into a TaskItem.
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


# Inserts a TaskItem into tasks table and returns it with generated task_id.
def insert_task(db_path: str, task_item: TaskItem, event_ids: list[int] | None = None) -> TaskItem:
    creation_date = task_item.creation_date or datetime.now().date().isoformat()
    next_id = get_next_task_id(db_path)
    priority = int(task_item.priority)
    if priority not in (1, 2, 3):
        raise ValueError("Priority must be 1 (highest), 2, or 3 (lowest).")

    insert_sql = (
        "INSERT INTO tasks (id, task_name, creation_date, due_date, task_time, duration, priority, is_completed, notes, task_type, created_by_user) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    created_at = datetime.now().isoformat(timespec="seconds")
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
                normalize_task_type(task_item.task_type),
                int(task_item.created_by_user),
            ),
        )
        # Link the newly created task to any selected events via the bridge table.
        conn.executemany(
            "INSERT INTO event_task_links (event_id, task_id, created_at) VALUES (?, ?, ?)",
            [(int(event_id), next_id, created_at) for event_id in set(event_ids or [])],
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


# Returns the next task ID based on current max(id) in tasks table.
def get_next_task_id(db_path: str) -> int:
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM tasks")
        row = cursor.fetchone()
    return int(row[0]) if row else 1


# Return the next local calendar event identifier.
def get_next_event_id(db_path: str) -> int:
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute("SELECT COALESCE(MAX(id), 0) + 1 AS next_id FROM calendar_events")
        row = cursor.fetchone()
    return int(row[0]) if row else 1


# Persist a calendar event and return it with its local identifier.
def insert_event(
    db_path: str,
    event_item: EventItem,
    task_ids: list[int] | None = None,
) -> EventItem:
    title = (event_item.title or "").strip()
    start_at = (event_item.start_at or "").strip()
    end_at = (event_item.end_at or "").strip()
    created_by_user = int(event_item.created_by_user) if event_item.created_by_user is not None else 1
    if created_by_user <= 0:
        raise ValueError("created_by_user must be a positive integer.")
    if not title or not start_at or not end_at:
        raise ValueError("Event title, start time, and end time are required.")

    event_id = get_next_event_id(db_path)
    created_at = event_item.created_at or datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO calendar_events (
                id, title, start_at, end_at, is_all_day,
                description, location, provider, calendar_id, external_event_id,
                sync_status, created_at, updated_at, last_synced_at, created_by_user
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                title,
                start_at,
                end_at,
                int(bool(event_item.is_all_day)),
                (event_item.description or "").strip(),
                (event_item.location or "").strip(),
                (event_item.provider or "local").strip(),
                (event_item.calendar_id or "").strip(),
                event_item.external_event_id,
                (event_item.sync_status or "local").strip(),
                created_at,
                (event_item.updated_at or "").strip() or None,
                (event_item.last_synced_at or "").strip() or None,
                created_by_user,
            ),
        )
        conn.executemany(
            "INSERT INTO event_task_links (event_id, task_id, created_at) VALUES (?, ?, ?)",
            [(event_id, int(task_id), created_at) for task_id in set(task_ids or [])],
        )
        conn.commit()

    event_item.id = event_id
    event_item.created_at = created_at
    return event_item


# Return task IDs linked to one event through the bridge table.
def get_event_task_ids(db_path: str, event_id: int) -> list[int]:
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            """
            SELECT task_id
            FROM event_task_links
            WHERE event_id = ?
            ORDER BY task_id
            """,
            (int(event_id),),
        ).fetchall()
    return [int(row[0]) for row in rows]


# Return every available flag type ordered by its identifier.
def get_flags(db_path: str) -> list[FlagItem]:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, flag_name FROM flags ORDER BY id ASC"
        ).fetchall()
    return [FlagItem(id=int(row["id"]), flag_name=row["flag_name"] or "") for row in rows]


# Return the flags assigned to one event.
def get_event_flags(db_path: str, event_id: int) -> list[FlagItem]:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT flags.id, flags.flag_name
            FROM event_flag_links
            INNER JOIN flags ON flags.id = event_flag_links.flag_id
            WHERE event_flag_links.event_id = ?
            ORDER BY flags.flag_name COLLATE NOCASE ASC
            """,
            (int(event_id),),
        ).fetchall()
    return [FlagItem(id=int(row["id"]), flag_name=row["flag_name"] or "") for row in rows]


# Assign a flag to an event. Duplicate assignments are ignored.
def add_event_flag(db_path: str, event_id: int, flag_id: int) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO event_flag_links (event_id, flag_id) VALUES (?, ?)",
            (int(event_id), int(flag_id)),
        )
        conn.commit()


# Remove one flag assignment from an event.
def remove_event_flag(db_path: str, event_id: int, flag_id: int) -> bool:
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute(
            "DELETE FROM event_flag_links WHERE event_id = ? AND flag_id = ?",
            (int(event_id), int(flag_id)),
        )
        conn.commit()
    return cursor.rowcount > 0


# Update an event and optionally replace its linked task IDs.
def update_event(db_path: str, event_item: EventItem, task_ids: list[int] | None = None) -> bool:
    title = (event_item.title or "").strip()
    start_at = (event_item.start_at or "").strip()
    end_at = (event_item.end_at or "").strip()
    if not title or not start_at or not end_at or int(event_item.id) <= 0:
        return False

    updated_at = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(str(db_path)) as conn:
        cursor = conn.execute(
            """
            UPDATE calendar_events
            SET title = ?, start_at = ?, end_at = ?, is_all_day = ?,
                description = ?, location = ?, provider = ?, calendar_id = ?,
                external_event_id = ?, sync_status = ?, updated_at = ?,
                last_synced_at = ?
            WHERE id = ?
            """,
            (
                title,
                start_at,
                end_at,
                int(bool(event_item.is_all_day)),
                (event_item.description or "").strip(),
                (event_item.location or "").strip(),
                (event_item.provider or "local").strip(),
                (event_item.calendar_id or "").strip(),
                event_item.external_event_id,
                (event_item.sync_status or "local").strip(),
                updated_at,
                (event_item.last_synced_at or "").strip() or None,
                int(event_item.id),
            ),
        )
        if cursor.rowcount == 0:
            return False

        if task_ids is not None:
            conn.execute("DELETE FROM event_task_links WHERE event_id = ?", (int(event_item.id),))
            conn.executemany(
                "INSERT INTO event_task_links (event_id, task_id, created_at) VALUES (?, ?, ?)",
                [
                    (int(event_item.id), int(task_id), updated_at)
                    for task_id in set(task_ids)
                ],
            )
        conn.commit()
    event_item.updated_at = updated_at
    return True


# Delete an event and its bridge-table links.
def delete_event_by_id(db_path: str, event_id: int) -> bool:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DELETE FROM event_task_links WHERE event_id = ?", (int(event_id),))
        conn.execute("DELETE FROM event_flag_links WHERE event_id = ?", (int(event_id),))
        cursor = conn.execute("DELETE FROM calendar_events WHERE id = ?", (int(event_id),))
        conn.commit()
    return cursor.rowcount > 0


# Retrieve calendar events ordered by start time and local ID.
def get_events(db_path: str, user_id: int | None = None) -> list[EventItem]:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT id, title, start_at, end_at, is_all_day, description,
                   location, provider, calendar_id, external_event_id,
                   sync_status, created_at, updated_at, last_synced_at
            FROM calendar_events
            WHERE (? IS NULL OR created_by_user = ?)
            ORDER BY start_at ASC, id ASC
            """
        , (user_id, user_id)
        ).fetchall()

    return [
        EventItem(
            id=int(row["id"]),
            title=row["title"] or "",
            start_at=row["start_at"] or "",
            end_at=row["end_at"] or "",
            is_all_day=bool(row["is_all_day"]),
            description=row["description"] or "",
            location=row["location"] or "",
            provider=row["provider"] or "local",
            calendar_id=row["calendar_id"] or "",
            external_event_id=row["external_event_id"],
            sync_status=row["sync_status"] or "local",
            created_at=row["created_at"] or "",
            updated_at=row["updated_at"] or "",
            last_synced_at=row["last_synced_at"] or "",
        )
        for row in rows
    ]


# Deletes a task by id. Returns True when a row is deleted.
def delete_task_by_id(db_path: str, task_id: int) -> bool:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DELETE FROM task_attachments WHERE task_id = ?", (int(task_id),))
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0


# Updates task priority and completion status by task id.
def update_task_priority_status(db_path: str, task_id: int, priority: int, is_completed: bool) -> bool:
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


# Updates all editable task fields by task id.
def update_task(db_path: str, task_item: TaskItem) -> bool:
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


# Retrieves all tasks from database and maps each row to TaskItem.
def get_tasks(db_path: str, user_id: int | None = None) -> list[TaskItem]:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM tasks " \
        "WHERE (? IS NULL OR created_by_user = ?)" \
        "ORDER BY id", (user_id, user_id))
        rows = cursor.fetchall()
    return [_row_to_task_item(row) for row in rows]


# Retrieves all tasks ordered by due_date in ascending or descending order.
def get_tasks_by_order(db_path: str, order_by_due_date: str = "asc") -> list[TaskItem]:
    order = (order_by_due_date or "asc").strip().lower()
    if order not in ("asc", "desc"):
        raise ValueError("order_by_due_date must be 'asc' or 'desc'.")

    sql = f"SELECT * FROM tasks ORDER BY due_date {order.upper()}, id ASC"
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
    return [_row_to_task_item(row) for row in rows]

# Add this inside db/db.py if not already present
def get_username_by_id(db_path: str, user_id: int) -> str | None:
    """Fetch username for a given user ID."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    try:
        db_path = resolve_db_path()
    except Exception:
        get_logger().exception("Failed to load config; using default DB path.")
        db_path = "data/app.db"

    init_db(db_path)
