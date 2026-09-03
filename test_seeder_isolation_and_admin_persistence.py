import unittest
from app import create_app
from app.extensions import db
from app.models import User
from app.seed import seed_data
from test_mfa_helper import login as mfa_login


class TestSeederIsolationAndAdminPersistence(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self._restore_defaults()

    def tearDown(self):
        self._restore_defaults()

    def _restore_defaults(self):
        with self.app.app_context():
            from app.blueprints.auth import _hash_password
            # Restore admin
            admin = User.query.filter((User.username == "admin") | (User.role == "System Admin")).first()
            if admin:
                admin.username = "admin"
                admin.password = _hash_password("admin123")
                admin.full_name = "System Administrator"
                admin.email = "blottercast@gmail.com"
                admin.failed_attempts = 0
                admin.locked_until = None
            # Restore captain
            captain = User.query.filter((User.username == "kapitan") | (User.role == "Barangay Captain")).first()
            if captain:
                captain.username = "kapitan"
                captain.password = _hash_password("kapitan123")
                captain.full_name = "Barangay Captain"
                captain.email = "fhalynramos4@gmail.com"
                captain.failed_attempts = 0
                captain.locked_until = None
            # Ensure dummy demo accounts are deleted
            User.query.filter(User.username.in_(["jdelacuz", "msantos", "pencoder"])).delete(synchronize_session=False)
            db.session.commit()

    def test_demo_accounts_never_respawn(self):
        with self.app.app_context():
            # 1. Run seeder
            seed_data(self.app, force_reset=False)

            # 2. Assert dummy accounts do NOT exist in DB
            for dummy in ["jdelacuz", "msantos", "pencoder"]:
                user = User.query.filter_by(username=dummy).first()
                self.assertIsNone(user, f"Demo account {dummy} should not exist in database")

            # 3. Re-run seeder again (simulating multiple restarts)
            seed_data(self.app, force_reset=False)

            for dummy in ["jdelacuz", "msantos", "pencoder"]:
                user = User.query.filter_by(username=dummy).first()
                self.assertIsNone(user, f"Demo account {dummy} must not respawn after re-seeding")

    def test_admin_and_captain_modifications_persist_permanently(self):
        with self.app.app_context():
            admin = User.query.filter_by(role="System Admin").first()
            self.assertIsNotNone(admin)
            captain = User.query.filter_by(role="Barangay Captain").first()
            self.assertIsNotNone(captain)

            # 1. Update Admin via API
            mfa_login(self.client, admin.username, "admin123")
            admin_new_name = "Dir. Alejandro M. Santos"
            admin_new_pass = "AdminSuperSecure2026!"
            res_admin = self.client.put(f"/api/users.php?action=update&id={admin.id}", json={
                "name": admin_new_name,
                "username": admin.username,
                "email": "alejandro.santos@mapulanglupa.gov.ph",
                "password": admin_new_pass,
            })
            self.assertEqual(res_admin.status_code, 200)

            # 2. Update Captain via API
            captain_new_name = "HON. EDUARDO B. FLORES"
            captain_new_pass = "CaptainSuperSecure2026!"
            res_capt = self.client.put(f"/api/users.php?action=update&id={captain.id}", json={
                "name": captain_new_name,
                "username": captain.username,
                "email": "eduardo.flores@mapulanglupa.gov.ph",
                "password": captain_new_pass,
            })
            self.assertEqual(res_capt.status_code, 200)

            # 3. Simulate multiple server reloads / re-seeding
            seed_data(self.app, force_reset=False)
            seed_data(self.app, force_reset=False)

            # 4. Clear sessions to test pure fresh auth
            with self.client.session_transaction() as sess:
                sess.clear()

            # 5. Old passwords MUST fail with 401
            fail_admin = self.client.post("/api/auth.php?action=login", json={"username": admin.username, "password": "admin123"})
            self.assertEqual(fail_admin.status_code, 401)

            fail_capt = self.client.post("/api/auth.php?action=login", json={"username": captain.username, "password": "kapitan123"})
            self.assertEqual(fail_capt.status_code, 401)

            # 6. New passwords MUST succeed with 200
            ok_admin = self.client.post("/api/auth.php?action=login", json={"username": admin.username, "password": admin_new_pass})
            self.assertEqual(ok_admin.status_code, 200)

            with self.client.session_transaction() as sess:
                sess.clear()

            ok_capt = self.client.post("/api/auth.php?action=login", json={"username": captain.username, "password": captain_new_pass})
            self.assertEqual(ok_capt.status_code, 200)

            # 7. Captain signature endpoint reflects updated name
            sig_res = self.client.get("/api/users.php?action=captain_signature")
            self.assertEqual(sig_res.status_code, 200)
            self.assertEqual(sig_res.get_json().get("fullName"), captain_new_name)

            # 8. Check database columns directly
            db_admin = db.session.get(User, admin.id)
            self.assertEqual(db_admin.full_name, admin_new_name)
            self.assertEqual(db_admin.email, "alejandro.santos@mapulanglupa.gov.ph")

            db_capt = db.session.get(User, captain.id)
            self.assertEqual(db_capt.full_name, captain_new_name)
            self.assertEqual(db_capt.email, "eduardo.flores@mapulanglupa.gov.ph")


if __name__ == "__main__":
    unittest.main()
