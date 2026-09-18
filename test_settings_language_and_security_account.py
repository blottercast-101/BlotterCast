import os
import unittest
from app import create_app
from app.extensions import db
from app.models import User, SystemSetting

class TestSettingsLanguageAndSecurityAccount(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Clean or prepare test users
        self.u1 = User.query.filter_by(username="test_sec_user1").first()
        if not self.u1:
            self.u1 = User(
                username="test_sec_user1",
                password="Password123!",
                full_name="Security User One",
                email="sec1@example.com",
                contact_no="09123456789",
                role="System Admin",
                status="Active"
            )
            db.session.add(self.u1)

        self.u2 = User.query.filter_by(username="test_sec_user2").first()
        if not self.u2:
            self.u2 = User(
                username="test_sec_user2",
                password="Password123!",
                full_name="Security User Two",
                email="sec2@example.com",
                contact_no="09987654321",
                role="Desk Officer",
                status="Active"
            )
            db.session.add(self.u2)

        db.session.commit()
        self.user1_id = self.u1.id
        self.user2_id = self.u2.id

    def tearDown(self):
        # Cleanup any modified usernames
        u1 = db.session.get(User, self.user1_id)
        if u1:
            u1.username = "test_sec_user1"
            u1.full_name = "Security User One"
            u1.role = "System Admin"
            u1.status = "Active"
        u2 = db.session.get(User, self.user2_id)
        if u2:
            u2.username = "test_sec_user2"
            u2.role = "Desk Officer"
            u2.status = "Active"
        db.session.commit()
        self.app_context.pop()

    def test_update_my_account_username_success_and_session_sync(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user1_id
            sess["username"] = "test_sec_user1"
            sess["role"] = "System Admin"

        # Update username and contact info
        payload = {
            "full_name": "Security User One Updated",
            "email": "sec1_updated@example.com",
            "contact": "09123456789",
            "username": "newsecusername1"
        }
        res = self.client.post("/api/auth.php?action=update_my_account", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("user", {}).get("username"), "newsecusername1")

        # Verify DB updated
        user = db.session.get(User, self.user1_id)
        self.assertEqual(user.username, "newsecusername1")
        self.assertEqual(user.full_name, "Security User One Updated")
        self.assertEqual(user.role, "System Admin")
        self.assertEqual(user.status, "Active")

        # Verify session synced
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("username"), "newsecusername1")

    def test_update_my_account_username_duplicate_conflict(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user1_id
            sess["username"] = "test_sec_user1"
            sess["role"] = "System Admin"

        # Attempt to take user2's username
        payload = {
            "full_name": "Conflict Attempt",
            "email": "conflict@example.com",
            "contact": "09123456789",
            "username": "test_sec_user2"
        }
        res = self.client.post("/api/auth.php?action=update_my_account", json=payload)
        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("already taken", data.get("error", "").lower())

    def test_update_my_account_username_short_invalid(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user1_id
            sess["username"] = "test_sec_user1"
            sess["role"] = "System Admin"

        payload = {
            "full_name": "Valid Name",
            "email": "valid@example.com",
            "contact": "09123456789",
            "username": "ab"
        }
        res = self.client.post("/api/auth.php?action=update_my_account", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("at least 3 characters", data.get("error", "").lower())

    def test_update_my_account_role_and_status_immutable(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user2_id
            sess["username"] = "test_sec_user2"
            sess["role"] = "Desk Officer"

        # Try to smuggle role and status updates
        payload = {
            "full_name": "Desk Officer Sample",
            "email": "officer_sample@example.com",
            "contact": "09987654321",
            "username": "test_sec_user2_mod",
            "role": "System Admin",
            "status": "Inactive"
        }
        res = self.client.post("/api/auth.php?action=update_my_account", json=payload)
        self.assertEqual(res.status_code, 200)

        # Check DB that role and status were not changed
        user = db.session.get(User, self.user2_id)
        self.assertEqual(user.username, "test_sec_user2_mod")
        self.assertEqual(user.role, "Desk Officer")
        self.assertEqual(user.status, "Active")

    def test_save_and_get_default_language_setting(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user1_id
            sess["role"] = "System Admin"

        # Save default_language = filipino
        payload = {
            "default_language": "filipino"
        }
        res = self.client.post("/api/settings.php?action=save", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))

        # Verify setting persisted in DB
        setting = SystemSetting.query.filter_by(setting_key="default_language").first()
        self.assertIsNotNone(setting)
        self.assertEqual(setting.setting_value, "filipino")

        # Verify GET /api/settings/general returns default_language in data
        res_get = self.client.get("/api/settings/general")
        self.assertEqual(res_get.status_code, 200)
        data_get = res_get.get_json()
        self.assertTrue(data_get.get("success"))
        self.assertEqual(data_get.get("data", {}).get("default_language"), "filipino")

        # Verify GET /api/settings.php?action=list returns default_language
        res_list = self.client.get("/api/settings.php?action=list")
        self.assertEqual(res_list.status_code, 200)
        data_list = res_list.get_json()
        self.assertEqual(data_list.get("default_language"), "filipino")

if __name__ == "__main__":
    unittest.main()
