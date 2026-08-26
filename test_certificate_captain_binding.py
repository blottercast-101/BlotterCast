import unittest
from app import create_app
from app.extensions import db
from app.models import SystemSetting, User
from test_mfa_helper import login as mfa_login


class TestCertificateCaptainBinding(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_captain_signature_returns_name(self):
        with self.app.app_context():
            # Login as Desk Officer
            mfa_login(self.client, "jdelacuz", "officer123")
            res = self.client.get("/api/users.php?action=captain_signature")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIsNotNone(data.get("fullName"))
            self.assertIn("captain_name", data)
            self.assertIn("punong_barangay", data)
            self.assertTrue(len(data.get("fullName", "")) > 0)

    def test_templates_contain_cert_captain_name_class(self):
        templates = [
            "frontend/clearance.html",
            "frontend/residency.html",
            "frontend/indigency.html",
            "frontend/non_residency.html",
        ]
        for tpath in templates:
            with open(tpath, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(
                    "cert-captain-name",
                    content,
                    f"Template {tpath} must contain the 'cert-captain-name' class for Punong Barangay dynamic binding"
                )


if __name__ == "__main__":
    unittest.main()
