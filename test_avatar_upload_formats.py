import base64
import io
import os
import unittest
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SERVER_NAME = "localhost"


class TestAvatarUploadFormats(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.created_avatar_files = []

        with self.app.app_context():
            db.create_all()
            user = User.query.filter_by(username="admin").first()
            if not user:
                user = User(
                    username="admin",
                    role="Administrator",
                    status="Active",
                    full_name="Admin Test",
                    email="admin@example.com",
                    contact_no="09171234567",
                )
                user.set_password("AdminPass123!")
                db.session.add(user)
                db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        for path in self.created_avatar_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_id
            sess["username"] = "admin"
            sess["role"] = "Administrator"
            sess["full_name"] = "Admin Test"
            sess["_user_id"] = str(self.user_id)
            sess["_fresh"] = True

    def test_uppercase_jpg_and_external_formats(self):
        self._login()

        # 1. Test uppercase .JPG
        dummy_jpg = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb")
        res = self.client.post(
            "/api/auth.php?action=upload_avatar",
            data={"avatar": (dummy_jpg, "PHONE_PHOTO_2026.JPG")},
            content_type="multipart/form-data",
        )
        self.assertEqual(res.status_code, 200, res.data.decode("utf-8"))
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        avatar_url = data.get("avatar_url")
        self.assertTrue(avatar_url.startswith("data:image/"))

        # 2. Test WebP format
        dummy_webp = io.BytesIO(b"RIFF\x24\x00\x00\x00WEBPVP8 \x18\x00\x00\x00")
        res_webp = self.client.post(
            "/api/auth.php?action=upload_avatar",
            data={"avatar": (dummy_webp, "downloaded_image.webp")},
            content_type="multipart/form-data",
        )
        self.assertEqual(res_webp.status_code, 200)
        data_webp = res_webp.get_json()
        self.assertTrue(data_webp.get("ok"))
        self.assertTrue(data_webp["avatar_url"].startswith("data:image/"))

    def test_base64_data_url_upload(self):
        self._login()

        # 1x1 transparent PNG / JPEG base64 data url
        tiny_jpeg_b64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        res = self.client.post(
            "/api/auth.php?action=upload_avatar",
            json={"avatar": tiny_jpeg_b64},
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200, res.data.decode("utf-8"))
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("avatar_url"), tiny_jpeg_b64)

    def test_update_my_account_with_base64_and_format(self):
        self._login()
        tiny_png_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        res = self.client.post(
            "/api/auth.php?action=update_my_account",
            json={
                "fullName": "Admin Test Updated",
                "email": "admin_updated@example.com",
                "contact": "09189876543",
                "avatar": tiny_png_b64,
            },
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200, res.data.decode("utf-8"))
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("avatar_url"), tiny_png_b64)

    def test_non_image_rejection(self):
        self._login()
        dummy_pdf = io.BytesIO(b"%PDF-1.4 dummy file content")
        res = self.client.post(
            "/api/auth.php?action=upload_avatar",
            data={"avatar": (dummy_pdf, "document.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("ok"))


if __name__ == "__main__":
    unittest.main()
