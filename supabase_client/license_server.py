import jwt
import datetime
import json
import sys
from pathlib import Path
from supabase import create_client, Client

# Adjust sys.path for relative imports when running as a script
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from objects.logger import get_logger

# --- Supabase Configuration ---
# This file contains functions for managing license activation and JWT issuance using Supabase.
_SECRET_FILE = Path(__file__).resolve().parents[1] / "security" / "supabase_secret.json"
_REQUIRED_SECRETS = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "JWT_SECRET_KEY")


# Read the Supabase and JWT secrets from the git-ignored secret file.
def _load_secrets() -> dict[str, str]:
    try:
        with _SECRET_FILE.open(encoding="utf-8") as secret_file:
            secrets = json.load(secret_file)
    except FileNotFoundError as error:
        raise RuntimeError(f"Secret file not found: {_SECRET_FILE}") from error

    missing = [name for name in _REQUIRED_SECRETS if not secrets.get(name)]
    if missing:
        raise ValueError(f"Missing values in {_SECRET_FILE}: {', '.join(missing)}")
    return secrets


_secrets = _load_secrets()
SUPABASE_URL = _secrets["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = _secrets["SUPABASE_SERVICE_ROLE_KEY"]
JWT_SECRET_KEY = _secrets["JWT_SECRET_KEY"]

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# --- License Activation Function ---
def activate_license(license_key: str, hardware_id: str) -> dict:
    """Validates key against Supabase and returns a signed 1-day JWT token."""
    try:
        # 1. Fetch license details from Supabase
        response = supabase.table("licenses").select("*").eq("key", license_key).execute()
        
        if not response.data:
            return {"status": "error", "message": "Invalid license key."}
            
        record = response.data[0]
        
        # 2. Status checks
        license_status = str(record.get("status") or "").strip().casefold()
        if license_status != "active":
            status_message = license_status or "unknown"
            return {"status": "error", "message": f"License is {status_message}."}
            
        activations = record.get("activations") or []
        
        # 3. Handle device activation limit
        if hardware_id not in activations:
            if len(activations) >= record["max_activations"]:
                return {"status": "error", "message": "Device activation limit reached."}
                
            activations.append(hardware_id)
            # Update activations array in database
            supabase.table("licenses").update({"activations": activations}).eq("key", license_key).execute()

        # 4. Issue offline JWT token valid for 1 day
        now = datetime.datetime.now(datetime.timezone.utc)
        exp = now + datetime.timedelta(days=1)
        
        payload = {
            "sub": record["key"],
            "email": record["email"],
            "hwid": hardware_id,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp())
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

        supabase.table("licenses").update({"expiry_date_time": exp.isoformat()}).eq("key", license_key).execute()
        
        return {
            "status": "success",
            "token": token,
            "expires_at": int(exp.timestamp())
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --- Main Execution for Testing ---
# This section allows for testing the license activation function independently.
if __name__ == "__main__":
    new_key = "PRO-KEY-1234-5678"
    test_user_key = "TEST-USER-KEY-9876-5432"
    admin_key = "ADMIN-KEY-0000-1111"
    
    # Optional: Insert a test license key into Supabase
    supabase.table("licenses").upsert({
        "key": new_key,
        "email": "yun@digitmind.co.nz",
        "max_activations": 2,
        "status": "active"
    }).execute()

    supabase.table("licenses").upsert({
            "key": test_user_key,
            "email": "test@digitmind.co.nz",
            "max_activations": 2,
            "status": "active"
        }).execute()

    supabase.table("licenses").upsert({
            "key": admin_key,
            "email": "admin@digitmind.co.nz",
            "max_activations": 2,
            "status": "active"
        }).execute()
    
    # Simulate an activation request
    result = activate_license(new_key, "WINDOWS-X86_64-9876543210")
    get_logger().info("Activation Result: %s", result)

    # Simulate an activation request for the test user key
    test_result = activate_license(test_user_key, "WINDOWS-X86_64-0123456789")
    get_logger().info("Test User Activation Result: %s", test_result)

    # Simulate an activation request for the admin key
    admin_result = activate_license(admin_key, "WINDOWS-X86_64-1122334455")
    get_logger().info("Admin Activation Result: %s", admin_result)
