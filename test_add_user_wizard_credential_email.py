import unittest
import bcrypt
from app import create_app
from app.extensions import db
from app.models import User
from app.email import DEV_OUTBOX, clear_dev_outbox, get_latest_credential_email


class TestAddUserWizardCredentialEmail(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        clear_dev_outbox()

    def tearDown(self):
        with self.app.app_context():
            User.query.filter(User.username.in_(["testdeskofficer1", "testdataencoder1", "testinvalidrole"])).delete()
            db.session.commit()
        clear_dev_outbox()

    def test_create_desk_officer_sends_credential_email_with_notice(self):
        with self.app.app_context():
            admin = User.query.filter_by(role="System Admin").first()
            self.assertIsNotNone(admin)

            # Log in as System Admin
            with self.client.session_transaction() as sess:
                sess["user_id"] = admin.id
                sess["username"] = admin.username
                sess["role"] = admin.role
                sess["auth_tier"] = 2
                sess["mfa_verified"] = True

            payload = {
                "name": "Maria Clara Santos",
                "username": "testdeskofficer1",
                "email": "mclara@barangay.gov.ph",
                "contact": "09171234567",
                "role": "Desk Officer",
                "password": "DSK-TEST99",
            }

            res = self.client.post("/api/users.php?action=create", json=payload)
            self.assertEqual(res.status_code, 201)
            data = res.get_json()
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("temp_password"), "DSK-TEST99")

            # Check User in database
            created_user = User.query.filter_by(username="testdeskofficer1").first()
            self.assertIsNotNone(created_user)
            self.assertEqual(created_user.full_name, "Maria Clara Santos")
            self.assertEqual(created_user.role, "Desk Officer")
            self.assertEqual(created_user.email, "mclara@barangay.gov.ph")
            # Password must be hashed with bcrypt
            self.assertTrue(bcrypt.checkpw("DSK-TEST99".encode("utf-8"), created_user.password.encode("utf-8")))

            # Check that automated credential email was dispatched
            cred_email = get_latest_credential_email("mclara@barangay.gov.ph")
            self.assertIsNotNone(cred_email, "Credential email must be dispatched upon account creation")
            self.assertIn("DSK-TEST99", cred_email["body"])
            self.assertIn("IMPORTANT: This is an auto-generated temporary password. You are required to change your password immediately upon logging in by visiting Settings -> Change Password.", cred_email["body"])
            self.assertIn("Maria Clara Santos", cred_email["body"])
            self.assertIn("testdeskofficer1", cred_email["body"])
            self.assertIn("Desk Officer", cred_email["body"])

    def test_create_data_encoder_sends_credential_email(self):
        with self.app.app_context():
            admin = User.query.filter_by(role="System Admin").first()
            self.assertIsNotNone(admin)

            with self.client.session_transaction() as sess:
                sess["user_id"] = admin.id
                sess["username"] = admin.username
                sess["role"] = admin.role
                sess["auth_tier"] = 2
                sess["mfa_verified"] = True

            payload = {
                "name": "Juan Dela Cruz",
                "username": "testdataencoder1",
                "email": "jdelacruz@barangay.gov.ph",
                "contact": "09189876543",
                "role": "Data Encoder",
                "password": "DTA-ENCODER7",
            }

            res = self.client.post("/api/users.php?action=create", json=payload)
            self.assertEqual(res.status_code, 201)

            cred_email = get_latest_credential_email("jdelacruz@barangay.gov.ph")
            self.assertIsNotNone(cred_email)
            self.assertIn("DTA-ENCODER7", cred_email["body"])
            self.assertIn("IMPORTANT: This is an auto-generated temporary password", cred_email["body"])

    def test_forbidden_roles_cannot_be_created(self):
        with self.app.app_context():
            admin = User.query.filter_by(role="System Admin").first()
            with self.client.session_transaction() as sess:
                sess["user_id"] = admin.id
                sess["username"] = admin.username
                sess["role"] = admin.role
                sess["auth_tier"] = 2
                sess["mfa_verified"] = True

            # Attempt to create System Admin
            res1 = self.client.post("/api/users.php?action=create", json={
                "name": "Hacker Admin",
                "username": "testinvalidrole",
                "email": "hacker@test.com",
                "role": "System Admin",
                "password": "ADM-INVALID1",
            })
            self.assertEqual(res1.status_code, 403)

            # Attempt to create Barangay Captain
            res2 = self.client.post("/api/users.php?action=create", json={
                "name": "Fake Captain",
                "username": "testinvalidrole",
                "email": "hacker2@test.com",
                "role": "Barangay Captain",
                "password": "CPT-INVALID1",
            })
            self.assertEqual(res2.status_code, 403)


if __name__ == "__main__":
    unittest.main()
