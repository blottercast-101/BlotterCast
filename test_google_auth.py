import json
import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.extensions import db
from app.models import User, OtpCode


class GoogleAuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["GOOGLE_CLIENT_ID"] = "test-client-id-12345.apps.googleusercontent.com"
        self.client = self.app.test_client()

        with self.app.app_context():
            # Setup test active user with MFA enabled
            self.user_mfa = User.query.filter_by(username="test_mfa_user").first()
            if not self.user_mfa:
                self.user_mfa = User(
                    username="test_mfa_user",
                    password="hashedpassword",
                    full_name="Test MFA User",
                    email="mfa_user@example.com",
                    role="Desk Officer",
                    status="Active",
                    mfa_enabled=True,
                )
                db.session.add(self.user_mfa)

            # Setup test active user with MFA disabled
            self.user_nomfa = User.query.filter_by(username="test_nomfa_user").first()
            if not self.user_nomfa:
                self.user_nomfa = User(
                    username="test_nomfa_user",
                    password="hashedpassword",
                    full_name="Test NoMFA User",
                    email="nomfa_user@example.com",
                    role="Desk Officer",
                    status="Active",
                    mfa_enabled=False,
                )
                db.session.add(self.user_nomfa)

            # Setup suspended user
            self.user_suspended = User.query.filter_by(username="test_suspended_user").first()
            if not self.user_suspended:
                self.user_suspended = User(
                    username="test_suspended_user",
                    password="hashedpassword",
                    full_name="Test Suspended User",
                    email="suspended_user@example.com",
                    role="Desk Officer",
                    status="Suspended",
                    mfa_enabled=True,
                )
                db.session.add(self.user_suspended)

            db.session.commit()

    def test_auth_config_returns_client_id(self):
        res = self.client.get("/api/auth.php?action=auth_config")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("google_client_id"), "test-client-id-12345.apps.googleusercontent.com")

    def test_google_login_missing_token(self):
        res = self.client.post("/api/auth.php?action=google_login", json={})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("required", data.get("error", "").lower())

    @patch("urllib.request.urlopen")
    def test_google_login_suspended_account_rejected_without_mfa(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "aud": "test-client-id-12345.apps.googleusercontent.com",
            "email": "suspended_user@example.com",
            "email_verified": "true",
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = self.client.post("/api/auth.php?action=google_login", json={"credential": "mock_token"})
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertIn("suspended", data.get("error", "").lower())

    @patch("urllib.request.urlopen")
    def test_google_login_enforces_2fa_when_enabled(self, mock_urlopen):
        with self.app.app_context():
            from app.models import SystemSecuritySetting
            sec = db.session.get(SystemSecuritySetting, 1)
            if not sec:
                sec = SystemSecuritySetting(id=1)
                db.session.add(sec)
            sec.is_2fa_globally_enabled = True
            db.session.commit()

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "aud": "test-client-id-12345.apps.googleusercontent.com",
            "email": "mfa_user@example.com",
            "email_verified": True,
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = self.client.post("/api/auth.php?action=google_login", json={"credential": "mock_token"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertTrue(data.get("mfaRequired"), "2FA MUST NOT BE BYPASSED")
        self.assertIsNotNone(data.get("maskedEmail"))
        pre_auth_token = data.get("pre_auth_token")
        self.assertIsNotNone(pre_auth_token, "Pre-auth token MUST be generated")

        # Security check: Protected API endpoints MUST reject pre_auth_token / partial state
        protected_res = self.client.get("/api/records.php?action=list", headers={"Authorization": f"Bearer {pre_auth_token}"})
        self.assertEqual(protected_res.status_code, 401, "Protected routes MUST reject pre_auth_token")

        me_res = self.client.get("/api/auth.php?action=me")
        self.assertFalse(me_res.get_json().get("authenticated"))

        # Check OTP created in DB
        with self.app.app_context():
            u = User.query.filter_by(email="mfa_user@example.com").first()
            otp = OtpCode.query.filter_by(user_id=u.id, purpose="login", consumed_at=None).order_by(OtpCode.id.desc()).first()
            self.assertIsNotNone(otp)

        # Test verification using pre_auth_token
        from app.blueprints.auth import _check_otp, _hash_otp
        with self.app.app_context():
            u = User.query.filter_by(email="mfa_user@example.com").first()
            otp = OtpCode.query.filter_by(user_id=u.id, purpose="login", consumed_at=None).order_by(OtpCode.id.desc()).first()
            test_code = "123456"
            otp.code_hash = _hash_otp(test_code)
            db.session.commit()

        verify_res = self.client.post("/api/auth.php?action=verify_otp", json={
            "code": "123456",
            "pre_auth_token": pre_auth_token,
        })
        self.assertEqual(verify_res.status_code, 200)
        self.assertTrue(verify_res.get_json().get("ok"))
        self.assertEqual(verify_res.get_json().get("user", {}).get("username"), "test_mfa_user")

        # Now fully authenticated
        me_after = self.client.get("/api/auth.php?action=me")
        self.assertTrue(me_after.get_json().get("authenticated"))

    @patch("urllib.request.urlopen")
    def test_google_login_completes_when_2fa_disabled(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = json.dumps({
            "aud": "test-client-id-12345.apps.googleusercontent.com",
            "email": "nomfa_user@example.com",
            "email_verified": True,
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = self.client.post("/api/auth.php?action=google_login", json={"credential": "mock_token"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertFalse(data.get("mfaRequired"))

        # User is authenticated
        me_res = self.client.get("/api/auth.php?action=me")
        self.assertTrue(me_res.get_json().get("authenticated"))


if __name__ == "__main__":
    unittest.main()
