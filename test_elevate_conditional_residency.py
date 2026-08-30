import json
import unittest
from datetime import date, time

from app import create_app
from app.extensions import db
from app.models import BlotterRecord, CensusRecord, Incident, User


class TestElevateConditionalResidency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "System Admin"

        # Create test Census resident
        self.resident = CensusRecord.query.filter_by(first_name="Juan", last_name="Dela Cruz").first()
        if not self.resident:
            self.resident = CensusRecord(
                resident_no="RES-9901",
                first_name="Juan",
                last_name="Dela Cruz",
                date_of_birth=date(1990, 1, 1),
                sex="Male",
                civil_status="Single",
                nationality="Filipino",
                zone_id="Zone 1",
                address="Zone 1, Barangay Mapulang Lupa",
                status="Active",
            )
            db.session.add(self.resident)
            db.session.commit()

        # Create active incident with resident reporter/complainant
        self.inc_res = Incident(
            report_no="INC-TEST-RES",
            incident_date=date(2026, 8, 30),
            time_reported=time(10, 0),
            category="Physical Assault",
            reporter="Juan Dela Cruz",
            reporter_resident_id=self.resident.id,
            reporter_address=self.resident.address,
            zone_id="Zone 1",
            description="Resident complainant test",
            status="Under Investigation",
            is_blotter=False,
        )
        # Create active incident with non-resident reporter/complainant
        self.inc_non_res = Incident(
            report_no="INC-TEST-NONRES",
            incident_date=date(2026, 8, 30),
            time_reported=time(11, 0),
            category="Theft",
            reporter="John Outsider",
            reporter_resident_id=None,
            reporter_address="Manila City",
            zone_id="Zone 1",
            description="Non-resident complainant test",
            status="Under Investigation",
            is_blotter=False,
        )
        db.session.add_all([self.inc_res, self.inc_non_res])
        db.session.commit()

    def tearDown(self):
        # Clean up
        if hasattr(self, "inc_res") and self.inc_res.id:
            BlotterRecord.query.filter_by(source_incident_id=self.inc_res.id).delete()
            Incident.query.filter_by(id=self.inc_res.id).delete()
        if hasattr(self, "inc_non_res") and self.inc_non_res.id:
            BlotterRecord.query.filter_by(source_incident_id=self.inc_non_res.id).delete()
            Incident.query.filter_by(id=self.inc_non_res.id).delete()
        db.session.commit()
        self.ctx.pop()

    def test_elevate_with_resident_complainant_and_freetext_respondent(self):
        """When Complainant is a verified resident, Respondent is strictly optional and can be free-text."""
        payload = {
            "complainant": "Juan Dela Cruz",
            "complainantId": self.resident.id,
            "respondent": "External Person From Another Town",
            "respondentId": None,
            "respondentAddr": "Barangay Sto. Cristo, San Jose Del Monte",
            "nature": "Physical Assault",
            "type": "CRIM",
        }
        res = self.client.post(f"/api/incidents/{self.inc_res.id}/elevate", json=payload)
        self.assertEqual(res.status_code, 201, f"Failed elevation: {res.get_json()}")
        data = res.get_json()
        self.assertTrue(data.get("ok"))

        # Verify blotter record
        blt = BlotterRecord.query.filter_by(source_incident_id=self.inc_res.id).first()
        self.assertIsNotNone(blt)
        self.assertEqual(blt.complainant_id, self.resident.id)
        self.assertIsNone(blt.respondent_id)
        self.assertEqual(blt.respondent, "External Person From Another Town")
        self.assertEqual(blt.respondent_addr, "Barangay Sto. Cristo, San Jose Del Monte")

    def test_elevate_with_nonresident_complainant_and_resident_respondent(self):
        """Fallback rule: If Complainant is non-resident, Respondent MUST be a Census resident."""
        payload = {
            "complainant": "John Outsider",
            "complainantId": None,
            "complainantAddr": "Manila City",
            "respondent": "Juan Dela Cruz",
            "respondentId": self.resident.id,
            "nature": "Theft",
            "type": "CRIM",
        }
        res = self.client.post(f"/api/incidents/{self.inc_non_res.id}/elevate", json=payload)
        self.assertEqual(res.status_code, 201, f"Failed elevation: {res.get_json()}")

    def test_elevate_rejected_when_neither_party_is_resident(self):
        """Elevation must be rejected if neither party is a verified Census resident."""
        payload = {
            "complainant": "John Outsider",
            "complainantId": None,
            "complainantAddr": "Manila City",
            "respondent": "Unknown Stranger",
            "respondentId": None,
            "respondentAddr": "Quezon City",
            "nature": "Theft",
            "type": "CRIM",
        }
        res = self.client.post(f"/api/incidents/{self.inc_non_res.id}/elevate", json=payload)
        self.assertEqual(res.status_code, 422)
        err = res.get_json()
        self.assertIn("registered resident in Census", err.get("error", "") or err.get("message", ""))


if __name__ == "__main__":
    unittest.main()
