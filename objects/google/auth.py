import os

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly"
]

SECRET_FILE = (
    Path(__file__).resolve().parent.parent.parent / "security" / "google_credentials.json"
)

TOKEN_FILE = (
    Path(__file__).resolve().parent.parent.parent / "security" / "google_token.json"
)

def get_credentials() -> Credentials:

    credentials = None

    # Load previously saved credentials
    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    # No valid credentials?
    if not credentials or not credentials.valid:

        # Access token expired, but refresh token available
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        # First time authentication
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                SECRET_FILE,
                SCOPES
            )

            credentials = flow.run_local_server(port=0)

        # Save credentials for next time
        with open(TOKEN_FILE, "w") as file:
            file.write(credentials.to_json())

    return credentials

if __name__ == "__main__":
    get_credentials()