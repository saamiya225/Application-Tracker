from src.gmail_client import (
    gmail_login,
    fetch_messages,
    send_message,
    create_label_if_missing,
    add_label_to_message,
)

from src.gmail_classifier import classify_email
from src.hr_db import (
    init_db,
    add_or_update_application,
    upsert_hr_contact,
    schedule_followup,
    get_pending_followups,
    mark_followup_sent,
)

from src.utils import first_email, split_sender
from src.keywords import LABEL_KEYWORDS


MASTER_LABEL = "ApplicationTracker"


def process_inbox():
    print("Processing inbox...")
    init_db()
    service = gmail_login()

    # Create master label
    master_label_id = create_label_if_missing(service, MASTER_LABEL)

    # Create all keyword-based labels
    label_ids = {}
    for label_name in LABEL_KEYWORDS.keys():
        label_ids[label_name] = create_label_if_missing(service, label_name)

    # Fetch relevant emails only
    query = (
        'subject:(application OR interview OR assessment OR regret OR offer) '
        'OR from:linkedin OR from:workday OR from:greenhouse'
    )

    emails = fetch_messages(service, query)
    actions = []

    for mail in emails:
        subject = mail.get("subject", "")
        body = mail.get("body", "") or mail.get("snippet", "")
        status = classify_email(subject, body)

        sender_raw = mail.get("from", "")
        name, sender_email = split_sender(sender_raw)


        record = {
            "id": mail["id"],
            "threadId": mail["threadId"],
            "subject": mail["subject"],
            "from": mail["from"],
            "body": mail["body"],
            "status": status,
            "company": None,
            "role": None,
        }

        add_or_update_application(record)

        # Always apply master label
        try:
            add_label_to_message(service, mail["id"], master_label_id)
        except Exception:
            pass

        # Apply classified label
        if status and status in label_ids:
            try:
                add_label_to_message(service, mail["id"], label_ids[status])
            except Exception:
                pass

        # Follow-up logic (only safe cases)
        if status in ["Rejections", "AutoFollowup", "NoReply"]:
            hr_email = first_email(mail["body"]) or sender_email

            if hr_email and "noreply" not in hr_email.lower():
                upsert_hr_contact(hr_email, name=name)
                actions.append(
                    ("auto_followup", mail["id"], hr_email, mail["subject"])
                )
            else:
                schedule_followup(mail["id"])
                actions.append(
                    ("manual_followup", mail["id"], None, mail["subject"])
                )

    return actions


def run_auto_followups(actions):
    service = gmail_login()

    for action in actions:
        if action[0] != "auto_followup":
            continue

        _, message_id, hr_email, subject = action

        body = f"""
Hi,

Thank you for the update regarding "{subject}".
If possible, I would really appreciate any brief feedback that could help me improve.

Best regards,
Saamiya
"""

        send_message(
            service,
            hr_email,
            f"Follow-up regarding application – {subject}",
            body,
        )

        mark_followup_sent(message_id)
        print("Sent auto follow-up to", hr_email)


def run_pending_scheduled():
    service = gmail_login()
    rows = get_pending_followups()

    if not rows:
        print("No pending scheduled follow-ups.")
        return

    for message_id, subject, hr_email in rows:
        if not hr_email:
            print("No HR email available for:", subject)
            continue

        body = f"""
Hello,

I am following up regarding my application for "{subject}".
I would appreciate any feedback you are able to share.

Best regards,
Saamiya
"""

        send_message(
            service,
            hr_email,
            f"Follow-up: {subject}",
            body,
        )

        mark_followup_sent(message_id)
        print("Scheduled follow-up sent to", hr_email)
