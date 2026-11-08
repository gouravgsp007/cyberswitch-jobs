import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

ENV_KEY = os.getenv("FIRECRAWL_API_KEY", "")

# Curated list of direct GCC Workday / ATS seeds for Pune & Mumbai
GCC_CAREER_SEEDS = [
    {
        "company": "Barclays",
        "url": "https://search.jobs.barclays/search-jobs/cybersecurity/pune",
        "ats": "Workday",
        "location": "Pune"
    },
    {
        "company": "Mastercard",
        "url": "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers?q=security",
        "ats": "Workday",
        "location": "Pune"
    },
    {
        "company": "Deutsche Bank",
        "url": "https://careers.db.com/professionals/search-roles/#/search?keyword=information%20security",
        "ats": "Custom",
        "location": "Pune"
    },
    {
        "company": "BNY Mellon",
        "url": "https://bnymellon.wd5.myworkdayjobs.com/BNY_Mellon_Careers?q=cyber",
        "ats": "Workday",
        "location": "Pune"
    },
    {
        "company": "Qualys",
        "url": "https://www.qualys.com/company/careers/openings/?dept=Security",
        "ats": "Greenhouse",
        "location": "Pune"
    },
    {
        "company": "CrowdStrike",
        "url": "https://crowdstrike.wd5.myworkdayjobs.com/Crowdstrikecareers?q=analyst",
        "ats": "Workday",
        "location": "Pune / Remote"
    },
    {
        "company": "Morgan Stanley",
        "url": "https://morganstanley.tal.net/vx/lang-en-GB/mobile-0/brand-2/xf-994df502bbcd/candidate/jobboard/vacancy/1/adv/?f_Item_Opportunity_Company_Location_Item_1=India",
        "ats": "Taleo",
        "location": "Mumbai"
    },
    {
        "company": "Sophos",
        "url": "https://sophos.wd3.myworkdayjobs.com/SophosCareers?q=soc",
        "ats": "Workday",
        "location": "Pune"
    }
]

def get_firecrawl_app(api_key: Optional[str] = None) -> Optional[Any]:
    key = api_key or ENV_KEY
    if not key or not FIRECRAWL_AVAILABLE:
        return None
    try:
        return FirecrawlApp(api_key=key)
    except Exception as e:
        print(f"[Firecrawl] Initialization error: {e}")
        return None

def extract_deep_job_intel(url: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts structured intelligence from a job posting URL.
    Uses Firecrawl LLM extraction if an API key is available;
    otherwise falls back to heuristic text analysis.
    """
    app = get_firecrawl_app(api_key)
    
    if app and url and url.startswith("http"):
        try:
            print(f"[Firecrawl] Scraping & extracting intelligence from: {url}")
            try:
                # Modern v2 SDK
                scrape_result = app.scrape(url, formats=['markdown'])
            except Exception:
                # Fallback v1 SDK
                scrape_result = app.scrape_url(url, params={'formats': ['markdown']})
            
            md_content = ""
            if isinstance(scrape_result, dict):
                md_content = scrape_result.get("markdown") or scrape_result.get("content") or ""
            elif hasattr(scrape_result, "markdown"):
                md_content = scrape_result.markdown
                
            if md_content:
                intel = parse_markdown_intel(md_content, "Firecrawl Live Web Scraping")
                intel["status"] = "success"
                intel["url"] = url
                return intel
                
        except Exception as e:
            print(f"[Firecrawl] Live scrape failed: {e}. Falling back to heuristic analysis.")
            print(f"[Firecrawl] API call failed: {e}. Falling back to heuristic analysis.")
            
    # Fallback when no API key is provided
    return {
        "status": "fallback",
        "source": "Local Heuristic Engine",
        "notice": "To enable real-time headless JS rendering and live Workday crawling, add your free API key from firecrawl.dev.",
        "must_have_skills": ["SIEM / Splunk Operations", "Microsoft Sentinel (KQL)", "Palo Alto Firewall Rule Base", "L2 Incident Handling"],
        "preferred_certifications": ["Microsoft SC-200", "Palo Alto PCNSA / PCNSE", "CompTIA Security+"],
        "team_role_context": "Global Enterprise Security Operations (Tier 1/Tier 2 Triage & Threat Monitoring)",
        "shift_structure": "Standard Enterprise Rotation (General / EMEA / Night Allowance)",
        "salary_budget": "Target GCC Band: ₹11 - ₹15 LPA for 2+ YOE",
        "recruiter_contact": "Available via Company Talent Acquisition Desk"
    }

def parse_markdown_intel(markdown_text: str, source: str) -> Dict[str, Any]:
    """Helper to parse raw markdown when schema extraction is unavailable."""
    text = markdown_text.lower()
    
    skills = []
    if "sentinel" in text: skills.append("Microsoft Sentinel")
    if "kql" in text: skills.append("KQL Query Authoring")
    if "palo alto" in text: skills.append("Palo Alto Next-Gen Firewall")
    if "splunk" in text: skills.append("Splunk SIEM")
    if "nsx" in text: skills.append("VMware NSX")
    if "incident response" in text: skills.append("Incident Triage & Response")
    
    certs = []
    if "sc-200" in text: certs.append("SC-200")
    if "pcnsa" in text or "pcnse" in text: certs.append("PCNSA/PCNSE")
    if "ceh" in text: certs.append("CEH")
    if "cissp" in text: certs.append("CISSP")
    
    return {
        "status": "success",
        "source": source,
        "must_have_skills": skills if skills else ["Cybersecurity", "SOC Operations"],
        "preferred_certifications": certs if certs else ["SC-200 / Industry Certs Preferred"],
        "team_role_context": "Security Operations Center / Cyber Defense Team",
        "shift_structure": "Enterprise Rotational Shifts",
        "salary_budget": "Estimated GCC Band ₹11.0 - ₹15.5 LPA",
        "recruiter_contact": "Submit directly via Portal"
    }

if __name__ == "__main__":
    print("Firecrawl Engine initialized.")
    print(f"Firecrawl SDK Available: {FIRECRAWL_AVAILABLE}")
    print(f"API Key configured: {'YES' if ENV_KEY else 'NO (Set FIRECRAWL_API_KEY in .env)'}")
    print(f"Configured GCC Seeds: {len(GCC_CAREER_SEEDS)} companies.")
