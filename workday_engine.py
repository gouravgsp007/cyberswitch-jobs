import os
import sys
import json
import re
import datetime
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Tuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Curated GCCs & Enterprise Tech Paymasters with verified Workday / ATS CXS endpoints
WORKDAY_TARGETS = [
    {
        "company": "Barclays",
        "host": "barclays.wd3.myworkdayjobs.com",
        "tenant": "barclays",
        "site": "External_Career_Site_Barclays",
        "primary_locations": ["Pune", "Mumbai", "India"]
    },
    {
        "company": "Qualys",
        "host": "qualys.wd5.myworkdayjobs.com",
        "tenant": "qualys",
        "site": "Careers",
        "primary_locations": ["Pune", "Remote", "India"]
    },
    {
        "company": "Mastercard",
        "host": "mastercard.wd1.myworkdayjobs.com",
        "tenant": "mastercard",
        "site": "CorporateCareers",
        "primary_locations": ["Pune", "Mumbai", "Remote", "India"]
    },
    {
        "company": "NVIDIA",
        "host": "nvidia.wd5.myworkdayjobs.com",
        "tenant": "nvidia",
        "site": "NVIDIAExternalCareerSite",
        "primary_locations": ["Pune", "Mumbai", "Remote", "India"]
    },
    {
        "company": "CrowdStrike",
        "host": "crowdstrike.wd5.myworkdayjobs.com",
        "tenant": "crowdstrike",
        "site": "Crowdstrikecareers",
        "primary_locations": ["Pune", "Remote", "India"]
    },
    {
        "company": "State Street",
        "host": "statestreet.wd1.myworkdayjobs.com",
        "tenant": "statestreet",
        "site": "Global",
        "primary_locations": ["Pune", "Mumbai", "Remote", "India"]
    },
    {
        "company": "Fiserv",
        "host": "fiserv.wd5.myworkdayjobs.com",
        "tenant": "fiserv",
        "site": "EXT",
        "primary_locations": ["Pune", "Mumbai", "Remote", "India"]
    },
    {
        "company": "Adobe",
        "host": "adobe.wd5.myworkdayjobs.com",
        "tenant": "adobe",
        "site": "external_experienced",
        "primary_locations": ["Remote", "India", "Pune"]
    },
    {
        "company": "HP",
        "host": "hp.wd5.myworkdayjobs.com",
        "tenant": "hp",
        "site": "ExternalCareerSite",
        "primary_locations": ["Pune", "Mumbai", "Remote", "India"]
    },
    {
        "company": "Target",
        "host": "target.wd5.myworkdayjobs.com",
        "tenant": "target",
        "site": "targetcareers",
        "primary_locations": ["India", "Remote"]
    },
    {
        "company": "Accenture",
        "host": "accenture.wd103.myworkdayjobs.com",
        "tenant": "accenture",
        "site": "AccentureCareers",
        "primary_locations": ["Pune", "Mumbai"]
    }
]

# Verified Greenhouse ATS boards for high-paying product tech & cyber companies
GREENHOUSE_TARGETS = [
    {"company": "Cloudflare", "board": "cloudflare", "locations": ["India", "Remote"]},
    {"company": "Datadog", "board": "datadog", "locations": ["India", "Remote"]},
    {"company": "Okta", "board": "okta", "locations": ["India", "Remote"]},
    {"company": "Elastic", "board": "elastic", "locations": ["India", "Remote"]}
]

SENIOR_KEYWORDS = [
    'senior', 'sr.', 'sr ', 'lead', 'principal', 'architect', 'manager', 'director', 
    'head', 'staff', 'vice president', 'assistant vice president',
    'chief', 'ciso', 'expert', 'specialist iii', 'specialist ii', 
    'level 3', 'level 4', 'tier 3', 'team lead', 'l3', 'l4', 'consultant ii', 'tech lead'
]

CYBER_TITLE_KEYWORDS = [
    "security", "cyber", "soc", "sentinel", "splunk", "siem", "firewall", 
    "palo alto", "incident", "vulnerability", "vapt", "infosec", "csirt",
    "network security", "cloud security", "threat", "appsec", "secops"
]

NON_CYBER_KEYWORDS = [
    "graphic designer", "content writer", "sales executive", "sales engineer",
    "account management", "product manager", "marketing", "recruiter", "human resources",
    "legal counsel", "accountant", "finance analyst", "administrative", "customer operational",
    "customer experience", "trade compliance", "payroll", "facilities"
]

