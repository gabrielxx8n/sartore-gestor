from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE = Path(__file__).resolve().parent
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def obtener_servicio_gmail():
    token = BASE / "token.json"
    credentials = BASE / "credentials.json"
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        if not credentials.exists():
            raise FileNotFoundError("Falta credentials.json junto a app.py")
        flow = InstalledAppFlow.from_client_secrets_file(str(credentials), SCOPES)
        creds = flow.run_local_server(port=0)
        token.write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)
