import unittest
from app import create_app
from app.extensions import db
from app.models import SystemBackup, SystemSetting
from test_mfa_helper import login as mfa_login


class TestBackupLifecycle(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_get_backup_settings_is_read_only(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            # Count initial backups
            count_before = SystemBackup.query.count()

            # Multiple GET calls to settings and history
            res1 = self.client.get("/api/backup/settings")
            self.assertEqual(res1.status_code, 200)
            data1 = res1.get_json()
            self.assertTrue(data1.get("ok"))
            self.assertIn("schedule_time", data1.get("data", {}))
            self.assertIn("frequency", data1.get("data", {}))

            res2 = self.client.get("/api/backup/history")
            self.assertEqual(res2.status_code, 200)

            res3 = self.client.get("/api/backup/status")
            self.assertEqual(res3.status_code, 200)

            # Count after - must NOT have increased!
            count_after = SystemBackup.query.count()
            self.assertEqual(count_before, count_after, "GET endpoints must be strictly read-only and never trigger backups")

    def test_update_backup_settings_does_not_trigger_backup(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            count_before = SystemBackup.query.count()

            res = self.client.post("/api/backup/settings", json={
                "backup_frequency": "Daily",
                "backup_time": "23:00",
                "retain_backups_days": 45,
                "auto_backup_enabled": True
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("ok"))

            # Verify saved in DB
            b_time = SystemSetting.query.get("backup_time")
            self.assertEqual(b_time.setting_value, "23:00")

            count_after = SystemBackup.query.count()
            self.assertEqual(count_before, count_after, "POST /api/backup/settings must update schedule without executing backup")

    def test_manual_backup_executes_strictly_on_demand(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            count_before = SystemBackup.query.count()

            res = self.client.post("/api/backup/manual")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("ok"))
            self.assertTrue(data.get("file").startswith("blottercast-backup-"))

            count_after = SystemBackup.query.count()
            self.assertEqual(count_after, count_before + 1, "Manual backup endpoint must create exactly 1 new backup")


if __name__ == "__main__":
    unittest.main()
