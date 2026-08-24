import datetime
import hashlib
import hmac
import os
import subprocess
import sys

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

if __name__ == "__main__":
    # Test the utility functions.
    print("Current date and time:", get_date_now())
    test_file = "test.txt"
    print(f"Attempting to open file: {test_file}")
    if open_file(test_file):
        print("File opened successfully.")
    else:
        print("Failed to open file.")
    
    test_password = "123456"
    hashed = hash_password(test_password)
    print(f"Hashed password for '{test_password}': {hashed}")

    if verify_password(test_password, hashed):
        print("Password verification succeeded.")
    else:
        print("Password verification failed.")
