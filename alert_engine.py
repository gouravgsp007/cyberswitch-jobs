"""
CyberSwitch 10X - Instant Alert Engine (Phase 4)
Monitors high-priority GCC job openings (strictly 2-3 YOE, 10-15+ LPA)
and pushes instant alerts locally and via Telegram / Webhooks.
"""

import os
import json
import urllib.request
import urllib.parse
import datetime
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

ALERTS_FILE = os.path.join(DATA_DIR, "job_alerts.json")
CONFIG_FILE = os.path.join(DATA_DIR, "alert_config.json")

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

def get_alert_config() -> Dict[str, Any]:
    config = load_json(CONFIG_FILE, {
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "enabled": True,
        "min_priority": "P1"
    })
    return config

def update_alert_config(bot_token: str, chat_id: str, enabled: bool = True) -> Dict[str, Any]:
    config = {
        "telegram_bot_token": bot_token.strip(),
        "telegram_chat_id": chat_id.strip(),
        "enabled": enabled,
        "min_priority": "P1"
    }
    save_json(CONFIG_FILE, config)
    return {"status": "success", "config": config}

def dispatch_telegram_message(token: str, chat_id: str, text: str) -> bool:
    """Sends message to Telegram chat using official Bot API."""
    if not token or not chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"Telegram dispatch error: {e}")
        return False

def trigger_job_alert(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates an alert for a 10-15 LPA 2-3 YOE GCC opportunity,
    logs it locally, and dispatches via Telegram if configured.
    """
    alerts_data = load_json(ALERTS_FILE, {"alerts": [], "unread_count": 0})
    alerts = alerts_data.get("alerts", [])

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert_id = f"alt_{os.urandom(4).hex()}"

    alert_item = {
        "id": alert_id,
        "title": job.get("title", "Cybersecurity Opening"),
        "company": job.get("company", "GCC Paymaster"),
        "location": job.get("location", "Pune / Mumbai"),
        "salary": job.get("salary", "₹10.0 - ₹15.0 LPA"),
        "experience": job.get("experience", "2 - 3 Years"),
        "priority": job.get("priority", "P1 - High Priority"),
        "apply_url": job.get("apply_url") or job.get("job_post_url", "#"),
        "source": job.get("source", "Direct ATS"),
        "created_at": now_str,
        "is_read": False
    }

    # Avoid duplicate alert for same company and title in last 24h
    for existing in alerts[:30]:
        if existing.get("company") == alert_item["company"] and existing.get("title") == alert_item["title"]:
            return {"status": "duplicate", "alert": existing}

    alerts.insert(0, alert_item)
    unread = sum(1 for a in alerts if not a.get("is_read", False))
    save_json(ALERTS_FILE, {"alerts": alerts[:100], "unread_count": unread})

    # Telegram Dispatch
    config = get_alert_config()
    tg_sent = False
    if config.get("enabled") and config.get("telegram_bot_token") and config.get("telegram_chat_id"):
        msg = (
            f"🎯 <b>NEW 10+ LPA JOB ALERT!</b>\n\n"
            f"🏢 <b>Company:</b> {alert_item['company']}\n"
            f"💼 <b>Role:</b> {alert_item['title']}\n"
            f"📍 <b>Location:</b> {alert_item['location']}\n"
            f"💰 <b>Package:</b> {alert_item['salary']}\n"
            f"⏳ <b>Exp:</b> {alert_item['experience']} (Strict 2-3 YOE Target)\n"
            f"⚡ <b>Priority:</b> {alert_item['priority']}\n\n"
            f"🔗 <a href=\"{alert_item['apply_url']}\">Click Here to Apply Directly</a>"
        )
        tg_sent = dispatch_telegram_message(
            config["telegram_bot_token"],
            config["telegram_chat_id"],
            msg
        )

    return {
        "status": "success",
        "alert": alert_item,
        "telegram_dispatched": tg_sent,
        "unread_count": unread
    }

def get_alerts() -> Dict[str, Any]:
    data = load_json(ALERTS_FILE, {"alerts": [], "unread_count": 0})
    return {
        "status": "success",
        "unread_count": sum(1 for a in data.get("alerts", []) if not a.get("is_read", False)),
        "alerts": data.get("alerts", [])
    }

def mark_all_alerts_read() -> Dict[str, Any]:
    data = load_json(ALERTS_FILE, {"alerts": [], "unread_count": 0})
    for a in data.get("alerts", []):
        a["is_read"] = True
    save_json(ALERTS_FILE, {"alerts": data.get("alerts", []), "unread_count": 0})
    return {"status": "success", "unread_count": 0}
