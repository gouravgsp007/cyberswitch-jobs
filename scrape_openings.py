import os
import json
import time
import random
import pandas as pd
from jobspy import scrape_jobs

queries = [
    # Pune (Primary Location)
    {"search_term": "cybersecurity analyst", "location": "Pune, India"},
    {"search_term": "SOC analyst", "location": "Pune, India"},
    {"search_term": "information security analyst", "location": "Pune, India"},
    {"search_term": "Palo Alto firewall engineer", "location": "Pune, India"},
    {"search_term": "network security engineer", "location": "Pune, India"},
    {"search_term": "Microsoft Sentinel analyst", "location": "Pune, India"},
    {"search_term": "cloud security analyst", "location": "Pune, India"},
    {"search_term": "incident response analyst", "location": "Pune, India"},
    {"search_term": "SIEM Splunk engineer", "location": "Pune, India"},
    {"search_term": "VAPT security analyst", "location": "Pune, India"},
    
    # Mumbai & Navi Mumbai (Secondary Hub)
    {"search_term": "cybersecurity analyst", "location": "Mumbai, India"},
    {"search_term": "SOC analyst", "location": "Mumbai, India"},
    {"search_term": "network security engineer", "location": "Mumbai, India"},
    {"search_term": "cloud security engineer", "location": "Mumbai, India"},
    {"search_term": "incident response analyst", "location": "Mumbai, India"},

    # Remote / Pan-India
    {"search_term": "cybersecurity analyst", "location": "Remote, India"},
    {"search_term": "SOC analyst", "location": "Remote, India"},
    {"search_term": "cloud security engineer", "location": "Remote, India"},
]

all_jobs = []
seen_urls = set()
seen_titles_companies = set()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
RAW_JSON = os.path.join(DATA_DIR, "live_scraped_jobs.json")

# Load existing jobs to preserve and deduplicate
if os.path.exists(RAW_JSON):
    try:
        with open(RAW_JSON, "r", encoding="utf-8") as f:
            existing = json.load(f)
            for j in existing:
                u = j.get("url") or j.get("job_url") or ""
                tc = f"{j.get('title', '').lower()}_{j.get('company', '').lower()}"
                if u: seen_urls.add(u)
                if tc: seen_titles_companies.add(tc)
            all_jobs = existing
            print(f"[Init] Loaded {len(all_jobs)} existing cached jobs.")
    except Exception as e:
        print(f"[Init] Could not load previous cache: {e}")

print("="*65)
print("Starting Expanded Multi-Portal Scrape: LinkedIn, Indeed, Glassdoor, Naukri")
print("Target: 18 Comprehensive Cybersecurity Roles (Pune, Mumbai, Remote)")
print("Date Horizon: Past 30 Days (hours_old=720)")
print("="*65)

new_added_count = 0

