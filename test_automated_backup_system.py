import os
import unittest
from datetime import datetime, timedelta, timezone

from app import create_app
from app.extensions import db
from app.models import SystemBackup, SystemSetting
from app.services.backup_scheduler import calculate_next_run, parse_schedule_settings, reschedule_backup_job
from app.services.backup_service import (
    BACKUP_DIR,
    MANILA_TZ,
    cleanup_old_backups,
    generate_sql_dump,
    run_database_backup,
)
from test_mfa_helper import login as mfa_login


class AutomatedBackupSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_sql_dump_generation(self):
        with self.app.app_context():
            dump = generate_sql_dump()
            self.assertIn("-- BlotterCast database backup", dump)
            self.assertIn("-- Local (Asia/Manila):", dump)
            self.assertIn("INSERT INTO", dump)

    def test_run_database_backup_and_retention_cleaner(self):
        with self.app.app_context():
            res = run_database_backup(triggered_by="system (automatic)", retain_days=30)
            self.assertTrue(res["success"])
            self.assertTrue(res["ok"])
            self.assertEqual(res["by"], "system (automatic)")
            self.assertTrue(os.path.isfile(os.path.join(BACKUP_DIR, res["file"])))

            # Verify recorded in database
            rec = SystemBackup.query.filter_by(file_name=res["file"]).first()
            self.assertIsNotNone(rec)
            self.assertEqual(rec.status, "Success")
            self.assertEqual(rec.created_by, "system (automatic)")

            # Create an artificial old record and old file to test retention pruning
            old_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=45)
            old_file = "blottercast-backup-20200101-000000.sql"
            old_path = os.path.join(BACKUP_DIR, old_file)
            with open(old_path, "w") as f:
                f.write("-- old backup test")
            os.utime(old_path, (old_time.timestamp(), old_time.timestamp()))

            db.session.add(SystemBackup(file_name=old_file, size_bytes=100, status="Success", created_by="system (automatic)", created_at=old_time))
            db.session.commit()

            cleaned = cleanup_old_backups(retain_days=30)
            self.assertGreaterEqual(cleaned, 1)
            self.assertIsNone(SystemBackup.query.filter_by(file_name=old_file).first())
            self.assertFalse(os.path.isfile(old_path))

    def test_schedule_calculation_in_manila_timezone(self):
        freq, hour, minute = parse_schedule_settings("Daily", "02:00")
        self.assertEqual(hour, 2)
        self.assertEqual(minute, 0)

        next_run = calculate_next_run("Daily", 2, 0)
        now_manila = datetime.now(MANILA_TZ)
        self.assertGreater(next_run, now_manila)
        self.assertEqual(next_run.hour, 2)
        self.assertEqual(next_run.minute, 0)

    def test_external_cloud_cron_trigger_endpoint(self):
        with self.app.app_context():
            # 1. Without secret -> 401 Unauthorized
            res = self.client.post("/api/backup/cron-trigger")
            self.assertEqual(res.status_code, 401)

            # 2. With valid secret in header -> 200 OK
            res2 = self.client.post(
                "/api/backup/cron-trigger",
                headers={"X-Cron-Secret": "blottercast-cron-secret-2026"}
            )
            self.assertEqual(res2.status_code, 200)
            data = res2.get_json()
            self.assertTrue(data["ok"])
            self.assertEqual(data["by"], "system (automatic)")
            self.assertIn("blottercast-backup-", data["file"])

    def test_dynamic_reschedule_on_settings_save(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            res = self.client.post("/api/settings.php?action=save", json={
                "backup_frequency": "Every 12 hours",
                "backup_time": "03:30",
                "retain_backups_days": "60"
            })
            self.assertEqual(res.status_code, 200)

            # Verify settings saved
            row_freq = SystemSetting.query.get("backup_frequency")
            row_time = SystemSetting.query.get("backup_time")
            row_retain = SystemSetting.query.get("retain_backups_days")
            self.assertEqual(row_freq.setting_value, "Every 12 hours")
            self.assertEqual(row_time.setting_value, "03:30")
            self.assertEqual(row_retain.setting_value, "60")


if __name__ == "__main__":
    unittest.main()
