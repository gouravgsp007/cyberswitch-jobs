"""
CyberSwitch 10X - Gmail / Email Interview & Rejection Auto-Sync Engine (Phase 7)
Parses incoming recruiter communications from target GCCs (Barclays, Mastercard, Qualys, etc.)
and automatically updates the Kanban application tracker stage.
"""

import os
import json
import re
import datetime
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

EMAILS_FILE = os.path.join(DATA_DIR, "synced_emails.json")
CONFIG_FILE = os.path.join(DATA_DIR, "email_sync_config.json")

# Keywords for stage classification
STAGE_KEYWORDS = {
    "offer": [
        "offer letter", "congratulations", "pleased to offer", "intent to offer",
        "compensation structure", "offer discussion", "employment offer", "welcome to the team"
    ],
    "technical": [
        "technical round", "technical interview", "technical discussion", "l2 interview",
        "hiring manager", "sentinel", "kql assessment", "coding assessment", "hackerrank",
        "panel interview", "system design"
    ],
    "screening": [
        "screening", "phone call", "introductory call", "telephonic", "brief discussion",
        "recruiter call", "talent acquisition", "availability for a call", "discuss your profile"
    ],
    "managerial": [
        "managerial round", "director interview", "leadership round", "final discussion", "vp interview"
    ],
    "rejected": [
        "unfortunately", "other candidates", "not moving forward", "decided to pursue other",
        "future opportunities", "not shortlisted", "regret to inform", "unsuccessful"
    ]
}

def load_json(filepath: str, default: Any) -> Any:
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(filepath: str, data: Any):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_email_config() -> Dict[str, Any]:
    return load_json(CONFIG_FILE, {
        "email_address": "",
        "app_password": "",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "enabled": False
    })

def update_email_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
    current = get_email_config()
    current.update(config_data)
    save_json(CONFIG_FILE, current)
    return {"status": "success", "config": current}

def detect_company_from_text(text: str, sender: str = "") -> str:
    """Detects target employer company name from sender domain or email body."""
    if sender:
        m_domain = re.search(r'@([a-zA-Z0-9.-]+)', sender)
        if m_domain:
            domain = m_domain.group(1).lower()
            known_domains = {
                "barclays": "Barclays",
                "mastercard": "Mastercard",
                "qualys": "Qualys",
                "nvidia": "NVIDIA",
                "crowdstrike": "CrowdStrike",
                "fiserv": "Fiserv",
                "statestreet": "State Street",
                "bnymellon": "BNY Mellon",
                "deutschebank": "Deutsche Bank",
                "db": "Deutsche Bank",
                "smith-nephew": "Smith+Nephew",
                "smithnephew": "Smith+Nephew",
                "wipro": "Wipro"
            }
            for k, comp in known_domains.items():
                if k in domain:
                    return comp

    # Check body for well known target GCCs
    text_lower = text.lower()
    targets = [
        "Barclays", "Mastercard", "Qualys", "NVIDIA", "CrowdStrike",
        "Fiserv", "State Street", "BNY Mellon", "Deutsche Bank", "Smith+Nephew"
    ]
    for t in targets:
        if t.lower() in text_lower:
            return t

    return "General Recruiter"

def classify_stage(text: str) -> str:
    """Classifies message into a pipeline stage based on linguistic keywords."""
    text_lower = text.lower()
    for stage in ["offer", "rejected", "technical", "managerial", "screening"]:
        for kw in STAGE_KEYWORDS[stage]:
            if kw in text_lower:
                return stage
    return "screening"

def extract_meeting_link(text: str) -> Optional[str]:
    """Extracts Teams, Zoom, or Google Meet links from email body."""
    m_teams = re.search(r'https://teams\.microsoft\.com/[^\s<>"]+', text)
    if m_teams: return m_teams.group(0)

    m_zoom = re.search(r'https://[a-zA-Z0-9.-]*zoom\.us/[^\s<>"]+', text)
    if m_zoom: return m_zoom.group(0)

    m_meet = re.search(r'https://meet\.google\.com/[a-z]{3}-[a-z]{4}-[a-z]{3}', text)
    if m_meet: return m_meet.group(0)

    return None

def parse_and_sync_recruiter_message(raw_text: str, sender_email: str = "") -> Dict[str, Any]:
    """
    Parses any pasted email or recruiter message, extracts company & stage,
    and updates the active Kanban application card.
    """
    company = detect_company_from_text(raw_text, sender_email)
    stage = classify_stage(raw_text)
    meeting_link = extract_meeting_link(raw_text)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary_note = f"[Auto-Sync {now_str}] Classified as {stage.upper()}"
    if meeting_link:
        summary_note += f" | Meeting: {meeting_link}"

    event = {
        "id": f"eml_{os.urandom(4).hex()}",
        "company": company,
        "sender": sender_email or "Recruiter InMail / Email",
        "detected_stage": stage,
        "meeting_link": meeting_link,
        "timestamp": now_str,
        "snippet": raw_text[:280].strip(),
        "applied_to_tracker": False
    }

    # Automatically transition the corresponding Kanban card if tracked
    try:
        import tracker_engine
        tracker_data = tracker_engine.load_tracker_data()
        items = tracker_data if isinstance(tracker_data, list) else tracker_data.get("items", [])
        comp_lower = company.lower()
        for item in items:
            if comp_lower != "general recruiter" and comp_lower in item.get("company", "").lower():
                tracker_engine.update_job_stage(item["id"], stage, note=summary_note)
                event["applied_to_tracker"] = True
                event["matched_tracker_company"] = item.get("company")
                break
    except Exception as e:
        print(f"Tracker auto-sync notice: {e}")

    # Log to synced emails database
    feed_data = load_json(EMAILS_FILE, {"events": []})
    events = feed_data.get("events", [])
    events.insert(0, event)
    save_json(EMAILS_FILE, {"events": events[:100]})

    return {
        "status": "success",
        "event": event
    }

def get_synced_email_events() -> Dict[str, Any]:
    feed = load_json(EMAILS_FILE, {"events": []})
    return {
        "status": "success",
        "events": feed.get("events", [])
    }

def sync_imap_inbox() -> Dict[str, Any]:
    """
    Connects to IMAP inbox (Gmail) if credentials are provided in settings.
    Otherwise returns safe status.
    """
    config = get_email_config()
    if not config.get("enabled") or not config.get("email_address") or not config.get("app_password"):
        return {
            "status": "not_configured",
            "message": "Gmail IMAP is not configured or disabled. Use the instant text paste parser or configure credentials."
        }

    try:
        import imaplib
        import email
        from email.header import decode_header

        mail = imaplib.IMAP4_SSL(config["imap_server"], config.get("imap_port", 993))
        mail.login(config["email_address"], config["app_password"])
        mail.select("inbox")

        # Search recent messages containing cybersecurity keywords
        status, messages = mail.search(None, '(OR FROM "barclays" (OR FROM "qualys" (OR FROM "mastercard" SUBJECT "interview")))')
        msg_ids = messages[0].split()
        
        parsed_count = 0
        for num in msg_ids[-10:]:
            status, data = mail.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            sender = msg.get("From", "")
            if body:
                parse_and_sync_recruiter_message(body, sender)
                parsed_count += 1

        mail.logout()
        return {"status": "success", "synced_messages": parsed_count}

    except Exception as e:
        return {"status": "error", "message": str(e)}
