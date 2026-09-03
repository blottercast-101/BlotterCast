import unittest
from app import create_app
from app.extensions import db
from app.models import SystemSetting
from test_mfa_helper import login as mfa_login


class TestBarangayInfoSync(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            from app.blueprints.auth import _hash_password
            from app.models import User
            u = User.query.filter_by(username="test_desk_officer").first()
            if not u:
                db.session.add(User(
                    username="test_desk_officer",
                    password=_hash_password("officer123"),
                    full_name="Test Officer",
                    role="Desk Officer",
                    email="test_desk@blottercast.local",
                    status="Active",
                ))
                db.session.commit()

    def test_get_general_settings(self):
        with self.app.app_context():
            # Login as officer
            mfa_login(self.client, "test_desk_officer", "officer123")
            res = self.client.get("/api/settings/general")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data.get("ok"))
            self.assertIn("barangay_name", data["data"])
            self.assertIn("municipality", data["data"])
            self.assertIn("captain_name", data["data"])

    def test_update_general_settings_rbac(self):
        with self.app.app_context():
            # Officer cannot update general settings (403)
            mfa_login(self.client, "test_desk_officer", "officer123")
            res = self.client.post("/api/settings/general", json={"barangay_name": "Unauthorized Barangay"})
            self.assertEqual(res.status_code, 403)

            # Admin can update general settings (200)
            mfa_login(self.client, "admin", "admin123")
            res = self.client.post("/api/settings/general", json={
                "barangay_name": "Barangay Mapulang Lupa Official",
                "municipality": "Pandi",
                "province": "Bulacan",
                "captain_name": "Kapitan Jose Reyes",
                "contact_number": "0917-888-9999",
                "email": "mapulanglupa@pandi.gov.ph",
                "official_logo_url": "img/seal.png"
            })
            self.assertEqual(res.status_code, 200)
            json_data = res.get_json()
            self.assertTrue(json_data.get("success"))
            self.assertEqual(json_data["data"]["barangay_name"], "Barangay Mapulang Lupa Official")
            self.assertEqual(json_data["data"]["captain_name"], "Kapitan Jose Reyes")
            self.assertEqual(json_data["data"]["punong_barangay"], "Kapitan Jose Reyes")
            self.assertEqual(json_data["data"]["contact_no"], "0917-888-9999")

            # Verify in DB
            b_name = SystemSetting.query.get("barangay_name")
            self.assertEqual(b_name.setting_value, "Barangay Mapulang Lupa Official")

            # Restore original name for cleanliness
            b_name.setting_value = "Barangay Mapulang Lupa"
            db.session.commit()


if __name__ == "__main__":
    unittest.main()
