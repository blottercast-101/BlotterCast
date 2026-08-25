import io
import unittest
from datetime import date
from app import create_app
from app.extensions import db
from app.models import BlotterRecord, Incident, CensusRecord, User
from test_mfa_helper import login as mfa_login


class LegacyImportSSOTTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_legacy_csv_import_creates_linked_incident_with_fallbacks(self):
        with self.app.app_context():
            # Seed a census resident
            res = CensusRecord.query.filter_by(first_name="Ramon", last_name="Magsaysay").first()
            if not res:
                res = CensusRecord(
                    resident_no="RES-IMPORT-001",
                    first_name="Ramon",
                    last_name="Magsaysay",
                    date_of_birth=date(1985, 3, 10),
                    sex="Male",
                    zone_id="Zone 1",
                    address="123 Mabini St",
                    status="Active"
                )
                db.session.add(res)
                db.session.commit()

            mfa_login(self.client, "admin", "admin123")

            # Prepare sample legacy CSV with standard headers
            csv_content = (
                "CASE NO.,CASE TITLE,COMPLAINT TITLE,NATURE OF CASE,DATE FILED,DATE OF CONFRONTATION,ACTION TAKEN,DATE OF SETTLEMENT,DATE OF EXECUTION,MAIN POINT OF AGREEMENT,STATUS\n"
                "BLT-2025-999,Ramon Magsaysay vs Juan Dela Cruz,,Criminal - Theft of Bicycle,2025-05-12,2025-05-15,Amicably Settled,2025-05-15,,Return bicycle,COMPLIED\n"
            )

            data = {
                "file": (io.BytesIO(csv_content.encode("utf-8")), "legacy_blotter.csv")
            }

            resp = self.client.post(
                "/api/blotter_import.php",
                data=data,
                content_type="multipart/form-data"
            )

            self.assertEqual(resp.status_code, 200)
            res_json = resp.get_json()
            self.assertTrue(res_json["ok"])
            self.assertEqual(res_json["imported"], 1)

            # Query imported Blotter record
            blotter = BlotterRecord.query.filter_by(complainant="Ramon Magsaysay").first()
            self.assertIsNotNone(blotter)
            self.assertIsNotNone(blotter.source_incident_id)

            # Query linked Incident Report and verify fallback defaults
            incident = Incident.query.get(blotter.source_incident_id)
            self.assertIsNotNone(incident)
            self.assertEqual(str(incident.incident_date), "2025-05-12")
            self.assertEqual(incident.category, "Theft")
            self.assertEqual(incident.priority, "Medium")
            self.assertEqual(incident.status, "Elevated to Blotter")
            self.assertTrue(incident.is_blotter)
            self.assertEqual(incident.blotter_docket_no, blotter.docket_no)
            self.assertIsNotNone(incident.lat)
            self.assertIsNotNone(incident.lng)
            self.assertEqual(incident.reporter, "Ramon Magsaysay")

    def test_blotter_entry_and_settlement_routes(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            # 1. Test POST /api/import/blotter-entry
            entry_csv = (
                "DOCKET NO.,DATE FILED,NAME OF COMPLAINANT,COMPLAINANT ADDRESS,NAME OF RESPONDENT,RESPONDENT ADDRESS,NATURE OF CASE,CRIM / CIVIL,ZONE\n"
                "BLT-2025-777,2025-07-10,Everlie Marquez,Zone 1,Juan Dela Cruz,Zone 1,Physical Assault,CRIM,Zone 1\n"
            )
            resp1 = self.client.post(
                "/api/import/blotter-entry",
                data={"file": (io.BytesIO(entry_csv.encode("utf-8")), "blotter_entries.csv")},
                content_type="multipart/form-data"
            )
            self.assertEqual(resp1.status_code, 200)
            data1 = resp1.get_json()
            self.assertTrue(data1["ok"])
            self.assertEqual(data1["imported"], 1)

            blt = BlotterRecord.query.filter_by(docket_no="BLT-2025-777").first()
            self.assertIsNotNone(blt)
            self.assertIsNotNone(blt.source_incident_id)

            inc = Incident.query.get(blt.source_incident_id)
            self.assertIsNotNone(inc)
            self.assertEqual(inc.category, "Physical Assault")
            self.assertEqual(inc.status, "Elevated to Blotter")

            # 2. Test POST /api/import/blotter-settlement
            settlement_csv = (
                "DOCKET NO.,HEARING DATE,STAGE,SETTLEMENT STATUS,REMARKS\n"
                "BLT-2025-777,2025-07-15,1st Patawag,Settled,Parties agreed amicably.\n"
            )
            resp2 = self.client.post(
                "/api/import/blotter-settlement",
                data={"file": (io.BytesIO(settlement_csv.encode("utf-8")), "blotter_settlements.csv")},
                content_type="multipart/form-data"
            )
            self.assertEqual(resp2.status_code, 200)
            data2 = resp2.get_json()
            self.assertTrue(data2["ok"])


if __name__ == "__main__":
    unittest.main()
