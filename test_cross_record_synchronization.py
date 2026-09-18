import os
import unittest
from datetime import date, time
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import CensusRecord, Incident, BlotterRecord, Settlement, Zone, User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-sync"
    WTF_CSRF_ENABLED = False


class TestCrossRecordSynchronization(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        for i in range(1, 5):
            zid = f"Zone {i}"
            z = Zone.query.get(zid)
            if not z:
                db.session.add(Zone(zone_id=zid, label=f"Substation {i}", lat=14.88, lng=120.97, weight=1.0))

        admin = User.query.filter_by(username="admin_test").first()
        if not admin:
            admin = User(username="admin_test", full_name="Admin Test", role="System Admin", is_active=True, status="Active", password="test-password")
            db.session.add(admin)
        db.session.commit()

        self.login_as(role="System Admin", username="admin_test")

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login_as(self, role="System Admin", username="admin_test"):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["role"] = role
            sess["username"] = username
            sess["full_name"] = "Admin Test"
            from datetime import datetime
            sess["last_activity"] = datetime.utcnow().timestamp()

    def test_01_blotter_edit_cascades_to_incident_and_settlement(self):
        """Editing Blotter shared details cascades to linked Incident and Settlement records."""
        complainant = CensusRecord(
            resident_no="RES-001", last_name="Santos", first_name="Maria",
            address="123 Apple St.", zone_id="Zone 1", sex="Female", status="Active",
            date_of_birth=date(1990, 1, 1)
        )
        respondent = CensusRecord(
            resident_no="RES-002", last_name="Reyes", first_name="Pedro",
            address="456 Orange St.", zone_id="Zone 2", sex="Male", status="Active",
            date_of_birth=date(1985, 5, 10)
        )
        db.session.add_all([complainant, respondent])
        db.session.commit()

        # 1. Create Incident
        res_inc = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-SYNC1",
            "date": "2026-04-01",
            "timeReported": "09:00",
            "reporter": "Maria Santos",
            "reporterResidentId": complainant.id,
            "complainant": "Maria Santos",
            "complainantResidentId": complainant.id,
            "category": "Physical Assault",
            "location": "Zone 1 Plaza",
            "zone": "Zone 1",
            "officer": "Officer Ramos"
        })
        self.assertEqual(res_inc.status_code, 201)
        inc_id = res_inc.get_json()["id"]

        # 2. Elevate Incident to Blotter (auto-creates Settlement)
        res_elev = self.client.post(f"/api/incidents/{inc_id}/elevate", json={
            "respondent": "Pedro Reyes",
            "respondentId": respondent.id,
            "type": "CRIM",
            "nature": "Physical Assault",
            "docketNo": "BLT-2026-SYNC1"
        })
        self.assertEqual(res_elev.status_code, 201)
        blt_id = res_elev.get_json()["id"]

        stl = Settlement.query.filter_by(blotter_id=blt_id).first()
        self.assertIsNotNone(stl)
        self.assertIn("Maria Santos", stl.case_title)
        self.assertIn("Pedro Reyes", stl.case_title)

        # 3. Edit Blotter record: Update complainant, respondent, date_filed, nature, zone
        res_blt_edit = self.client.put(f"/api/records.php?type=blotter&id={blt_id}", json={
            "complainant": "Maria Santos-Cruz",
            "complainantId": complainant.id,
            "respondent": "Pedro Reyes Jr.",
            "respondentId": respondent.id,
            "dateFiled": "2026-04-05",
            "nature": "Aggravated Physical Assault",
            "type": "CRIM",
            "zone": "Zone 2"
        })
        self.assertEqual(res_blt_edit.status_code, 200)

        # Verify linked Incident was cascaded
        inc = Incident.query.get(inc_id)
        self.assertEqual(inc.complainant, "Maria Santos-Cruz")
        self.assertEqual(str(inc.incident_date), "2026-04-05")
        self.assertEqual(inc.zone_id, "Zone 2")
        self.assertEqual(inc.description, "Aggravated Physical Assault")
        self.assertIn("Pedro Reyes Jr.", inc.involved_parties)

        # Verify linked Settlement was cascaded
        stl_refreshed = Settlement.query.get(stl.id)
        self.assertEqual(stl_refreshed.case_title, "Maria Santos-Cruz vs. Pedro Reyes Jr.")
        self.assertEqual(stl_refreshed.complaint_title, "Aggravated Physical Assault")
        self.assertEqual(str(stl_refreshed.date_filed), "2026-04-05")
        self.assertEqual(stl_refreshed.nature, "Criminal")

    def test_02_incident_edit_cascades_to_blotter_and_settlement(self):
        """Editing an elevated Incident cascades shared details to linked Blotter and Settlement."""
        complainant = CensusRecord(
            resident_no="RES-003", last_name="Dela Cruz", first_name="Juan",
            address="789 Pine Rd.", zone_id="Zone 3", sex="Male", status="Active",
            date_of_birth=date(1992, 3, 15)
        )
        db.session.add(complainant)
        db.session.commit()

        # 1. Create Incident
        res_inc = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-SYNC2",
            "date": "2026-04-10",
            "timeReported": "14:00",
            "reporter": "Juan Dela Cruz",
            "reporterResidentId": complainant.id,
            "complainant": "Juan Dela Cruz",
            "complainantResidentId": complainant.id,
            "category": "Property Damage",
            "location": "Zone 3 Corner",
            "zone": "Zone 3",
            "officer": "Officer Santos"
        })
        self.assertEqual(res_inc.status_code, 201)
        inc_id = res_inc.get_json()["id"]

        # 2. Elevate Incident
        res_elev = self.client.post(f"/api/incidents/{inc_id}/elevate", json={
            "respondent": "Mario Bautista",
            "type": "CIVIL",
            "nature": "Property Damage",
            "docketNo": "BLT-2026-SYNC2"
        })
        self.assertEqual(res_elev.status_code, 201)
        blt_id = res_elev.get_json()["id"]

        # 3. Edit Incident: update complainant, date, time, zone, officer
        res_inc_edit = self.client.put(f"/api/records.php?type=incidents&id={inc_id}", json={
            "complainant": "Juan Dela Cruz Sr.",
            "complainantResidentId": complainant.id,
            "reporter": "Juan Dela Cruz Sr.",
            "reporterResidentId": complainant.id,
            "date": "2026-04-12",
            "timeReported": "16:30",
            "zone": "Zone 4",
            "location": "Zone 4 Highway",
            "category": "Property Damage",
            "description": "Repaired vehicle boundary damage",
            "officer": "Chief Inspector Ramos",
            "involvedParties": "Juan Dela Cruz Sr. vs Mario Bautista"
        })
        self.assertEqual(res_inc_edit.status_code, 200)

        # Verify linked Blotter was cascaded
        blt = BlotterRecord.query.get(blt_id)
        self.assertEqual(blt.complainant, "Juan Dela Cruz Sr.")
        self.assertEqual(str(blt.date_filed), "2026-04-12")
        self.assertEqual(str(blt.incident_time), "16:30:00")
        self.assertEqual(blt.zone_id, "Zone 4")

        # Verify linked Settlement was cascaded
        stl = Settlement.query.filter_by(blotter_id=blt_id).first()
        self.assertIsNotNone(stl)
        self.assertEqual(stl.case_title, "Juan Dela Cruz Sr. vs. Mario Bautista")
        self.assertEqual(str(stl.date_filed), "2026-04-12")
        self.assertEqual(stl.officer, "Chief Inspector Ramos")

    def test_03_settlement_edit_cascades_to_blotter_and_incident(self):
        """Editing Settlement shared details cascades to linked Blotter and Incident records."""
        complainant = CensusRecord(
            resident_no="RES-004", last_name="Lim", first_name="Ana",
            address="321 Elm St.", zone_id="Zone 1", sex="Female", status="Active",
            date_of_birth=date(1995, 7, 20)
        )
        db.session.add(complainant)
        db.session.commit()

        # 1. Create Incident
        res_inc = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-SYNC3",
            "date": "2026-05-01",
            "timeReported": "10:00",
            "reporter": "Ana Lim",
            "reporterResidentId": complainant.id,
            "complainant": "Ana Lim",
            "complainantResidentId": complainant.id,
            "category": "Boundary Dispute",
            "location": "Zone 1 Alley",
            "zone": "Zone 1",
            "officer": "Officer Dizon"
        })
        inc_id = res_inc.get_json()["id"]

        # 2. Elevate Incident
        res_elev = self.client.post(f"/api/incidents/{inc_id}/elevate", json={
            "respondent": "Carlos Mendoza",
            "type": "CIVIL",
            "nature": "Boundary Dispute",
            "docketNo": "BLT-2026-SYNC3"
        })
        blt_id = res_elev.get_json()["id"]
        stl = Settlement.query.filter_by(blotter_id=blt_id).first()

        # 3. Edit Settlement shared fields (caseTitle, complaintTitle, dateFiled, officer, nature)
        res_stl_edit = self.client.put(f"/api/records.php?type=settlements&id={stl.id}", json={
            "caseTitle": "Ana Lim-Tan vs. Carlos Mendoza Jr.",
            "complaintTitle": "Encroachment and Boundary Dispute",
            "dateFiled": "2026-05-04",
            "nature": "Civil",
            "officer": "Barangay Mediator Cruz",
            "actionTaken": "Mediation Hearing",
            "dateSettlement": "2026-05-05",
            "mainPoint": "Agreed on surveyor demarcation"
        })
        self.assertEqual(res_stl_edit.status_code, 200)

        # Verify linked Blotter updated
        blt = BlotterRecord.query.get(blt_id)
        self.assertEqual(blt.complainant, "Ana Lim-Tan")
        self.assertEqual(blt.respondent, "Carlos Mendoza Jr.")
        self.assertEqual(blt.nature, "Encroachment and Boundary Dispute")
        self.assertEqual(str(blt.date_filed), "2026-05-04")
        self.assertEqual(blt.case_type, "CIVIL")

        # Verify linked Incident updated
        inc = Incident.query.get(inc_id)
        self.assertEqual(inc.complainant, "Ana Lim-Tan")
        self.assertEqual(inc.involved_parties, "Ana Lim-Tan vs Carlos Mendoza Jr.")
        self.assertEqual(inc.description, "Encroachment and Boundary Dispute")
        self.assertEqual(str(inc.incident_date), "2026-05-04")
        self.assertEqual(inc.officer, "Barangay Mediator Cruz")

    def test_04_unlinked_records_are_isolated_and_unaffected(self):
        """Updates to one record do not affect unlinked records."""
        person_a = CensusRecord(
            resident_no="RES-005", last_name="Santos", first_name="Alan",
            address="111 Pine St.", zone_id="Zone 1", sex="Male", status="Active",
            date_of_birth=date(1991, 2, 2)
        )
        person_b = CensusRecord(
            resident_no="RES-006", last_name="Cruz", first_name="Ben",
            address="222 Oak St.", zone_id="Zone 2", sex="Male", status="Active",
            date_of_birth=date(1993, 4, 4)
        )
        db.session.add_all([person_a, person_b])
        db.session.commit()

        # Record A (linked)
        res_a = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-ISOL-A",
            "date": "2026-06-01",
            "timeReported": "08:00",
            "reporter": "Alan Santos",
            "reporterResidentId": person_a.id,
            "complainant": "Alan Santos",
            "complainantResidentId": person_a.id,
            "category": "Noise Complaint",
            "location": "Zone 1",
            "zone": "Zone 1"
        })
        inc_a_id = res_a.get_json()["id"]

        # Record B (unlinked)
        res_b = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-ISOL-B",
            "date": "2026-06-01",
            "timeReported": "08:30",
            "reporter": "Ben Cruz",
            "reporterResidentId": person_b.id,
            "complainant": "Ben Cruz",
            "complainantResidentId": person_b.id,
            "category": "Lost Item",
            "location": "Zone 2",
            "zone": "Zone 2"
        })
        inc_b_id = res_b.get_json()["id"]

        # Elevate A only
        res_elev = self.client.post(f"/api/incidents/{inc_a_id}/elevate", json={
            "respondent": "Respondent A",
            "type": "CIVIL",
            "nature": "Noise Complaint",
            "docketNo": "BLT-2026-ISOL-A"
        })
        blt_a_id = res_elev.get_json()["id"]

        # Edit Blotter A
        self.client.put(f"/api/records.php?type=blotter&id={blt_a_id}", json={
            "complainant": "Alan Santos Modified",
            "complainantId": person_a.id,
            "respondent": "Respondent A Modified",
            "dateFiled": "2026-06-05",
            "nature": "Severe Noise",
            "zone": "Zone 3"
        })

        # Incident B must remain completely unchanged
        inc_b = Incident.query.get(inc_b_id)
        self.assertEqual(inc_b.complainant, "Ben Cruz")
        self.assertEqual(inc_b.category, "Lost Item")
        self.assertEqual(str(inc_b.incident_date), "2026-06-01")
        self.assertEqual(inc_b.zone_id, "Zone 2")


if __name__ == "__main__":
    unittest.main()
