import os
import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from bs4 import BeautifulSoup


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]


def gmail_login():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def fetch_messages(service, query, max_results=50):
    """
    Fetch emails and normalize them into a clean structure.
    """

    results = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        msg_data = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )

        headers = msg_data.get("payload", {}).get("headers", [])
        header_map = {h["name"].lower(): h["value"] for h in headers}

        subject = header_map.get("subject", "")
        sender = header_map.get("from", "")
        snippet = msg_data.get("snippet", "")

        body = ""
        payload = msg_data.get("payload", {})
        parts = payload.get("parts", [])

        # Extract email body
        for part in parts:
            mime_type = part.get("mimeType")
            data = part.get("body", {}).get("data")

            if not data:
                continue

            decoded = base64.urlsafe_b64decode(data).decode(
                "utf-8", errors="ignore"
            )

            if mime_type == "text/html":
                soup = BeautifulSoup(decoded, "html.parser")
                body = soup.get_text(" ", strip=True)
                break

            if mime_type == "text/plain":
                body = decoded
                break

        emails.append(
            {
                "id": msg_data["id"],
                "threadId": msg_data["threadId"],
                "from": sender,
                "subject": subject,
                "body": body,
                "snippet": snippet,
            }
        )

    return emails


def create_label_if_missing(service, label_name):
    labels = (
        service.users()
        .labels()
        .list(userId="me")
        .execute()
        .get("labels", [])
    )

    for label in labels:
        if label["name"] == label_name:
            return label["id"]

    label_body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }

    label = (
        service.users()
        .labels()
        .create(userId="me", body=label_body)
        .execute()
    )

    return label["id"]


def add_label_to_message(service, message_id, label_id):
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"addLabelIds": [label_id]},
    ).execute()


def send_message(service, to, subject, body_text):
    message = MIMEText(body_text)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    body = {"raw": raw}

    service.users().messages().send(userId="me", body=body).execute()
