import os
import unittest
from datetime import date
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import CensusRecord, Incident, BlotterRecord, Zone, User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret-elevate"
    WTF_CSRF_ENABLED = False


class TestElevateVictimAddressMapping(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        z1 = Zone.query.get("Zone 1")
        if not z1:
            db.session.add(Zone(zone_id="Zone 1", label="Zone 1", lat=14.88, lng=120.97, weight=1.0))
        z2 = Zone.query.get("Zone 2")
        if not z2:
            db.session.add(Zone(zone_id="Zone 2", label="Zone 2", lat=14.88, lng=120.96, weight=1.0))
        z3 = Zone.query.get("Zone 3")
        if not z3:
            db.session.add(Zone(zone_id="Zone 3", label="Zone 3", lat=14.87, lng=120.97, weight=1.0))
        z4 = Zone.query.get("Zone 4")
        if not z4:
            db.session.add(Zone(zone_id="Zone 4", label="Zone 4", lat=14.88, lng=120.96, weight=1.0))

        admin = User.query.filter_by(username="admin_test").first()
        if not admin:
            admin = User(username="admin_test", full_name="Admin Test", role="System Admin", is_active=True, status="Active", password="test-password")
            db.session.add(admin)
        db.session.commit()

        self.login_as(role="System Admin", username="admin_test")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.incident_html_path = os.path.join(self.base_dir, "frontend", "incident.html")
        with open(self.incident_html_path, "r", encoding="utf-8") as f:
            self.incident_html = f.read()

        self.blotter_html_path = os.path.join(self.base_dir, "frontend", "blotter.html")
        with open(self.blotter_html_path, "r", encoding="utf-8") as f:
            self.blotter_html = f.read()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def login_as(self, role="System Admin", username="admin_test"):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = username
            sess["role"] = role

    def test_01_elevate_vehicular_accident_uses_victim_address_not_reporter_address(self):
        """Verify elevating a vehicular accident maps the victim's address and NOT the eyewitness reporter's address."""
        tanod = CensusRecord(
            resident_no="RES-TND-99", last_name="Santos", first_name="Juan",
            address="123 Tanod Outpost St.", zone_id="Zone 1", sex="Male", status="Active",
            date_of_birth=date(1980, 1, 1)
        )
        victim = CensusRecord(
            resident_no="RES-VIC-99", last_name="Dela Cruz", first_name="Maria",
            address="456 Victim Residence Ave.", zone_id="Zone 2", sex="Female", status="Active",
            date_of_birth=date(1995, 5, 10)
        )
        respondent = CensusRecord(
            resident_no="RES-RSP-99", last_name="Reyes", first_name="Pedro",
            address="789 Driver Road", zone_id="Zone 3", sex="Male", status="Active",
            date_of_birth=date(1990, 8, 20)
        )
        db.session.add_all([tanod, victim, respondent])
        db.session.commit()

        # File Vehicular Accident with Tanod as Eyewitness Reporter and Maria as Victim
        res = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-TEST-VEH",
            "date": "2026-09-18",
            "timeReported": "10:30",
            "reporter": "Juan Santos",
            "reporterResidentId": tanod.id,
            "reporterAddress": tanod.address,
            "complainant": "Maria Dela Cruz",
            "complainantResidentId": victim.id,
            "involvedParties": "Maria Dela Cruz (Sedan ABC-123) vs Pedro Reyes (Truck XYZ-789)",
            "category": "Vehicular Accident",
            "location": "Zone 1 Main Rd",
            "zone": "Zone 1"
        })
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()["id"]

        # Elevate to blotter
        res_elev = self.client.post(f"/api/incidents/{inc_id}/elevate", json={
            "respondent": "Pedro Reyes",
            "respondentId": respondent.id,
            "nature": "Vehicular Accident"
        })
        self.assertEqual(res_elev.status_code, 201)
        blt_id = res_elev.get_json()["id"]

        blt = BlotterRecord.query.get(blt_id)
        self.assertIsNotNone(blt)
        self.assertEqual(blt.complainant, "Maria Dela Cruz")
        self.assertEqual(blt.complainant_id, victim.id)
        # Verify address is the victim's address and NOT the eyewitness reporter's address
        self.assertEqual(blt.complainant_addr, "456 Victim Residence Ave.")
        self.assertNotEqual(blt.complainant_addr, tanod.address)

    def test_02_elevate_vehicular_accident_no_victim_address_does_not_override_with_reporter_address(self):
        """Verify that when no victim address is available, it is not overridden with the reporter's address."""
        tanod = CensusRecord(
            resident_no="RES-TND-98", last_name="Santos", first_name="Juan",
            address="123 Tanod Outpost St.", zone_id="Zone 1", sex="Male", status="Active",
            date_of_birth=date(1980, 1, 1)
        )
        respondent = CensusRecord(
            resident_no="RES-RSP-98", last_name="Reyes", first_name="Pedro",
            address="789 Driver Road", zone_id="Zone 3", sex="Male", status="Active",
            date_of_birth=date(1990, 8, 20)
        )
        db.session.add_all([tanod, respondent])
        db.session.commit()

        # Incidents with involved parties text but no resident ID for victim
        res = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-TEST-VEH2",
            "date": "2026-09-18",
            "timeReported": "11:00",
            "reporter": "Juan Santos",
            "reporterResidentId": tanod.id,
            "reporterAddress": tanod.address,
            "involvedParties": "Unknown Motorist vs Pedro Reyes",
            "category": "Vehicular Accident",
            "location": "Zone 1 Intersection",
            "zone": "Zone 1"
        })
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()["id"]

        res_elev = self.client.post(f"/api/incidents/{inc_id}/elevate", json={
            "complainant": "Unknown Motorist",
            "respondent": "Pedro Reyes",
            "respondentId": respondent.id,
            "nature": "Vehicular Accident"
        })
        self.assertEqual(res_elev.status_code, 201)
        blt_id = res_elev.get_json()["id"]

        blt = BlotterRecord.query.get(blt_id)
        self.assertIsNotNone(blt)
        self.assertEqual(blt.complainant, "Unknown Motorist")
        # Must not override with the reporter's address
        self.assertNotEqual(blt.complainant_addr, tanod.address)
        self.assertEqual(blt.complainant_addr, "")

    def test_03_elevate_vehicular_accident_reporter_is_victim_uses_reporter_address(self):
        """Verify that when the reporter is themselves the declared victim, reporter address is used."""
        driver_victim = CensusRecord(
            resident_no="RES-DRV-97", last_name="Torres", first_name="Eduardo",
            address="777 Driver Residence Rd.", zone_id="Zone 4", sex="Male", status="Active",
            date_of_birth=date(1992, 3, 15)
        )
        respondent = CensusRecord(
            resident_no="RES-RSP-97", last_name="Reyes", first_name="Pedro",
            address="789 Driver Road", zone_id="Zone 3", sex="Male", status="Active",
            date_of_birth=date(1990, 8, 20)
        )
        db.session.add_all([driver_victim, respondent])
        db.session.commit()

        # Reporter is the victim Eduardo Torres
        res = self.client.post("/api/records.php?type=incidents", json={
            "reportNo": "INC-2026-TEST-VEH3",
            "date": "2026-09-18",
            "timeReported": "12:00",
            "reporter": "Eduardo Torres",
            "reporterResidentId": driver_victim.id,
            "reporterAddress": driver_victim.address,
            "complainant": "Eduardo Torres",
            "complainantResidentId": driver_victim.id,
            "involvedParties": "Eduardo Torres vs Pedro Reyes",
            "category": "Vehicular Accident",
            "location": "Zone 4 Highway",
            "zone": "Zone 4"
        })
        self.assertEqual(res.status_code, 201)
        inc_id = res.get_json()["id"]

        res_elev = self.client.post(f"/api/incidents/{inc_id}/elevate", json={
            "respondent": "Pedro Reyes",
            "respondentId": respondent.id,
            "nature": "Vehicular Accident"
        })
        self.assertEqual(res_elev.status_code, 201)
        blt_id = res_elev.get_json()["id"]

        blt = BlotterRecord.query.get(blt_id)
        self.assertIsNotNone(blt)
        self.assertEqual(blt.complainant, "Eduardo Torres")
        self.assertEqual(blt.complainant_addr, "777 Driver Residence Rd.")

    def test_04_frontend_incident_html_victim_address_mapping(self):
        """Verify frontend incident.html maps victim address in proceedToBlotterElevation and stores if_complainantAddress."""
        # Hidden input for complainant address
        self.assertIn(
            'id="if_complainantAddress"',
            self.incident_html,
            "incident.html must have an input with id if_complainantAddress",
        )
        # onComplainantPicked populates if_complainantAddress
        self.assertIn(
            "document.getElementById('if_complainantAddress')",
            self.incident_html,
            "onComplainantPicked must update if_complainantAddress",
        )
        # proceedToBlotterElevation checks victimAddress and isReporterVictim
        self.assertIn(
            "victimAddress",
            self.incident_html,
            "proceedToBlotterElevation must define victimAddress",
        )
        self.assertIn(
            "isReporterVictim",
            self.incident_html,
            "proceedToBlotterElevation must check if reporter is explicitly the declared victim",
        )

    def test_05_frontend_blotter_html_prefills_victim_address(self):
        """Verify frontend blotter.html prefills victim address and clears if absent without defaulting to reporter."""
        self.assertIn(
            "resolvedCompAddr",
            self.blotter_html,
            "blotter.html must resolve complainant address from data or census without falling back to reporter",
        )
        self.assertIn(
            "document.getElementById('f_complainantAddr').value = resolvedCompAddr || '';",
            self.blotter_html,
            "blotter.html must set f_complainantAddr to resolvedCompAddr or empty string",
        )


if __name__ == "__main__":
    unittest.main()
