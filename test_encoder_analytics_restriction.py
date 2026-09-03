import unittest
from datetime import datetime

from app import create_app
from app.alert_dispatcher import (
    ANALYTICS_NOTIFICATION_TYPES,
    get_eligible_analytics_users,
    is_encoder_role,
    notify_analytics_change,
)
from app.config import Config
from app.extensions import db
from app.models import Incident, Notification, NotificationRead, Settlement, User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-encoder-secret"
    WTF_CSRF_ENABLED = False


class TestEncoderAnalyticsRestriction(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Admin user
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@test.gov",
                full_name="System Administrator",
                role="System Admin",
                status="Active",
                password="password"
            )
            db.session.add(admin)
            db.session.commit()
        self.admin_id = admin.id

        # Barangay Captain user
        captain = User.query.filter_by(username="captain").first()
        if not captain:
            captain = User(
                username="captain",
                email="captain@test.gov",
                full_name="Barangay Captain",
                role="Barangay Captain",
                status="Active",
                password="password"
            )
            db.session.add(captain)
            db.session.commit()
        self.captain_id = captain.id

        # Data Encoder user
        encoder = User.query.filter_by(username="encoder_user").first()
        if not encoder:
            encoder = User(
                username="encoder_user",
                email="encoder@test.gov",
                full_name="Data Encoder User",
                role="Data Encoder",
                status="Active",
                password="password"
            )
            db.session.add(encoder)
            db.session.commit()
        self.encoder_id = encoder.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self, user_id, role, username):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["username"] = username
            sess["role"] = role
            sess["last_activity"] = datetime.utcnow().timestamp()

    def test_01_is_encoder_role_helper(self):
        """Verify is_encoder_role correctly classifies roles"""
        self.assertTrue(is_encoder_role("Data Encoder"))
        self.assertTrue(is_encoder_role("data_encoder"))
        self.assertTrue(is_encoder_role("Encoder"))
        self.assertFalse(is_encoder_role("System Admin"))
        self.assertFalse(is_encoder_role("Barangay Captain"))
        self.assertFalse(is_encoder_role("Desk Officer"))

    def test_02_get_eligible_analytics_users_excludes_encoders(self):
        """Verify get_eligible_analytics_users returns Admin and Captain but never Data Encoder"""
        eligible = get_eligible_analytics_users()
        eligible_roles = [u.role for u in eligible]
        self.assertIn("System Admin", eligible_roles)
        self.assertIn("Barangay Captain", eligible_roles)
        self.assertNotIn("Data Encoder", eligible_roles)

    def test_03_notify_analytics_change_marks_read_for_encoders(self):
        """Verify notify_analytics_change creates notification and records read receipt for encoder"""
        notif = notify_analytics_change({
            "type": "prediction_alert",
            "title": "Elevated Risk Forecast Alert: Zone 2",
            "message": "Predictive models project high risk in Zone 2.",
            "route": "predictions.html",
            "priority": "High"
        })
        db.session.commit()

        self.assertIsNotNone(notif)
        self.assertEqual(notif.type, "prediction_alert")

        # Check that encoder has read receipt recorded automatically
        read_entry = NotificationRead.query.filter_by(user_id=self.encoder_id, notification_id=notif.id).first()
        self.assertIsNotNone(read_entry)

    def test_04_server_query_scope_admin_vs_encoder(self):
        """Verify Admin sees analytics alerts while Data Encoder strictly receives zero analytics alerts"""
        # Create standard notification
        db.session.add(Notification(
            type="incident_crud",
            title="New Incident Report Filed: INC-2026-0001",
            body="New incident reported in Zone 1",
            severity="info",
            link="incident.html?highlight=INC-2026-0001"
        ))

        # Create analytics alerts
        db.session.add(Notification(
            type="prediction_alert",
            title="Elevated Risk Forecast Alert: Zone 3",
            body="Zone 3 forecasted with heightened risk",
            severity="critical",
            link="predictions.html"
        ))
        db.session.add(Notification(
            type="trend_alert",
            title="Unusual Trend Spike Detected: Theft",
            body="Theft increased by 40% this week",
            severity="warning",
            link="trends.html"
        ))
        db.session.add(Notification(
            type="heatmap_hotspot",
            title="Geospatial Hotspot Alert: Zone 5",
            body="Cluster detected in Zone 5",
            severity="warning",
            link="heatmap.html"
        ))
        db.session.commit()

        # 1. System Admin query
        self._login(self.admin_id, "System Admin", "admin")
        res_admin = self.client.get("/api/notifications.php?action=list")
        self.assertEqual(res_admin.status_code, 200)
        admin_items = res_admin.get_json()
        admin_types = [item["type"] for item in admin_items]
        self.assertIn("incident_crud", admin_types)
        self.assertIn("prediction_alert", admin_types)
        self.assertIn("trend_alert", admin_types)
        self.assertIn("heatmap_hotspot", admin_types)

        # 2. Data Encoder query
        self._login(self.encoder_id, "Data Encoder", "encoder_user")
        res_encoder = self.client.get("/api/notifications.php?action=list")
        self.assertEqual(res_encoder.status_code, 200)
        encoder_items = res_encoder.get_json()
        encoder_types = [item["type"] for item in encoder_items]
        self.assertIn("incident_crud", encoder_types)
        self.assertNotIn("prediction_alert", encoder_types)
        self.assertNotIn("trend_alert", encoder_types)
        self.assertNotIn("heatmap_hotspot", encoder_types)
        self.assertNotIn("predictive_risk", encoder_types)
        self.assertNotIn("trend_spike", encoder_types)
        self.assertEqual(len(encoder_items), 1)

    def test_05_unread_counter_isolation_for_encoder(self):
        """Verify unread counter for Data Encoder does not count analytics alerts"""
        # Clear existing records so _generate_notifications does not generate seeded overdue/high priority items
        Incident.query.delete()
        Settlement.query.delete()
        Notification.query.delete()
        NotificationRead.query.delete()
        db.session.commit()

        # Add 1 standard incident notification and 2 analytics notifications
        db.session.add(Notification(
            type="incident_crud",
            title="Incident INC-999",
            body="Details",
            severity="info"
        ))
        db.session.add(Notification(
            type="prediction_alert",
            title="Prediction Alert",
            body="Details",
            severity="critical"
        ))
        db.session.add(Notification(
            type="trend_alert",
            title="Trend Alert",
            body="Details",
            severity="warning"
        ))
        db.session.commit()

        # Admin unread count: sees all 3
        self._login(self.admin_id, "System Admin", "admin")
        res_admin = self.client.get("/api/notifications.php?action=unread_count")
        self.assertEqual(res_admin.status_code, 200)
        self.assertEqual(res_admin.get_json()["count"], 3)

        # Encoder unread count: strictly sees only 1 (incident_crud), 0 analytics alerts
        self._login(self.encoder_id, "Data Encoder", "encoder_user")
        res_encoder = self.client.get("/api/notifications.php?action=unread_count")
        self.assertEqual(res_encoder.status_code, 200)
        self.assertEqual(res_encoder.get_json()["count"], 1)


if __name__ == "__main__":
    unittest.main()
