import unittest
import bcrypt
from app import create_app, db
from app.models import User, PasswordHistory


class TestChangePasswordValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True

    @classmethod
    def tearDownClass(cls):
        with cls.app.app_context():
            user = User.query.filter_by(username="pw_test_user").first()
            if user:
                PasswordHistory.query.filter_by(user_id=user.id).delete()
                db.session.delete(user)
                db.session.commit()

    def setUp(self):
        self.client = self.app.test_client()
        with self.app.app_context():
            user = User.query.filter_by(username="pw_test_user").first()
            if not user:
                user = User(
                    username="pw_test_user",
                    full_name="Password Test User",
                    email="pwtest@blottercast.local",
                    role="Desk Officer",
                    status="Active",
                    password=bcrypt.hashpw(b"InitialPassword123!", bcrypt.gensalt()).decode("utf-8")
                )
                db.session.add(user)
            else:
                user.password = bcrypt.hashpw(b"InitialPassword123!", bcrypt.gensalt()).decode("utf-8")
                user.failed_attempts = 0
                user.locked_until = None
                PasswordHistory.query.filter_by(user_id=user.id).delete()
            db.session.commit()

    def _login(self, username="pw_test_user", password="InitialPassword123!"):
        return self.client.post("/api/auth.php?action=login", json={
            "username": username,
            "password": password
        })

    def test_incorrect_current_password(self):
        with self.app.app_context():
            res_login = self._login()
            self.assertEqual(res_login.status_code, 200)

            res = self.client.post("/api/auth.php?action=change_password", json={
                "currentPassword": "wrongpassword999",
                "newPassword": "BrandNewPassword123!",
                "confirmPassword": "BrandNewPassword123!"
            })
            self.assertEqual(res.status_code, 400)
            data = res.get_json()
            self.assertFalse(data.get("ok"))
            self.assertEqual(data.get("error"), "Current password is incorrect.")

    def test_same_new_password_rejected(self):
        with self.app.app_context():
            res_login = self._login()
            self.assertEqual(res_login.status_code, 200)

            res = self.client.post("/api/auth.php?action=change_password", json={
                "currentPassword": "InitialPassword123!",
                "newPassword": "InitialPassword123!",
                "confirmPassword": "InitialPassword123!"
            })
            self.assertEqual(res.status_code, 400)
            data = res.get_json()
            self.assertFalse(data.get("ok"))
            self.assertEqual(data.get("error"), "New password cannot be the same as your current password.")

    def test_mismatched_confirm_password_rejected(self):
        with self.app.app_context():
            res_login = self._login()
            self.assertEqual(res_login.status_code, 200)

            res = self.client.post("/api/auth.php?action=change_password", json={
                "currentPassword": "InitialPassword123!",
                "newPassword": "ValidNewPassword456!",
                "confirmPassword": "DifferentPassword789!"
            })
            self.assertEqual(res.status_code, 400)
            data = res.get_json()
            self.assertFalse(data.get("ok"))
            self.assertEqual(data.get("error"), "New passwords do not match.")

    def test_successful_password_change_lifecycle(self):
        with self.app.app_context():
            # 1. Login with initial password
            res_login = self._login("pw_test_user", "InitialPassword123!")
            self.assertEqual(res_login.status_code, 200)

            # 2. Change password
            new_pw = "SuperSecurePw2026!"
            res_change = self.client.post("/api/auth.php?action=change_password", json={
                "currentPassword": "InitialPassword123!",
                "newPassword": new_pw,
                "confirmPassword": new_pw
            })
            self.assertEqual(res_change.status_code, 200)
            data = res_change.get_json()
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("message"), "Password changed successfully.")

            # 3. Logout
            self.client.post("/api/auth.php?action=logout")

            # 4. Old password must fail
            res_old = self._login("pw_test_user", "InitialPassword123!")
            self.assertEqual(res_old.status_code, 401)

            # 5. New password must succeed
            res_new = self._login("pw_test_user", new_pw)
            self.assertEqual(res_new.status_code, 200)

            # 6. Reusing old password from history must be rejected
            res_reused = self.client.post("/api/auth.php?action=change_password", json={
                "currentPassword": new_pw,
                "newPassword": "InitialPassword123!",
                "confirmPassword": "InitialPassword123!"
            })
            self.assertEqual(res_reused.status_code, 400)
            self.assertEqual(res_reused.get_json().get("error"), "New password cannot be the same as your current password.")

            self.client.post("/api/auth.php?action=logout")


if __name__ == "__main__":
    unittest.main()
