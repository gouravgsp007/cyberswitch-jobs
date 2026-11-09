import unittest
import os
import json
import shutil
import tempfile
import tracker_engine
import workday_engine

class TestEngines(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_json = os.path.join(self.test_dir, "test_tracker.json")
        self.orig_path = tracker_engine.TRACKER_JSON_PATH
        tracker_engine.TRACKER_JSON_PATH = self.test_json

    def tearDown(self):
        tracker_engine.TRACKER_JSON_PATH = self.orig_path
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_tracker_workflow(self):
        # 1. Add job
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
        
        # 2. Duplicate prevention
        dup_res = tracker_engine.add_job_to_tracker(job)
        self.assertEqual(dup_res["status"], "exists")
        
        # 3. Update stage
        updated = tracker_engine.update_job_stage(track_id, "screening", note="HR called from Pune office")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["stage"], "screening")
        self.assertEqual(len(updated["history"]), 2)
        
        # 4. Update notes
        noted = tracker_engine.update_job_notes(track_id, "Reviewed KQL queries for screening", "Alumni John")
        self.assertEqual(noted["notes"], "Reviewed KQL queries for screening")
        self.assertEqual(noted["referral_contact"], "Alumni John")
        
        # 5. Summary
        summary = tracker_engine.get_tracker_summary()
        self.assertEqual(summary["total_tracked"], 1)
        self.assertEqual(summary["stage_counts"]["screening"], 1)
        self.assertEqual(summary["stage_counts"]["wishlist"], 0)
        
        # 6. Delete
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
        # Should accept 2-3 years
        valid, msg = workday_engine.is_strictly_2_to_3_years("Cybersecurity Analyst", "Looking for 2 to 3 years experience in SOC")
        self.assertTrue(valid)
        
        # Should reject >3 years
        invalid_5y, msg_5y = workday_engine.is_strictly_2_to_3_years("Cybersecurity Analyst", "Candidate must have 5+ years experience")
        self.assertFalse(invalid_5y)
        self.assertIn("Exceeds 3 Years", msg_5y)
        
        # Should reject Senior / Lead titles
        invalid_lead, msg_lead = workday_engine.is_strictly_2_to_3_years("Lead Security Engineer", "2 years exp required")
        self.assertFalse(invalid_lead)

if __name__ == "__main__":
    unittest.main()
