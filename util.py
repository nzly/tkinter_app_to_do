import datetime
import hashlib
import hmac
import os
import subprocess
import sys

from PIL import ImageTk

# Utility functions for the application.
def get_date_now() -> str:
    """Returns the current date and time as a formatted string."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Opens a file with the default application for the current OS.
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

# Hashes a plaintext password using PBKDF2 with SHA-256 and a random salt.
def hash_password(plain_password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${digest.hex()}"

# Checks a plaintext password against a salted hash produced by hash_password.
def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
    except (AttributeError, ValueError):
        return False
    salt = bytes.fromhex(salt_hex)
    expected_digest = bytes.fromhex(digest_hex)
    candidate_digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
    return hmac.compare_digest(candidate_digest, expected_digest)

# Resizes an image to the specified size and returns the path to the resized image.
def resize_image(image_path: str, size: tuple) -> ImageTk.PhotoImage:
    """Resize an image to the specified size and return a PhotoImage object."""
    from PIL import Image

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    with Image.open(image_path) as original_img:
        resized_img = original_img.resize(size=size, resample=Image.Resampling.LANCZOS)
        image = ImageTk.PhotoImage(resized_img)

    return image

# Resizes an image using subsampling and returns a PhotoImage object.
def resize_image_subsample(image_path: str, width: int, height: int) -> ImageTk.PhotoImage:
    """Resize an image to the specified width and height and return a PhotoImage object."""
    import tkinter as tk

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        image = tk.PhotoImage(file=image_path)
        # Reduces the size of the image. (width divides it by width, height divides it by height, etc.)
        image = image.subsample(width, height)
    except:
        # Fallback if no image file is found
        image = None

    return image

# Gets the absolute path to a resource, works for development and PyInstaller.
def get_resource_path(relative_path: str) -> str:
    """Get the absolute path to a resource, works for dev and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Main block to test utility functions when the script is run directly.
if __name__ == "__main__":
    # Test the utility functions.
    print("Current date and time:", get_date_now())
    test_file = "test.txt"
    print(f"Attempting to open file: {test_file}")
    if open_file(test_file):
        print("File opened successfully.")
    else:
        print("Failed to open file.")
    
    #test_password = "123456"
    test_password = "123"
    hashed = hash_password(test_password)
    print(f"Hashed password for '{test_password}': {hashed}")

    if verify_password(test_password, hashed):
        print("Password verification succeeded.")
    else:
        print("Password verification failed.")
