"""
CyberSwitch 10X - 1-Click ATS Auto-Fill Engine (Phase 6)
Stores Gourav Pandit Parit's standardized candidate profile and generates
autofill scripts/extensions for Workday, Greenhouse, Lever, and Taleo ATS portals.
"""

import os
import json
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

PROFILE_FILE = os.path.join(DATA_DIR, "candidate_profile.json")

DEFAULT_CANDIDATE_PROFILE = {
    "first_name": "Gourav",
    "last_name": "Parit",
    "full_name": "Gourav Pandit Parit",
    "email": "gourav.parit.cyber@gmail.com",
    "phone": "+91 9876543210",
    "address_line": "Hinjawadi Phase 1",
    "city": "Pune",
    "state": "Maharashtra",
    "country": "India",
    "postal_code": "411057",
    "current_company": "Wipro",
    "current_title": "Cybersecurity Analyst (SOC L2)",
    "years_experience": "2.5",
    "notice_period_days": "30",
    "current_ctc": "4 LPA",
    "expected_ctc": "12 - 15 LPA",
    "linkedin_url": "https://www.linkedin.com/in/gourav-parit/",
    "github_url": "https://github.com/gourav-parit",
    "portfolio_url": "https://www.credly.com/users/gourav-parit/",
    "certifications": "Microsoft Certified: Security Operations Analyst Associate (SC-200)",
    "primary_skills": "Microsoft Sentinel, KQL, Microsoft Defender for Endpoint (MDE), Palo Alto NGFW, Panorama, Splunk SIEM, VMware NSX, SOC L2 Incident Triage, MITRE ATT&CK",
    "work_authorization": "Yes, authorized to work in India without sponsorship",
    "require_sponsorship": "No",
    "gender": "Male",
    "summary": "Cybersecurity Analyst at Wipro with 2+ years of specialized experience in SOC L2 triage, Microsoft Sentinel KQL query engineering, Palo Alto Next-Gen Firewall policy administration (Panorama), and threat containment across enterprise environments."
}

def load_candidate_profile() -> Dict[str, Any]:
    if not os.path.exists(PROFILE_FILE):
        save_candidate_profile(DEFAULT_CANDIDATE_PROFILE)
        return DEFAULT_CANDIDATE_PROFILE
    try:
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CANDIDATE_PROFILE

def save_candidate_profile(profile: Dict[str, Any]):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

def get_bookmarklet_code(host_url: str = "http://localhost:8000") -> str:
    """
    Generates a 1-click JavaScript Bookmarklet that candidate can drag to bookmarks bar.
    When clicked on any Workday, Greenhouse, or Lever page, it fetches the candidate profile
    from localhost:8000 and fills out all matching fields in 500ms.
    """
    js = f"""(function(){{
  var host='{host_url}';
  fetch(host+'/api/autofill/profile')
    .then(r=>r.json())
    .then(p=>{{
      var fill=function(selectors, val){{
        if(!val) return;
        for(var i=0; i<selectors.length; i++){{
          var el=document.querySelector(selectors[i]);
          if(el){{
            el.value=val;
            el.dispatchEvent(new Event('input', {{bubbles:true}}));
            el.dispatchEvent(new Event('change', {{bubbles:true}}));
            el.style.border='2px solid #10b981';
            return;
          }}
        }}
      }};
      fill(['input[data-automation-id="legalNameSection_firstName"]', 'input[id*="first_name"]', 'input[name*="first_name"]'], p.first_name);
      fill(['input[data-automation-id="legalNameSection_lastName"]', 'input[id*="last_name"]', 'input[name*="last_name"]'], p.last_name);
      fill(['input[data-automation-id="email"]', 'input[id*="email"]', 'input[type="email"]'], p.email);
      fill(['input[data-automation-id="phone-number"]', 'input[id*="phone"]', 'input[type="tel"]'], p.phone);
      fill(['input[data-automation-id="addressSection_city"]', 'input[id*="city"]'], p.city);
      fill(['input[data-automation-id="addressSection_postalCode"]', 'input[id*="postal"]'], p.postal_code);
      fill(['input[id*="linkedin"]', 'input[name*="linkedin"]'], p.linkedin_url);
      fill(['input[id*="github"]', 'input[name*="github"]'], p.github_url);
      fill(['input[data-automation-id="jobTitle"]', 'input[id*="title"]'], p.current_title);
      fill(['input[data-automation-id="company"]', 'input[id*="company"]'], p.current_company);
      alert('⚡ CyberSwitch: Autofilled application for '+p.full_name+'!');
    }})
    .catch(e=>alert('CyberSwitch Autofill: Ensure localhost:8000 is running!'));
}})();"""
    return "javascript:" + "".join(line.strip() for line in js.splitlines())