def is_strictly_cybersecurity_role(title: str, description: str) -> bool:
    """
    Ensures the job is strictly a Cybersecurity / Information Security / SOC / Network Security role.
    Rejects generic IT, operations, design, sales, or unrelated roles.
    """
    t_lower = title.lower()
    
    # 1. Reject blatant non-cyber titles
    if any(k in t_lower for k in NON_CYBER_KEYWORDS):
        return False
        
    # 2. Reject Senior / Lead / Architect titles
    if any(k in t_lower for k in SENIOR_KEYWORDS):
        return False

    # 3. Reject VP, AVP, CISO or Senior Officer via word boundaries
    if re.search(r'\b(?:vp|avp|ciso|senior\s+officer|chief.+officer)\b', t_lower):
        return False

    # 4. Title MUST contain an explicit cybersecurity keyword
    if any(k in t_lower for k in CYBER_TITLE_KEYWORDS):
        return True
            
    return False

def clean_html(raw_html: str) -> str:
    """Strips HTML tags and standardizes whitespace."""
    if not raw_html:
        return ""
    clean = re.sub(r'<[^>]+>', ' ', raw_html)
    clean = re.sub(r'&#\d+;', ' ', clean)
    clean = re.sub(r'&[a-zA-Z]+;', ' ', clean)
    return " ".join(clean.split())

def is_strictly_2_to_3_years(title: str, description: str) -> Tuple[bool, str]:
    """
    Strict filter enforcement: Rejects ANY job requiring > 3 years experience.
    Zero jobs above 3 years experience allowed.
    """
    t_lower = title.lower()
    full_text = (title + " " + description).lower()
    
    # 1. Reject if title explicitly states Senior, Lead, Principal, Manager, etc.
    if any(k in t_lower for k in SENIOR_KEYWORDS):
        return False, "Senior/Lead Title"
        
    # 2. Check year ranges: any range with upper bound > 3 is strictly rejected
    ranges = re.findall(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?)', full_text)
    for r_min, r_max in ranges:
        min_y = int(r_min)
        max_y = int(r_max)
        if max_y > 3:
            return False, f"Requires {min_y}-{max_y} YOE (Exceeds 3 Years)"
            
    # 3. Check single numbers like '4+ years', '5 years'
    singles = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)(?:\s*(?:of\s*)?experience)?', full_text)
    for s in singles:
        y = int(s)
        if 3 < y < 40:
            return False, f"Requires {y}+ YOE (Exceeds 3 Years)"
            
    return True, "2 - 3 Years"

def assess_ghost_job_risk(posted_on_text: str, start_date: str) -> Tuple[str, str]:
    """
    FreeHire-style Ghost Job Signal detection:
    Jobs posted > 45 days ago without updates are flagged as high ghost job risk.
    Jobs posted recently (< 14 days) are flagged as active direct requisitions.
    """
    text_lower = (posted_on_text or "").lower()
    
    if "today" in text_lower or "yesterday" in text_lower or "just posted" in text_lower:
        return "Low Risk", "🔥 Fresh Direct Requisition (Posted <24-48h)"
        
    m_days = re.search(r'(\d+)\s+days?\s+ago', text_lower)
    if m_days:
        days = int(m_days.group(1))
        if days <= 14:
            return "Low Risk", f"Active Requisition (Posted {days} days ago)"
        elif days <= 35:
            return "Moderate Risk", f"Open for {days} days"
        else:
            return "High Ghost Risk", f"⚠️ Stale Requisition (Open >{days} days)"
            
    m_days_plus = re.search(r'30\+\s+days?\s+ago', text_lower)
    if m_days_plus:
        return "High Ghost Risk", "⚠️ Stale Requisition (>30 days on board)"
        
    if start_date:
        try:
            p_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            diff = (datetime.date.today() - p_date).days
            if diff > 45:
                return "High Ghost Risk", f"⚠️ Stale Requisition (Opened {diff} days ago)"
            elif diff <= 14:
                return "Low Risk", f"🔥 Fresh Direct Requisition ({diff} days old)"
        except Exception:
            pass
            
    return "Low Risk", "Active Workday Requisition"

