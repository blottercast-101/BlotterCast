import unittest
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import User
from app.seed import seed_data


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class TestAvatarE2EPipeline(unittest.TestCase):
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

    def test_end_to_end_avatar_base64_pipeline(self):
        # 1. Sign in as admin
        login_res = self.client.post("/api/auth.php?action=login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.get_json()
        self.assertTrue(login_data["ok"])

        # 2. Simulate 256x256 Base64 canvas export payload from settings.html
        b64_avatar_data = (
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        )

        # 3. Test direct upload endpoint /api/auth.php?action=upload_avatar with JSON Base64 string
        upload_res = self.client.post(
            "/api/auth.php?action=upload_avatar",
            json={"avatar_data": b64_avatar_data},
            content_type="application/json"
        )
        self.assertEqual(upload_res.status_code, 200)
        upload_json = upload_res.get_json()
        self.assertTrue(upload_json["ok"])
        self.assertEqual(upload_json["avatar_url"], b64_avatar_data)
        self.assertEqual(upload_json["profile_photo_path"], b64_avatar_data)

        # 4. Verify DB persistence - User table has exact Base64 string and NO local ephemeral disk file path
        user_db = User.query.filter_by(username="admin").first()
        self.assertEqual(user_db.avatar_url, b64_avatar_data)
        self.assertEqual(user_db.profile_photo_path, b64_avatar_data)
        self.assertFalse(str(user_db.avatar_url).startswith("/uploads/"))

        # 5. Verify /api/auth.php?action=me returns the Base64 Data URL
        me_res = self.client.get("/api/auth.php?action=me")
        self.assertEqual(me_res.status_code, 200)
        me_json = me_res.get_json()
        self.assertEqual(me_json["user"]["avatar_url"], b64_avatar_data)

        # 6. Verify /api/auth.php?action=my_account returns the Base64 Data URL
        acct_res = self.client.get("/api/auth.php?action=my_account")
        self.assertEqual(acct_res.status_code, 200)
        acct_json = acct_res.get_json()
        self.assertEqual(acct_json["avatar_url"], b64_avatar_data)

        # 7. Verify /api/users returns Base64 Data URL for table rendering
        users_res = self.client.get("/api/users")
        self.assertEqual(users_res.status_code, 200)
        users_json = users_res.get_json()
        admin_entry = next((u for u in users_json if u["username"] == "admin"), None)
        self.assertIsNotNone(admin_entry)
        self.assertEqual(admin_entry.get("avatar_url"), b64_avatar_data)

        # 8. Test /api/users.php?action=upload_avatar with avatar_data JSON payload
        b64_kapitan_data = (
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        )
        self.client.post("/api/auth.php?action=login", json={"username": "kapitan", "password": "kapitan123"})
        users_upload_res = self.client.post(
            "/api/users.php?action=upload_avatar",
            json={"avatar_data": b64_kapitan_data},
            content_type="application/json"
        )
        self.assertEqual(users_upload_res.status_code, 200)
        users_upload_json = users_upload_res.get_json()
        self.assertTrue(users_upload_json["ok"])
        self.assertEqual(users_upload_json["avatar_url"], b64_kapitan_data)

        # 9. Verify server restart/reseed does not wipe the avatar
        seed_data(self.app, force_reset=False)
        kapitan_db = User.query.filter_by(username="kapitan").first()
        self.assertEqual(kapitan_db.avatar_url, b64_kapitan_data)

        # 10. Test avatar removal
        del_res = self.client.delete("/api/user/avatar")
        self.assertEqual(del_res.status_code, 200)
        del_json = del_res.get_json()
        self.assertTrue(del_json["ok"])
        self.assertIsNone(del_json["avatar_url"])

        kapitan_after_del = User.query.filter_by(username="kapitan").first()
        self.assertIsNone(kapitan_after_del.avatar_url)
        self.assertIsNone(kapitan_after_del.profile_photo_path)


if __name__ == "__main__":
    unittest.main()
