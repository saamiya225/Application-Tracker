import re

EMAIL_REGEX = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')


def extract_emails(text):
    if not text:
        return []
    return list(set(EMAIL_REGEX.findall(text)))


def first_email(text):
    emails = extract_emails(text)
    return emails[0] if emails else None


def split_sender(sender):
    import re
    m = re.match(r'(.*)<([^>]+)>', sender)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    if '@' in sender:
        return None, sender.strip()
    return sender, None
