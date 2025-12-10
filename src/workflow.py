from src.gmail_client import gmail_login, fetch_messages, send_message, create_label_if_missing, add_label_to_message
from src.gmail_classifier import classify_email
from src.hr_db import (
    init_db, add_or_update_application, upsert_hr_contact,
    schedule_followup, get_pending_followups, mark_followup_sent
)
from src.utils import first_email, split_sender


FOLLOWUP_LABEL = "ApplicationTracker"


def process_inbox():
    init_db()
    service = gmail_login()

    label_id = create_label_if_missing(service, FOLLOWUP_LABEL)

    query = 'subject:(application OR interview OR assessment OR regret OR offer)'
    emails = fetch_messages(service, query)

    actions = []

    for mail in emails:
        status = classify_email(mail['subject'], mail['body'])

        name, sender_email = split_sender(mail['from'])

        record = {
            'id': mail['id'],
            'threadId': mail['threadId'],
            'subject': mail['subject'],
            'from': mail['from'],
            'body': mail['body'],
            'status': status,
            'company': None,
            'role': None
        }

        add_or_update_application(record)

        try:
            add_label_to_message(service, mail['id'], label_id)
        except:
            pass

        if status == "Rejection":
            hr = first_email(mail['body']) or sender_email
            if hr:
                upsert_hr_contact(hr, name=name)
                actions.append(("auto_followup", mail['id'], hr, mail['subject']))
            else:
                schedule_followup(mail['id'])
                actions.append(("manual_followup", mail['id'], None, mail['subject']))

    return actions


def run_auto_followups(actions):
    service = gmail_login()

    for act in actions:
        if act[0] != "auto_followup":
            continue

        _, message_id, hr_email, subject = act

        body = f"""
Hi,

Thank you for the update regarding "{subject}". 
If possible, I would really appreciate any quick feedback that could help me improve.

Best regards,
Saamiya
"""

        send_message(service, hr_email, f"Feedback request – {subject}", body)
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

I am following up regarding the application outcome for "{subject}". 
I would be grateful for any quick feedback you can share.

Best,
Saamiya
"""

        send_message(service, hr_email, f"Follow-up: {subject}", body)
        mark_followup_sent(message_id)
        print("Scheduled follow-up sent to", hr_email)
