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
import autofill_engine
import email_sync_engine
import salary_intel_engine
import interview_copilot_engine

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

        # Isolate autofill profile
        self.orig_profile_file = autofill_engine.PROFILE_FILE
        autofill_engine.PROFILE_FILE = os.path.join(self.test_dir, "test_candidate_profile.json")

        # Isolate email sync
        self.orig_emails_file = email_sync_engine.EMAILS_FILE
        self.orig_email_cfg_file = email_sync_engine.CONFIG_FILE
        email_sync_engine.EMAILS_FILE = os.path.join(self.test_dir, "test_synced_emails.json")
        email_sync_engine.CONFIG_FILE = os.path.join(self.test_dir, "test_email_sync_config.json")

    def tearDown(self):
        tracker_engine.TRACKER_JSON_PATH = self.orig_path
        tracer_links_engine.LINKS_FILE = self.orig_links_file
        tracer_links_engine.CLICKS_FILE = self.orig_clicks_file
        alert_engine.ALERTS_FILE = self.orig_alerts_file
        autofill_engine.PROFILE_FILE = self.orig_profile_file
        email_sync_engine.EMAILS_FILE = self.orig_emails_file
        email_sync_engine.CONFIG_FILE = self.orig_email_cfg_file
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

    def test_autofill_engine(self):
        # 1. Load default profile
        profile = autofill_engine.load_candidate_profile()
        self.assertEqual(profile["first_name"], "Gourav")
        self.assertEqual(profile["current_company"], "Wipro")
        self.assertIn("SC-200", profile["certifications"])

        # 2. Update profile
        profile["expected_ctc"] = "14 - 16 LPA"
        autofill_engine.save_candidate_profile(profile)
        reloaded = autofill_engine.load_candidate_profile()
        self.assertEqual(reloaded["expected_ctc"], "14 - 16 LPA")

        # 3. Bookmarklet generation
        code = autofill_engine.get_bookmarklet_code("http://localhost:8000")
        self.assertTrue(code.startswith("javascript:"))
        self.assertIn("http://localhost:8000", code)
        self.assertIn("legalNameSection_firstName", code)

    def test_email_sync_engine(self):
        # 1. Pre-track a job for Barclays in tracker
        job = {
            "id": "barclays_sec_1",
            "title": "SOC Analyst",
            "company": "Barclays",
            "location": "Pune",
            "salary": "₹12.0 - ₹15.0 LPA",
            "apply_url": "https://barclays.example/job/1"
        }
        add_res = tracker_engine.add_job_to_tracker(job, initial_stage="applied")
        track_id = add_res["item"]["id"]

        # 2. Parse recruiter invite email
        invite_email = (
            "Hi Gourav,\n\n"
            "Thank you for applying to Barclays. We are impressed by your Microsoft Sentinel and SC-200 profile.\n"
            "We would like to invite you for a Technical Round with our Incident Response Lead.\n\n"
            "Please join via Microsoft Teams: https://teams.microsoft.com/l/meetup-join/19-meeting_12345\n\n"
            "Best regards,\nBarclays Talent Acquisition"
        )
        sync_res = email_sync_engine.parse_and_sync_recruiter_message(invite_email, "recruiter@barclays.com")
        self.assertEqual(sync_res["status"], "success")
        ev = sync_res["event"]
        self.assertEqual(ev["company"], "Barclays")
        self.assertEqual(ev["detected_stage"], "technical")
        self.assertIn("teams.microsoft.com", ev["meeting_link"])
        self.assertTrue(ev["applied_to_tracker"])

        # Verify Kanban stage progressed to technical
        tr_data = tracker_engine.load_tracker_data()
        updated_job = next(it for it in tr_data if it["id"] == track_id)
        self.assertEqual(updated_job["stage"], "technical")

        # 3. Parse rejection email
        reject_email = (
            "Dear Candidate,\n\n"
            "Thank you for your interest in the Security Operations role at Mastercard. "
            "Unfortunately, we have decided to pursue other candidates whose profiles align more closely at this time.\n"
            "We wish you success in your job search."
        )
        rej_res = email_sync_engine.parse_and_sync_recruiter_message(reject_email, "careers@mastercard.com")
        self.assertEqual(rej_res["event"]["detected_stage"], "rejected")
        self.assertEqual(rej_res["event"]["company"], "Mastercard")

    def test_salary_intel_engine(self):
        benchmarks = salary_intel_engine.get_market_benchmarks()
        self.assertGreaterEqual(len(benchmarks), 5)
        barclays = next(b for b in benchmarks if b["company"] == "Barclays")
        self.assertGreaterEqual(barclays["min_ctc_lpa"], 10.0)
        self.assertEqual(barclays["yoe_bracket"], "2 - 3 Years")

        # Test CTC breakdown for 13.5 LPA
        breakdown = salary_intel_engine.calculate_ctc_breakdown(13.5, fixed_pct=0.85)
        self.assertEqual(breakdown["target_ctc_lpa"], 13.5)
        self.assertAlmostEqual(breakdown["fixed_lpa"], 11.48, delta=0.05)
        self.assertGreater(breakdown["estimated_inhand_monthly_inr"], 65000)
        self.assertGreater(breakdown["hike_over_4lpa_pct"], 200.0)

        # Test negotiation playbook
        playbook = salary_intel_engine.get_negotiation_playbook()
        self.assertGreaterEqual(len(playbook), 3)
        self.assertIn("Wipro", playbook[0]["verbatim_script"])

    def test_interview_copilot_engine(self):
        # 1. KQL cheat sheet
        kql_list = interview_copilot_engine.get_kql_cheatsheet()
        self.assertGreaterEqual(len(kql_list), 4)
        has_lsass = any("lsass" in q["kql"].lower() for q in kql_list)
        self.assertTrue(has_lsass)

        # 2. Palo Alto troubleshooting
        pa_list = interview_copilot_engine.get_palo_alto_troubleshooting()
        self.assertGreaterEqual(len(pa_list), 3)

        # 3. Interview coaching Q&A
        qa_list = interview_copilot_engine.get_interview_coaching()
        self.assertGreaterEqual(len(qa_list), 3)
        self.assertIn("Sentinel", qa_list[0]["star_response"])

if __name__ == "__main__":
    unittest.main()
