import unittest
from datetime import datetime, date, time
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Incident, BlotterRecord, User, Zone


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False


class TestTrendsAndElevation(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed test zones
        for i in range(1, 8):
            zid = f"Zone {i}"
            if not Zone.query.get(zid):
                z = Zone(zone_id=zid, label=f"Substation {i}", lat=14.7000 + i*0.001, lng=120.9800 + i*0.001, weight=1.0)
                db.session.add(z)

        # Seed test admin user
        self.admin = User(
            username="admin_tester",
            email="admin_trends@example.com",
            full_name="Admin Trends",
            role="Admin",
            status="Active",
            password="AdminPass123!"
        )
        db.session.add(self.admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login_as_admin(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.admin.id
            sess["username"] = "admin_tester"
            sess["role"] = "System Admin"
            sess["full_name"] = "Admin Trends"
            sess["last_activity"] = datetime.utcnow().timestamp()

    def test_trends_aggregation_and_elevation(self):
        self.login_as_admin()

        # Seed sample incidents with unique report numbers
        inc1 = Incident(
            report_no="INC-TEST-9001",
            incident_date=date(2026, 1, 15),
            time_reported=time(14, 0),
            hour=14,
            zone_id="Zone 1",
            category="Physical Assault",
            is_blotter=True,
            blotter_docket_no="BLT-TEST-9001",
            status="Under Investigation",
            archived=False
        )
        inc2 = Incident(
            report_no="INC-TEST-9002",
            incident_date=date(2026, 1, 20),
            time_reported=time(18, 30),
            hour=18,
            zone_id="Zone 2",
            category="Theft",
            is_blotter=False,
            status="Resolved",
            archived=False
        )
        db.session.add_all([inc1, inc2])

        # Seed sample blotter record
        blt1 = BlotterRecord(
            docket_no="BLT-TEST-9001",
            date_filed=date(2026, 1, 15),
            source_incident_id=inc1.id,
            complainant="Juan Dela Cruz",
            respondent="Pedro Penduko",
            nature="Physical Assault",
            status="Resolved",
            zone_id="Zone 1",
            archived=False
        )
        db.session.add(blt1)
        db.session.commit()

        # Test GET /api/analytics/trends
        res = self.client.get("/api/analytics/trends?year=2026")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertEqual(data["status"], "success")
        self.assertTrue(data["ok"])
        
        # Summary verification
        summary = data["summary"]
        self.assertGreater(summary["total_incidents"], 0)
        self.assertGreaterEqual(summary["total_blottered"], 1)
        self.assertGreater(summary["elevation_rate"], 0.0)
        self.assertGreaterEqual(summary["total_blotter_cases"], 1)
        self.assertGreaterEqual(summary["lupon_settlement_rate"], 0.0)

        # Timeline verification
        timeline = data["timeline"]
        self.assertEqual(len(timeline), 12)
        jan = timeline[0]
        self.assertEqual(jan["month_name"], "Jan")
        self.assertGreaterEqual(jan["total_incidents"], 2)

        # Categories verification
        categories = {c["category"]: c for c in data["categories"]}
        self.assertIn("Physical Assault", categories)

        # Zonal matrix verification
        zonal = {z["zone_id"]: z for z in data["zonal"]}
        self.assertEqual(len(zonal), 7)
        self.assertIn("Zone 1", zonal)
        self.assertIn("Zone 7", zonal)


if __name__ == '__main__':
    unittest.main()
