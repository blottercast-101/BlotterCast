import unittest
from datetime import datetime, date, time
from app import create_app
from app.extensions import db
from app.models import Incident, BlotterRecord, CensusRecord, Zone, User
from test_mfa_helper import login as mfa_login


class IncidentReporterCensusTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            # Ensure zone
            if not Zone.query.get("Zone 1"):
                db.session.add(Zone(zone_id="Zone 1", label="Zone 1 - Pandi Residences 3"))
                db.session.commit()

            # Create test Census Resident
            res = CensusRecord.query.filter_by(resident_no="RES-TEST-99").first()
            if not res:
                res = CensusRecord(
                    resident_no="RES-TEST-99",
                    last_name="Dela Cruz",
                    first_name="Juan",
                    middle_name="Santos",
                    zone_id="Zone 1",
                    address="123 Mabini St., Zone 1",
                    status="Active"
                )
                db.session.add(res)
                db.session.commit()
            self.resident_id = res.id

    def test_create_incident_with_census_resident(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            # 1. Create incident with Census Resident
            res = self.client.post("/api/records.php?type=incidents", json={
                "date": "2026-08-25",
                "timeReported": "14:30",
                "location": "Residence 3",
                "zone": "Zone 1",
                "category": "Theft",
                "priority": "Medium",
                "status": "Under Investigation",
                "reporter": "Dela Cruz, Juan Santos",
                "reporterResidentId": self.resident_id,
                "isNonResident": False,
            })
            self.assertEqual(res.status_code, 201)
            inc_id = res.get_json()["id"]

            inc = Incident.query.get(inc_id)
            self.assertIsNotNone(inc)
            self.assertFalse(inc.is_non_resident)
            self.assertEqual(inc.reporter_resident_id, self.resident_id)
            self.assertIn("123 Mabini St.", inc.reporter_address)

            # 2. Verify GET returns reporter resident fields
            get_res = self.client.get("/api/records.php?type=incidents")
            self.assertEqual(get_res.status_code, 200)
            items = get_res.get_json()
            matching = next((x for x in items if x["id"] == inc_id), None)
            self.assertIsNotNone(matching)
            self.assertEqual(matching["reporter_resident_id"], self.resident_id)
            self.assertFalse(matching["is_non_resident"])
            self.assertIn("123 Mabini St.", matching["reporter_address"])

    def test_create_incident_with_non_resident(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            # Create incident with Non-Resident
            res = self.client.post("/api/records.php?type=incidents", json={
                "date": "2026-08-25",
                "timeReported": "16:00",
                "location": "Residence 3 Gate",
                "zone": "Zone 1",
                "category": "Physical Assault",
                "priority": "High",
                "status": "Under Investigation",
                "reporter": "Roberto Gomez",
                "reporterAddress": "Meycauayan, Bulacan (Outside Barangay)",
                "isNonResident": True,
            })
            self.assertEqual(res.status_code, 201)
            inc_id = res.get_json()["id"]

            inc = Incident.query.get(inc_id)
            self.assertIsNotNone(inc)
            self.assertTrue(inc.is_non_resident)
            self.assertIsNone(inc.reporter_resident_id)
            self.assertEqual(inc.reporter_address, "Meycauayan, Bulacan (Outside Barangay)")


if __name__ == "__main__":
    unittest.main()
