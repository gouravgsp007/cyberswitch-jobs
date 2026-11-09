import os
import sys
import json
import job_engine
import workday_engine

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_FILE = os.path.join(DATA_DIR, "live_scraped_jobs.json")
PROCESSED_FILE = os.path.join(DATA_DIR, "processed_openings.json")

def run_sync():
    print("=" * 65)
    print("Direct Workday CXS & Greenhouse ATS Ingestion Engine")
    print("Strict Constraint: Strictly 2-3 YOE | Zero >3 YOE listings allowed")
    print("=" * 65)

    # 1. Crawl direct ATS jobs
    ats_jobs = workday_engine.crawl_all_direct_ats_jobs()
    print(f"\nCrawled {len(ats_jobs)} direct ATS jobs.")

    # 2. Load existing raw jobs
    raw_jobs = []
    if os.path.exists(RAW_FILE):
        with open(RAW_FILE, "r", encoding="utf-8") as f:
            raw_jobs = json.load(f)

    print(f"Existing raw database size: {len(raw_jobs)} jobs.")

    # 3. Merge ATS jobs with deduplication
    existing_urls = {j.get("url") or j.get("job_url") for j in raw_jobs}
    existing_tc = {f"{j.get('title', '').lower()}_{j.get('company', '').lower()}" for j in raw_jobs}

    added = 0
    for j in ats_jobs:
        u = j.get("url")
        tc = f"{j.get('title', '').lower()}_{j.get('company', '').lower()}"
        if u not in existing_urls and tc not in existing_tc:
            raw_jobs.append(j)
            if u:
                existing_urls.add(u)
            existing_tc.add(tc)
            added += 1

    print(f"Merged {added} fresh, unique direct ATS postings into raw database.")

    # Save updated raw database
    with open(RAW_FILE, "w", encoding="utf-8") as f:
        json.dump(raw_jobs, f, indent=2)

    # 4. Process and prioritize strictly 2-3 YOE
    processed = job_engine.process_raw_jobs(raw_jobs)
    print(f"Total processed database size (strictly 2-3 YOE): {len(processed)} jobs.")

    # 5. Save processed and Excel
    with open(PROCESSED_FILE, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2)

    job_engine.generate_excel_file(processed)
    print(f"Regenerated prioritized Excel workbook successfully ({job_engine.EXCEL_PATH})!")

    # 6. Dispatch alerts for top priority fresh matches
    try:
        import alert_engine
        p1_fresh = [p for p in processed if ("P1" in p.get("priority", "")) and ("Today" in p.get("posted_date", "") or "Just" in p.get("posted_date", "") or "1 day" in p.get("posted_date", ""))]
        alert_count = 0
        for j in p1_fresh[:10]:
            res = alert_engine.trigger_job_alert(j)
            if res.get("status") == "success":
                alert_count += 1
        if alert_count > 0:
            print(f"Dispatched {alert_count} fresh P1 job alerts (Telegram/Local)!")
    except Exception as e:
        print(f"Alert dispatch note: {e}")

    # Summary of direct ATS jobs currently in processed list
    ats_in_processed = [p for p in processed if "workday" in p["source"].lower() or "greenhouse" in p["source"].lower()]
    print(f"\nDirect ATS Jobs in Processed List: {len(ats_in_processed)}")
    for j in ats_in_processed[:5]:
        print(f" -> [{j['priority']}] {j['company']} - {j['title']} ({j['match_score']}%) | {j['location']}")

if __name__ == "__main__":
    run_sync()
