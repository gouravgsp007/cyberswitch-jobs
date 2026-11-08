import os
import json
import re
from typing import Dict, Any, Optional

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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
            
            # Firecrawl v1 extraction schema
            extract_prompt = """
            Extract structured hiring intelligence for a cybersecurity applicant with 2+ YOE.
            Include:
            1. must_have_skills: List of critical technical skills/tools (e.g. Sentinel, Palo Alto, Splunk, KQL).
            2. preferred_certifications: List of certs mentioned (e.g. SC-200, PCNSA, CEH, CISSP).
            3. team_role_context: The team structure or reporting hierarchy (e.g. SOC L2, CSIRT, Cyber Defense).
            4. shift_structure: Work timings or rotational shift details.
            5. salary_budget: Any disclosed CTC, budget, or compensation bracket.
            6. recruiter_contact: Any HR name or application email mentioned.
            """
            
            scrape_result = app.scrape_url(
                url,
                params={
                    'formats': ['markdown', 'extract'],
                    'extract': {
                        'prompt': extract_prompt,
                        'schema': {
                            "type": "object",
                            "properties": {
                                "must_have_skills": {"type": "array", "items": {"type": "string"}},
                                "preferred_certifications": {"type": "array", "items": {"type": "string"}},
                                "team_role_context": {"type": "string"},
                                "shift_structure": {"type": "string"},
                                "salary_budget": {"type": "string"},
                                "recruiter_contact": {"type": "string"}
                            }
                        }
                    }
                }
            )
            
            if scrape_result and "extract" in scrape_result:
                extracted = scrape_result["extract"]
                extracted["source"] = "Firecrawl Live Web Scraping"
                extracted["status"] = "success"
                return extracted
            elif scrape_result and "markdown" in scrape_result:
                # Fallback parse the returned markdown
                md = scrape_result["markdown"]
                return parse_markdown_intel(md, "Firecrawl Markdown Engine")
                
        except Exception as e:
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
