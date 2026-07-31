import datetime
import os
import subprocess
import sys

def get_date_now() -> str:
    """Returns the current date and time as a formatted string."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def open_file(file_path: str) -> bool:
    """Open a file with the default application for the current OS."""
    if not file_path:
        return False

    normalized_path = os.path.abspath(file_path)
    if not os.path.exists(normalized_path):
        return False

    try:
        if os.name == "nt":
            os.startfile(normalized_path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", normalized_path])
        else:
            subprocess.Popen(["xdg-open", normalized_path])
        return True
    except Exception:
        return False