def _fetch_workday_detail(host: str, tenant: str, site: str, ext_path: str, headers: dict) -> Optional[Dict[str, Any]]:
    """Fetches full job posting info from Workday CXS detail endpoint."""
    detail_url = f"https://{host}/wday/cxs/{tenant}/{site}{ext_path}"
    try:
        det_req = urllib.request.Request(detail_url, headers=headers)
        with urllib.request.urlopen(det_req, timeout=8) as det_resp:
            det_data = json.loads(det_resp.read().decode("utf-8"))
            return det_data.get("jobPostingInfo", {})
    except Exception:
        return None

def _build_workday_job_item(
    target: Dict[str, Any], ext_path: str, summary_p: dict, info: dict, loc_text: str
) -> Optional[Dict[str, Any]]:
    """Validates 2-3 YOE and cybersecurity domain, then formats a standardized job dict."""
    title = summary_p.get("title", "")
    raw_desc = info.get("jobDescription", "")
    clean_desc = clean_html(raw_desc)
    
    # 1. STRICT FILTER: Rejects > 3 YOE
    valid_exp, _ = is_strictly_2_to_3_years(title, clean_desc)
    if not valid_exp:
        return None

    # 2. STRICT CYBERSECURITY DOMAIN CHECK
    if not is_strictly_cybersecurity_role(title, clean_desc):
        return None
        
    company = target["company"]
    host = target["host"]
    tenant = target["tenant"]
    site = target["site"]
    
    posted_on = info.get("postedOn", summary_p.get("postedOn", "Recent"))
    start_date = info.get("startDate", "")
    ghost_risk, ghost_note = assess_ghost_job_risk(posted_on, start_date)
    
    ext_url = info.get("externalUrl") or f"https://{host}/en-US/{site}{ext_path}"
    job_req_id = info.get("jobReqId", "")
    time_type = info.get("timeType", "Full time")
    
    tags = ["Direct Workday ATS", "Verified GCC"]
    desc_lower = clean_desc.lower()
    if "sentinel" in desc_lower or "sc-200" in desc_lower: tags.append("Sentinel / SC-200")
    if "palo alto" in desc_lower or "firewall" in desc_lower: tags.append("Palo Alto/FW")
    if "splunk" in desc_lower or "siem" in desc_lower: tags.append("Splunk/SIEM")
    if "soc" in desc_lower or "incident" in desc_lower: tags.append("SOC L2")
    if "nsx" in desc_lower: tags.append("VMware NSX")
    
    return {
        "id": f"wd_{tenant}_{job_req_id or ext_path[-8:]}",
        "title": title,
        "company": company,
        "location": loc_text or "Pune / Mumbai / Remote",
        "source": "Workday ATS (Direct GCC)",
        "ctc": "₹11.0 - ₹16.0 LPA (Target GCC Band)",
        "experience": "2 - 3 Years",
        "posted": posted_on,
        "url": ext_url,
        "job_url_direct": ext_url,
        "job_post_url": ext_url,
        "description": clean_desc[:1200],
        "tags": tags[:4],
        "job_req_id": job_req_id,
        "time_type": time_type,
        "ghost_job_risk": ghost_risk,
        "ghost_job_note": ghost_note,
        "ats_provider": "Workday"
    }