for i, q in enumerate(queries, 1):
    term = q["search_term"]
    loc = q["location"]
    print(f"\n[{i}/{len(queries)}] Scraping: '{term}' in '{loc}'...")
    
    try:
        df = scrape_jobs(
            site_name=["indeed", "glassdoor", "linkedin", "naukri"],
            search_term=term,
            location=loc,
            results_wanted=30,
            hours_old=720,  # Past 30 days to catch all active GCC postings
            country_indeed='india'
        )
        
        if df is not None and len(df) > 0:
            found_this_batch = 0
            for _, row in df.iterrows():
                url = str(row.get("job_url", "")).strip()
                title = str(row.get("title", "Cybersecurity Analyst")).strip()
                company = str(row.get("company", "Enterprise")).strip()
                dedup_key = f"{title.lower()}_{company.lower()}"
                
                if url in seen_urls or dedup_key in seen_titles_companies:
                    continue
                if url: seen_urls.add(url)
                seen_titles_companies.add(dedup_key)
                
                location = str(row.get("location", loc)).strip()
                site = str(row.get("site", "portal")).capitalize()
                
                min_amt = row.get("min_amount")
                max_amt = row.get("max_amount")
                interval = row.get("interval", "")
                
                ctc_str = "Competitive / Market Standard"
                if pd.notna(min_amt) and pd.notna(max_amt) and min_amt > 0:
                    if interval == "yearly" or min_amt > 100000:
                        ctc_str = f"₹{min_amt/100000:.1f} - ₹{max_amt/100000:.1f} LPA"
                    elif interval == "monthly":
                        ctc_str = f"₹{min_amt:,.0f} - ₹{max_amt:,.0f} / mo"
                    else:
                        ctc_str = f"₹{min_amt} - ₹{max_amt} ({interval})"
                elif pd.notna(min_amt) and min_amt > 0:
                    ctc_str = f"From ₹{min_amt/100000:.1f} LPA" if min_amt > 100000 else f"₹{min_amt:,.0f}"
                else:
                    comp_lower = company.lower()
                    if any(t in comp_lower for t in ["barclays", "mastercard", "deutsche", "bny", "qualys", "crowdstrike", "morgan stanley", "ubs", "jefferies", "cisco"]):
                        ctc_str = "₹11.0 - ₹16.0 LPA (Target GCC Band)"
                    elif any(t in comp_lower for t in ["wipro", "tcs", "infosys", "cognizant", "tech mahindra"]):
                        ctc_str = "₹4.5 - ₹6.5 LPA (Service Band)"
                    else:
                        ctc_str = "₹9.0 - ₹14.0 LPA (Market Estimate)"

                date_posted = str(row.get("date_posted", "Recent"))
                if pd.isna(date_posted) or date_posted.lower() == "nan":
                    date_posted = "Recent"

                # Extract key matching tags
                tags = []
                lower_title = title.lower()
                desc = str(row.get("description", "")).lower()
                combined_text = lower_title + " " + desc
                
                if "soc" in combined_text or "tier 2" in combined_text or "l2" in combined_text: tags.append("SOC L2")
                if "splunk" in combined_text or "siem" in combined_text: tags.append("Splunk/SIEM")
                if "palo alto" in combined_text or "panorama" in combined_text or "firewall" in combined_text: tags.append("Palo Alto/FW")
                if "sentinel" in combined_text or "sc-200" in combined_text or "kql" in combined_text or "defender" in combined_text: tags.append("Sentinel / SC-200")
                if "nsx" in combined_text or "microsegmentation" in combined_text: tags.append("VMware NSX")
                if "incident" in combined_text or "csirt" in combined_text: tags.append("Incident Response")
                if "vulnerability" in combined_text or "vapt" in combined_text: tags.append("VAPT / Vulnerability")
                if "cloud" in combined_text or "azure" in combined_text or "aws" in combined_text: tags.append("Cloud Security")
                if not tags: tags.append("Cybersecurity")

                new_job = {
                    "id": f"live_{len(all_jobs) + 1}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": site,
                    "ctc": ctc_str,
                    "experience": "1-4 years",
                    "posted": date_posted,
                    "url": url,
                    "description": str(row.get("description", ""))[:1000],
                    "tags": tags[:4]
                }
                all_jobs.append(new_job)
                found_this_batch += 1
                new_added_count += 1
                
            print(f" -> Found {len(df)} postings ({found_this_batch} new unique added).")
        else:
            print(f" -> No new jobs returned.")
            
    except Exception as e:
        print(f" -> Scrape notice for '{term}': {e}")
        
    # Politeness jitter between searches
    time.sleep(random.uniform(1.5, 2.5))

print("\n" + "="*65)
print(f"Scrape Complete! Added {new_added_count} new postings.")
print(f"Total Unique Job Database Size: {len(all_jobs)} jobs.")
print("="*65)

# Save raw database
with open(RAW_JSON, "w", encoding="utf-8") as f:
    json.dump(all_jobs, f, indent=2)

print(f"Updated {RAW_JSON} successfully.")

# Run job_engine to prioritize and update Excel
try:
    import job_engine
    processed = job_engine.process_raw_jobs(all_jobs)
    job_engine.generate_excel_file(processed)
    
    PROCESSED_JSON = os.path.join(DATA_DIR, "processed_openings.json")
    with open(PROCESSED_JSON, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)
    print(f"Successfully regenerated prioritized Excel and processed database ({len(processed)} jobs)!")
except Exception as e:
    print(f"Error during job_engine prioritization: {e}")
