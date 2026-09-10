import io
import os
import unittest
from flask import current_app
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


class TestProfilePhotoPersistence(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        seed_data(self.app, force_reset=True)
        self.created_avatar_files = []

    def tearDown(self):
        for path in self.created_avatar_files:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _create_dummy_png(self):
        # 1x1 pixel PNG bytes
        png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05'
            b'\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        return io.BytesIO(png_bytes)

    def test_upload_avatar_and_persistence(self):
        # 1. Log in as kapitan
        login_res = self.client.post("/api/auth.php?action=login", json={
            "username": "kapitan",
            "password": "kapitan123"
        })
        self.assertEqual(login_res.status_code, 200)

        # 2. Upload dummy avatar image via direct REST endpoint /api/user/avatar
        file_data = self._create_dummy_png()
        upload_res = self.client.post(
            "/api/user/avatar",
            data={"avatar": (file_data, "test_avatar.png")},
            content_type="multipart/form-data"
        )
        self.assertEqual(upload_res.status_code, 200)
        upload_json = upload_res.get_json()
        self.assertTrue(upload_json["ok"])
        self.assertTrue(upload_json["success"])
        avatar_url = upload_json["avatar_url"]
        self.assertTrue(avatar_url.startswith("/uploads/avatars/avatar_"))

        # Verify physical file existence
        full_disk_path = os.path.join(self.app.static_folder, avatar_url.lstrip("/"))
        self.assertTrue(os.path.isfile(full_disk_path))
        self.created_avatar_files.append(full_disk_path)

        # 3. Check /api/auth.php?action=me returns avatar
        me_res = self.client.get("/api/auth.php?action=me")
        self.assertEqual(me_res.status_code, 200)
        me_json = me_res.get_json()
        self.assertEqual(me_json["user"]["avatar_url"], avatar_url)

        # 4. Check /api/auth.php?action=my_account returns avatar
        acct_res = self.client.get("/api/auth.php?action=my_account")
        self.assertEqual(acct_res.status_code, 200)
        acct_json = acct_res.get_json()
        self.assertEqual(acct_json["avatar_url"], avatar_url)

        # 5. Check action parameter endpoint /api/auth.php?action=upload_avatar
        rest_file = self._create_dummy_png()
        rest_upload_res = self.client.post(
            "/api/auth.php?action=upload_avatar",
            data={"photo": (rest_file, "rest_avatar.png")},
            content_type="multipart/form-data"
        )
        self.assertEqual(rest_upload_res.status_code, 200)
        rest_json = rest_upload_res.get_json()
        new_avatar_url = rest_json["avatar_url"]
        new_disk_path = os.path.join(self.app.static_folder, new_avatar_url.lstrip("/"))
        self.assertTrue(os.path.isfile(new_disk_path))
        self.created_avatar_files.append(new_disk_path)

        # Old avatar file should have been cleaned up
        self.assertFalse(os.path.isfile(full_disk_path))

        # 6. Verify seeder does not overwrite avatar_url on restart/seed_data
        seed_data(self.app, force_reset=False)
        user_db = User.query.filter_by(username="kapitan").first()
        self.assertEqual(user_db.avatar_url, new_avatar_url)

        # 7. Update account details and verify avatar is retained
        update_res = self.client.post("/api/auth.php?action=update_my_account", json={
            "fullName": "Captain Jose Updated",
            "email": "fhalynramos4@gmail.com",
            "contact": "09170000000"
        })
        self.assertEqual(update_res.status_code, 200)
        update_json = update_res.get_json()
        self.assertEqual(update_json["user"]["avatar_url"], new_avatar_url)

        # 8. Remove avatar via DELETE /api/user/avatar
        remove_res = self.client.delete("/api/user/avatar")
        self.assertEqual(remove_res.status_code, 200)
        remove_json = remove_res.get_json()
        self.assertTrue(remove_json["ok"])
        self.assertTrue(remove_json["success"])
        self.assertIsNone(remove_json["avatar_url"])
        self.assertFalse(os.path.isfile(new_disk_path))

        # Check /api/auth.php?action=me after remove
        me_after_remove = self.client.get("/api/auth.php?action=me").get_json()
        self.assertIsNone(me_after_remove["user"]["avatar_url"])

    def test_cors_options_preflight_and_avatar_endpoints(self):
        # 1. Test OPTIONS on /api/user/avatar with Origin header
        options_res = self.client.options(
            "/api/user/avatar",
            headers={"Origin": "http://192.168.100.82:5000", "Access-Control-Request-Method": "POST"}
        )
        self.assertIn(options_res.status_code, (200, 204))
        self.assertEqual(options_res.headers.get("Access-Control-Allow-Origin"), "http://192.168.100.82:5000")
        self.assertIn("POST", options_res.headers.get("Access-Control-Allow-Methods", ""))

        # 2. Test OPTIONS on /api/auth.php
        opt_auth = self.client.options("/api/auth.php", headers={"Origin": "http://localhost:5500"})
        self.assertIn(opt_auth.status_code, (200, 204))
        self.assertEqual(opt_auth.headers.get("Access-Control-Allow-Origin"), "http://localhost:5500")

        # 3. Log in and test POST /api/user/avatar never returns 405
        self.client.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})
        file_data = self._create_dummy_png()
        post_res = self.client.post(
            "/api/user/avatar",
            data={"avatar": (file_data, "admin_avatar.png")},
            content_type="multipart/form-data"
        )
        self.assertNotEqual(post_res.status_code, 405)
        self.assertEqual(post_res.status_code, 200)
        avatar_url = post_res.get_json()["avatar_url"]
        full_disk_path = os.path.join(self.app.static_folder, avatar_url.lstrip("/"))
        self.created_avatar_files.append(full_disk_path)

        # 4. Test DELETE /api/user/avatar works cleanly
        del_res = self.client.delete("/api/user/avatar")
        self.assertNotEqual(del_res.status_code, 405)
        self.assertEqual(del_res.status_code, 200)

    def test_replicated_signature_upload_pattern_for_avatar(self):
        # 1. Log in as admin
        self.client.post("/api/auth.php?action=login", json={"username": "admin", "password": "admin123"})

        # 2. Upload avatar via POST /api/users.php?action=upload_avatar (signature-pattern)
        file_data = self._create_dummy_png()
        res = self.client.post(
            "/api/users.php?action=upload_avatar",
            data={"avatar": (file_data, "users_sig_style_avatar.png")},
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 200)
        res_json = res.get_json()
        self.assertTrue(res_json.get("ok") or res_json.get("success"))
        avatar_path = res_json["avatar_url"]
        self.assertTrue(avatar_path.startswith("/uploads/avatars/"))
        full_disk_path = os.path.join(self.app.static_folder, avatar_path.lstrip("/"))
        self.assertTrue(os.path.isfile(full_disk_path))
        self.created_avatar_files.append(full_disk_path)

        # 3. Test Base64 Data URL avatar update via update_my_account
        data_url = (
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        up_res = self.client.post("/api/auth.php?action=update_my_account", json={
            "fullName": "System Administrator",
            "email": "blottercast@gmail.com",
            "contact": "09784561232",
            "avatar": data_url
        })
        self.assertEqual(up_res.status_code, 200)
        up_json = up_res.get_json()
        b64_avatar_path = up_json["avatar_url"]
        self.assertTrue(b64_avatar_path.startswith("/uploads/avatars/"))
        b64_disk_path = os.path.join(self.app.static_folder, b64_avatar_path.lstrip("/"))
        self.assertTrue(os.path.isfile(b64_disk_path))
        self.created_avatar_files.append(b64_disk_path)

        # 4. Remove avatar via POST /api/users.php?action=remove_avatar
        rem_res = self.client.post("/api/users.php?action=remove_avatar")
        self.assertEqual(rem_res.status_code, 200)
        rem_json = rem_res.get_json()
        self.assertTrue(rem_json.get("ok") or rem_json.get("success"))
        self.assertIsNone(rem_json["avatar_url"])


if __name__ == "__main__":
    unittest.main()
