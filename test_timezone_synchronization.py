import os
import re
import unittest
from datetime import datetime, timezone, timedelta

from app import create_app
from app.timezone import ph_now, ph_today, ph_time, MANILA_TZ


class TestTimezoneSynchronization(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_backend_environment_and_timezone(self):
        # 1. Check environment variable TZ
        self.assertEqual(os.environ.get("TZ"), "Asia/Manila")

        # 2. Check MANILA_TZ offset is UTC+8 (+28800 seconds)
        now_ph = ph_now()
        self.assertEqual(now_ph.utcoffset(), timedelta(hours=8))

        # 3. Check ph_today and ph_time consistency
        self.assertEqual(ph_today(), now_ph.date())
        self.assertEqual(ph_time().hour, now_ph.hour)
        self.assertEqual(ph_time().minute, now_ph.minute)

    def test_backend_notification_timestamp_generation(self):
        # Read records.py and verify all ts generation uses ph_now()
        with open("app/blueprints/records.py", "r", encoding="utf-8") as f:
            records_code = f.read()

        self.assertNotIn('datetime.utcnow().strftime', records_code, "records.py should not use datetime.utcnow() for timestamp formatting")
        self.assertIn('ph_now().strftime', records_code, "records.py should use ph_now() for timestamp formatting")

    def test_backend_documents_and_reports_defaults(self):
        # Verify documents.py uses ph_today
        with open("app/blueprints/documents.py", "r", encoding="utf-8") as f:
            docs_code = f.read()
        self.assertNotIn('datetime.utcnow().date()', docs_code, "documents.py should not use datetime.utcnow().date()")
        self.assertIn('ph_today()', docs_code, "documents.py should use ph_today()")

        # Verify reports.py uses ph_today and ph_now
        with open("app/blueprints/reports.py", "r", encoding="utf-8") as f:
            reports_code = f.read()
        self.assertNotIn('datetime.utcnow().replace(day=1)', reports_code)
        self.assertIn('ph_today().replace(day=1)', reports_code)

    def test_backend_db_engine_connect_listener(self):
        # Verify __init__.py has Engine connect listener setting session timezone to +08:00
        with open("app/__init__.py", "r", encoding="utf-8") as f:
            init_code = f.read()
        self.assertIn("SET time_zone = '+08:00'", init_code)
        self.assertIn("SET TIME ZONE 'Asia/Manila'", init_code)

    def test_frontend_format_system_date_implementation(self):
        with open("frontend/app.js", "r", encoding="utf-8") as f:
            js_code = f.read()

        # Check formatSystemDate implementation
        self.assertIn('function formatSystemDate(dateString)', js_code)
        self.assertIn("timeZone: 'Asia/Manila'", js_code)
        self.assertIn("Intl.DateTimeFormat", js_code)
        self.assertIn("window.formatSystemDate = formatSystemDate;", js_code)

        # Check bcFormatTimestamp uses BC_SYSTEM_TIMEZONE = 'Asia/Manila'
        self.assertIn("const BC_SYSTEM_TIMEZONE = 'Asia/Manila';", js_code)

    def test_frontend_time_ago_handles_naive_and_utc_strings(self):
        with open("frontend/app.js", "r", encoding="utf-8") as f:
            js_code = f.read()

        # Verify timeAgo handles naive timestamps by appending Z if needed
        time_ago_match = re.search(r'function timeAgo\(dateStr\)\s*{(.*?)\n}', js_code, re.DOTALL)
        self.assertIsNotNone(time_ago_match)
        time_ago_body = time_ago_match.group(1)
        self.assertIn("+ 'Z'", time_ago_body)


if __name__ == "__main__":
    unittest.main()
