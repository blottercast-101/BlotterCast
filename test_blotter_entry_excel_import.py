import io
import unittest
from openpyxl import Workbook

from app import create_app
from app.extensions import db
from app.models import BlotterRecord, Incident, Settlement, User


class TestBlotterEntryExcelImport(unittest.TestCase):
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

    def tearDown(self):
        self.ctx.pop()

    def test_import_blotter_entry_record_xlsx(self):
        """Simulate importing the exact Excel spreadsheet format shown in the user's screenshot."""
        wb = Workbook()
        ws = wb.active
        ws.title = "Blotter Entry Record"

        # Row 1: Title
        ws.append(["BLOTTER ENTRY RECORD 2025"])

        # Row 2: Headers
        ws.append([
            "DOCKET NO.", "DATE FILED", "NAME OF COMPLAINANT", "ADDRESS",
            "NAME OF RESPONDENT", "ADDRESS", "NATURE OF CASE", "CRIMINAL", "CIVIL"
        ])

        # Rows 3+: Sample data from screenshot
        data = [
            [1, "2025-01-06", "JONALD J. BORRETA", "Pandi Residence 3", "ARNOLD ATCHACOSO", "Bangko St.", "Pag-aaway", "", "/"],
            [2, "2025-01-06", "JONALD J. BORRETA", "Pandi Residence 3", "ARNOLD ATCHACOSO", "Bangko St.", "Pag-aaway", "", "/"],
            [3, "2025-01-06", "JONALD J. BORRETA", "Pandi Residence 3", "ARNOLD ATCHACOSO", "Bangko St.", "Pag-aaway", "", "/"],
            [4, "2025-01-22", "ELENA BORRETA", "Sampaloc St.", "SOFIA VALDEZ", "Barangay Hall Road", "Iskandalo", "/", ""],
            [5, "2025-01-22", "ELENA BORRETA", "Sampaloc St.", "SOFIA VALDEZ", "Barangay Hall Road", "Iskandalo", "", "/"],
            [6, "2025-01-22", "ELENA BORRETA", "Sampaloc St.", "SOFIA VALDEZ", "Barangay Hall Road", "Iskandalo", "", "/"],
            [7, "2025-02-07", "NOEL ESPINO", "Sitio Ilog", "ARNOLD TORRES", "Barangay Hall Road", "Pananakit", "", "/"],
            [8, "2025-02-07", "NOEL ESPINO", "Sitio Ilog", "ARNOLD TORRES", "Barangay Hall Road", "Pananakit", "", "/"],
            [9, "2025-02-07", "NOEL ESPINO", "Sitio Ilog", "ARNOLD TORRES", "Barangay Hall Road", "Pananakit", "", "/"],
            [10, "2025-02-14", "MARIA SANTOS", "Sitio Gubat", "PEDRO PENDUKO", "Barangka St.", "Nakawan", "/", ""],
        ]
        for row in data:
            ws.append(row)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        response = self.client.post(
            "/api/import/blotter-entry",
            data={
                "file": (buf, "blotter-entry-record-20260827.xlsx"),
                "importType": "blotter-entry"
            },
            content_type="multipart/form-data"
        )

        self.assertEqual(response.status_code, 200, f"Import failed: {response.get_json()}")
        json_data = response.get_json()
        self.assertTrue(json_data["ok"])
        self.assertEqual(json_data["imported"], 10, f"Expected 10 imported rows, got: {json_data}")
        self.assertEqual(json_data["skipped"], 0)

        # Verify records created in database
        b1 = BlotterRecord.query.filter_by(complainant="JONALD J. BORRETA").first()
        self.assertIsNotNone(b1)
        self.assertEqual(b1.respondent, "ARNOLD ATCHACOSO")
        self.assertEqual(b1.complainant_addr, "Pandi Residence 3, Barangay Mapulang Lupa")
        self.assertEqual(b1.respondent_addr, "Bangko St.")
        self.assertEqual(b1.case_type, "CIVIL")

        b4 = BlotterRecord.query.filter_by(docket_no="4").first()
        self.assertIsNotNone(b4)
        self.assertEqual(b4.complainant, "ELENA BORRETA")
        self.assertEqual(b4.case_type, "CRIM")

        # Verify linked incident reports were created
        self.assertIsNotNone(b1.source_incident_id)
        inc1 = Incident.query.get(b1.source_incident_id)
        self.assertIsNotNone(inc1)
        self.assertEqual(inc1.reporter, "JONALD J. BORRETA")
        self.assertEqual(inc1.category, "Physical Assault")


if __name__ == "__main__":
    unittest.main()
