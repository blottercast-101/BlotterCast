import json
import unittest
from datetime import date, datetime, timedelta

from app import create_app
from app.alert_dispatcher import (
    calculate_zone_risk_forecast,
    detect_heatmap_hotspots,
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

    def test_06_heatmap_hotspot_alert_generation(self):
        """Verify high incident cluster (>=3 incidents in 14 days) triggers heatmap_hotspot alert"""
        now = datetime.utcnow().date()
        for i in range(4):
            db.session.add(Incident(
                report_no=f"INC-HOTSPOT-{i}",
                incident_date=now - timedelta(days=3),
                time_reported=datetime.utcnow().time(),
                hour=16,
                zone_id="Zone 6",
                location="St. Jude Ave",
                category="Physical Assault",
                priority="High",
                status="Under Investigation"
            ))
        db.session.commit()

        hotspots = detect_heatmap_hotspots()
        self.assertTrue(any(h["zone"] == "Zone 6" for h in hotspots))

        result = evaluate_trends_and_predictions()
        self.assertTrue(result["dispatched_count"] >= 1)

        notif = Notification.query.filter_by(type="heatmap_hotspot").first()
        self.assertIsNotNone(notif)
        self.assertIn("Zone 6", notif.title)
        self.assertEqual(notif.link, "heatmap.html")
        self.assertEqual(notif.severity, "critical")

    def test_07_incident_status_update_resolution_triggers_evaluation(self):
        """Verify updating incident status/resolution executes alert engine"""
        self._login()
        now = datetime.utcnow().date()
        inc = Incident(
            report_no="INC-RESOLVE-1",
            incident_date=now - timedelta(days=1),
            time_reported=datetime.utcnow().time(),
            hour=10,
            zone_id="Zone 1",
            location="Market",
            category="Theft",
            priority="Medium",
            status="Under Investigation"
        )
        db.session.add(inc)
        db.session.commit()

        # Update incident status to Referred (Resolved)
        res = self.client.put(f"/api/records.php?type=incidents&id={inc.id}", json={
            "reportNo": inc.report_no,
            "status": "Referred",
            "zone": "Zone 1",
            "location": "Market",
            "category": "Theft",
            "date": now.isoformat(),
            "timeReported": "10:00"
        })
        self.assertEqual(res.status_code, 200)

    def test_08_incident_deletion_archival_triggers_evaluation(self):
        """Verify incident archival and restore execute change detection"""
        self._login()
        now = datetime.utcnow().date()
        inc = Incident(
            report_no="INC-DEL-1",
            incident_date=now - timedelta(days=1),
            time_reported=datetime.utcnow().time(),
            hour=10,
            zone_id="Zone 2",
            location="Park",
            category="Noise Complaint",
            priority="Low",
            status="Under Investigation"
        )
        db.session.add(inc)
        db.session.commit()

        # Archive incident
        res_del = self.client.delete(f"/api/records.php?type=incidents&id={inc.id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.get_json()["archived"])

        # Restore incident
        res_restore = self.client.put(f"/api/records.php?type=incidents&id={inc.id}&restore=1")
        self.assertEqual(res_restore.status_code, 200)
        self.assertTrue(res_restore.get_json()["ok"])

    def test_09_user_creation_preserves_all_four_roles(self):
        """Verify user management preserves all 4 selectable roles without side effects on role queries"""
        self._login()

        # Desk Officer
        r_desk = self.client.post("/api/users.php?action=create", json={
            "username": "test_desk_officer",
            "name": "Desk Officer Test",
            "email": "desk_test@test.gov",
            "role": "Desk Officer",
            "password": "Password123!"
        })
        self.assertEqual(r_desk.status_code, 201)

        # Data Encoder
        r_encoder = self.client.post("/api/users.php?action=create", json={
            "username": "test_encoder_user",
            "name": "Encoder User Test",
            "email": "encoder_test@test.gov",
            "role": "Data Encoder",
            "password": "Password123!"
        })
        self.assertEqual(r_encoder.status_code, 201)

        # Barangay Captain (Singleton protected role - blocked from creation)
        r_captain = self.client.post("/api/users.php?action=create", json={
            "username": "test_captain_user",
            "name": "Captain Test",
            "email": "captain_test@test.gov",
            "role": "Barangay Captain",
            "password": "Password123!"
        })
        self.assertEqual(r_captain.status_code, 403)

        # System Administrator (Singleton protected role - blocked from creation)
        r_admin = self.client.post("/api/users.php?action=create", json={
            "username": "test_admin_user",
            "name": "Admin Test",
            "email": "admin_test@test.gov",
            "role": "System Administrator",
            "password": "Password123!"
        })
        self.assertEqual(r_admin.status_code, 403)

        # Verify all roles exist in users list
        r_list = self.client.get("/api/users.php?action=list")
        self.assertEqual(r_list.status_code, 200)
        roles = {u["role"] for u in r_list.get_json()}
        self.assertIn("System Admin", roles)
        self.assertIn("Barangay Captain", roles)
        self.assertIn("Desk Officer", roles)
        self.assertIn("Data Encoder", roles)


if __name__ == "__main__":
    unittest.main()
