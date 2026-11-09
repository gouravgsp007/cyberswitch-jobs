import os
import json
import datetime
from typing import Optional
import uvicorn
from pydantic import BaseModel
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from job_engine import process_raw_jobs, generate_excel_file, EXCEL_PATH
from firecrawl_engine import extract_deep_job_intel, GCC_CAREER_SEEDS
import tracker_engine

app = FastAPI(title="Cybersecurity Job Search & Excel Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATIC_DIR = os.path.join(BASE_DIR, "static")
PROCESSED_JSON = os.path.join(DATA_DIR, "processed_openings.json")
RAW_JSON = os.path.join(DATA_DIR, "live_scraped_jobs.json")

def get_processed_jobs():
    if os.path.exists(PROCESSED_JSON):
        with open(PROCESSED_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    elif os.path.exists(RAW_JSON):
        with open(RAW_JSON, "r", encoding="utf-8") as f:
            raw = json.load(f)
        processed = process_raw_jobs(raw)
        generate_excel_file(processed)
        with open(PROCESSED_JSON, "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=2)
        return processed
    return []

@app.get("/api/jobs")
def get_jobs(
    q: str = Query("", description="Search term"),
    location: str = Query("all", description="Location filter"),
    source: str = Query("all", description="Portal filter (linkedin, naukri)")
):
    all_jobs = get_processed_jobs()
    filtered = all_jobs
    
    if q:
        query_str = q.lower()
        filtered = [
            j for j in filtered if
            query_str in j["title"].lower() or
            query_str in j["company"].lower() or
            query_str in j["location"].lower() or
            query_str in j["experience"].lower()
        ]
        
    if location != "all":
        loc_str = location.lower()
        filtered = [j for j in filtered if loc_str in j["location"].lower()]
        
    if source != "all":
        src_str = source.lower()
        filtered = [j for j in filtered if src_str in j["source"].lower()]
        
    last_mod = "Recent"
    if os.path.exists(EXCEL_PATH):
        mtime = os.path.getmtime(EXCEL_PATH)
        last_mod = datetime.datetime.fromtimestamp(mtime).strftime("%d %b %Y, %I:%M %p")
        
    return {
        "status": "success",
        "last_updated": last_mod,
        "total_count": len(all_jobs),
        "filtered_count": len(filtered),
        "jobs": filtered
    }

STATIC_EXCEL_PATH = os.path.join(STATIC_DIR, "Cybersecurity_Job_Openings.xlsx")

@app.get("/api/download-excel")
def download_excel():
    """
    Directly streams the generated Excel workbook (.xlsx) with explicit attachment headers.
    """
    target_path = EXCEL_PATH if os.path.exists(EXCEL_PATH) else STATIC_EXCEL_PATH
    if not os.path.exists(target_path):
        jobs = get_processed_jobs()
        generate_excel_file(jobs, EXCEL_PATH)
        target_path = EXCEL_PATH
        
    # Ensure static copy is in sync
    try:
        import shutil
        shutil.copyfile(target_path, STATIC_EXCEL_PATH)
    except Exception:
        pass

    return FileResponse(
        path=target_path,
        filename="Cybersecurity_Job_Openings.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": 'attachment; filename="Cybersecurity_Job_Openings.xlsx"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.post("/api/scrape-and-export")
def scrape_and_export(
    search_term: str = Query("cybersecurity analyst", description="Job search term"),
    location: str = Query("Pune, India", description="Location"),
    results_wanted: int = Query(25, description="Number of results per site")
):
    """
    Triggers a live scrape on LinkedIn and Naukri, updates database, and regenerates the Excel spreadsheet.
    """
    try:
        from jobspy import scrape_jobs
        print(f"Scraping fresh jobs for: {search_term} in {location}...")
        
        df = scrape_jobs(
            site_name=["indeed", "glassdoor", "linkedin", "naukri"],
            search_term=search_term,
            location=location,
            results_wanted=results_wanted,
            hours_old=720,
            country_indeed='india'
        )
        
        if df is not None and len(df) > 0:
            existing = get_processed_jobs()
            existing_urls = {j["job_post_url"] for j in existing if j.get("job_post_url")}
            
            raw_new = df.to_dict(orient="records")
            new_processed = process_raw_jobs(raw_new)
            
            # Combine unique
            added = []
            for item in new_processed:
                if item["job_post_url"] not in existing_urls:
                    added.append(item)
                    existing_urls.add(item["job_post_url"])
                    
            combined = [{**j, "sl_no": idx} for idx, j in enumerate(added + existing, 1)]
                
            # Save files
            with open(PROCESSED_JSON, "w", encoding="utf-8") as f:
                json.dump(combined, f, indent=2)
                
            generate_excel_file(combined, EXCEL_PATH)
            
            return {
                "status": "success",
                "new_added": len(added),
                "total_jobs": len(combined),
                "excel_path": "/api/download-excel"
            }
    except Exception as e:
        print(f"Scrape error: {e}")
        
    jobs = get_processed_jobs()
    return {"status": "fallback", "total_jobs": len(jobs), "excel_path": "/api/download-excel"}

@app.post("/api/sync-workday-ats")
def sync_workday_ats():
    """
    Crawls direct Workday CXS & Greenhouse ATS feeds from verified GCC paymasters (Mastercard, NVIDIA, CrowdStrike, etc.).
    Filters strictly for 2-3 YOE, detects Ghost Jobs, and merges into active database and Excel.
    """
    try:
        import workday_engine
        direct_jobs = workday_engine.crawl_all_direct_ats_jobs()
        if direct_jobs:
            existing = get_processed_jobs()
            existing_urls = {j.get("job_post_url") or j.get("apply_url") for j in existing if j.get("job_post_url") or j.get("apply_url")}
            existing_titles_comp = {f"{j.get('title', '').lower()}_{j.get('company', '').lower()}" for j in existing}
            
            new_processed = process_raw_jobs(direct_jobs)
            added = []
            for item in new_processed:
                u = item.get("job_post_url") or item.get("apply_url")
                tc = f"{item.get('title', '').lower()}_{item.get('company', '').lower()}"
                if u not in existing_urls and tc not in existing_titles_comp:
                    added.append(item)
                    if u: existing_urls.add(u)
                    existing_titles_comp.add(tc)
                    
            combined = [{**j, "sl_no": idx} for idx, j in enumerate(added + existing, 1)]
                
            with open(PROCESSED_JSON, "w", encoding="utf-8") as f:
                json.dump(combined, f, indent=2)
                
            generate_excel_file(combined, EXCEL_PATH)
            
            return {
                "status": "success",
                "new_added": len(added),
                "total_jobs": len(combined),
                "excel_path": "/api/download-excel"
            }
    except Exception as e:
        print(f"ATS sync error: {e}")
        return {"status": "error", "message": str(e)}
        
    jobs = get_processed_jobs()
    return {"status": "success", "new_added": 0, "total_jobs": len(jobs), "excel_path": "/api/download-excel"}

class AnalyzeRequest(BaseModel):
    url: str
    api_key: Optional[str] = None

@app.post("/api/analyze-job")
def analyze_job(req: AnalyzeRequest):
    """
    Uses Firecrawl to extract structured intelligence from a job posting URL.
    """
    intel = extract_deep_job_intel(req.url, req.api_key)
    return intel

@app.get("/api/gcc-seeds")
def get_gcc_seeds():
    """
    Returns curated list of direct GCC Workday / ATS career portal seeds.
    """
    return {"status": "success", "seeds": GCC_CAREER_SEEDS}

# ==================== KANBAN APPLICATION TRACKER ENDPOINTS ====================

class AddTrackerRequest(BaseModel):
    job: dict
    stage: Optional[str] = "wishlist"

class UpdateStageRequest(BaseModel):
    id: str
    stage: str
    note: Optional[str] = ""

class UpdateNotesRequest(BaseModel):
    id: str
    notes: str
    referral_contact: Optional[str] = ""

@app.get("/api/tracker")
def get_tracker():
    """Returns all tracked jobs grouped by Kanban stage."""
    return tracker_engine.get_tracker_summary()

@app.post("/api/tracker/add")
def add_to_tracker(req: AddTrackerRequest):
    """Adds an opening directly to the Kanban tracker."""
    result = tracker_engine.add_job_to_tracker(req.job, initial_stage=req.stage or "wishlist")
    return result

@app.post("/api/tracker/update-stage")
def update_tracker_stage(req: UpdateStageRequest):
    """Moves an application to a new Kanban stage."""
    updated = tracker_engine.update_job_stage(req.id, req.stage, req.note or "")
    if not updated:
        raise HTTPException(status_code=400, detail="Invalid stage or job ID")
    return {"status": "success", "item": updated}

@app.post("/api/tracker/update-notes")
def update_tracker_notes(req: UpdateNotesRequest):
    """Updates personal strategy notes and referral contact."""
    updated = tracker_engine.update_job_notes(req.id, req.notes, req.referral_contact or "")
    if not updated:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "success", "item": updated}

@app.delete("/api/tracker/{track_id}")
def delete_tracker_item(track_id: str):
    """Deletes an application from the tracker."""
    success = tracker_engine.delete_tracker_job(track_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "success", "id": track_id}

@app.get("/")
def serve_index():
    return FileResponse(
        os.path.join(STATIC_DIR, "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

# Mount frontend
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    print("="*60)
    print("Cybersecurity Job Search & Excel Generator Engine")
    print("Running on: http://localhost:8000")
    print("="*60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
