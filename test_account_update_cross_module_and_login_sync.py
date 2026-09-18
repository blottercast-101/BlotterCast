import os
import unittest
from app import create_app
from app.extensions import db
from app.models import User, SystemSecuritySetting
import bcrypt

class TestAccountUpdateCrossModuleAndLoginSync(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Disable master 2FA during unit testing so password login completes directly
        sec = SystemSecuritySetting.query.get(1)
        if not sec:
            sec = SystemSecuritySetting(id=1, is_2fa_globally_enabled=False, enforce_2fa_all_users=False)
            db.session.add(sec)
        else:
            sec.is_2fa_globally_enabled = False
            sec.enforce_2fa_all_users = False
        db.session.commit()

        # Prepare test user
        self.password = "Password123!"
        hashed_pw = bcrypt.hashpw(self.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        self.user = User.query.filter_by(username="test_sync_user").first()
        if not self.user:
            self.user = User(
                username="test_sync_user",
                password=hashed_pw,
                full_name="Original Name",
                email="original_sync@example.com",
                contact_no="09111111111",
                role="System Admin",
                status="Active"
            )
            db.session.add(self.user)
            db.session.commit()
        else:
            self.user.username = "test_sync_user"
            self.user.password = hashed_pw
            self.user.full_name = "Original Name"
            self.user.email = "original_sync@example.com"
            self.user.contact_no = "09111111111"
            self.user.role = "System Admin"
            self.user.status = "Active"
            db.session.commit()

        self.user_id = self.user.id

    def tearDown(self):
        u = db.session.get(User, self.user_id)
        if u:
            u.username = "test_sync_user"
            u.full_name = "Original Name"
            u.email = "original_sync@example.com"
            u.contact_no = "09111111111"
            db.session.commit()
        self.app_context.pop()

    def test_profile_update_reflects_in_users_list_and_login_credentials(self):
        # 1. Sign in as test user
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_id
            sess["username"] = "test_sync_user"
            sess["role"] = "System Admin"

        # 2. Update account profile via update_my_account
        new_username = "updated_sync_user"
        new_fullname = "Updated Sync Fullname"
        new_email = "updated_sync@example.com"
        new_contact = "09222222222"

        update_payload = {
            "username": new_username,
            "fullName": new_fullname,
            "email": new_email,
            "contact": new_contact,
        }
        res = self.client.post("/api/auth.php?action=update_my_account", json=update_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("username"), new_username)
        self.assertEqual(data.get("user", {}).get("email"), new_email)

        # 3. Verify session was updated
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("username"), new_username)
            self.assertEqual(sess.get("full_name"), new_fullname)
            self.assertEqual(sess.get("email"), new_email)

        # 4. Cross-Module Sync: Verify /api/users.php?action=list reflects new details
        res_users = self.client.get("/api/users.php?action=list")
        self.assertEqual(res_users.status_code, 200)
        users_list = res_users.get_json()
        matched_user = next((u for u in users_list if u.get("id") == self.user_id), None)
        self.assertIsNotNone(matched_user, "Updated user must be found in users list")
        self.assertEqual(matched_user.get("username"), new_username)
        self.assertEqual(matched_user.get("name"), new_fullname)
        self.assertEqual(matched_user.get("email"), new_email)
        self.assertEqual(matched_user.get("contact"), new_contact)

        # 5. Clear session to simulate logging out
        with self.client.session_transaction() as sess:
            sess.clear()

        # 6. Verify Old Username CANNOT log in
        res_old_user = self.client.post("/api/auth.php?action=login", json={
            "username": "test_sync_user",
            "password": self.password
        })
        self.assertEqual(res_old_user.status_code, 401)

        # 7. Verify Old Email CANNOT log in
        res_old_email = self.client.post("/api/auth.php?action=login", json={
            "username": "original_sync@example.com",
            "password": self.password
        })
        self.assertEqual(res_old_email.status_code, 401)

        # 8. Verify New Username CAN log in
        res_new_user = self.client.post("/api/auth.php?action=login", json={
            "username": new_username,
            "password": self.password
        })
        self.assertEqual(res_new_user.status_code, 200)
        login_data_u = res_new_user.get_json()
        self.assertEqual(login_data_u.get("status"), "success")
        self.assertEqual(login_data_u.get("user", {}).get("username"), new_username)
        self.assertEqual(login_data_u.get("user", {}).get("email"), new_email)

        # Clear session
        with self.client.session_transaction() as sess:
            sess.clear()

        # 9. Verify New Email CAN log in
        res_new_email = self.client.post("/api/auth.php?action=login", json={
            "username": new_email,
            "password": self.password
        })
        self.assertEqual(res_new_email.status_code, 200)
        login_data_e = res_new_email.get_json()
        self.assertEqual(login_data_e.get("status"), "success")
        self.assertEqual(login_data_e.get("user", {}).get("username"), new_username)
        self.assertEqual(login_data_e.get("user", {}).get("email"), new_email)

if __name__ == "__main__":
    unittest.main()
