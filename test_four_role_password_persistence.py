import unittest
from app import create_app
from app.extensions import db
from app.models import User
from app.seed import seed_data
from test_mfa_helper import login as mfa_login


class TestFourRolePasswordPersistence(unittest.TestCase):
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
            defaults = [
                ("admin", "admin123", "System Administrator", "blottercast@gmail.com"),
                ("kapitan", "kapitan123", "Barangay Captain", "fhalynramos4@gmail.com"),
                ("jdelacuz", "officer123", "J. Dela Cruz", "jdelacuz@blottercast.local"),
                ("msantos", "officer123", "M. Santos", "msantos@blottercast.local"),
                ("pencoder", "encoder123", "P. Encoder", "pencoder@blottercast.local"),
            ]
            for username, password, full_name, email in defaults:
                u = User.query.filter_by(username=username).first()
                if not u and username in ("admin", "kapitan"):
                    role_name = "System Admin" if username == "admin" else "Barangay Captain"
                    u = User.query.filter_by(role=role_name).first()
                if u:
                    u.username = username
                    u.password = _hash_password(password)
                    u.full_name = full_name
                    u.email = email
                    u.failed_attempts = 0
                    u.locked_until = None
            db.session.commit()

    def test_all_four_roles_password_and_profile_persistence(self):
        roles_to_test = [
            {
                "role": "System Admin",
                "default_username": "admin",
                "default_password": "admin123",
                "new_name": "Chief Administrator Alpha",
                "new_password": "AdminNewSecret99!",
            },
            {
                "role": "Barangay Captain",
                "default_username": "kapitan",
                "default_password": "kapitan123",
                "new_name": "HON. ROBERTO DELA SERNA",
                "new_password": "CaptainNewSecret99!",
            },
            {
                "role": "Desk Officer",
                "default_username": "jdelacuz",
                "default_password": "officer123",
                "new_name": "Officer Juan Dela Cruz Jr.",
                "new_password": "DeskNewSecret99!",
            },
            {
                "role": "Data Encoder",
                "default_username": "pencoder",
                "default_password": "encoder123",
                "new_name": "Encoder Patricia Santos",
                "new_password": "EncoderNewSecret99!",
            },
        ]

        with self.app.app_context():
            admin_user = User.query.filter_by(role="System Admin").first()
            self.assertIsNotNone(admin_user)

            # Ensure we are logged in as admin to perform updates
            mfa_login(self.client, admin_user.username, "admin123")

            for item in roles_to_test:
                user = User.query.filter_by(role=item["role"]).first()
                self.assertIsNotNone(user, f"User with role {item['role']} must exist")

                old_password = item["default_password"]
                new_password = item["new_password"]
                new_name = item["new_name"]

                # 1. Update user profile and password via update API
                update_res = self.client.put(f"/api/users.php?action=update&id={user.id}", json={
                    "name": new_name,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "password": new_password,
                })
                self.assertEqual(update_res.status_code, 200, f"Update failed for {item['role']}: {update_res.data}")
                res_data = update_res.get_json()
                self.assertTrue(res_data.get("ok"))
                self.assertEqual(res_data.get("user", {}).get("full_name"), new_name)

                # Clear session to test fresh logins
                with self.client.session_transaction() as sess:
                    sess.clear()

                # 2. Attempt login with OLD password -> MUST BE REJECTED (401)
                login_old_res = self.client.post("/api/auth.php?action=login", json={
                    "username": user.username,
                    "password": old_password,
                })
                self.assertEqual(login_old_res.status_code, 401, f"Old password should be rejected for {item['role']}")

                # 3. Attempt login with NEW password -> MUST SUCCEED (200)
                login_new_res = self.client.post("/api/auth.php?action=login", json={
                    "username": user.username,
                    "password": new_password,
                })
                self.assertEqual(login_new_res.status_code, 200, f"New password should succeed for {item['role']}")

                # 4. Trigger seed_data (simulating server restart / re-seeding)
                seed_data(self.app, force_reset=False)

                # Clear session again
                with self.client.session_transaction() as sess:
                    sess.clear()

                # 5. After restart/re-seed, attempt login with OLD password -> MUST STILL BE REJECTED (401)
                login_old_after_seed = self.client.post("/api/auth.php?action=login", json={
                    "username": user.username,
                    "password": old_password,
                })
                self.assertEqual(login_old_after_seed.status_code, 401, f"Old password must stay rejected after seed for {item['role']}")

                # 6. After restart/re-seed, attempt login with NEW password -> MUST STILL SUCCEED (200)
                login_new_after_seed = self.client.post("/api/auth.php?action=login", json={
                    "username": user.username,
                    "password": new_password,
                })
                self.assertEqual(login_new_after_seed.status_code, 200, f"New password must persist after seed for {item['role']}")

                # 7. Check that updated name is preserved in database
                db_user = db.session.get(User, user.id)
                self.assertEqual(db_user.full_name, new_name, f"Full name must persist after seed for {item['role']}")

                # Re-login as admin for next iteration if needed
                with self.client.session_transaction() as sess:
                    sess.clear()
                mfa_login(self.client, admin_user.username, roles_to_test[0]["new_password"])

    def test_empty_password_in_update_payload_does_not_overwrite_existing_hash(self):
        with self.app.app_context():
            user = User.query.filter_by(role="Desk Officer").first()
            self.assertIsNotNone(user)
            original_hash = user.password

            # Log in as admin
            admin_user = User.query.filter_by(role="System Admin").first()
            # If admin password was changed in previous test, check which works
            try:
                mfa_login(self.client, admin_user.username, "AdminNewSecret99!")
            except Exception:
                mfa_login(self.client, admin_user.username, "admin123")

            # Update with empty password
            res = self.client.put(f"/api/users.php?action=update&id={user.id}", json={
                "name": user.full_name,
                "username": user.username,
                "email": user.email,
                "password": "",
            })
            self.assertEqual(res.status_code, 200)

            refreshed_user = db.session.get(User, user.id)
            self.assertEqual(refreshed_user.password, original_hash, "Empty password string must not alter existing hash")

            # Update with omitted password
            res_omitted = self.client.put(f"/api/users.php?action=update&id={user.id}", json={
                "name": user.full_name,
                "username": user.username,
                "email": user.email,
            })
            self.assertEqual(res_omitted.status_code, 200)

            refreshed_user_2 = db.session.get(User, user.id)
            self.assertEqual(refreshed_user_2.password, original_hash, "Omitted password must not alter existing hash")


if __name__ == "__main__":
    unittest.main()
