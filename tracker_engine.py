import os
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
TRACKER_JSON_PATH = os.path.join(DATA_DIR, "application_tracker.json")

VALID_STAGES = [
    "wishlist",
    "applied",
    "screening",
    "technical",
    "managerial",
    "offer",
    "rejected"
]

STAGE_LABELS = {
    "wishlist": "Wishlist",
    "applied": "Applied / Referred",
    "screening": "HR Screening",
    "technical": "Technical L2",
    "managerial": "Managerial Round",
    "offer": "10+ LPA Offer",
    "rejected": "Archived"
}

def load_tracker_data() -> List[Dict[str, Any]]:
    """Loads all tracked job applications from persistent storage."""
    if not os.path.exists(TRACKER_JSON_PATH):
        return []
    try:
        with open(TRACKER_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[Tracker] Error loading tracker data: {e}")
        return []

def save_tracker_data(items: List[Dict[str, Any]]) -> bool:
    """Saves tracked job applications atomically."""
    try:
        temp_path = TRACKER_JSON_PATH + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        os.replace(temp_path, TRACKER_JSON_PATH)
        return True
    except Exception as e:
        print(f"[Tracker] Error saving tracker data: {e}")
        return False

def add_job_to_tracker(job_data: Dict[str, Any], initial_stage: str = "wishlist") -> Dict[str, Any]:
    """
    Adds a job to the Kanban tracker. Prevents duplicate tracking by URL or job title + company.
    """
    items = load_tracker_data()
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_stage = initial_stage if initial_stage in VALID_STAGES else "wishlist"
    
    url = job_data.get("apply_url") or job_data.get("job_post_url") or job_data.get("url") or ""
    title = str(job_data.get("title", "Cybersecurity Analyst")).strip()
    company = str(job_data.get("company", "Enterprise")).strip()
    
    # Check if already tracked
    for item in items:
        if (url and item.get("apply_url") == url) or (
            item.get("title", "").lower() == title.lower() and 
            item.get("company", "").lower() == company.lower()
        ):
            return {"status": "exists", "message": "Job is already on your tracking board", "item": item}
            
    track_id = f"trk_{uuid.uuid4().hex[:8]}"
    new_entry = {
        "id": track_id,
        "job_id": job_data.get("id", track_id),
        "title": title,
        "company": company,
        "location": job_data.get("location", "Pune / Mumbai"),
        "salary": job_data.get("salary") or job_data.get("ctc") or "₹11.0 - ₹15.5 LPA (Target GCC Band)",
        "experience": job_data.get("experience", "2 - 3 Years"),
        "source": job_data.get("source", "Direct ATS / Portal"),
        "apply_url": url,
        "stage": target_stage,
        "ghost_job_risk": job_data.get("ghost_job_risk", "Low Risk"),
        "ghost_job_note": job_data.get("ghost_job_note", "Active Requisition"),
        "notes": job_data.get("notes", "Added from CyberSwitch Job Radar. Target: 10-15 LPA."),
        "referral_contact": job_data.get("referral_contact", ""),
        "created_at": now_iso,
        "updated_at": now_iso,
        "history": [
            {"stage": target_stage, "timestamp": now_iso, "note": "Initial placement"}
        ]
    }
    
    updated_items = [new_entry] + items
    save_tracker_data(updated_items)
    return {"status": "success", "message": f"Added {title} at {company} to {STAGE_LABELS[target_stage]}", "item": new_entry}

def update_job_stage(track_id: str, new_stage: str, note: str = "") -> Optional[Dict[str, Any]]:
    """
    Moves an application to a new Kanban stage and appends an audit event to its history.
    """
    if new_stage not in VALID_STAGES:
        return None
        
    items = load_tracker_data()
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_item = None
    
    new_items = []
    for item in items:
        if item.get("id") == track_id:
            old_stage = item.get("stage", "wishlist")
            history = list(item.get("history", []))
            history.append({
                "from": old_stage,
                "stage": new_stage,
                "timestamp": now_iso,
                "note": note or f"Moved to {STAGE_LABELS[new_stage]}"
            })
            item_copy = dict(item)
            item_copy["stage"] = new_stage
            item_copy["updated_at"] = now_iso
            item_copy["history"] = history
            updated_item = item_copy
            new_items.append(item_copy)
        else:
            new_items.append(item)
            
    if updated_item:
        save_tracker_data(new_items)
    return updated_item

def update_job_notes(track_id: str, notes: str, referral_contact: str = "") -> Optional[Dict[str, Any]]:
    """Updates notes and referral contacts on a tracked job."""
    items = load_tracker_data()
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updated_item = None
    
    new_items = []
    for item in items:
        if item.get("id") == track_id:
            item_copy = dict(item)
            item_copy["notes"] = notes
            if referral_contact is not None:
                item_copy["referral_contact"] = referral_contact
            item_copy["updated_at"] = now_iso
            updated_item = item_copy
            new_items.append(item_copy)
        else:
            new_items.append(item)
            
    if updated_item:
        save_tracker_data(new_items)
    return updated_item

def delete_tracker_job(track_id: str) -> bool:
    """Removes an application from the tracker."""
    items = load_tracker_data()
    new_items = [i for i in items if i.get("id") != track_id]
    if len(new_items) != len(items):
        save_tracker_data(new_items)
        return True
    return False

def get_tracker_summary() -> Dict[str, Any]:
    """Generates counts grouped by Kanban stage."""
    items = load_tracker_data()
    counts = {s: 0 for s in VALID_STAGES}
    for item in items:
        st = item.get("stage", "wishlist")
        if st in counts:
            counts[st] += 1
            
    return {
        "total_tracked": len(items),
        "stage_counts": counts,
        "items": items
    }
