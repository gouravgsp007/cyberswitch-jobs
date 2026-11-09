import unittest
import os
import json
import shutil
import tempfile
import tracker_engine
import workday_engine
import tracer_links_engine
import experience_bank
import alert_engine

class TestEngines(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_json = os.path.join(self.test_dir, "test_tracker.json")
        self.orig_path = tracker_engine.TRACKER_JSON_PATH
        tracker_engine.TRACKER_JSON_PATH = self.test_json

        # Isolate tracer links
        self.orig_links_file = tracer_links_engine.LINKS_FILE
        self.orig_clicks_file = tracer_links_engine.CLICKS_FILE
        tracer_links_engine.LINKS_FILE = os.path.join(self.test_dir, "test_tracer_links.json")
        tracer_links_engine.CLICKS_FILE = os.path.join(self.test_dir, "test_tracer_clicks.json")

        # Isolate alerts
        self.orig_alerts_file = alert_engine.ALERTS_FILE
        alert_engine.ALERTS_FILE = os.path.join(self.test_dir, "test_alerts.json")

    def tearDown(self):
        tracker_engine.TRACKER_JSON_PATH = self.orig_path
        tracer_links_engine.LINKS_FILE = self.orig_links_file
        tracer_links_engine.CLICKS_FILE = self.orig_clicks_file
        alert_engine.ALERTS_FILE = self.orig_alerts_file
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_tracker_workflow(self):
        job = {
            "id": "job_123",
            "title": "SOC Analyst L2",
            "company": "Barclays",
            "location": "Pune",
            "salary": "₹12.0 - ₹15.0 LPA",
            "apply_url": "https://barclays.example/job/123"
        }
        res = tracker_engine.add_job_to_tracker(job, initial_stage="wishlist")
        self.assertEqual(res["status"], "success")
        item = res["item"]
        track_id = item["id"]
        self.assertEqual(item["stage"], "wishlist")
        self.assertEqual(item["company"], "Barclays")
        
        dup_res = tracker_engine.add_job_to_tracker(job)
        self.assertEqual(dup_res["status"], "exists")
        
        updated = tracker_engine.update_job_stage(track_id, "screening", note="HR called from Pune office")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["stage"], "screening")
        self.assertEqual(len(updated["history"]), 2)
        
        noted = tracker_engine.update_job_notes(track_id, "Reviewed KQL queries for screening", "Alumni John")
        self.assertEqual(noted["notes"], "Reviewed KQL queries for screening")
        self.assertEqual(noted["referral_contact"], "Alumni John")
        
        summary = tracker_engine.get_tracker_summary()
        self.assertEqual(summary["total_tracked"], 1)
        self.assertEqual(summary["stage_counts"]["screening"], 1)
        self.assertEqual(summary["stage_counts"]["wishlist"], 0)
        
        deleted = tracker_engine.delete_tracker_job(track_id)
        self.assertTrue(deleted)
        self.assertEqual(tracker_engine.get_tracker_summary()["total_tracked"], 0)

    def test_ghost_job_risk_assessment(self):
        risk_low, note_low = workday_engine.assess_ghost_job_risk("Posted Today", "")
        self.assertEqual(risk_low, "Low Risk")
        self.assertIn("Fresh", note_low)
        
        risk_stale, note_stale = workday_engine.assess_ghost_job_risk("Posted 45 days ago", "")
        self.assertEqual(risk_stale, "High Ghost Risk")
        self.assertIn("Stale", note_stale)

    def test_strict_experience_filter(self):
        valid, msg = workday_engine.is_strictly_2_to_3_years("Cybersecurity Analyst", "Looking for 2 to 3 years experience in SOC")
        self.assertTrue(valid)
        
        invalid_5y, msg_5y = workday_engine.is_strictly_2_to_3_years("Cybersecurity Analyst", "Candidate must have 5+ years experience")
        self.assertFalse(invalid_5y)
        self.assertIn("Exceeds 3 Years", msg_5y)
        
        invalid_lead, msg_lead = workday_engine.is_strictly_2_to_3_years("Lead Security Engineer", "2 years exp required")
        self.assertFalse(invalid_lead)

    def test_cv_tracer_links(self):
        # 1. Create tracer link for Barclays application
        link = tracer_links_engine.create_tracer_link(
            company="Barclays",
            role="Cybersecurity Analyst",
            destination_key="linkedin"
        )
        self.assertIn("barclays-linkedin", link["slug"])
        self.assertEqual(link["total_clicks"], 0)

        # 2. Record recruiter click
        dest = tracer_links_engine.record_tracer_click(
            slug=link["slug"],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            client_ip="198.51.100.25",
            referrer="https://barclays.wd3.myworkdayjobs.com"
        )
        self.assertIsNotNone(dest)
        self.assertIn("linkedin.com", dest)

        # 3. Check stats
        stats = tracer_links_engine.get_tracer_stats()
        self.assertEqual(stats["total_active_links"], 1)
        self.assertEqual(stats["total_recruiter_clicks"], 1)
        self.assertEqual(len(stats["recent_clicks"]), 1)
        self.assertEqual(stats["recent_clicks"][0]["company"], "Barclays")

    def test_experience_bank_tailoring(self):
        bank = experience_bank.load_experience_bank()
        self.assertGreater(len(bank), 5)

        # Tailor for Barclays Sentinel role
        res = experience_bank.tailor_for_job(
            company="Barclays",
            title="Cybersecurity Analyst - Sentinel & Incident Response",
            description="We are seeking an analyst with experience in Microsoft Sentinel, KQL queries, and SOC L2 triage.",
            user_tracer_url="http://localhost:8000/t/barclays-linkedin"
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["company"], "Barclays")
        self.assertGreaterEqual(len(res["tailored_bullets"]), 3)
        self.assertIn("Sentinel", str(res["tailored_bullets"]))
        self.assertIn("Gourav", res["elevator_pitch"])
        self.assertIn("Barclays", res["elevator_pitch"])
        self.assertIn("http://localhost:8000/t/barclays-linkedin", res["recruiter_dm"])

    def test_alert_engine(self):
        sample_job = {
            "title": "Security Analyst L2",
            "company": "Mastercard",
            "location": "Pune",
            "salary": "₹12.0 - ₹16.0 LPA",
            "experience": "2 - 3 Years",
            "priority": "P1 - High Priority",
            "apply_url": "https://mastercard.wd1.myworkdayjobs.com"
        }
        res = alert_engine.trigger_job_alert(sample_job)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["unread_count"], 1)

        # Duplicate check
        dup_res = alert_engine.trigger_job_alert(sample_job)
        self.assertEqual(dup_res["status"], "duplicate")

        # Mark read
        mr_res = alert_engine.mark_all_alerts_read()
        self.assertEqual(mr_res["unread_count"], 0)

if __name__ == "__main__":
    unittest.main()