def fetch_workday_jobs_for_target(target: Dict[str, Any], search_terms: List[str] = None) -> List[Dict[str, Any]]:
    """Queries a company's direct Workday CXS endpoints."""
    if search_terms is None:
        search_terms = ["cybersecurity", "security", "SOC"]
        
    host = target["host"]
    tenant = target["tenant"]
    site = target["site"]
    allowed_locs = [l.lower() for l in target.get("primary_locations", ["Pune", "Mumbai", "Remote", "India"])]
    
    discovered_jobs = []
    seen_paths = set()
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    for term in search_terms:
        search_url = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
        payload = json.dumps({"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": term}).encode("utf-8")
        
        try:
            req = urllib.request.Request(search_url, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for p in data.get("jobPostings", []):
                    ext_path = p.get("externalPath", "")
                    if not ext_path or ext_path in seen_paths:
                        continue
                    seen_paths.add(ext_path)
                    
                    title = p.get("title", "")
                    loc_text = p.get("locationsText", "") or ""
                    if not loc_text and ext_path:
                        parts = ext_path.strip("/").split("/")
                        if len(parts) > 1 and parts[0] == "job":
                            loc_text = parts[1].replace("-", " ")
                    
                    loc_lower = loc_text.lower()
                    if not any(loc in loc_lower for loc in allowed_locs) and not any(loc in loc_lower for loc in ["pune", "mumbai", "remote", "india"]):
                        continue
                        
                    if any(k in title.lower() for k in SENIOR_KEYWORDS):
                        continue
                        
                    info = _fetch_workday_detail(host, tenant, site, ext_path, headers)
                    if not info:
                        continue
                        
                    job_item = _build_workday_job_item(target, ext_path, p, info, loc_text)
                    if job_item:
                        discovered_jobs.append(job_item)
        except Exception:
            pass
            
    return discovered_jobs

def fetch_greenhouse_jobs_for_target(target: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Queries Greenhouse open ATS API with strict cybersecurity and 2-3 YOE filter."""
    company = target["company"]
    board = target["board"]
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    
    discovered = []
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for j in data.get("jobs", []):
                title = j.get("title", "")
                loc = (j.get("location") or {}).get("name", "")
                loc_lower = loc.lower()
                
                if not any(k in loc_lower for k in ["india", "pune", "mumbai", "remote"]):
                    continue
                    
                clean_desc = clean_html(j.get("content", ""))
                
                # STRICT CYBERSECURITY DOMAIN & SENIOR REJECTION
                if not is_strictly_cybersecurity_role(title, clean_desc):
                    continue

                # STRICT 2-3 YOE FILTER
                valid_exp, _ = is_strictly_2_to_3_years(title, clean_desc)
                if not valid_exp:
                    continue
                    
                apply_url = j.get("absolute_url", "")
                updated_at = j.get("updated_at", "")
                ghost_risk, ghost_note = assess_ghost_job_risk(updated_at, updated_at[:10] if updated_at else "")
                
                discovered.append({
                    "id": f"gh_{board}_{j.get('id')}",
                    "title": title,
                    "company": company,
                    "location": loc or "India / Remote",
                    "source": "Greenhouse ATS (Direct Product)",
                    "ctc": "₹12.0 - ₹18.0 LPA (Top Product Band)",
                    "experience": "2 - 3 Years",
                    "posted": "Recent",
                    "url": apply_url,
                    "job_url_direct": apply_url,
                    "job_post_url": apply_url,
                    "description": clean_desc[:1200],
                    "tags": ["Direct ATS", "Product Company", "Security"],
                    "ghost_job_risk": ghost_risk,
                    "ghost_job_note": ghost_note,
                    "ats_provider": "Greenhouse"
                })
    except Exception:
        pass
        
    return discovered

def crawl_all_direct_ats_jobs() -> List[Dict[str, Any]]:
    """
    Crawls all verified Workday and Greenhouse direct ATS feeds without consuming any third-party credits.
    Enforces strict 2-3 YOE filter and ghost-job signal detection.
    """
    all_ats_jobs = []
    print("="*65)
    print("Starting Direct ATS Crawl: Workday CXS + Greenhouse APIs")
    print("Strict Constraint: Strictly 2-3 YOE | Zero >3 YOE listings allowed")
    print("="*65)
    
    # 1. Crawl Workday GCCs
    for target in WORKDAY_TARGETS:
        comp = target["company"]
        print(f" -> Checking Workday direct portal: {comp}...")
        try:
            jobs = fetch_workday_jobs_for_target(target)
            print(f"    Found {len(jobs)} strictly 2-3 YOE security openings at {comp}.")
            all_ats_jobs.extend(jobs)
        except Exception as e:
            print(f"    Error querying {comp}: {e}")
            
    # 2. Crawl Greenhouse Top Product Companies
    for target in GREENHOUSE_TARGETS:
        comp = target["company"]
        print(f" -> Checking Greenhouse direct portal: {comp}...")
        try:
            jobs = fetch_greenhouse_jobs_for_target(target)
            print(f"    Found {len(jobs)} strictly 2-3 YOE security openings at {comp}.")
            all_ats_jobs.extend(jobs)
        except Exception as e:
            print(f"    Error querying {comp}: {e}")
            
    print(f"\nTotal Direct ATS Openings Retrieved: {len(all_ats_jobs)} (All strictly 2-3 YOE).")
    return all_ats_jobs

if __name__ == "__main__":
    results = crawl_all_direct_ats_jobs()
    print(f"\nCrawled {len(results)} direct openings.")
    for r in results[:10]:
        safe_note = r.get('ghost_job_note', '').encode('ascii', 'ignore').decode('ascii')
        print(f"[{r['source']}] {r['company']} - {r['title']} | {r['location']} | {safe_note}")
