import unittest
from datetime import datetime
from app import create_app
from app.extensions import db
from app.models import User


class TestMyAccountActiveSince(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_my_account_returns_created_at_and_profile_data(self):
        with self.app.app_context():
            user = User.query.filter_by(role="System Admin").first()
            self.assertIsNotNone(user)

            # Ensure user has created_at
            if not user.created_at:
                user.created_at = datetime.utcnow()
                db.session.commit()

            with self.client.session_transaction() as sess:
                sess["user_id"] = user.id
                sess["username"] = user.username
                sess["role"] = user.role
                sess["auth_tier"] = 2
                sess["mfa_verified"] = True

            res = self.client.get("/api/auth.php?action=my_account")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("username"), user.username)
            self.assertEqual(data.get("role"), user.role)
            self.assertEqual(data.get("status"), user.status or "Active")
            self.assertIn("created_at", data)
            self.assertIsNotNone(data["created_at"])
            self.assertIn("createdAt", data)
            self.assertIsNotNone(data["createdAt"])

    def test_me_endpoint_returns_created_at(self):
        with self.app.app_context():
            user = User.query.filter_by(role="System Admin").first()
            self.assertIsNotNone(user)

            with self.client.session_transaction() as sess:
                sess["user_id"] = user.id
                sess["username"] = user.username
                sess["role"] = user.role
                sess["auth_tier"] = 2
                sess["mfa_verified"] = True

            res = self.client.get("/api/auth.php?action=me")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("authenticated"))
            u = data.get("user", {})
            self.assertEqual(u.get("status"), user.status or "Active")
            self.assertIn("created_at", u)
            self.assertIsNotNone(u["created_at"])

    def test_update_my_account_preserves_created_at(self):
        with self.app.app_context():
            user = User.query.filter_by(role="System Admin").first()
            self.assertIsNotNone(user)

            with self.client.session_transaction() as sess:
                sess["user_id"] = user.id
                sess["username"] = user.username
                sess["role"] = user.role
                sess["auth_tier"] = 2
                sess["mfa_verified"] = True

            payload = {
                "fullName": "System Administrator",
                "contact": "09171234567",
                "email": user.email or "admin@test.com",
            }
            res = self.client.put("/api/auth.php?action=update_my_account", json=payload)
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("user", {}).get("status"), user.status or "Active")
            self.assertIn("created_at", data.get("user", {}))
            self.assertIsNotNone(data.get("user", {}).get("created_at"))


if __name__ == "__main__":
    unittest.main()
