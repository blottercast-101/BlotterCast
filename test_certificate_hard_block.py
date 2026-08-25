import unittest
from datetime import date
from app import create_app
from app.extensions import db
from app.models import CensusRecord, BlotterRecord, BarangayNonResidency
from test_mfa_helper import login as mfa_login


class CertificateHardBlockTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_non_residency_blocked_with_unresolved_blotter(self):
        with self.app.app_context():
            # 1. Create a transferred resident
            resident = CensusRecord.query.filter_by(first_name="Teodoro", last_name="Agoncillo").first()
            if not resident:
                resident = CensusRecord(
                    resident_no="RES-BLOCK-001",
                    first_name="Teodoro",
                    last_name="Agoncillo",
                    date_of_birth=date(1980, 5, 20),
                    sex="Male",
                    zone_id="Zone 2",
                    address="456 Bonifacio St, Mapulang Lupa",
                    status="Transferred",
                )
                db.session.add(resident)
                db.session.commit()

            # 2. Add an active/unresolved blotter record where resident is Respondent
            blotter = BlotterRecord.query.filter_by(docket_no="BLT-TEST-BLOCK-01").first()
            if not blotter:
                blotter = BlotterRecord(
                    docket_no="BLT-TEST-BLOCK-01",
                    date_filed=date(2025, 6, 1),
                    complainant="Emilio Aguinaldo",
                    respondent="Teodoro Agoncillo",
                    respondent_id=resident.id,
                    nature="Physical Assault",
                    case_type="CRIM",
                    status="Ongoing",
                    zone_id="Zone 2",
                )
                db.session.add(blotter)
                db.session.commit()
            else:
                blotter.status = "Ongoing"
                db.session.commit()

            mfa_login(self.client, "admin", "admin123")

            # 3. Attempt to issue Certificate of Non-Residency
            payload = {
                "residentId": resident.id,
                "previousAddress": resident.address,
                "purpose": "Bank Requirement",
                "fee": 20.00,
                "dateIssued": "2025-06-15",
            }
            resp = self.client.post("/api/documents/non_residency", json=payload)
            self.assertEqual(resp.status_code, 422)
            data = resp.get_json()
            self.assertFalse(data.get("ok", True))
            self.assertTrue(data.get("blocked"))
            self.assertEqual(data.get("error"), "CERTIFICATE_ISSUANCE_BLOCKED")
            self.assertIn("active/unsettled", data.get("message", ""))
            self.assertTrue(len(data.get("pendingCases", [])) > 0)

            # 4. Resolve the blotter case and verify that issuance succeeds
            blotter.status = "Resolved"
            db.session.commit()

            resp_success = self.client.post("/api/documents/non_residency", json=payload)
            self.assertEqual(resp_success.status_code, 201)
            data_success = resp_success.get_json()
            self.assertTrue(data_success.get("ok"))
            self.assertIsNotNone(data_success.get("ctrlNo"))


if __name__ == "__main__":
    unittest.main()
