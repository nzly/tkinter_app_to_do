import os
import json
import sys
import time
import platform
import uuid
import jwt
from pathlib import Path

# Adjust sys.path for relative imports when running as a script
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from objects.logger import get_logger

# MUST match the secret key used on the server side
_SECRET_FILE = Path(__file__).resolve().parents[1] / "security" / "supabase_secret.json"


# Read the JWT secret from the git-ignored secret file.
def _load_jwt_secret() -> str:
    try:
        with _SECRET_FILE.open(encoding="utf-8") as secret_file:
            secret = json.load(secret_file).get("JWT_SECRET_KEY")
    except FileNotFoundError as error:
        raise RuntimeError(f"Secret file not found: {_SECRET_FILE}") from error
    if not secret:
        raise ValueError(f"Missing JWT_SECRET_KEY in {_SECRET_FILE}")
    return secret


JWT_SECRET_KEY = _load_jwt_secret()
CACHE_FILE = "license_cache.json"

# In production, route this request through your API backend endpoint
SERVER_ACTIVATION_URL = "https://your-api.com/v1/activate"

# Hardware ID and license token management functions.
def get_hardware_id() -> str:
    """Generates a stable hardware identifier for this computer."""
    node = uuid.getnode()
    return f"{platform.system()}-{platform.machine()}-{node}"

# Functions to load and save cached license tokens.
def load_cached_token() -> str | None:
    """Reads cached license token from local disk."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("token")
        except Exception:
            get_logger().error("Failed to load cached license token from %s", CACHE_FILE)
            return None
    return None

# Functions to verify and authorize license tokens.
def save_cached_token(token: str):
    """Saves license token to local disk."""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"token": token}, f)

# Function to verify license token offline.
def verify_token_offline(token: str, current_hwid: str) -> dict | None:
    """Verifies token validity locally without network access."""
    try:
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        
        # Verify hardware identity matches
        if decoded.get("hwid") != current_hwid:
            get_logger().error("❌ License error: Token hardware ID mismatch.")
            return None
            
        return decoded
    # If we reach here, the token is invalid for some other reason
    except jwt.ExpiredSignatureError:
        get_logger().warning("⚠️ Local license expired. Online re-validation required.")
        return None
    except jwt.InvalidTokenError as e:
        get_logger().error("❌ Invalid license token: %s", e)
        return None


def authorize_application(license_key_input: str | None = None) -> bool:
    """Primary application access controller."""
    hwid = get_hardware_id()
    
    # Step A: Check offline cache
    cached_token = load_cached_token()
    if cached_token:
        payload = verify_token_offline(cached_token, hwid)
        if payload:
            days_remaining = int((payload["exp"] - time.time()) / 86400)
            get_logger().info("✅ Authorization Successful (OFFLINE)!")
            get_logger().info("👤 Licensed to: %s", payload['email'])
            get_logger().info("📅 Offline period valid for: %s more days.", days_remaining)
            return True

    # Step B: Fall back to online activation
    if not license_key_input:
        get_logger().error("❌ Authorization failed. No valid offline key found, please enter license key.")
        return False

    get_logger().info("🌐 Connecting to activation server...")
    
    # Substitute with your server function call or HTTP API request
    from license_server import activate_license
    response = activate_license(license_key_input, hwid)

    if response.get("status") == "success":
        save_cached_token(response["token"])
        get_logger().info("✅ License successfully activated online!")
        return True
    else:
        get_logger().error("❌ Activation failed: %s", response.get('message'))
        return False


# --- Test App Execution ---
# This section allows for testing the application authorization flow,
# including both online activation and offline verification.
if __name__ == "__main__":
    # Select the test license key for the first run (online activation)
    # "PRO-KEY-1234-5678" is for yun@digitmind.co.nz
    # "PRO-KEY-1357-2468" is for admin@digitmind.co.nz
    license_key_input_list = ["PRO-KEY-1234-5678", "PRO-KEY-1357-2468"]
    get_logger().info("--- START RUNNING TEST ---")
    test_license_key_input = license_key_input_list[0]
    get_logger().info("--- 1. First Run (Online Activation) ---")
    get_logger().info("Using license key: %s", test_license_key_input)
    authorized = authorize_application(license_key_input=test_license_key_input)
    get_logger().info("App State: %s", "RUNNING" if authorized else "LOCKED")
    get_logger().info("\n--- 2. Subsequent Launch (Fully Offline) ---")
    authorized_offline = authorize_application()
    get_logger().info("App State: %s", "RUNNING" if authorized_offline else "LOCKED")
    get_logger().info("--- END RUNNING TEST ---")