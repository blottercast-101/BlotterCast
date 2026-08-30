import unittest
from app import create_app
from app.extensions import db
from app.models import User
from app.seed import seed_data


from app.config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False


class TestUserProfilePersistence(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        seed_data(self.app, force_reset=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_update_my_account_persists_in_session_and_me(self):
        # 1. Log in as kapitan
        res = self.client.post("/api/auth.php?action=login", json={
            "username": "kapitan",
            "password": "kapitan123"
        })
        self.assertEqual(res.status_code, 200)

        # 2. Check initial /api/auth.php?action=me
        me_res = self.client.get("/api/auth.php?action=me")
        self.assertEqual(me_res.status_code, 200)
        me_data = me_res.get_json()
        self.assertTrue(me_data["authenticated"])
        self.assertEqual(me_data["user"]["full_name"], "Barangay Captain")

        # 3. Update account full name to "Mang Juan"
        update_res = self.client.post("/api/auth.php?action=update_my_account", json={
            "fullName": "Mang Juan",
            "email": "fhalynramos4@gmail.com",
            "contact": "09171234567"
        })
        self.assertEqual(update_res.status_code, 200)
        update_data = update_res.get_json()
        self.assertTrue(update_data["ok"])
        self.assertEqual(update_data["user"]["fullName"], "Mang Juan")
        self.assertEqual(update_data["user"]["full_name"], "Mang Juan")

        # 4. Subsequent /api/auth.php?action=me (simulating client navigating to any page)
        me_after = self.client.get("/api/auth.php?action=me")
        self.assertEqual(me_after.status_code, 200)
        me_after_data = me_after.get_json()
        self.assertTrue(me_after_data["authenticated"])
        self.assertEqual(me_after_data["user"]["full_name"], "Mang Juan")
        self.assertEqual(me_after_data["user"]["fullName"], "Mang Juan")

        # 5. /api/auth.php?action=my_account
        acct_res = self.client.get("/api/auth.php?action=my_account")
        self.assertEqual(acct_res.status_code, 200)
        acct_data = acct_res.get_json()
        self.assertEqual(acct_data["fullName"], "Mang Juan")


if __name__ == "__main__":
    unittest.main()
