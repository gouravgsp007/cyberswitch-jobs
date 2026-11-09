"""
CyberSwitch 10X - CV Tracer Links Engine (Phase 3)
Generates smart "Read Receipt" tracking URLs for Gourav's resume PDF.
Alerts the exact second an HR recruiter or hiring manager clicks his LinkedIn, Credly, or Portfolio.
"""

import os
import json
import re
import datetime
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

LINKS_FILE = os.path.join(DATA_DIR, "tracer_links.json")
CLICKS_FILE = os.path.join(DATA_DIR, "tracer_clicks.json")

DEFAULT_DESTINATIONS = {
    "linkedin": "https://www.linkedin.com/in/gourav-parit/",
    "credly": "https://www.credly.com/users/gourav-parit/",
    "portfolio": "https://github.com/gourav-parit"
}

def load_json_file(filepath: str, default: Any) -> Any:
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json_file(filepath: str, data: Any):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def slugify(text: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text.strip().lower())
    return slug.strip('-')[:30]

def create_tracer_link(
    company: str,
    role: str = "Cybersecurity Analyst",
    destination_key: str = "linkedin",
    custom_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a unique tracking link for a specific company job application.
    """
    links_data = load_json_file(LINKS_FILE, {"links": []})
    links = links_data.get("links", [])

    dest_url = custom_url if custom_url else DEFAULT_DESTINATIONS.get(destination_key, DEFAULT_DESTINATIONS["linkedin"])
    
    # Generate unique slug
    base_slug = f"{slugify(company)}-{destination_key}"
    slug = base_slug
    counter = 1
    existing_slugs = {item["slug"] for item in links}
    while slug in existing_slugs:
        counter += 1
        slug = f"{base_slug}-{counter}"

    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_link = {
        "id": f"trklink_{os.urandom(4).hex()}",
        "slug": slug,
        "company": company.strip(),
        "role": role.strip(),
        "destination_key": destination_key,
        "destination_url": dest_url,
        "tracking_path": f"/t/{slug}",
        "created_at": now_iso,
        "total_clicks": 0,
        "last_clicked": None,
        "recent_clicks": []
    }

    links.insert(0, new_link)
    save_json_file(LINKS_FILE, {"links": links})
    return new_link

def record_tracer_click(slug: str, user_agent: str, client_ip: str, referrer: str = "") -> Optional[str]:
    """
    Logs a click event when recruiter clicks the tracking link on Gourav's resume,
    and returns the final destination URL to redirect to.
    """
    links_data = load_json_file(LINKS_FILE, {"links": []})
    links = links_data.get("links", [])
    
    target_link = None
    for link in links:
        if link.get("slug") == slug:
            target_link = link
            break

    if not target_link:
        return None

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_link["total_clicks"] = target_link.get("total_clicks", 0) + 1
    target_link["last_clicked"] = now_str

    device_type = "Desktop"
    ua_lower = user_agent.lower()
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        device_type = "Mobile"
    elif "tablet" in ua_lower or "ipad" in ua_lower:
        device_type = "Tablet"

    click_event = {
        "id": f"clk_{os.urandom(4).hex()}",
        "slug": slug,
        "company": target_link.get("company", "Unknown"),
        "role": target_link.get("role", "Cybersecurity Analyst"),
        "destination_key": target_link.get("destination_key", "linkedin"),
        "timestamp": now_str,
        "device_type": device_type,
        "user_agent": user_agent[:150],
        "client_ip": client_ip,
        "referrer": referrer[:120] if referrer else "Direct / PDF Resume"
    }

    # Prepend to link's recent clicks
    target_link.setdefault("recent_clicks", []).insert(0, click_event)
    target_link["recent_clicks"] = target_link["recent_clicks"][:10]

    save_json_file(LINKS_FILE, {"links": links})

    # Also log to global clicks log
    all_clicks = load_json_file(CLICKS_FILE, {"clicks": []})
    clicks_list = all_clicks.get("clicks", [])
    clicks_list.insert(0, click_event)
    save_json_file(CLICKS_FILE, {"clicks": clicks_list[:200]})

    # Notify / update tracker board if job exists
    try:
        import tracker_engine
        tracker_data = tracker_engine.load_tracker_data()
        comp_lower = target_link.get("company", "").lower()
        for item in tracker_data.get("items", []):
            if comp_lower in item.get("company", "").lower():
                old_note = item.get("notes") or ""
                note_addition = f"\n[👀 Recruiter Click ({target_link['destination_key'].upper()}) at {now_str} via {device_type}]"
                if note_addition not in old_note:
                    tracker_engine.update_job_notes(
                        item["id"],
                        old_note + note_addition,
                        item.get("referral_contact") or ""
                    )
                break
    except Exception:
        pass

    return target_link.get("destination_url")

def get_tracer_stats() -> Dict[str, Any]:
    """
    Returns summary statistics of resume link clicks.
    """
    links_data = load_json_file(LINKS_FILE, {"links": []})
    clicks_data = load_json_file(CLICKS_FILE, {"clicks": []})

    links = links_data.get("links", [])
    clicks = clicks_data.get("clicks", [])

    total_clicks = sum(link.get("total_clicks", 0) for link in links)
    
    companies_clicked = {}
    for clk in clicks:
        comp = clk.get("company", "Other")
        companies_clicked[comp] = companies_clicked.get(comp, 0) + 1

    return {
        "status": "success",
        "total_active_links": len(links),
        "total_recruiter_clicks": total_clicks,
        "links": links,
        "recent_clicks": clicks[:20],
        "top_engaged_companies": sorted(
            [{"company": k, "clicks": v} for k, v in companies_clicked.items()],
            key=lambda x: x["clicks"],
            reverse=True
        )[:5]
    }
