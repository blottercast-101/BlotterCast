import unittest
import json
from datetime import datetime, date, time
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Incident, BlotterRecord, User, Zone, CensusRecord


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
            password="AdminPass123!",
            full_name="Admin Trends",
            role="System Admin",
            status="Active"
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
            location="Near Barangay Hall",
            category="Physical Assault",
            priority="High",
            description="Testing physical assault",
            reporter="Juan Dela Cruz",
            officer="PO1 Santos",
            status="Elevated to Blotter",
            is_blotter=True,
            blotter_docket_no="BLT-2026-0001"
        )
        inc2 = Incident(
            report_no="INC-TEST-9002",
            incident_date=date(2026, 1, 20),
            time_reported=time(10, 0),
            hour=10,
            zone_id="Zone 2",
            location="Pandi Village",
            category="Theft",
            priority="Medium",
            description="Testing theft incident",
            reporter="Pedro Penduko",
            officer="PO2 Reyes",
            status="Under Investigation",
            is_blotter=False
        )
        inc3 = Incident(
            report_no="INC-TEST-9003",
            incident_date=date(2026, 2, 5),
            time_reported=time(16, 30),
            hour=16,
            zone_id="Zone 7",
            location="Barangka St.",
            category="Vandalism",
            priority="Low",
            description="Testing vandalism incident",
            reporter="Ana Reyes",
            officer="PO1 Cruz",
            status="Resolved",
            is_blotter=False
        )
        db.session.add_all([inc1, inc2, inc3])

        # Seed sample blotter record
        blt1 = BlotterRecord(
            docket_no="BLT-2026-0001",
            date_filed=date(2026, 1, 16),
            complainant="Juan Dela Cruz",
            respondent="Mario Lopez",
            nature="Physical Assault",
            case_type="CRIM",
            status="Settled",
            zone_id="Zone 1"
        )
        db.session.add(blt1)
        db.session.commit()

        # Query trends endpoint
        res = self.client.get('/api/trends.php')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))

        # Summary KPIs verification
        summary = data["summary"]
        self.assertGreater(summary["total_incidents"], 0)
        self.assertGreaterEqual(summary["total_blottered"], 1)
        self.assertGreater(summary["elevation_rate"], 0.0)
        self.assertGreaterEqual(summary["total_blotter_cases"], 1)

        # Timeline verification
        timeline = data["timeline"]
        self.assertEqual(len(timeline), 12)
        jan = timeline[0]
        self.assertEqual(jan["month_name"], "Jan")
        self.assertGreaterEqual(jan["total_incidents"], 1)

        # Categories verification
        categories = {c["category"]: c for c in data["categories"]}
        self.assertIn("Physical Assault", categories)

        # Zonal matrix verification
        zonal = {z["zone_id"]: z for z in data["zonal"]}
        self.assertEqual(len(zonal), 7)
        self.assertIn("Zone 1", zonal)
        self.assertIn("Zone 7", zonal)

    def test_incident_elevation_and_edit_lock(self):
        self.login_as_admin()

        # Seed a census resident
        resident = CensusRecord(
            resident_no="RES-2026-0001",
            first_name="Maria",
            last_name="Santos",
            date_of_birth=date(1990, 5, 15),
            sex="Female",
            zone_id="Zone 2",
            address="Residence 1, Zone 2",
            status="Active"
        )
        db.session.add(resident)
        db.session.commit()

        # 1. Create a fresh test incident
        inc_data = {
            "date": "2026-08-20",
            "timeReported": "14:30",
            "zone": "Zone 2",
            "location": "Residence 1",
            "category": "Theft",
            "priority": "Medium",
            "description": "Elevation and lock testing incident",
            "reporter": "Maria Santos",
            "officer": "PO1 Cruz",
            "status": "Under Investigation"
        }
        res = self.client.post('/api/records.php?type=incidents', data=json.dumps(inc_data), content_type='application/json')
        self.assertIn(res.status_code, [200, 201])
        inc_id = res.get_json()["id"]

        with self.app.app_context():
            inc = Incident.query.get(inc_id)
            self.assertFalse(inc.is_blotter)
            report_no = inc.report_no

        # 2. Elevate to Blotter by creating a BlotterRecord referencing this source_incident_id
        blotter_payload = {
            "sourceIncidentId": inc_id,
            "complainant": "Maria Santos",
            "complainantId": resident.id,
            "respondent": "Unknown Suspect",
            "dateFiled": "2026-08-20",
            "incidentTime": "14:30",
            "nature": "Theft",
            "zone": "Zone 2",
            "narrative": "Elevation and lock testing incident narrative",
            "status": "Active"
        }
        b_res = self.client.post('/api/records.php?type=blotters', data=json.dumps(blotter_payload), content_type='application/json')
        self.assertIn(b_res.status_code, [200, 201])
        docket_no = b_res.get_json()["docket_no"]

        # 3. Verify source incident was updated
        with self.app.app_context():
            inc_updated = Incident.query.get(inc_id)
            self.assertTrue(inc_updated.is_blotter)
            self.assertEqual(inc_updated.blotter_docket_no, docket_no)
            self.assertEqual(inc_updated.status, "Elevated to Blotter")

        # 4. Verify editing this elevated incident directly is blocked with 403 Forbidden
        edit_payload = {
            "description": "Attempting illegal edit on elevated incident"
        }
        put_res = self.client.put(f'/api/records.php?type=incidents&id={inc_id}', data=json.dumps(edit_payload), content_type='application/json')
        self.assertEqual(put_res.status_code, 403)
        self.assertIn("official Blotter case", put_res.get_json()["error"])

        # 5. SSOT Synchronization: Update Blotter record and verify changes reflect on linked Incident
        blotter_id = b_res.get_json()["id"]
        update_blotter_payload = {
            "dateFiled": "2026-08-21",
            "complainant": "Maria Santos",
            "complainantId": resident.id,
            "respondent": "Identified Suspect",
            "nature": "Aggravated Theft Incident",
            "type": "Theft",
            "zone": "Zone 2",
            "status": "Under Investigation"
        }
        blotter_put_res = self.client.put(f'/api/records.php?type=blotters&id={blotter_id}', data=json.dumps(update_blotter_payload), content_type='application/json')
        self.assertEqual(blotter_put_res.status_code, 200)

        with self.app.app_context():
            inc_synced = Incident.query.get(inc_id)
            self.assertEqual(str(inc_synced.incident_date), "2026-08-21")
            self.assertEqual(inc_synced.description, "Aggravated Theft Incident")
            self.assertEqual(inc_synced.category, "Theft")
            self.assertEqual(inc_synced.zone_id, "Zone 2")


if __name__ == '__main__':
    unittest.main()

