# src/keywords.py

LABEL_KEYWORDS = {
    "Interviews": [
        "interview",
        "schedule a call",
        "invite you to interview",
        "book a meeting",
    ],

    "Assessment": [
        "assessment",
        "technical test",
        "coding test",
        "online test",
    ],

    "Rejections": [
        "regret to inform you",
        "unfortunately",
        "not moving forward",
        "unsuccessful",
        "we will not be proceeding",
    ],

    "Confirmations": [
        "thank you for applying",
        "application received",
        "we received your application",
        "your application was submitted",
    ],

    "InProgress": [
        "under review",
        "being reviewed",
        "shortlisted",
        "currently reviewing",
    ],

    "NoReply": [
        "no-reply",
        "noreply",
        "do not reply",
        "automated message",
    ],

    "AutoFollowup": [
        "your application to",
        "we received your application",
        "applied to",
    ],
}


# Order matters — higher priority first
LABEL_PRIORITY = [
    "Interviews",
    "Assessment",
    "Rejections",
    "Confirmations",
    "InProgress",
    "NoReply",
    "AutoFollowup",
]
