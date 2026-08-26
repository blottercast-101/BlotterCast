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

    def test_captain_signature_decoupled_from_session(self):
        with self.app.app_context():
            # Update settings directly to custom captain name
            row = SystemSetting.query.get("barangay_captain")
            if not row:
                row = SystemSetting(setting_key="barangay_captain", setting_value="Alex Roque Cruz")
                db.session.add(row)
            else:
                row.setting_value = "Alex Roque Cruz"

            c_row = SystemSetting.query.get("captain_name")
            if c_row:
                c_row.setting_value = "Alex Roque Cruz"
            p_row = SystemSetting.query.get("punong_barangay")
            if p_row:
                p_row.setting_value = "Alex Roque Cruz"
            db.session.commit()

            # Login as Desk Officer (jdelacuz)
            mfa_login(self.client, "jdelacuz", "officer123")

            # Signatory endpoint must return "Alex Roque Cruz", NOT "J. Dela Cruz"
            res = self.client.get("/api/users.php?action=captain_signature")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("fullName"), "Alex Roque Cruz")
            self.assertEqual(data.get("signatory_captain"), "Alex Roque Cruz")
            self.assertEqual(data.get("barangay_captain"), "Alex Roque Cruz")

            # Restore original
            row.setting_value = "Kapitan Jose Reyes"
            if c_row:
                c_row.setting_value = "Kapitan Jose Reyes"
            if p_row:
                p_row.setting_value = "Kapitan Jose Reyes"
            db.session.commit()

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
