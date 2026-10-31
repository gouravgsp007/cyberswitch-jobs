import time
import schedule
import subprocess
import datetime

def run_sync():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{now}] Starting Daily Scheduled Cybersecurity Scrape...")
    try:
        result = subprocess.run(["python", "scrape_openings.py"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors/Warnings:", result.stderr)
        print(f"[{now}] Daily Sync Completed Successfully!")
    except Exception as e:
        print(f"Error during daily sync: {e}")

# Run once immediately on launch
print("Running initial job sync...")
run_sync()

# Schedule to run every day at 08:00 AM IST
schedule.every().day.at("08:00").do(run_sync)
schedule.every().day.at("14:00").do(run_sync)
schedule.every().day.at("19:00").do(run_sync)

print("\nScheduler is active. Will auto-sync everyday at 8:00 AM, 2:00 PM, and 7:00 PM IST.")
print("Keep this terminal open in the background, or add to Windows Task Scheduler.")

while True:
    schedule.run_pending()
    time.sleep(60)
