"""
CyberSwitch 10X - Experience Bank & Anti-Hallucination CV Tailor (Phase 5)
Stores Gourav Pandit Parit's verified Wipro SOC L2 accomplishments.
Matches target JDs with 100% truthful, pre-vetted STAR bullets,
customized 30s interview pitches, and recruiter outreach messages with embedded tracer links.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
BANK_FILE = os.path.join(DATA_DIR, "experience_bank.json")

# Verified Accomplishments of Gourav Pandit Parit (Wipro SOC L2, SC-200, Palo Alto, Splunk)
DEFAULT_EXPERIENCE_BANK = [
    # Category: Microsoft Sentinel & SC-200 (KQL)
    {
        "id": "exp_sentinel_01",
        "category": "Microsoft Sentinel & KQL",
        "keywords": ["sentinel", "kql", "azure", "entra", "detection", "analytics", "hunting"],
        "impact_score": 96,
        "bullet": "Architected and tuned 25+ KQL analytics rules in Microsoft Sentinel to detect credential stuffing, Entra ID token theft, and lateral movement, reducing false positives by 42%.",
        "star_story": {
            "situation": "High false-positive rate from native Azure sign-in alerts overloading the SOC L1 triage queue.",
            "task": "Build customized KQL detection logic to isolate high-risk sign-ins and correlate with Defender for Endpoint signals.",
            "action": "Engineered multi-table KQL joins across SigninLogs, AADNonInteractiveUserSignInLogs, and DeviceNetworkEvents with anomaly baselining.",
            "result": "Reduced false-positive noise by 42% and caught 3 distinct unauthorized OAuth app consent grants within 15 minutes of occurrence."
        }
    },
    {
        "id": "exp_sentinel_02",
        "category": "Microsoft Sentinel & KQL",
        "keywords": ["sentinel", "playbooks", "logic apps", "automation", "soar", "mttr"],
        "impact_score": 93,
        "bullet": "Automated SOC L2 incident triage playbooks via Azure Logic Apps, enabling instant host isolation and IP blocking that cut Mean Time to Remediate (MTTR) by 35%.",
        "star_story": {
            "situation": "Manual IP containment on border firewalls took an average of 45 minutes during off-peak hours.",
            "task": "Automate response playbooks triggered directly by high-severity Sentinel incidents.",
            "action": "Built Logic App connectors integrating Sentinel with Palo Alto Panorama and Microsoft Defender for Endpoint APIs.",
            "result": "Automated initial containment to under 90 seconds, freeing up 20+ hours of analyst time weekly."
        }
    },
    {
        "id": "exp_mde_03",
        "category": "Microsoft Defender for Endpoint (MDE)",
        "keywords": ["defender", "mde", "edr", "endpoint", "live response", "ioc", "malware"],
        "impact_score": 91,
        "bullet": "Executed deep-dive threat hunting and malware investigations across 12,000+ endpoints using Microsoft Defender for Endpoint (MDE) Live Response, memory inspection, and timeline triage.",
        "star_story": {
            "situation": "A workstation flagged anomalous PowerShell script execution with disguised base64 payloads.",
            "task": "Determine root cause, scope of compromise, and prevent lateral spread.",
            "action": "Initiated Live Response session, isolated machine, dumped process memory, decoded obfuscated script, and identified living-off-the-land binary (LOLBin) usage.",
            "result": "Blocked command-and-control IP enterprise-wide and issued a remediation advisory before any data staging occurred."
        }
    },

    # Category: Palo Alto Next-Gen Firewalls & Panorama
    {
        "id": "exp_palo_01",
        "category": "Palo Alto NGFW & Panorama",
        "keywords": ["palo alto", "panorama", "ngfw", "security policies", "nat", "decryption"],
        "impact_score": 95,
        "bullet": "Administered enterprise Palo Alto Next-Gen Firewalls (PA-3200 & PA-5200 series) via Panorama, managing Security Policies, Decryption, and NAT rules across segmented corporate zones.",
        "star_story": {
            "situation": "Corporate perimeter needed strict micro-segmentation to comply with ISO 27001 and RBI cyber security frameworks.",
            "task": "Migrate legacy port-based policies into zero-trust application-based rules without breaking production traffic.",
            "action": "Audited traffic using Panorama Policy Optimizer, converted legacy Any-Any rules to App-ID specific policies with App-ID adoption.",
            "result": "Zero downtime migration across 140+ policy rules, reducing attack surface by 60%."
        }
    },
    {
        "id": "exp_palo_02",
        "category": "Palo Alto NGFW & Panorama",
        "keywords": ["wildfire", "threat prevention", "app-id", "user-id", "url filtering", "c2"],
        "impact_score": 92,
        "bullet": "Configured and maintained Palo Alto Security Profiles (Antivirus, Anti-Spyware with DNS Sinkholing, Vulnerability Protection, and WildFire) blocking 100% of detected C2 beaconing attempts.",
        "star_story": {
            "situation": "DNS-tunneling malware variants attempting C2 exfiltration across egress gateways.",
            "task": "Enforce strict DNS sinkholing and real-time WildFire threat intelligence feeds.",
            "action": "Activated Palo Alto DNS Security, sinkholed malicious domains to internal loopback, and tuned anti-spyware profiles for strict blocking.",
            "result": "Blocked over 1,200 malicious connection attempts in Q3 alone with full attribution via User-ID."
        }
    },

    # Category: VMware NSX Micro-segmentation
    {
        "id": "exp_nsx_01",
        "category": "VMware NSX",
        "keywords": ["nsx", "vmware", "micro-segmentation", "east-west", "virtualization", "distributed firewall"],
        "impact_score": 88,
        "bullet": "Enforced East-West micro-segmentation policies using VMware NSX Distributed Firewall (DFW) and Security Groups, preventing unauthorized lateral movement within virtualized datacenter clusters.",
        "star_story": {
            "situation": "Flat virtual network allowed internal VM-to-VM traversal between development and staging environments.",
            "task": "Implement zero-trust security tagging and distributed firewall filtering at the virtual NIC level.",
            "action": "Mapped application dependency flows, applied NSX security tags, and defined least-privilege DFW rules.",
            "result": "Isolated PCI-DSS and sensitive workload clusters with zero impact on legitimate application performance."
        }
    },

    # Category: Splunk SIEM & Correlation Searches
    {
        "id": "exp_splunk_01",
        "category": "Splunk SIEM (SPL)",
        "keywords": ["splunk", "spl", "siem", "correlation", "dashboards", "data models"],
        "impact_score": 94,
        "bullet": "Authored advanced Splunk SPL queries, correlation searches, and executive security dashboards ingesting 2.5+ TB daily logs from Windows Event Logs, Sysmon, and proxy appliances.",
        "star_story": {
            "situation": "SOC analysts lacked visibility into anomalous service creations (Event ID 7045) across tier-0 domain controllers.",
            "task": "Build high-fidelity Splunk correlation searches with automated alert dispatching.",
            "action": "Constructed optimized SPL searches leveraging tstats and CIM-compliant data models for sub-second execution across massive index clusters.",
            "result": "Detected 100% of unauthorized service installations with zero pipeline latency."
        }
    },

    # Category: SOC L2 Incident Triage & MITRE ATT&CK
    {
        "id": "exp_soc_01",
        "category": "SOC L2 Incident Response",
        "keywords": ["soc", "incident response", "mitre", "nist", "forensics", "triage", "escalation"],
        "impact_score": 97,
        "bullet": "Spearheaded SOC L2 incident triage and forensic containment for P1/P2 incidents adhering to NIST SP 800-61 and mapping threat actor TTPs directly to the MITRE ATT&CK matrix.",
        "star_story": {
            "situation": "Critical ransomware precursor alert triggered across an internal database server cluster.",
            "task": "Coordinate immediate containment, trace patient zero, and prevent payload deployment.",
            "action": "Invoked incident response protocol, isolated affected VLAN via firewall rule override, retrieved artifact memory dumps, and sanitized persistence registry keys.",
            "result": "Prevented data encryption with zero data loss; delivered post-mortem report to CISO within 4 hours."
        }
    }
]

def load_experience_bank() -> List[Dict[str, Any]]:
    if not os.path.exists(BANK_FILE):
        save_experience_bank(DEFAULT_EXPERIENCE_BANK)
        return DEFAULT_EXPERIENCE_BANK
    try:
        with open(BANK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_EXPERIENCE_BANK

def save_experience_bank(bank_data: List[Dict[str, Any]]):
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(bank_data, f, indent=2, ensure_ascii=False)

def tailor_for_job(
    company: str,
    title: str,
    description: str,
    user_tracer_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes a target job, scores Gourav's verified experience points,
    and returns tailored resume bullets, match percentage, customized pitch,
    and personalized recruiter outreach message.
    """
    bank = load_experience_bank()
    jd_lower = (company + " " + title + " " + description).lower()

    # Score each bullet against JD
    scored_items = []
    matched_skills = set()

    for item in bank:
        score = 0
        hits = []
        for kw in item["keywords"]:
            if kw in jd_lower:
                score += 15
                hits.append(kw)
                matched_skills.add(kw.capitalize())

        # Additional domain bonus
        if "sentinel" in jd_lower and "sentinel" in item["category"].lower():
            score += 25
        if "palo alto" in jd_lower and "palo alto" in item["category"].lower():
            score += 25
        if "splunk" in jd_lower and "splunk" in item["category"].lower():
            score += 25
        if "incident" in jd_lower and "incident" in item["category"].lower():
            score += 20

        scored_items.append({
            "item": item,
            "score": score + (item.get("impact_score", 85) // 5),
            "hits": hits
        })

    # Sort by relevance score
    scored_items.sort(key=lambda x: x["score"], reverse=True)
    top_bullets = [x["item"]["bullet"] for x in scored_items[:5]]
    top_stories = [x["item"]["star_story"] for x in scored_items[:2]]

    # Generate customized 30s elevator pitch
    elev_pitch = (
        f"Hi, I'm Gourav. Over the past 2+ years as a Cybersecurity Analyst at Wipro, "
        f"I've specialized in SOC L2 incident triage, Microsoft Sentinel KQL rule engineering, "
        f"and Palo Alto Next-Gen Firewall policy administration via Panorama. "
        f"When evaluating {company}'s security posture, my background in automating threat containment "
        f"and reducing MTTR by 35% directly translates to protecting {company}'s enterprise infrastructure "
        f"from Day 1 without requiring ramp-up time."
    )

    # Generate high-impact LinkedIn Recruiter / Referral Outreach DM
    tracer_part = f"\n📄 My Verified Profile & Credly Badges: {user_tracer_url}" if user_tracer_url else ""
    recruiter_dm = (
        f"Hi [Name],\n\n"
        f"I noticed the {title} opening at {company}. "
        f"I'm a Cybersecurity Analyst at Wipro with 2+ years of hands-on experience across "
        f"Microsoft Sentinel (SC-200 / KQL), Palo Alto NGFWs (Panorama), and SOC L2 incident response.\n\n"
        f"In my current role, I've reduced MTTR by 35% and engineered automated triage playbooks. "
        f"I would love to learn more about the team's security priorities or connect for an internal referral!{tracer_part}\n\n"
        f"Best regards,\n"
        f"Gourav Pandit Parit"
    )

    return {
        "status": "success",
        "company": company,
        "title": title,
        "matched_skills": sorted(list(matched_skills)),
        "tailored_bullets": top_bullets,
        "star_case_studies": top_stories,
        "elevator_pitch": elev_pitch,
        "recruiter_dm": recruiter_dm
    }
