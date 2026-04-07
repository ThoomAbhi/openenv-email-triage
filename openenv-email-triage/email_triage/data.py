"""Email datasets for each difficulty level."""
from .models import EmailMessage, EmailCategory, Department


def get_easy_emails() -> list[EmailMessage]:
    return [
        EmailMessage(
            id="e1", sender="promo@deals.com", subject="50% OFF EVERYTHING!!!",
            body="Click here for amazing deals! Limited time offer. Unsubscribe link at bottom.",
            timestamp="2025-01-15T09:00:00Z",
            ground_truth_category=EmailCategory.SPAM,
        ),
        EmailMessage(
            id="e2", sender="ceo@company.com", subject="Q4 Board Meeting - Action Required",
            body="Please review the attached Q4 financials before Thursday's board meeting. Your presentation slot is at 2pm.",
            timestamp="2025-01-15T09:15:00Z", attachments=["q4_financials.pdf"],
            ground_truth_category=EmailCategory.IMPORTANT,
        ),
        EmailMessage(
            id="e3", sender="newsletter@techdigest.io", subject="This Week in AI - Jan 15",
            body="Top stories: GPT-5 rumors, new robotics breakthroughs, and more. Read the full digest online.",
            timestamp="2025-01-15T09:30:00Z",
            ground_truth_category=EmailCategory.NEWSLETTER,
        ),
        EmailMessage(
            id="e4", sender="mom@family.com", subject="Dinner Sunday?",
            body="Hi sweetie, are you free for dinner this Sunday? Dad is grilling. Let me know! Love, Mom",
            timestamp="2025-01-15T10:00:00Z",
            ground_truth_category=EmailCategory.PERSONAL,
        ),
        EmailMessage(
            id="e5", sender="security@bank.com.fake.ru", subject="URGENT: Your account is compromised",
            body="Dear customer, we detected suspicious activity. Click here immediately to verify your identity. Enter your SSN and password.",
            timestamp="2025-01-15T10:30:00Z",
            ground_truth_category=EmailCategory.SPAM,
        ),
        EmailMessage(
            id="e6", sender="manager@company.com", subject="Project deadline moved up",
            body="Hi team, the client wants delivery by Friday instead of next Wednesday. Please reprioritize accordingly.",
            timestamp="2025-01-15T11:00:00Z",
            ground_truth_category=EmailCategory.IMPORTANT,
        ),
    ]


def get_medium_emails() -> list[EmailMessage]:
    return [
        EmailMessage(
            id="m1", sender="client-vip@bigcorp.com", subject="Contract renewal - urgent discussion needed",
            body="Our contract expires in 48 hours. We need to discuss revised terms ASAP. This is a $2M account. Please connect me with your sales lead today.",
            timestamp="2025-01-15T08:00:00Z",
            ground_truth_category=EmailCategory.URGENT, ground_truth_priority=5,
            ground_truth_department=Department.SALES,
        ),
        EmailMessage(
            id="m2", sender="user@customer.com", subject="Bug: App crashes on login",
            body="Since the latest update, I can't log in. The app crashes immediately. I'm on iOS 17, iPhone 15. This is blocking my whole team of 50 people.",
            timestamp="2025-01-15T08:30:00Z",
            ground_truth_category=EmailCategory.IMPORTANT, ground_truth_priority=4,
            ground_truth_department=Department.ENGINEERING,
        ),
        EmailMessage(
            id="m3", sender="hr@company.com", subject="Updated PTO Policy",
            body="Please review the updated PTO policy attached. Changes take effect Feb 1. No action needed unless you have questions.",
            timestamp="2025-01-15T09:00:00Z", attachments=["pto_policy_v2.pdf"],
            ground_truth_category=EmailCategory.NEWSLETTER, ground_truth_priority=2,
            ground_truth_department=Department.HR,
        ),
        EmailMessage(
            id="m4", sender="angry-customer@email.com", subject="TERRIBLE SERVICE - I WANT A REFUND",
            body="I've been waiting 3 weeks for my order. Nobody responds to my tickets. I'm posting this on social media. Order #98765.",
            timestamp="2025-01-15T09:15:00Z",
            ground_truth_category=EmailCategory.URGENT, ground_truth_priority=5,
            ground_truth_department=Department.SUPPORT,
        ),
        EmailMessage(
            id="m5", sender="recruiter@linkedin.com", subject="Exciting opportunity at StartupXYZ",
            body="Hi, I came across your profile and think you'd be a great fit for our Senior Engineer role. 200k+ comp. Interested?",
            timestamp="2025-01-15T09:30:00Z",
            ground_truth_category=EmailCategory.PERSONAL, ground_truth_priority=1,
            ground_truth_department=Department.GENERAL,
        ),
        EmailMessage(
            id="m6", sender="cto@company.com", subject="Production database slow - need eyes",
            body="Prod DB response times spiked 10x in the last hour. Not critical yet but trending badly. Can someone investigate?",
            timestamp="2025-01-15T10:00:00Z",
            ground_truth_category=EmailCategory.IMPORTANT, ground_truth_priority=4,
            ground_truth_department=Department.ENGINEERING,
        ),
        EmailMessage(
            id="m7", sender="vendor@supplies.com", subject="Invoice #4521 - Payment overdue",
            body="This is a reminder that invoice #4521 ($15,000) is 30 days overdue. Please remit payment to avoid service interruption.",
            timestamp="2025-01-15T10:30:00Z",
            ground_truth_category=EmailCategory.IMPORTANT, ground_truth_priority=3,
            ground_truth_department=Department.SALES,
        ),
        EmailMessage(
            id="m8", sender="win@lottery-prize.net", subject="You've won $1,000,000!!!",
            body="Congratulations! You've been selected as our grand prize winner. Send your bank details to claim.",
            timestamp="2025-01-15T11:00:00Z",
            ground_truth_category=EmailCategory.SPAM, ground_truth_priority=1,
            ground_truth_department=Department.GENERAL,
        ),
    ]


def get_hard_emails() -> list[EmailMessage]:
    emails = get_medium_emails()
    # Mark which ones require responses and add key points for grading
    for em in emails:
        if em.id == "m1":
            em.requires_response = True
            em.key_points = ["acknowledge urgency", "confirm sales contact", "mention timeline"]
        elif em.id == "m2":
            em.requires_response = True
            em.key_points = ["acknowledge the bug", "ask for crash logs", "provide workaround or ETA"]
        elif em.id == "m4":
            em.requires_response = True
            em.key_points = ["apologize", "reference order number", "offer resolution", "de-escalate"]
        elif em.id == "m6":
            em.requires_response = True
            em.key_points = ["acknowledge issue", "confirm investigation", "ask for metrics"]
        elif em.id == "m7":
            em.requires_response = True
            em.key_points = ["acknowledge invoice", "provide payment timeline"]
    return emails
