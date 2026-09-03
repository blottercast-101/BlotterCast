import json
import unittest
from datetime import date, datetime, timedelta

from app import create_app
from app.alert_dispatcher import (
    calculate_zone_risk_forecast,
    detect_weekly_category_surges,
    evaluate_trends_and_predictions,
    trigger_trend_and_prediction_check,
)
from app.config import Config
from app.extensions import db
from app.models import (
    BlotterRecord,
    CensusRecord,
    Incident,
    MlRun,
    Notification,
    Settlement,
    SystemSetting,
    User,
    Zone,
)


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-alert-secret"
    WTF_CSRF_ENABLED = False


class TestPredictionTrendAlerts(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        # Seed zones
        for i in range(1, 8):
            zid = f"Zone {i}"
            if not Zone.query.get(zid):
                db.session.add(Zone(zone_id=zid, label=zid, description=f"Barangay {zid}"))

        # Query existing or seed admin user
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(
                username="admin",
                email="admin@test.gov",
                full_name="Admin Officer",
                role="System Admin",
                status="Active",
                password="testpassword"
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

    def test_01_predictive_model_shift_alert(self):
        """Verify predictive model shift from Low baseline to High triggers prediction_alert"""
        # 1. Establish baseline where Zone 3 is Low
        baseline = {
            f"Zone {i}": {"level": "Low", "prob": 0.05} for i in range(1, 8)
        }
        db.session.add(SystemSetting(
            setting_key="purok_risk_levels",
            setting_value=json.dumps(baseline)
        ))
        db.session.commit()

        # 2. Seed incidents in Zone 3 to push it into High risk
        now = datetime.utcnow().date()
        for i in range(5):
            inc = Incident(
                report_no=f"INC-Z3-00{i}",
                incident_date=now - timedelta(days=2),
                time_reported=datetime.utcnow().time(),
                hour=14,
                zone_id="Zone 3",
                location="Purok 3",
                category="Physical Assault",
                priority="High",
                status="Under Investigation"
            )
            db.session.add(inc)
        db.session.commit()

        # 3. Evaluate trends and predictions
        result = evaluate_trends_and_predictions()
        self.assertTrue(result["dispatched_count"] >= 1)

        # 4. Verify notification in database
        notif = Notification.query.filter_by(type="prediction_alert").first()
        self.assertIsNotNone(notif)
        self.assertIn("Zone 3", notif.title)
        self.assertEqual(notif.severity, "critical")
        self.assertEqual(notif.link, "predictions.html")

        # 5. Verify updated baseline persisted in SystemSetting
        updated_setting = SystemSetting.query.get("purok_risk_levels")
        self.assertIsNotNone(updated_setting)
        updated_data = json.loads(updated_setting.setting_value)
        self.assertIn("Zone 3", updated_data)
        self.assertEqual(updated_data["Zone 3"]["level"], "High")

    def test_02_trend_category_surge_alert(self):
        """Verify >20% increase in category (e.g. Theft) triggers trend_alert"""
        now = datetime.utcnow().date()
        # Prior week (days 8-14 ago): 1 Theft incident
        db.session.add(Incident(
            report_no="INC-THEFT-OLD-1",
            incident_date=now - timedelta(days=10),
            time_reported=datetime.utcnow().time(),
            hour=11,
            zone_id="Zone 1",
            location="Market St",
            category="Theft",
            priority="Medium",
            status="Under Investigation"
        ))

        # Current week (days 1-7 ago): 4 Theft incidents (+300% surge)
        for i in range(4):
            db.session.add(Incident(
                report_no=f"INC-THEFT-NEW-{i}",
                incident_date=now - timedelta(days=2),
                time_reported=datetime.utcnow().time(),
                hour=15,
                zone_id="Zone 1",
                location="Market St",
                category="Theft",
                priority="High",
                status="Under Investigation"
            ))
        db.session.commit()

        # Run detection engine
        surges = detect_weekly_category_surges()
        self.assertTrue(any(s["category"] == "Theft" for s in surges))
        theft_surge = next(s for s in surges if s["category"] == "Theft")
        self.assertGreaterEqual(theft_surge["percentage"], 20)

        evaluate_trends_and_predictions()

        # Verify trend alert notification
        notif = Notification.query.filter_by(type="trend_alert").first()
        self.assertIsNotNone(notif)
        self.assertIn("Theft", notif.title)
        self.assertIn("Theft incidents increased by", notif.body)
        self.assertEqual(notif.link, "trends.html")

    def test_03_mutation_hooks_auto_trigger_evaluation(self):
        """Verify creating/updating an incident automatically executes the alert engine"""
        self._login()
        now = datetime.utcnow().date()

        # Initial baseline
        baseline = {f"Zone {i}": {"level": "Low", "prob": 0.05} for i in range(1, 8)}
        db.session.add(SystemSetting(setting_key="purok_risk_levels", setting_value=json.dumps(baseline)))
        db.session.commit()

        # Pre-seed prior week to prepare surge
        db.session.add(Incident(
            report_no="INC-SURGE-BASE",
            incident_date=now - timedelta(days=9),
            time_reported=datetime.utcnow().time(),
            hour=10,
            zone_id="Zone 2",
            location="Purok 2",
            category="Vandalism",
            priority="Low",
            status="Under Investigation"
        ))
        db.session.commit()

        # POST multiple incidents via REST API to trigger mutation hook
        for i in range(3):
            res = self.client.post("/api/records.php?type=incidents", json={
                "reportNo": f"INC-VANDAL-{i}",
                "date": (now - timedelta(days=1)).isoformat(),
                "timeReported": "12:00",
                "zone": "Zone 2",
                "location": "Purok 2",
                "category": "Vandalism",
                "priority": "Medium",
                "status": "Under Investigation"
            })
            self.assertEqual(res.status_code, 201)

        # Check that Notification Center generated the alert automatically
        notifs = Notification.query.filter_by(type="trend_alert").all()
        self.assertTrue(len(notifs) >= 1)
        self.assertTrue(any("Vandalism" in n.title for n in notifs))

    def test_04_cooldown_prevents_duplicate_spam(self):
        """Verify that duplicate notifications are not spammed within the cooldown period"""
        now = datetime.utcnow().date()
        for i in range(5):
            db.session.add(Incident(
                report_no=f"INC-Z5-{i}",
                incident_date=now - timedelta(days=1),
                time_reported=datetime.utcnow().time(),
                hour=14,
                zone_id="Zone 5",
                location="Main Ave",
                category="Physical Assault",
                priority="High",
                status="Under Investigation"
            ))
        db.session.commit()

        # First evaluation
        res1 = evaluate_trends_and_predictions()
        initial_count = Notification.query.filter(
            Notification.type.in_(["prediction_alert", "trend_alert"])
        ).count()
        self.assertGreater(initial_count, 0)

        # Second evaluation immediately after
        res2 = evaluate_trends_and_predictions()
        after_count = Notification.query.filter(
            Notification.type.in_(["prediction_alert", "trend_alert"])
        ).count()

        # Count must remain unchanged because cooldown and baseline prevent duplicate spam
        self.assertEqual(initial_count, after_count)

    def test_05_notification_api_endpoint_lists_prediction_and_trend_alerts(self):
        """Verify notifications list API returns prediction_alert and trend_alert with proper flags"""
        self._login()
        now = datetime.utcnow().date()

        # Create one prediction alert and one trend alert directly
        db.session.add(Notification(
            type="prediction_alert",
            title="Elevated Risk Forecast Alert: Zone 4",
            body="Predictive models project a significant increase in incidents for Zone 4 over the next 14 days.",
            severity="critical",
            link="predictions.html"
        ))
        db.session.add(Notification(
            type="trend_alert",
            title="Unusual Trend Spike Detected: Theft",
            body="Theft incidents increased by 50% this week.",
            severity="warning",
            link="trends.html"
        ))
        db.session.commit()

        res = self.client.get("/api/notifications.php?action=list")
        self.assertEqual(res.status_code, 200)
        items = res.get_json()
        types = [item["type"] for item in items]
        self.assertIn("prediction_alert", types)
        self.assertIn("trend_alert", types)

        pred_item = next(item for item in items if item["type"] == "prediction_alert")
        self.assertEqual(pred_item["link"], "predictions.html")
        self.assertEqual(pred_item["severity"], "critical")


if __name__ == "__main__":
    unittest.main()
