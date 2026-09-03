import unittest
from app import create_app
from app.extensions import db
from app.models import SystemSetting, User
from app.seed import seed_data
from test_mfa_helper import login as mfa_login


class TestProfilePersistenceAndSeederGuard(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            from app.blueprints.auth import _hash_password
            admin = User.query.filter_by(role="System Admin").first()
            if admin:
                admin.username = "admin"
                admin.password = _hash_password("admin123")
                admin.full_name = "System Administrator"
                admin.email = "blottercast@gmail.com"
                admin.failed_attempts = 0
                admin.locked_until = None
            captain = User.query.filter_by(role="Barangay Captain").first()
            if captain:
                captain.username = "kapitan"
                captain.password = _hash_password("kapitan123")
                captain.full_name = "Barangay Captain"
                captain.email = "fhalynramos4@gmail.com"
                captain.failed_attempts = 0
                captain.locked_until = None
            db.session.commit()

    def test_seeder_does_not_overwrite_customized_admin_and_captain(self):
        with self.app.app_context():
            # 1. Update Admin and Captain to custom names
            admin = User.query.filter_by(role="System Admin").first()
            self.assertIsNotNone(admin)
            admin.full_name = "Super Admin Jane Doe"
            admin.email = "jane.admin@mapulanglupa.gov.ph"

            captain = User.query.filter_by(role="Barangay Captain").first()
            self.assertIsNotNone(captain)
            captain.full_name = "Hon. Roberto F. Santos"
            captain.email = "roberto.santos@mapulanglupa.gov.ph"

            db.session.commit()

            # 2. Re-run seed_data (simulating server restart or migration fixture)
            seed_data(self.app, force_reset=False)

            # 3. Verify neither account was reverted
            refreshed_admin = User.query.filter_by(role="System Admin").first()
            self.assertEqual(refreshed_admin.full_name, "Super Admin Jane Doe")
            self.assertEqual(refreshed_admin.email, "jane.admin@mapulanglupa.gov.ph")

            refreshed_captain = User.query.filter_by(role="Barangay Captain").first()
            self.assertEqual(refreshed_captain.full_name, "Hon. Roberto F. Santos")
            self.assertEqual(refreshed_captain.email, "roberto.santos@mapulanglupa.gov.ph")

    def test_user_update_synchronizes_captain_and_session(self):
        with self.app.app_context():
            admin = User.query.filter_by(role="System Admin").first()
            mfa_login(self.client, admin.username, "admin123")

            captain = User.query.filter_by(role="Barangay Captain").first()
            self.assertIsNotNone(captain)

            # Update Captain profile via API
            new_name = "HON. CARLOS MIGUEL VEGA"
            res = self.client.put(f"/api/users.php?action=update&id={captain.id}", json={
                "name": new_name,
                "email": "carlos.vega@mapulanglupa.gov.ph",
                "contact": "09181234567",
                "role": "Barangay Captain"
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("user", {}).get("full_name"), new_name)

            # Verify Captain signature endpoint returns new name
            sig_res = self.client.get("/api/users.php?action=captain_signature")
            self.assertEqual(sig_res.status_code, 200)
            sig_data = sig_res.get_json()
            self.assertEqual(sig_data.get("fullName"), new_name)
            self.assertEqual(sig_data.get("barangay_captain"), new_name)

            # Verify settings/general returns new name
            gen_res = self.client.get("/api/settings/general")
            self.assertEqual(gen_res.status_code, 200)
            gen_data = gen_res.get_json()
            self.assertEqual(gen_data["data"]["captain_name"], new_name)
            self.assertEqual(gen_data["data"]["punong_barangay"], new_name)

    def test_settings_update_synchronizes_captain_user(self):
        with self.app.app_context():
            admin = User.query.filter_by(role="System Admin").first()
            mfa_login(self.client, admin.username, "admin123")

            # Update captain name via settings endpoint
            new_captain = "Hon. Fernando Ramos"
            res = self.client.post("/api/settings/general", json={
                "captain_name": new_captain
            })
            self.assertEqual(res.status_code, 200)

            # Verify User table was synchronized
            captain_user = User.query.filter_by(role="Barangay Captain").first()
            self.assertEqual(captain_user.full_name, new_captain)

            # Verify captain signature endpoint
            sig_res = self.client.get("/api/users.php?action=captain_signature")
            self.assertEqual(sig_res.get_json().get("fullName"), new_captain)


if __name__ == "__main__":
    unittest.main()
