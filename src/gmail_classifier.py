from src.keywords import LABEL_KEYWORDS, LABEL_PRIORITY


def classify_email(subject: str, body: str):
    """
    Classify an email based on subject + body text using keyword matching.
    Returns the label name or None.
    """

    text = f"{subject} {body}".lower()

    for label in LABEL_PRIORITY:
        keywords = LABEL_KEYWORDS.get(label, [])
        for keyword in keywords:
            if keyword.lower() in text:
                return label

    return None
