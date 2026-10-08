import os
import json
import sys
import time
import platform
import uuid
import jwt
import math
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

# Load the JWT secret key from the secure file.
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

# Function to authorize the application either offline or online.
def authorize_application(license_key_input: str | None = None) -> bool:
    """Primary application access controller."""
    hwid = get_hardware_id()
    
    # Step A: Check offline cache
    cached_token = load_cached_token()
    if cached_token:
        payload = verify_token_offline(cached_token, hwid)
        if payload:
            seconds_remaining = max(0, payload["exp"] - time.time())
            get_logger().info("✅ Authorization Successful (OFFLINE)!")
            get_logger().info("👤 Licensed to: %s", payload['email'])
            
            if seconds_remaining < 86400:
                hours_remaining = math.ceil(seconds_remaining / 3600)
                get_logger().info("📅 Offline period valid for: %s more hours.", hours_remaining)
            else:
                days_remaining = int(seconds_remaining / 86400)
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

# Function to authorize the application and return the associated email if available.
def authorize_application_with_email(
    license_key_input: str | None = None,
) -> tuple[str | None, str | None]:
    """Authorize the supplied key and return its email or a failure message."""
    if not license_key_input or not license_key_input.strip():
        message = "Please enter your product key."
        get_logger().error("Product key authorization failed: no key was provided.")
        return None, message

    license_key = license_key_input.strip()
    hardware_id = get_hardware_id()
    cached_token = load_cached_token()

    if cached_token:
        payload = verify_token_offline(cached_token, hardware_id)
        if payload and payload.get("sub") == license_key:
            email = payload.get("email")
            if isinstance(email, str) and email.strip():
                get_logger().info("Product key authorized using the offline license cache.")
                return email.strip(), None
            get_logger().error("The authorized license does not contain an email address.")

    get_logger().info("Validating the entered product key with Supabase.")
    try:
        if __package__:
            from .license_server import activate_license
        else:
            from license_server import activate_license
        response = activate_license(license_key, hardware_id)
    except Exception:
        get_logger().exception("Product key authorization request failed.")
        return None, "Could not verify the product key. Please try again."

    if response.get("status") != "success":
        message = str(response.get("message") or "Product key authorization failed.")
        get_logger().warning("Product key authorization failed: %s", message)
        return None, message

    token = response.get("token")
    if not isinstance(token, str):
        get_logger().error("Product key authorization returned no valid token.")
        return None, "Product key authorization returned an invalid license."

    payload = verify_token_offline(token, hardware_id)
    if not payload or payload.get("sub") != license_key:
        get_logger().error("Product key authorization returned a token for a different key.")
        return None, "Product key authorization returned a license for a different key."

    email = payload.get("email")
    if not isinstance(email, str) or not email.strip():
        get_logger().error("The authorized license does not contain an email address.")
        return None, "The authorized license does not contain an email address."

    save_cached_token(token)
    get_logger().info("Product key authorized successfully.")
    return email.strip(), None


# --- Test App Execution ---
# This section allows for testing the application authorization flow,
# including both online activation and offline verification.
if __name__ == "__main__":
    # Select the test license key for the first run (online activation)
    # "PRO-KEY-1234-5678" is for yun@digitmind.co.nz
    # "PRO-KEY-1357-2468" is for admin@digitmind.co.nz
    license_key_input_list = ["PRO-KEY-1234-5678", "PRO-KEY-1357-2468"]
    get_logger().info("--- START RUNNING TEST ---")
    # Read the license key by index from the list for testing
    test_license_key_input = license_key_input_list[0]
    get_logger().info("--- 1. First Run (Online Activation) ---")
    get_logger().info("Using license key: %s", test_license_key_input)
    authorized = authorize_application(license_key_input=test_license_key_input)
    get_logger().info("authorize_application result: %s", "RUNNING" if authorized else "LOCKED")
    get_logger().info("--- 2. Subsequent Run (Cached Authorization) ---")
    authorized_offline = authorize_application()
    get_logger().info(
        "authorize_application cached result: %s",
        "RUNNING" if authorized_offline else "LOCKED",
    )

    get_logger().info("--- 3. Email-Returning Authorization ---")
    authorized_email, authorization_error = authorize_application_with_email(test_license_key_input)
    get_logger().info(
        "App State: %s; licensed email: %s; error: %s",
        "RUNNING" if authorized_email else "LOCKED",
        authorized_email or "unavailable",
        authorization_error or "none",
    )
    get_logger().info("\n--- 4. Subsequent Launch (Cached Email Authorization) ---")
    authorized_offline_email, offline_authorization_error = authorize_application_with_email(test_license_key_input)
    get_logger().info(
        "App State: %s; licensed email: %s; error: %s",
        "RUNNING" if authorized_offline_email else "LOCKED",
        authorized_offline_email or "unavailable",
        offline_authorization_error or "none",
    )
    get_logger().info("--- END RUNNING TEST ---")