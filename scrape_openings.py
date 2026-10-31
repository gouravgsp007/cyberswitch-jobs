import os
import json
import pandas as pd
from jobspy import scrape_jobs

queries = [
    {"search_term": "cybersecurity analyst", "location": "Pune, India"},
    {"search_term": "SOC analyst", "location": "Pune, India"},
    {"search_term": "cybersecurity analyst", "location": "Mumbai, India"},
    {"search_term": "SOC analyst", "location": "Mumbai, India"},
    {"search_term": "information security analyst", "location": "Pune, India"},
    {"search_term": "Palo Alto firewall engineer", "location": "Pune, India"},
    {"search_term": "cybersecurity", "location": "Remote, India"},
]

all_jobs = []
seen_urls = set()

print("="*60)
print("Starting Comprehensive Live Job Scrape: LinkedIn & Naukri")
print("Target: Cybersecurity / SOC / SecOps (Pune, Mumbai, Remote)")
print("="*60)

for q in queries:
    term = q["search_term"]
    loc = q["location"]
    print(f"\n[Scraping] Term: '{term}' | Location: '{loc}'...")
    try:
        df = scrape_jobs(
            site_name=["linkedin", "naukri"],
            search_term=term,
            location=loc,
            results_wanted=20,
            hours_old=168, # past 7 days
            country_indeed='india'
        )
        if df is not None and len(df) > 0:
            print(f" -> Found {len(df)} jobs for '{term}' in {loc}")
            for _, row in df.iterrows():
                url = str(row.get("job_url", "")).strip()
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                title = str(row.get("title", "Cybersecurity Analyst")).strip()
                company = str(row.get("company", "Tech Company")).strip()
                location = str(row.get("location", loc)).strip()
                site = str(row.get("site", "portal")).capitalize()
                
                min_amt = row.get("min_amount")
                max_amt = row.get("max_amount")
                interval = row.get("interval", "")
                
                ctc_str = "Competitive / Market Standard"
                if pd.notna(min_amt) and pd.notna(max_amt) and min_amt > 0:
                    if interval == "yearly":
                        ctc_str = f"₹{min_amt/100000:.1f} - ₹{max_amt/100000:.1f} LPA"
                    else:
                        ctc_str = f"₹{min_amt} - ₹{max_amt} ({interval})"
                elif pd.notna(min_amt) and min_amt > 0:
                    ctc_str = f"From ₹{min_amt/100000:.1f} LPA"
                else:
                    # Provide realistic estimation based on company/role tier
                    if any(t in company.lower() for t in ["barclays", "mastercard", "deutsche", "bny", "qualys", "crowdstrike", "morgan stanley"]):
                        ctc_str = "₹11.0 - ₹15.5 LPA (Target GCC Band)"
                    elif any(t in company.lower() for t in ["wipro", "tcs", "infosys", "cognizant"]):
                        ctc_str = "₹4.5 - ₹6.5 LPA (Service Band)"
                    else:
                        ctc_str = "₹9.0 - ₹14.0 LPA (Market Estimate)"

                date_posted = str(row.get("date_posted", "Recent"))
                if pd.isna(date_posted) or date_posted.lower() == "nan":
                    date_posted = "Recent"

                # Extract key matching tags
                tags = []
                lower_title = title.lower()
                if "soc" in lower_title: tags.append("SOC L2")
                if "splunk" in lower_title or "siem" in lower_title: tags.append("Splunk/SIEM")
                if "palo alto" in lower_title or "firewall" in lower_title: tags.append("Firewall Admin")
                if "incident" in lower_title: tags.append("Incident Response")
                if "vulnerability" in lower_title or "vapt" in lower_title: tags.append("Vulnerability Mgmt")
                if "cloud" in lower_title or "sentinel" in lower_title: tags.append("Cloud / SC-200")
                if not tags: tags.append("Cybersecurity")

                all_jobs.append({
                    "id": f"live_{len(all_jobs) + 1}",
                    "title": title,
                    "company": company,
                    "location": location,
                    "source": site,
                    "ctc": ctc_str,
                    "experience": "1-4 years",
                    "posted": date_posted,
                    "url": url,
                    "tags": tags
                })
        else:
            print(f" -> No jobs returned for '{term}' in {loc}")
    except Exception as e:
        print(f" -> Error during scrape for '{term}' in {loc}: {e}")

print(f"\nCompleted! Total unique live jobs aggregated: {len(all_jobs)}")

# Save to data/live_scraped_jobs.json
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "live_scraped_jobs.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_jobs, f, indent=2)

print(f"Saved {len(all_jobs)} jobs to {out_path}")
