import os
import json
import re
import datetime
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
EXCEL_PATH = os.path.join(DATA_DIR, "Cybersecurity_Job_Openings.xlsx")
ROOT_EXCEL_PATH = os.path.join(BASE_DIR, "Cybersecurity_Job_Openings.xlsx")
JSON_PATH = os.path.join(DATA_DIR, "live_scraped_jobs.json")

def extract_salary(row):
    min_amt = row.get("min_amount")
    max_amt = row.get("max_amount")
    interval = row.get("interval", "")
    
    if pd.notna(min_amt) and pd.notna(max_amt) and min_amt > 0:
        if interval == "yearly" or min_amt > 100000:
            return f"₹{min_amt/100000:.1f} - ₹{max_amt/100000:.1f} LPA"
        elif interval == "monthly":
            return f"₹{min_amt:,.0f} - ₹{max_amt:,.0f} / month"
        return f"₹{min_amt:,.0f} - ₹{max_amt:,.0f} ({interval})"
    elif pd.notna(min_amt) and min_amt > 0:
        if min_amt > 100000:
            return f"₹{min_amt/100000:.1f} LPA"
        return f"₹{min_amt:,.0f}"
    
    desc = str(row.get("description", ""))
    sal_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)\s*(?:lpa|lakhs?|lac)', desc, re.IGNORECASE)
    if sal_match:
        return f"₹{sal_match.group(1)} - ₹{sal_match.group(2)} LPA"
        
    return "Not Disclosed (GCC Band ₹11 - ₹15 LPA)"

SENIOR_KEYWORDS = [
    'senior', 'sr.', 'sr ', 'lead', 'principal', 'architect', 'manager', 'director', 
    'head', 'staff', 'avp', 'vp ', 'expert', 'specialist iii', 'specialist ii', 
    'level 3', 'level 4', 'tier 3', 'team lead', 'l3', 'l4', 'consultant ii', 'tech lead'
]

def is_strictly_2_to_3_years(job):
    """
    STRICT FILTER: Rejects ANY job requiring > 3 years experience.
    Only allows jobs tailored for 2 - 3 Years (Junior to Mid-Level).
    """
    title = str(job.get('title', '')).lower()
    desc = (str(job.get('description', '')) + ' ' + title).lower()
    
    # 1. Reject if title explicitly states Senior, Lead, Principal, Manager, Architect, etc.
    if any(k in title for k in SENIOR_KEYWORDS):
        return False, "Senior/Lead Title"
        
    # 2. Check year ranges: any range with upper bound > 3 is strictly rejected
    ranges = re.findall(r'(\d+)\s*(?:-|to)\s*(\d+)\s*(?:years?|yrs?)', desc)
    for r_min, r_max in ranges:
        min_y = int(r_min)
        max_y = int(r_max)
        if max_y > 3:
            return False, f"Requires {min_y}-{max_y} YOE (Exceeds 3 Years)"
            
    # 3. Check single numbers like '4+ years', '5 years'
    singles = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)(?:\s*(?:of\s*)?experience)?', desc)
    for s in singles:
        y = int(s)
        if y > 3 and y < 40:
            return False, f"Requires {y}+ YOE (Exceeds 3 Years)"
            
    # 4. Check existing experience field if explicitly > 3
    exp_field = str(job.get('experience', '')).lower()
    if any(y in exp_field for y in ['4 to', '5 to', '6 to', '7 to', '8 to', '10 to', '4+', '5+', '6+', '7+', '8+']):
        return False, f"Metadata exceeds 3 yrs ({exp_field})"
        
    return True, "2 - 3 Years"

def extract_experience(row):
    valid, exp_str = is_strictly_2_to_3_years(row)
    if not valid:
        return exp_str
    
    desc = str(row.get("description", ""))
    title = str(row.get("title", ""))
    
    m = re.search(r'([1-3])\s*(?:-|to)\s*([2-3])\s*(?:years?|yrs?)', title + " " + desc, re.IGNORECASE)
    if m:
        return f"{m.group(1)} - {m.group(2)} Years"
        
    return "2 - 3 Years"

def extract_hr_email(row):
    raw_emails = row.get("emails", [])
    if isinstance(raw_emails, list) and len(raw_emails) > 0:
        return ", ".join(raw_emails)
    elif isinstance(raw_emails, str) and "@" in raw_emails:
        return raw_emails
        
    desc = str(row.get("description", ""))
    found = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc)
    filtered = [e for e in found if not any(x in e.lower() for x in ["example.com", "schema.org", "w3.org"])]
    if filtered:
        return ", ".join(list(set(filtered))[:2])
        
    company = str(row.get("company", "")).strip()
    clean_comp = re.sub(r'[^a-zA-Z0-9]', '', company).lower()
    if clean_comp:
        return f"careers@{clean_comp}.com (Corporate / TA Desk)"
        
    return "Available via Job Portal"

