def classify_email(subject="", body=""):
    text = f"{subject} {body}".lower()

    application_kw = [
        "thank you for your application",
        "received your application",
        "application submitted",
        "thanks for applying"
    ]

    interview_kw = [
        "invite you to interview",
        "schedule your interview",
        "interview invitation",
        "shortlisted"
    ]

    assessment_kw = [
        "complete your assessment",
        "invite you to complete",
        "online test",
        "coding test"
    ]

    rejection_kw = [
        "regret to inform",
        "unfortunately",
        "not moving forward",
        "not successful",
        "we will not be progressing"
    ]

    offer_kw = [
        "pleased to inform",
        "offer letter",
        "congratulations"
    ]

    if any(k in text for k in application_kw):
        return "Application Submitted"
    if any(k in text for k in interview_kw):
        return "Interview Invite"
    if any(k in text for k in assessment_kw):
        return "Assessment Request"
    if any(k in text for k in rejection_kw):
        return "Rejection"
    if any(k in text for k in offer_kw):
        return "Offer"

    return "Other"
