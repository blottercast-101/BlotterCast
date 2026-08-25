import unittest
from datetime import datetime, timedelta
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Incident, MlRun, Notification, User, SystemSetting


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False


class TestNotificationsAndSearch(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(
                username="admin",
                email="admin@test.gov",
                full_name="Admin User",
                role="System Admin",
                status="Active",
                password="hashedpassword"
            )
            db.session.add(user)
        db.session.commit()
        self.user_id = user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.user_id
            sess["username"] = "admin"
            sess["role"] = "System Admin"
            sess["last_activity"] = datetime.utcnow().timestamp()

    def test_incident_crud_notifications(self):
        self._login()
        # 1. Test Incident ADD creates notification
        res = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-0099",
            "date": "2026-08-22",
            "timeReported": "14:30",
            "zone": "Zone 2",
            "location": "Purok 3",
            "category": "Theft",
            "priority": "High",
            "status": "Under Investigation",
            "reporter": "John Doe",
            "officer": "Officer Santos",
            "description": "Stolen bicycle"
        })
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()["id"]

        notifs = Notification.query.filter_by(type="incident_crud", ref_id=inc_id).all()
        self.assertTrue(len(notifs) >= 1)
        self.assertIn("INC-2026-0099", notifs[0].body)
        self.assertIn("[ADD]", notifs[0].body)
        self.assertIn("admin", notifs[0].body)

        # 2. Test Incident EDIT creates notification
        res_put = self.client.put(f"/api/records.php?type=incidents&id={inc_id}", json={
            "reportNo": "INC-2026-0099",
            "date": "2026-08-22",
            "timeReported": "14:30",
            "zone": "Zone 2",
            "location": "Purok 3",
            "category": "Theft",
            "priority": "High",
            "status": "Resolved",
            "reporter": "John Doe",
            "officer": "Officer Santos",
            "description": "Recovered"
        })
        self.assertEqual(res_put.status_code, 200)

        edit_notifs = Notification.query.filter(
            Notification.type == "incident_crud",
            Notification.body.like("%[EDIT]%")
        ).all()
        self.assertTrue(len(edit_notifs) >= 1)
        self.assertIn("INC-2026-0099", edit_notifs[0].body)

    def test_multi_source_intelligence_notifications(self):
        self._login()
        # Seed 3 incidents in Zone 4 in the past week to trigger geospatial hotspot
        for i in range(3):
            inc = Incident(
                report_no=f"INC-TEST-00{i}",
                incident_date=datetime.utcnow().date() - timedelta(days=2),
                time_reported=datetime.utcnow().time(),
                hour=10,
                zone_id="Zone 4",
                location="Main St",
                category="Disturbance",
                priority="Medium",
                status="Pending"
            )
            db.session.add(inc)

        # Seed an ML Run with a predicted hotspot in Zone 3
        ml = MlRun(
            trained_at=datetime.utcnow(),
            record_count=100,
            active_occurrence_model="random_forest",
            active_type_model="gradient_boosting",
            active_hotspot_model="random_forest",
            occurrence_metrics_json="{}",
            type_metrics_json="{}",
            hotspot_metrics_json="{}",
            hotspots_json='[{"zone": "Zone 3", "meanDailyProb": 0.85}]'
        )
        db.session.add(ml)
        db.session.commit()

        # Call notifications list endpoint
        res = self.client.get("/api/notifications.php?action=list")
        self.assertEqual(res.status_code, 200)
        items = res.get_json()

        types = [item["type"] for item in items]
        self.assertIn("heatmap_hotspot", types)
        self.assertIn("predictive_risk", types)


if __name__ == "__main__":
    unittest.main()