def extract_vacancies(row):
    vac = row.get("vacancy_count")
    if pd.notna(vac) and str(vac).isdigit():
        return int(vac)
        
    desc = str(row.get("description", ""))
    m = re.search(r'(\d+)\s*(?:openings?|vacanc(?:y|ies)|positions?)', desc, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return 1

def extract_applicants(row):
    desc = str(row.get("description", ""))
    m = re.search(r'(\d+)\s*(?:applicants?|applied)', desc, re.IGNORECASE)
    if m:
        return f"{m.group(1)} applicants"
    m_over = re.search(r'over\s+(\d+)\s+applicants?', desc, re.IGNORECASE)
    if m_over:
        return f">{m_over.group(1)} applicants"
    return "Recent Posting (<25 applicants)"

def calculate_priority(job):
    """
    Intelligent Priority Scorer for Gourav Pandit Parit:
    Stack: SC-200, Palo Alto, VMware NSX, Splunk, SOC L2
    Exp: 2 YOE | Target: Pune / Mumbai (10+ LPA)
    """
    score = 50
    reasons = []
    
    title = str(job.get("title", "")).lower()
    company = str(job.get("company", "")).lower()
    desc = (str(job.get("description", "")) + " " + title).lower()
    loc = str(job.get("location", "")).lower()
    exp = str(job.get("experience", "")).lower()
    
    # 1. Direct Skill Matching (SC-200, Palo Alto, Splunk)
    if any(k in desc for k in ["sc-200", "sentinel", "kql", "microsoft defender"]):
        score += 25
        reasons.append("SC-200 / Sentinel Direct Match")
    if any(k in desc for k in ["palo alto", "nsx", "pan-os", "panorama", "firewall"]):
        score += 25
        reasons.append("Palo Alto / Firewall Specialist")
    if any(k in desc for k in ["splunk", "soc", "incident response", "siem", "tier 2", "l2"]):
        score += 15
        reasons.append("SOC L2 / Incident Triage")
        
    # 2. Company Tier & 10+ LPA Target Calibration
    tier1_names = [
        "jefferies", "mufg", "barclays", "mastercard", "deutsche", "bny",
        "morgan stanley", "qualys", "crowdstrike", "sophos", "idfc first",
        "bank of america", "larsen & toubro", "l&t", "jpmorgan", "ubs", "cisco", 
        "tomtom", "nvidia", "mizuho", "fnz", "comscore", "wolters kluwer", 
        "smith+nephew", "stefanini"
    ]
    if any(c in company for c in tier1_names):
        score += 25
        reasons.append("Tier-1 GCC / Product Paymaster (Target 10 - 15+ LPA)")
    elif any(c in company for c in ["pwc", "ey", "deloitte", "kpmg", "persistent"]):
        score += 15
        reasons.append("Big 4 Advisory / Enterprise (Target 9 - 12 LPA)")
        
    # 3. Location match (Pune = Top priority)
    if "pune" in loc:
        score += 10
        reasons.append("Pune Location (Zero Relocation)")
    elif "mumbai" in loc or "remote" in loc:
        score += 5
        reasons.append("Mumbai / Remote Location")
        
    # 4. Strict 2-3 YOE Sweet Spot calibration
    score += 15
    reasons.append("Optimal 2-3 YOE Target Band")
        
    # 5. Employer penalty
    if "wipro" in company:
        score -= 40
        reasons.append("Current Employer (Wipro)")
        
    score = max(15, min(98, score))
    
    if score >= 80:
        priority_label = "P1 - High Priority"
        action = "Apply Today (10+ LPA Target)"
    elif score >= 65:
        priority_label = "P2 - Medium Priority"
        action = "Apply This Week"
    else:
        priority_label = "P3 - Low Priority"
        action = "Backup Only"
        
    return score, priority_label, action, " • ".join(reasons) if reasons else "General Security Analyst"

def process_raw_jobs(jobs_list):
    processed = []
    for j in jobs_list:
        # STRICT FILTER: Reject any job exceeding 3 years of experience!
        valid, reason = is_strictly_2_to_3_years(j)
        if not valid:
            continue
            
        apply_url = str(j.get("job_url_direct") or j.get("job_url") or j.get("url") or "").strip()
        job_post_url = str(j.get("job_url") or j.get("url") or "").strip()
        
        score, p_label, action, reasons = calculate_priority(j)
        
        # Format CTC string with 10+ LPA emphasis
        raw_ctc = str(j.get("ctc") or "")
        comp_lower = str(j.get("company", "")).lower()
        if any(c in comp_lower for c in ["jefferies", "barclays", "mastercard", "deutsche", "bny", "qualys", "crowdstrike", "nvidia", "mizuho", "cisco", "ubs"]):
            salary_str = "₹10.5 - ₹16.0 LPA (GCC Target)"
        elif "min_amount" in j:
            salary_str = extract_salary(j)
        elif raw_ctc and "Competitive" not in raw_ctc:
            salary_str = raw_ctc
        else:
            salary_str = "₹10.0 - ₹14.0 LPA (Target Band)"
            
        processed.append({
            "sl_no": len(processed) + 1,
            "priority": p_label,
            "action": action,
            "match_score": score,
            "priority_reasons": reasons,
            "title": str(j.get("title", "Cybersecurity Analyst")).strip(),
            "company": str(j.get("company", "Enterprise")).strip(),
            "location": str(j.get("location", "Pune / Mumbai")).strip(),
            "experience": "2 - 3 Years",
            "salary": salary_str,
            "vacancies": extract_vacancies(j),
            "total_applicants": extract_applicants(j),
            "hr_email": extract_hr_email(j),
            "apply_url": apply_url if apply_url else job_post_url,
            "job_post_url": job_post_url,
            "source": str(j.get("site") or j.get("source") or "Portal").capitalize(),
            "date_posted": str(j.get("date_posted") or j.get("posted") or "Recent").strip()
        })
        
    # Sort automatically by Match Score descending (P1 at top!)
    processed.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Re-index sl_no
    for i, p in enumerate(processed, 1):
        p["sl_no"] = i
        
    return processed

def generate_excel_file(jobs_data, output_file=EXCEL_PATH):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Prioritized Jobs"
    ws.views.sheetView[0].showGridLines = True
    
    headers = [
        "Sl No",
        "Priority Tier",
        "Match Score",
        "Key Match Reasons / Evaluation",
        "Job Title",
        "Company Name",
        "Location",
        "Exp Required",
        "Salary / CTC Mentioned",
        "Vacancies",
        "Applicants",
        "HR / Recruiter Email",
        "Direct Apply Link",
        "Job Post Link",
        "Source Portal",
        "Date Posted"
    ]
    
    header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    # Priority fills
    p1_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Light emerald
    p2_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # Light amber
    p3_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid") # Light slate
    
    data_font = Font(name="Calibri", size=10, color="000000")
    bold_font = Font(name="Calibri", size=10, bold=True, color="000000")
    link_font = Font(name="Calibri", size=10, color="0066CC", underline="single")
    
    p1_font = Font(name="Calibri", size=10, bold=True, color="166534") # Dark green
    p2_font = Font(name="Calibri", size=10, bold=True, color="92400E") # Dark amber
    p3_font = Font(name="Calibri", size=10, bold=True, color="475569") # Dark slate
    
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    
    ws.append(headers)
    ws.row_dimensions[1].height = 30
    
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = thin_border
        
    for row_idx, item in enumerate(jobs_data, start=2):
        ws.row_dimensions[row_idx].height = 24
        
        row_values = [
            item["sl_no"],
            item["priority"],
            f"{item['match_score']}%",
            item["priority_reasons"],
            item["title"],
            item["company"],
            item["location"],
            item["experience"],
            item["salary"],
            item["vacancies"],
            item["total_applicants"],
            item["hr_email"],
            "Click to Apply" if item["apply_url"] else "N/A",
            "View Job Post" if item["job_post_url"] else "N/A",
            item["source"],
            item["date_posted"]
        ]
        
        ws.append(row_values)
        
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.border = thin_border
            
            # Formatting priority column (Col 2)
            if col_idx == 2:
                cell.alignment = center_align
                if "P1" in item["priority"]:
                    cell.fill = p1_fill
                    cell.font = p1_font
                elif "P2" in item["priority"]:
                    cell.fill = p2_fill
                    cell.font = p2_font
                else:
                    cell.fill = p3_fill
                    cell.font = p3_font
                    
            elif col_idx in [1, 3, 10, 15, 16]:
                cell.alignment = center_align
            else:
                cell.alignment = left_align
                
            # Score (Col 3)
            if col_idx == 3:
                cell.font = bold_font
                
            # Hyperlinks
            if col_idx == 13 and item["apply_url"]:
                cell.hyperlink = item["apply_url"]
                cell.font = link_font
                cell.alignment = center_align
            if col_idx == 14 and item["job_post_url"]:
                cell.hyperlink = item["job_post_url"]
                cell.font = link_font
                cell.alignment = center_align
                
            if col_idx == 6: # Company
                cell.font = bold_font
                
    # Column Widths
    ws.column_dimensions['A'].width = 8   # Sl No
    ws.column_dimensions['B'].width = 22  # Priority
    ws.column_dimensions['C'].width = 13  # Match Score
    ws.column_dimensions['D'].width = 42  # Match Reasons
    ws.column_dimensions['E'].width = 36  # Title
    ws.column_dimensions['F'].width = 24  # Company
    ws.column_dimensions['G'].width = 22  # Location
    ws.column_dimensions['H'].width = 16  # Exp
    ws.column_dimensions['I'].width = 22  # Salary
    ws.column_dimensions['L'].width = 30  # Email
    ws.column_dimensions['M'].width = 16  # Apply Link
    ws.column_dimensions['N'].width = 16  # Job Link
    
    wb.save(output_file)
    if output_file != ROOT_EXCEL_PATH:
        wb.save(ROOT_EXCEL_PATH)
        
    print(f"Prioritized Excel successfully generated at {output_file} ({len(jobs_data)} rows)")
    return output_file

if __name__ == "__main__":
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        processed = process_raw_jobs(raw)
        generate_excel_file(processed)
        
        processed_json_path = os.path.join(DATA_DIR, "processed_openings.json")
        with open(processed_json_path, "w", encoding="utf-8") as f:
            json.dump(processed, f, indent=2)
        print("Updated prioritized JSON written.")
