"""Unit and integration tests for Google OAuth and Account Linking.
"""
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import User
from test_mfa_helper import login as mfa_login


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    GOOGLE_CLIENT_ID = "test-google-client-id"


def setup_test_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed test users
        from seed import DEMO_USERS, SETTINGS, ZONES, hash_password
        from app.models import SystemSetting, Zone
        for zone_id, label, lat, lng, weight in ZONES:
            db.session.add(Zone(zone_id=zone_id, label=label, lat=lat, lng=lng, weight=weight))
        for key, value in SETTINGS.items():
            db.session.add(SystemSetting(setting_key=key, setting_value=value))
        for username, password, full_name, role, email in DEMO_USERS:
            db.session.add(User(
                username=username, password=hash_password(password),
                full_name=full_name, role=role, status="Active", email=email,
            ))
        db.session.commit()
    return app


def test_google_auth_flow():
    app = setup_test_app()
    client = app.test_client()

    # 1. Test auth_config endpoint
    r = client.get("/api/auth.php?action=auth_config")
    assert r.status_code == 200, r.get_json()
    assert r.get_json().get("googleClientId") == "test-google-client-id"
    print("1. auth_config OK")

    # 2. Test google_login with unlinked account
    # Token format: "mock-google-token:<email>:<sub_id>"
    unlinked_token = "mock-google-token:unknown_user@gmail.com:google-sub-9999"
    r = client.post("/api/auth.php?action=google_login", json={"credential": unlinked_token})
    assert r.status_code == 403, r.get_json()
    assert "No registered account found" in r.get_json().get("error", "")
    print("2. Unlinked google_login rejected with 403 OK")

    # 3. Normal login then link Google account in settings
    mfa_login(client, "jdelacuz", "officer123")
    r = client.get("/api/auth.php?action=my_account")
    assert r.status_code == 200
    assert r.get_json().get("isGoogleLinked") is False

    officer_google_token = "mock-google-token:jdelacruz.official@gmail.com:google-sub-1001"
    r = client.post("/api/auth.php?action=link_google", json={"credential": officer_google_token})
    assert r.status_code == 200, r.get_json()
    assert r.get_json().get("isGoogleLinked") is True
    assert r.get_json().get("googleEmail") == "jdelacruz.official@gmail.com"

    r = client.get("/api/auth.php?action=my_account")
    assert r.get_json().get("isGoogleLinked") is True
    assert r.get_json().get("googleEmail") == "jdelacruz.official@gmail.com"
    print("3. Google account linked in settings OK")

    # 4. Log out and log in via Google
    client.get("/api/auth.php?action=logout")
    r = client.get("/api/auth.php?action=me")
    assert r.get_json().get("authenticated") is False

    r = client.post("/api/auth.php?action=google_login", json={"credential": officer_google_token})
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert data.get("ok") is True
    assert data["user"]["username"] == "jdelacuz"
    print("4. Google sign-in for linked account succeeded OK")

    # 5. Prevent duplicate linking across accounts
    client.get("/api/auth.php?action=logout")
    mfa_login(client, "msantos", "officer123")
    r = client.post("/api/auth.php?action=link_google", json={"credential": officer_google_token})
    assert r.status_code == 409, r.get_json()
    assert "already linked to another" in r.get_json().get("error", "")
    print("5. Duplicate linking rejected with 409 OK")

    # 6. Unlink Google account
    client.get("/api/auth.php?action=logout")
    mfa_login(client, "jdelacuz", "officer123")
    r = client.post("/api/auth.php?action=unlink_google")
    assert r.status_code == 200, r.get_json()
    assert r.get_json().get("isGoogleLinked") is False

    client.get("/api/auth.php?action=logout")
    r = client.post("/api/auth.php?action=google_login", json={"credential": officer_google_token})
    assert r.status_code == 403
    print("6. Unlinked Google account rejected from sign-in OK")

    # 7. Account matching registered email (e.g. admin has fileyourname@gmail.com)
    admin_token = "mock-google-token:fileyourname@gmail.com:google-sub-admin"
    r = client.post("/api/auth.php?action=google_login", json={"credential": admin_token})
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["user"]["username"] == "admin"
    print("7. Login matching registered email OK")

    # 8. Suspended user rejection
    with app.app_context():
        u = User.query.filter_by(username="pencoder").first()
        u.status = "Suspended"
        u.google_id = "google-sub-pencoder"
        u.google_email = "pencoder@gmail.com"
        db.session.commit()

    pencoder_token = "mock-google-token:pencoder@gmail.com:google-sub-pencoder"
    r = client.post("/api/auth.php?action=google_login", json={"credential": pencoder_token})
    assert r.status_code == 403, r.get_json()
    assert "suspended" in r.get_json().get("error", "").lower()
    print("8. Suspended user rejected from Google sign-in OK")

    print("\nAll Google authentication tests PASSED successfully!")


if __name__ == "__main__":
    test_google_auth_flow()
