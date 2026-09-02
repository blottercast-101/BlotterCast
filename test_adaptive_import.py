import csv
import io
import unittest
from datetime import date
from openpyxl import Workbook

from app import create_app
from app.extensions import db
from app.models import BlotterRecord, CensusRecord, Incident, Settlement, User
from app.blueprints.blotter_import import resolve_zone_from_address


class TestAdaptiveImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def setUp(self):
        self.ctx = self.app.app_context()
        self.ctx.push()
        # Login admin user
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "System Admin"

        # Ensure seed Census residents exist for testing
        test_residents = [
            ("Juan", "Dela Cruz", "Zone 2", "Pasong Kalabaw"),
            ("Maria", "Clara", "Zone 3", "Atlantica Homes PV2"),
            ("Elias", "Salome", "Zone 4", "Sitio Mitay"),
            ("Simoun", "Ibarra", "Zone 7", "Barangka Street"),
            ("Cardo", "Dalisay", "Zone 1", "Residence 3"),
            ("Narda", "Custodio", "Zone 5", "Sitio Gubat"),
            ("Enteng", "Kabisote", "Zone 6", "Calle Bangko"),
        ]
        for idx, (first, last, zone, addr) in enumerate(test_residents, start=1000):
            res = CensusRecord.query.filter_by(first_name=first, last_name=last).first()
            if not res:
                res = CensusRecord(
                    resident_no=f"RES-TEST-{idx}",
                    first_name=first,
                    last_name=last,
                    zone_id=zone,
                    address=addr,
                    status="Active",
                    archived=False,
                )
                db.session.add(res)
        db.session.commit()

    def tearDown(self):
        self.ctx.pop()

    def test_zone_resolver_unit_mappings(self):
        """Test that varied street names, puroks, landmarks map to their authentic zones."""
        test_cases = [
            ("Purok 1, Pandi Residences 3", "Zone 1"),
            ("Res 3 Blk 14 Lot 2", "Zone 1"),
            ("Barangay Hall Bagtasan", "Zone 1"),
            ("Phase 3 Residence", "Zone 1"),
            ("Pasong Kalabaw St.", "Zone 2"),
            ("Residens 1 Ph 1", "Zone 2"),
            ("Purok 2, Kalabaw", "Zone 2"),
            ("Atlantica Homes Pandi Village 2", "Zone 3"),
            ("PV2 Phase 2", "Zone 3"),
            ("Sitio Mitay Purok 4", "Zone 4"),
            ("Pandi Village 1 PV1", "Zone 4"),
            ("Sitio Gubat Main Road", "Zone 5"),
            ("Purok 5 Mapulang Lupa Center", "Zone 5"),
            ("Bangko St. Purok 6", "Zone 6"),
            ("Calle Bangko", "Zone 6"),
            ("Barangka St. Pandi-Angat Road", "Zone 7"),
            ("Purok 7 Encampment", "Zone 7"),
        ]
        for address, expected_zone in test_cases:
            zone_id, lat, lng = resolve_zone_from_address(address)
            self.assertEqual(zone_id, expected_zone, f"Address '{address}' failed to resolve to {expected_zone}, got {zone_id}")
            self.assertGreater(lat, 14.8)
            self.assertGreater(lng, 120.9)

    def test_external_town_dispersion(self):
        """Ensure external addresses don't blindly default to Zone 1."""
        external_addresses = [
            ("Bocaue, Bulacan", "DOCKET-EXT-1"),
            ("Santa Maria, Bulacan", "DOCKET-EXT-2"),
            ("Poblacion, Pandi", "DOCKET-EXT-3"),
            ("Valenzuela City", "DOCKET-EXT-4"),
            ("Manila", "DOCKET-EXT-5"),
            ("Quezon City", "DOCKET-EXT-6"),
            ("San Rafael, Bulacan", "DOCKET-EXT-7"),
        ]
        resolved_zones = set()
        for addr, seed in external_addresses:
            z_id, _, _ = resolve_zone_from_address(addr, deterministic_seed=seed)
            resolved_zones.add(z_id)
        self.assertGreater(len(resolved_zones), 2, "External records are clustering into too few zones")

    def test_csv_import_with_tagalog_headers_and_varied_addresses(self):
        """Import a CSV with Tagalog column headers and diverse local street addresses."""
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)
        # Header banner row (should be skipped by header scanner)
        writer.writerow(["BARANGAY MAPULANG LUPA", "OFFICIAL BLOTTER LOG", "", "", "", ""])
        # True header with Tagalog / mixed labels
        writer.writerow(["Entry No.", "Petsa", "Nagrereklamo", "Tirahan", "Ipinagrereklamo", "Kaso", "Uri", "Katayuan"])
        # Data rows with registered Census residents
        writer.writerow(["BLT-TEST-001", "2026-08-10", "Juan Dela Cruz", "Pasong Kalabaw, Zone 2", "Pedro Santos", "Suntukan sa kalsada", "Criminal", "Settled"])
        writer.writerow(["BLT-TEST-002", "2026-08-11", "Maria Clara", "Atlantica Homes PV2", "Crisostomo Ibarra", "Alitan ng kapitbahay", "Civil", "Pending"])
        writer.writerow(["BLT-TEST-003", "2026-08-12", "Elias Salome", "Sitio Mitay", "Lucas Tirona", "Paninira ng gamit", "Criminal", "Settled"])
        writer.writerow(["BLT-TEST-004", "2026-08-13", "Simoun Ibarra", "Barangka Street", "Basilio Rizal", "Ingay sa gabi", "Civil", "Not Complied"])

        csv_bytes = csv_data.getvalue().encode("utf-8")
        data = {
            "file": (io.BytesIO(csv_bytes), "tagalog_blotter.csv"),
            "importType": "blotter-entry"
        }
        res = self.client.post("/api/import/blotter-entry", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        res_json = res.get_json()
        self.assertTrue(res_json["ok"])
        self.assertEqual(res_json["imported"], 4)
        self.assertIn("Zone 2", res_json["zoneBreakdown"])
        self.assertIn("Zone 3", res_json["zoneBreakdown"])
        self.assertIn("Zone 4", res_json["zoneBreakdown"])
        self.assertIn("Zone 7", res_json["zoneBreakdown"])

    def test_xlsx_import_with_shifted_columns_and_combined_titles(self):
        """Import an Excel workbook with combined case titles ('Party A vs. Party B') and shifted columns."""
        wb = Workbook()
        ws = wb.active
        # Title row
        ws.append(["RECORD EXTRACT - 2026"])
        ws.append([])
        # Header with different aliases
        ws.append(["Docket", "Date of Filing", "Case Title", "Location", "Nature of Complaint", "Classification", "Remarks"])
        ws.append(["BLT-XLS-01", "2026-08-14", "Cardo Dalisay vs. Joaquin Tuazon", "Residence 3", "Theft of motorcycle parts", "CRIM", "Resolved amicably"])
        ws.append(["BLT-XLS-02", "2026-08-15", "Narda Custodio vs. Valentina Snake", "Sitio Gubat", "Trespassing into property", "CIVIL", "Ongoing"])
        ws.append(["BLT-XLS-03", "2026-08-16", "Enteng Kabisote vs. Reyna Sinturyon", "Calle Bangko", "Physical injury", "CRIM", "Complied"])

        xlsx_io = io.BytesIO()
        wb.save(xlsx_io)
        xlsx_io.seek(0)

        data = {
            "file": (xlsx_io, "shifted_blotter.xlsx"),
            "importType": "blotter-entry"
        }
        res = self.client.post("/api/import/blotter-entry", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 200)
        res_json = res.get_json()
        self.assertTrue(res_json["ok"])
        self.assertEqual(res_json["imported"], 3)
        self.assertIn("Zone 1", res_json["zoneBreakdown"])
        self.assertIn("Zone 5", res_json["zoneBreakdown"])
        self.assertIn("Zone 6", res_json["zoneBreakdown"])

    def test_rejection_of_census_resident_file_under_blotter_import(self):
        """Uploading a Census demographic Excel/CSV to Blotter must be strictly rejected with 422."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Residents"
        # Exact headers from residents_import (1).xlsx
        ws.append(["RESIDENT NO.", "FULL NAME", "DATE OF BIRTH", "AGE", "SEX", "CIVIL STATUS", "ZONE / PUROK", "ADDRESS", "HOUSEHOLD NO.", "STATUS", "ACTIONS"])
        ws.append(["RES-001", "Leon F. Cruz", "01/25/1954", "72", "Male", "Widowed", "Zone 5 - Sitio Gubat", "148 Sitio Gubat, Zone 5", "HH-001", "Active"])
        ws.append(["RES-002", "Domingo P. Reyes", "01/23/1995", "31", "Male", "Single", "Zone 3 - Pandi Village 2 (Atlantica)", "60 Pandi Village 2 (Atlantica)", "HH-002", "Active"])

        xlsx_io = io.BytesIO()
        wb.save(xlsx_io)
        xlsx_io.seek(0)

        data = {
            "file": (xlsx_io, "residents_import (1).xlsx"),
            "importType": "blotter-entry"
        }
        res = self.client.post("/api/import/blotter-entry", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 422)
        res_json = res.get_json()
        self.assertFalse(res_json["ok"])
        self.assertIn("Invalid Template", res_json["error"])
        self.assertIn("Census Resident list", res_json["error"])

    def test_rejection_of_random_unrelated_csv_headers(self):
        """A CSV file with unrelated/random headers must be rejected without creating synthetic records."""
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)
        writer.writerow(["Product SKU", "Item Description", "Unit Price", "Quantity in Stock", "Supplier"])
        writer.writerow(["SKU-1001", "Ballpen 0.5 Black", "15.00", "500", "Pandi Office Supplies"])

        csv_bytes = csv_data.getvalue().encode("utf-8")
        data = {
            "file": (io.BytesIO(csv_bytes), "inventory_data.csv"),
            "importType": "blotter-entry"
        }
        res = self.client.post("/api/import/blotter-entry", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 422)
        res_json = res.get_json()
        self.assertFalse(res_json["ok"])
        self.assertIn("Invalid Template", res_json["error"])


if __name__ == "__main__":
    unittest.main()

