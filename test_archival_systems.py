import unittest
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Incident, Settlement, CensusRecord, BlotterRecord, Zone, User
from datetime import datetime, date, time


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    WTF_CSRF_ENABLED = False


class TestArchivalSystems(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        z1 = Zone.query.get("Zone 1")
        if not z1:
            z1 = Zone(zone_id="Zone 1", label="Zone 1", lat=14.0, lng=121.0, weight=1.0)
            db.session.add(z1)
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(
                username="admin",
                email="admin@example.com",
                full_name="Admin User",
                role="Admin",
                status="Active",
                password="test-password",
            )
            db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login_as(self, role="System Admin", username="admin"):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = username
            sess["role"] = role

    def test_incident_archival_and_restore(self):
        self.login_as()
        # 1. Create incident
        res = self.client.post("/api/records.php?type=incidents", json={
            "date": "2026-08-20",
            "timeReported": "10:30:00",
            "zone": "Zone 1",
            "location": "Main St",
            "category": "Theft",
            "priority": "Medium",
            "description": "Stolen bike",
            "reporter": "Juan Cruz",
            "officer": "Officer Santos",
            "status": "Under Investigation"
        })
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()["id"]

        # 2. Check in active list
        res = self.client.get("/api/records.php?type=incidents")
        self.assertEqual(res.status_code, 200)
        records = res.get_json()
        self.assertTrue(any(r["id"] == inc_id for r in records))

        # 3. Check initial archived count
        res = self.client.get("/api/records.php?type=incidents&archived=1")
        self.assertEqual(res.status_code, 200)
        archived_before = len(res.get_json())

        # 4. Soft-delete / Archive
        res = self.client.delete(f"/api/records.php?type=incidents&id={inc_id}")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("archived"))

        # 5. Check in archived list (count increased by 1)
        res = self.client.get("/api/records.php?type=incidents&archived=1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()), archived_before + 1)

        # 6. Check active list (inc_id no longer in active)
        res = self.client.get("/api/records.php?type=incidents")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(any(r["id"] == inc_id for r in res.get_json()))

        # 7. Restore
        res = self.client.put(f"/api/records.php?type=incidents&id={inc_id}&restore=1", json={})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("ok"))

        # 8. Check active list (restored)
        res = self.client.get("/api/records.php?type=incidents")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(any(r["id"] == inc_id for r in res.get_json()))

    def test_settlement_archival_and_restore(self):
        self.login_as()
        res_c = CensusRecord(resident_no="RES-0001", last_name="Santos", first_name="Maria", sex="Female")
        res_r = CensusRecord(resident_no="RES-0002", last_name="Reyes", first_name="Pedro", sex="Male")
        db.session.add_all([res_c, res_r])
        db.session.flush()
        b = BlotterRecord(
            docket_no="BLT-2026-0001", date_filed=date(2026, 8, 1),
            complainant="Santos, Maria", complainant_id=res_c.id,
            respondent="Reyes, Pedro", respondent_id=res_r.id,
            nature="Boundary Dispute", case_type="CIVIL", status="Ongoing", zone_id="Zone 1"
        )
        db.session.add(b)
        db.session.commit()
        blotter_id = b.id

        # 1. Create settlement
        res = self.client.post("/api/records.php?type=settlements", json={
            "blotterId": blotter_id,
            "status": "Pending",
            "actionTaken": "First Mediation Hearing",
            "dateConfrontation": "2026-08-10",
        })
        self.assertEqual(res.status_code, 201)
        stl_id = res.get_json()["id"]

        # 2. Check active list
        res = self.client.get("/api/records.php?type=settlements")
        self.assertEqual(len(res.get_json()), 1)
        self.assertEqual(res.get_json()[0]["id"], stl_id)

        # 3. Archive settlement
        res = self.client.delete(f"/api/records.php?type=settlements&id={stl_id}")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("archived"))

        # 4. Check active list (empty) & archived list (1)
        res = self.client.get("/api/records.php?type=settlements")
        self.assertEqual(len(res.get_json()), 0)
        res = self.client.get("/api/records.php?type=settlements&archived=1")
        self.assertEqual(len(res.get_json()), 1)
        self.assertEqual(res.get_json()[0]["id"], stl_id)

        # 5. Restore
        res = self.client.put(f"/api/records.php?type=settlements&id={stl_id}&restore=1", json={})
        self.assertEqual(res.status_code, 200)

        # 6. Check active list (restored)
        res = self.client.get("/api/records.php?type=settlements")
        self.assertEqual(len(res.get_json()), 1)

    def test_census_archival_and_restore(self):
        self.login_as()
        # 1. Create census resident
        res = self.client.post("/api/documents.php?type=census", json={
            "lastName": "Dela Cruz",
            "firstName": "Juan",
            "middleName": "Protacio",
            "dob": "1990-05-15",
            "sex": "Male",
            "civilStatus": "Single",
            "nationality": "Filipino",
            "zone": "Zone 1",
            "address": "123 Mabini St",
            "householdNo": "HH-001",
            "contactNo": "09171234567",
            "voterStatus": "Registered Voter",
            "occupation": "Carpenter",
            "status": "Active"
        })
        self.assertEqual(res.status_code, 201)
        res_id = res.get_json()["id"]

        # 2. Check active list
        res = self.client.get("/api/documents.php?type=census")
        self.assertEqual(len(res.get_json()), 1)
        self.assertEqual(res.get_json()[0]["id"], res_id)

        # 3. Archive resident
        res = self.client.delete(f"/api/documents.php?type=census&id={res_id}")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("archived"))

        # 4. Check active list (empty) & archived list (1)
        res = self.client.get("/api/documents.php?type=census")
        self.assertEqual(len(res.get_json()), 0)
        res = self.client.get("/api/documents.php?type=census&archived=1")
        self.assertEqual(len(res.get_json()), 1)
        self.assertEqual(res.get_json()[0]["id"], res_id)

        # 5. Restore resident
        res = self.client.put(f"/api/documents.php?type=census&id={res_id}&restore=1", json={})
        self.assertEqual(res.status_code, 200)

        # 6. Check active list (restored)
        res = self.client.get("/api/documents.php?type=census")
        self.assertEqual(len(res.get_json()), 1)
        self.assertEqual(res.get_json()[0]["id"], res_id)

    def test_permanent_delete_incident(self):
        self.login_as()
        # 1. Create incident
        res = self.client.post("/api/records.php?type=incidents", json={
            "incidentDate": "2026-08-01",
            "timeReported": "14:30",
            "category": "Theft",
            "zone": "Zone 1",
            "location": "Market St",
            "description": "Stolen bicycle",
            "priority": "Medium",
            "status": "Under Investigation",
        })
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()["id"]

        # 2. Attempt permanent delete while active (MUST fail)
        res = self.client.delete(f"/api/records.php?type=incidents&id={inc_id}&permanent=1")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Only archived records", res.get_json().get("error", ""))

        # 3. Archive first
        res = self.client.delete(f"/api/records.php?type=incidents&id={inc_id}")
        self.assertEqual(res.status_code, 200)

        # 4. Now permanently delete
        res = self.client.delete(f"/api/records.php?type=incidents&id={inc_id}&permanent=1")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("deleted"))

        # 5. Verify record is completely purged from database
        self.assertIsNone(Incident.query.get(inc_id))

    def test_permanent_delete_blotter_and_cascade(self):
        self.login_as()
        res_c = CensusRecord(resident_no="RES-0101", last_name="Cruz", first_name="Ana", sex="Female")
        res_r = CensusRecord(resident_no="RES-0102", last_name="Luna", first_name="Mark", sex="Male")
        db.session.add_all([res_c, res_r])
        db.session.flush()

        b = BlotterRecord(
            docket_no="BLT-2026-0099", date_filed=date(2026, 8, 1),
            complainant="Cruz, Ana", complainant_id=res_c.id,
            respondent="Luna, Mark", respondent_id=res_r.id,
            nature="Property Damage", case_type="CRIM", status="Pending", zone_id="Zone 1"
        )
        db.session.add(b)
        db.session.commit()
        blotter_id = b.id

        # Add child settlement
        stl = Settlement(blotter_id=blotter_id, case_no="STL-2026-0099", status="Pending", nature="Criminal")
        db.session.add(stl)
        db.session.commit()
        stl_id = stl.id

        # Archive blotter
        res = self.client.delete(f"/api/records.php?type=blotter&id={blotter_id}")
        self.assertEqual(res.status_code, 200)

        # Permanently delete blotter
        res = self.client.delete(f"/api/records.php?type=blotter&id={blotter_id}&permanent=1")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("deleted"))

        # Verify blotter and child settlement are both purged
        self.assertIsNone(BlotterRecord.query.get(blotter_id))
        self.assertIsNone(Settlement.query.get(stl_id))

    def test_permanent_delete_settlement(self):
        self.login_as()
        res_c = CensusRecord(resident_no="RES-0201", last_name="Tan", first_name="Bob", sex="Male")
        res_r = CensusRecord(resident_no="RES-0202", last_name="Lee", first_name="Ann", sex="Female")
        db.session.add_all([res_c, res_r])
        db.session.flush()

        b = BlotterRecord(
            docket_no="BLT-2026-0100", date_filed=date(2026, 8, 1),
            complainant="Tan, Bob", complainant_id=res_c.id,
            respondent="Lee, Ann", respondent_id=res_r.id,
            nature="Noise Complaint", case_type="CIVIL", status="Pending", zone_id="Zone 1"
        )
        db.session.add(b)
        db.session.commit()
        blotter_id = b.id

        stl = Settlement(blotter_id=blotter_id, case_no="STL-2026-0100", status="Pending", nature="Civil")
        db.session.add(stl)
        db.session.commit()
        stl_id = stl.id

        # Archive settlement
        res = self.client.delete(f"/api/records.php?type=settlements&id={stl_id}")
        self.assertEqual(res.status_code, 200)

        # Permanently delete settlement
        res = self.client.delete(f"/api/records.php?type=settlements&id={stl_id}&permanent=1")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("deleted"))

        # Verify settlement is purged but parent blotter remains
        self.assertIsNone(Settlement.query.get(stl_id))
        self.assertIsNotNone(BlotterRecord.query.get(blotter_id))

    def test_batch_archive_and_restore_incidents(self):
        self.login_as()
        inc1 = Incident(report_no="INC-2026-B001", incident_date=date(2026, 8, 1), time_reported=time(10, 0), zone_id="Zone 1", category="Theft", archived=False)
        inc2 = Incident(report_no="INC-2026-B002", incident_date=date(2026, 8, 2), time_reported=time(11, 0), zone_id="Zone 1", category="Assault", archived=False)
        db.session.add_all([inc1, inc2])
        db.session.commit()
        ids = [inc1.id, inc2.id]

        # Batch archive
        res = self.client.post("/api/incidents/batch-archive", json={"ids": ids})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json().get("count"), 2)
        self.assertTrue(res.get_json().get("archived"))

        # Verify in DB
        self.assertTrue(Incident.query.get(inc1.id).archived)
        self.assertTrue(Incident.query.get(inc2.id).archived)

        # Batch restore
        res = self.client.post("/api/records.php?type=incidents&action=batch_restore", json={"ids": ids})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json().get("count"), 2)
        self.assertTrue(res.get_json().get("restored"))

        # Verify restored in DB
        self.assertFalse(Incident.query.get(inc1.id).archived)
        self.assertFalse(Incident.query.get(inc2.id).archived)

    def test_batch_permanent_delete_with_validation_and_cascade(self):
        self.login_as()
        res_c = CensusRecord(resident_no="RES-0301", last_name="Batch", first_name="User1", sex="Male")
        res_r = CensusRecord(resident_no="RES-0302", last_name="Batch", first_name="User2", sex="Female")
        db.session.add_all([res_c, res_r])
        db.session.flush()

        b1 = BlotterRecord(docket_no="BLT-2026-B001", date_filed=date(2026, 8, 1), complainant="Batch User1", complainant_id=res_c.id, respondent="Batch User2", respondent_id=res_r.id, nature="Dispute", archived=False)
        b2 = BlotterRecord(docket_no="BLT-2026-B002", date_filed=date(2026, 8, 2), complainant="Batch User1", complainant_id=res_c.id, respondent="Batch User2", respondent_id=res_r.id, nature="Noise", archived=False)
        db.session.add_all([b1, b2])
        db.session.commit()
        b_ids = [b1.id, b2.id]

        stl1 = Settlement(blotter_id=b1.id, case_no="STL-2026-B001", status="Pending", nature="Civil")
        db.session.add(stl1)
        db.session.commit()
        stl1_id = stl1.id

        # 1. Attempt batch permanent delete on active records (MUST FAIL)
        res = self.client.post("/api/blotter/batch-permanent-delete", json={"ids": b_ids})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Only archived records", res.get_json().get("error", ""))

        # 2. Batch archive first
        res = self.client.post("/api/blotter/batch-archive", json={"ids": b_ids})
        self.assertEqual(res.status_code, 200)

        # 3. Now batch permanent delete
        res = self.client.post("/api/blotter/batch-permanent-delete", json={"ids": b_ids})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json().get("count"), 2)
        self.assertTrue(res.get_json().get("deleted"))

        # 4. Verify blotter records and child settlement are purged
        self.assertIsNone(BlotterRecord.query.get(b1.id))
        self.assertIsNone(BlotterRecord.query.get(b2.id))
        self.assertIsNone(Settlement.query.get(stl1_id))

    def test_delete_permission_rbac_guards(self):
        inc = Incident(report_no="INC-2026-PERM1", incident_date=date(2026, 8, 1), time_reported=time(10, 0), zone_id="Zone 1", category="Theft", archived=True)
        db.session.add(inc)
        db.session.commit()
        inc_id = inc.id

        # Non-admin roles should be rejected with 403 Forbidden
        for role in ["Barangay Captain", "Desk Officer", "Data Encoder"]:
            self.login_as(role=role, username="user_" + role.lower().replace(" ", "_"))
            
            # Single permanent delete
            res = self.client.delete(f"/api/records.php?type=incidents&id={inc_id}&permanent=1")
            self.assertEqual(res.status_code, 403)
            self.assertIn("Only System Administrators are authorized", res.get_json().get("message", ""))

            # Batch permanent delete
            res = self.client.post("/api/incidents/batch-permanent-delete", json={"ids": [inc_id]})
            self.assertEqual(res.status_code, 403)
            self.assertIn("Only System Administrators are authorized", res.get_json().get("message", ""))

        # System Admin should succeed
        self.login_as(role="System Admin", username="admin")
        res = self.client.delete(f"/api/records.php?type=incidents&id={inc_id}&permanent=1")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.get_json().get("deleted"))
        self.assertIsNone(Incident.query.get(inc_id))


if __name__ == "__main__":
    unittest.main()
