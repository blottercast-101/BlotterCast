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
        with self.app.app_context():
            BlotterRecord.query.filter(BlotterRecord.docket_no.like("BLT-TEST-%")).delete(synchronize_session=False)
            BlotterRecord.query.filter(BlotterRecord.docket_no.in_(["BLT-2025-999", "BLT-2025-777"])).delete(synchronize_session=False)
            Incident.query.filter(Incident.report_no.like("INC-TEST-%")).delete(synchronize_session=False)
            db.session.commit()

    def test_legacy_csv_import_creates_linked_incident_with_fallbacks(self):
        with self.app.app_context():
            res = CensusRecord.query.filter_by(first_name="Ramon", last_name="Magsaysay").first()
            if not res:
                res = CensusRecord(
                    resident_no="RES-IMPORT-001",
                    first_name="Ramon",
                    last_name="Magsaysay",
                    date_of_birth=date(1985, 3, 10),
                    sex="Male",
                    zone_id="Zone 1",
                    address="Residence 3, Mapulang Lupa",
                    status="Active"
                )
                db.session.add(res)
                db.session.commit()

            mfa_login(self.client, "admin", "admin123")

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

            blotter = BlotterRecord.query.filter_by(complainant="Ramon Magsaysay").first()
            self.assertIsNotNone(blotter)
            self.assertIsNotNone(blotter.source_incident_id)

            incident = Incident.query.get(blotter.source_incident_id)
            self.assertIsNotNone(incident)
            self.assertEqual(str(incident.incident_date), "2025-05-12")
            self.assertEqual(incident.category, "Theft")
            self.assertEqual(incident.priority, "Medium")
            self.assertEqual(incident.status, "Elevated to Blotter")
            self.assertTrue(incident.is_blotter)
            self.assertEqual(incident.blotter_docket_no, blotter.docket_no)
            self.assertEqual(incident.reporter, "Ramon Magsaysay")

    def test_zone_resolution_table_mapping(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            # CSV testing all 7 official zone mapping landmarks and addresses
            zone_csv = (
                "DOCKET NO.,DATE FILED,NAME OF COMPLAINANT,COMPLAINANT ADDRESS,NAME OF RESPONDENT,RESPONDENT ADDRESS,NATURE OF CASE,CRIM / CIVIL,ZONE\n"
                "BLT-TEST-Z1,2025-01-10,Ana Santos,Ph1 Blk 5 Lot 2 Residence 3,Pedro Cruz,Residence 3,Physical Assault,CRIM,\n"
                "BLT-TEST-Z2,2025-01-11,Carlos Garcia,Phase 2 Pandi Residence 1,Elena Reyes,Residence 1,Noise Disturbance,CIVIL,\n"
                "BLT-TEST-Z3,2025-01-12,Felipe Diaz,Pandi Village 2 Atlantica,Mario Lopez,Atlantica,Property Damage,CIVIL,\n"
                "BLT-TEST-Z4,2025-01-13,Gina Gomez,Sitio Mitay 1,Rosa Torres,Mitay,Theft,CRIM,\n"
                "BLT-TEST-Z5,2025-01-14,Hector Ramos,Sitio Gubat Purok 5,Lucia Ramos,Sitio Gubat,Family Dispute,CIVIL,\n"
                "BLT-TEST-Z6,2025-01-15,Irene Castro,Bangko St. near corner,Jorge Flores,Bangko Street,Boundary Dispute,CIVIL,\n"
                "BLT-TEST-Z7,2025-01-16,Kevin Bautista,Barangka St. Pandi-Angat Road,Mila Perez,Barangka,Vehicular Accident,CIVIL,\n"
            )

            resp = self.client.post(
                "/api/import/blotter-entry",
                data={"file": (io.BytesIO(zone_csv.encode("utf-8")), "zone_test.csv")},
                content_type="multipart/form-data"
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data["ok"])
            self.assertEqual(data["imported"], 7)
            self.assertEqual(data["skipped"], 0)

            # Check each imported record zone assignment
            expected_zones = {
                "BLT-TEST-Z1": "Zone 1",
                "BLT-TEST-Z2": "Zone 2",
                "BLT-TEST-Z3": "Zone 3",
                "BLT-TEST-Z4": "Zone 4",
                "BLT-TEST-Z5": "Zone 5",
                "BLT-TEST-Z6": "Zone 6",
                "BLT-TEST-Z7": "Zone 7",
            }
            for docket, exp_zone in expected_zones.items():
                b = BlotterRecord.query.filter_by(docket_no=docket).first()
                self.assertIsNotNone(b, f"Record {docket} must exist")
                self.assertEqual(b.zone_id, exp_zone, f"{docket} should resolve to {exp_zone}")
                
                # Check linked incident
                inc = Incident.query.get(b.source_incident_id)
                self.assertIsNotNone(inc)
                self.assertEqual(inc.zone_id, exp_zone)
                self.assertNotEqual(inc.reporter, "Legacy Walk-In")
                self.assertEqual(inc.reporter, b.complainant)
                self.assertIn("Barangay Mapulang Lupa", inc.location)
                self.assertNotEqual(inc.description, "Legacy Blotter Case Record")

    def test_skip_rows_with_missing_critical_fields(self):
        with self.app.app_context():
            mfa_login(self.client, "admin", "admin123")

            # CSV with valid row, empty participant row, and empty address row
            invalid_csv = (
                "DOCKET NO.,DATE FILED,NAME OF COMPLAINANT,COMPLAINANT ADDRESS,NAME OF RESPONDENT,RESPONDENT ADDRESS,NATURE OF CASE,CRIM / CIVIL,ZONE\n"
                "BLT-TEST-VAL,2025-02-01,Valid Complainant,Residence 3,Valid Respondent,Residence 3,Physical Assault,CRIM,Zone 1\n"
                "BLT-TEST-NO-NAMES,2025-02-02,,,Pedro Cruz,Residence 3,Physical Assault,CRIM,Zone 1\n"
                "BLT-TEST-NO-ADDR,2025-02-03,John Doe,,,Unknown Nature,CIVIL,\n"
            )

            # In the 2nd row: complainant is empty, but respondent is 'Pedro Cruz'. It should be parsed.
            # In the 3rd row: both addresses, location, and zone are empty. It must be skipped.
            # Add an entirely blank participant row
            empty_row_csv = (
                "DOCKET NO.,DATE FILED,NAME OF COMPLAINANT,COMPLAINANT ADDRESS,NAME OF RESPONDENT,RESPONDENT ADDRESS,NATURE OF CASE,CRIM / CIVIL,ZONE\n"
                "BLT-TEST-V1,2025-02-01,Valid Complainant,Residence 3,Valid Respondent,Residence 3,Physical Assault,CRIM,Zone 1\n"
                "BLT-TEST-EMPTY-PARTICIPANTS,2025-02-02,,,,,,CIVIL,Zone 1\n"
                "BLT-TEST-EMPTY-ADDR,2025-02-03,John Doe,,Jane Doe,,Unknown Nature,CIVIL,\n"
            )

            resp = self.client.post(
                "/api/import/blotter-entry",
                data={"file": (io.BytesIO(empty_row_csv.encode("utf-8")), "skip_test.csv")},
                content_type="multipart/form-data"
            )
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertTrue(data["ok"])
            self.assertEqual(data["imported"], 1)
            self.assertEqual(data["skipped"], 2)


if __name__ == "__main__":
    unittest.main()
