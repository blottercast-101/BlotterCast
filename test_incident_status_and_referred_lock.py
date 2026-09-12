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


class TestIncidentStatusAndReferredLock(unittest.TestCase):
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
                z = Zone(zone_id=zid, label=f"Substation {i}", lat=14.7000 + i * 0.001, lng=120.9800 + i * 0.001, weight=1.0)
                db.session.add(z)

        # Seed test admin user
        self.admin = User(
            username="admin_tester",
            password="AdminPass123!",
            full_name="Admin Tester",
            role="System Admin",
            status="Active"
        )
        db.session.add(self.admin)

        # Seed Census resident
        self.resident = CensusRecord(
            first_name="Juan",
            last_name="Dela Cruz",
            middle_name="Santos",
            date_of_birth=date(1990, 5, 20),
            address="123 Mabini St",
            zone_id="Zone 1",
            status="ACTIVE"
        )
        db.session.add(self.resident)
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
            sess["full_name"] = "Admin Tester"
            sess["last_activity"] = datetime.utcnow().timestamp()

    def test_resolved_status_creation_and_update(self):
        self.login_as_admin()

        # 1. Create an incident with "Resolved" status
        payload = {
            "date": "2026-03-01",
            "timeReported": "10:30",
            "zone": "Zone 1",
            "location": "Near Barangay Hall",
            "category": "Domestic Dispute",
            "priority": "Medium",
            "description": "Settled peacefully by barangay mediators",
            "reporter": "Juan Dela Cruz",
            "reporterResidentId": self.resident.id,
            "status": "Resolved"
        }
        res = self.client.post("/api/records.php?type=incidents", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        inc_id = data["id"]

        inc = Incident.query.get(inc_id)
        self.assertEqual(inc.status, "Resolved")

        # 2. Update an Under Investigation incident to "Resolved"
        payload2 = {
            "date": "2026-03-02",
            "timeReported": "11:00",
            "zone": "Zone 1",
            "location": "Near Health Center",
            "category": "Public Disturbance",
            "priority": "Low",
            "description": "Loud music complaint",
            "reporter": "Juan Dela Cruz",
            "reporterResidentId": self.resident.id,
            "status": "Under Investigation"
        }
        res2 = self.client.post("/api/records.php?type=incidents", json=payload2)
        self.assertEqual(res2.status_code, 201)
        inc_id2 = res2.get_json()["id"]

        update_payload = {
            **payload2,
            "status": "Resolved",
            "description": "Resolved after neighbor turned down volume"
        }
        res_update = self.client.put(f"/api/records.php?type=incidents&id={inc_id2}", json=update_payload)
        self.assertEqual(res_update.status_code, 200)

        inc2 = Incident.query.get(inc_id2)
        self.assertEqual(inc2.status, "Resolved")

    def test_referred_incident_immutability(self):
        self.login_as_admin()

        # 1. Create a Referred incident
        payload = {
            "date": "2026-03-03",
            "timeReported": "14:00",
            "zone": "Zone 2",
            "location": "Pandi Village",
            "category": "Physical Assault",
            "priority": "High",
            "description": "Severe injury, referred directly to PNP",
            "reporter": "Juan Dela Cruz",
            "reporterResidentId": self.resident.id,
            "status": "Referred"
        }
        res = self.client.post("/api/records.php?type=incidents", json=payload)
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()["id"]

        inc = Incident.query.get(inc_id)
        self.assertEqual(inc.status, "Referred")

        # 2. Attempt to update Referred incident via PUT -> Must be rejected with HTTP 403
        update_payload = {
            **payload,
            "description": "Attempting unauthorized modification"
        }
        res_put = self.client.put(f"/api/records.php?type=incidents&id={inc_id}", json=update_payload)
        self.assertEqual(res_put.status_code, 403)
        self.assertIn("Referred incidents are final and cannot be modified", res_put.get_json()["error"])

    def test_referred_incident_cannot_be_elevated(self):
        self.login_as_admin()

        # 1. Create a Referred incident
        payload = {
            "date": "2026-03-04",
            "timeReported": "15:00",
            "zone": "Zone 3",
            "location": "Main Road",
            "category": "Drug-Related Activity",
            "priority": "High",
            "description": "Referred to PDEA",
            "reporter": "Juan Dela Cruz",
            "reporterResidentId": self.resident.id,
            "status": "Referred"
        }
        res = self.client.post("/api/records.php?type=incidents", json=payload)
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()["id"]

        # 2. Attempt elevation via dedicated /elevate endpoint -> Must be rejected with HTTP 422
        elevate_payload = {
            "complainant": "Juan Dela Cruz",
            "complainantId": self.resident.id,
            "respondent": "Pedro Penduko",
            "type": "CRIM"
        }
        res_elevate = self.client.post(f"/api/incidents/{inc_id}/elevate", json=elevate_payload)
        self.assertEqual(res_elevate.status_code, 422)
        self.assertIn("cannot be elevated to a barangay blotter record", res_elevate.get_json()["error"])

        # 3. Attempt elevation via POST /api/records.php?type=blotter -> Must be rejected with HTTP 422
        blt_payload = {
            "sourceIncidentId": inc_id,
            "complainant": "Juan Dela Cruz",
            "complainantId": self.resident.id,
            "respondent": "Pedro Penduko",
            "type": "CRIM",
            "nature": "Drug-Related Activity"
        }
        res_blt = self.client.post("/api/records.php?type=blotter", json=blt_payload)
        self.assertEqual(res_blt.status_code, 422)
        self.assertIn("cannot be elevated to a barangay blotter record", res_blt.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
