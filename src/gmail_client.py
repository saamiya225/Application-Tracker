import os
import base64
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.send'
]

TOKEN_PATH = 'token.json'
CREDENTIALS_PATH = 'credentials.json'


def gmail_login():
    creds = None

    # Load saved tokens if they exist
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If there are no valid credentials, go through OAuth again
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token for reuse
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service



def fetch_messages(service, query, max_results=5000):
    """Fetch all messages matching query using pagination."""
    messages = []
    request = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=500  # Gmail max is 500 per page
    )

    while request is not None and len(messages) < max_results:
        response = request.execute()
        if "messages" in response:
            messages.extend(response["messages"])
        request = service.users().messages().list_next(
            previous_request=request,
            previous_response=response
        )
    
    return messages



def send_message(service, to_email, subject, body_text, thread_id=None):
    message = MIMEText(body_text)
    message["to"] = to_email
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    payload = {
        "raw": raw
    }

    if thread_id:
        payload["threadId"] = thread_id

    return service.users().messages().send(
        userId='me',
        body=payload
    ).execute()


def create_label_if_missing(service, label_name):
    labels = service.users().labels().list(
        userId='me'
    ).execute().get("labels", [])

    for label in labels:
        if label["name"] == label_name:
            return label["id"]

    new_label = service.users().labels().create(
        userId='me',
        body={
            "name": label_name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show"
        }
    ).execute()

    return new_label["id"]

def add_label_to_message(service, message_id, label_id):
    return service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [label_id],
            "removeLabelIds": []
        }
    ).execute()
