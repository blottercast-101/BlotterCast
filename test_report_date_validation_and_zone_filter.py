import csv
import io
import unittest
from app import create_app
from app.extensions import db
from app.models import Incident, BlotterRecord, Settlement
from test_mfa_helper import login as mfa_login


class ReportDateValidationAndZoneFilterTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            mfa_login(cls.client, "admin", "admin123")

    def test_date_range_validation_rejected_when_to_earlier_than_from(self):
        """Date To earlier than Date From must return HTTP 400 with error message."""
        payload = {
            "type": "Incident Summary Report",
            "from": "2026-08-20",
            "to": "2026-08-10",
            "zone": "Zone 1",
            "format": "pdf",
        }
        res = self.client.post("/api/reports.php?action=generate", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("ok", True))
        self.assertIn("Date To cannot be earlier than Date From", data.get("error", ""))

    def test_date_range_validation_accepted_when_equal_or_valid(self):
        """Date To >= Date From must succeed."""
        payload = {
            "type": "Incident Summary Report",
            "from": "2026-08-10",
            "to": "2026-08-10",
            "zone": "",
            "format": "excel",
        }
        res = self.client.post("/api/reports.php?action=generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))

    def test_incident_summary_zone_filtering(self):
        """Selecting a specific zone must exclusively include records from that zone."""
        # Query Excel format to easily inspect rows
        payload = {
            "type": "Incident Summary Report",
            "from": "2026-01-01",
            "to": "2026-12-31",
            "zone": "Zone 1",
            "format": "excel",
        }
        res = self.client.post("/api/reports.php?action=generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))

        dl = self.client.get(f"/api/reports.php?action=download&file={data['file']}")
        self.assertEqual(dl.status_code, 200)
        csv_content = dl.data.decode("utf-8")
        reader = csv.reader(io.StringIO(csv_content))
        rows = list(reader)

        # Header rows: row 0 is title, row 1 is blank, row 2 is ["Report No.", "Date", "Zone", ...]
        header_idx = -1
        for i, r in enumerate(rows):
            if r and r[0] == "Report No.":
                header_idx = i
                break
        self.assertNotEqual(header_idx, -1, "Header row not found in generated CSV")

        data_rows = rows[header_idx + 1:]
        # Every row must belong to Zone 1 (or 1)
        for r in data_rows:
            zone_val = r[2]
            self.assertIn(zone_val, ("Zone 1", "1"), f"Record from unexpected zone found: {r}")

    def test_blotter_summary_zone_filtering(self):
        """Blotter Summary Report must filter exclusively by selected zone."""
        payload = {
            "type": "Blotter Summary Report",
            "from": "2026-01-01",
            "to": "2026-12-31",
            "zone": "Zone 2",
            "format": "excel",
        }
        res = self.client.post("/api/reports.php?action=generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))

        dl = self.client.get(f"/api/reports.php?action=download&file={data['file']}")
        self.assertEqual(dl.status_code, 200)
        # Check backend BlotterRecord query directly to confirm match
        with self.app.app_context():
            zone2_dockets = {
                b.docket_no for b in BlotterRecord.query.filter(
                    BlotterRecord.zone_id.in_(["Zone 2", "2"])
                ).all()
            }
            csv_content = dl.data.decode("utf-8")
            reader = csv.reader(io.StringIO(csv_content))
            rows = list(reader)
            header_idx = -1
            for i, r in enumerate(rows):
                if r and r[0] == "Docket No.":
                    header_idx = i
                    break
            if header_idx != -1:
                data_rows = rows[header_idx + 1:]
                for r in data_rows:
                    self.assertIn(r[0], zone2_dockets, f"Docket {r[0]} does not belong to Zone 2")

    def test_settlement_compliance_zone_filtering(self):
        """Settlement Compliance Report must filter cases whose parent blotter is in the zone."""
        payload = {
            "type": "Settlement Compliance Report",
            "from": "2026-01-01",
            "to": "2026-12-31",
            "zone": "Zone 1",
            "format": "excel",
        }
        res = self.client.post("/api/reports.php?action=generate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))

        dl = self.client.get(f"/api/reports.php?action=download&file={data['file']}")
        self.assertEqual(dl.status_code, 200)
        with self.app.app_context():
            zone1_cases = {
                s.case_no for s in Settlement.query.join(
                    BlotterRecord, Settlement.blotter_id == BlotterRecord.id
                ).filter(BlotterRecord.zone_id.in_(["Zone 1", "1"])).all()
            }
            csv_content = dl.data.decode("utf-8")
            reader = csv.reader(io.StringIO(csv_content))
            rows = list(reader)
            header_idx = -1
            for i, r in enumerate(rows):
                if r and r[0] == "Case No.":
                    header_idx = i
                    break
            if header_idx != -1:
                data_rows = rows[header_idx + 1:]
                for r in data_rows:
                    self.assertIn(r[0], zone1_cases, f"Case {r[0]} does not belong to Zone 1")

    def test_pdf_generation_with_zone_filter(self):
        """All report types must generate valid PDFs when zone is selected."""
        report_types = [
            "Incident Summary Report",
            "Settlement Compliance Report",
            "Blotter Summary Report",
            "Trend Analysis Report",
            "Predictive Risk Assessment",
        ]
        for rt in report_types:
            payload = {
                "type": rt,
                "from": "2026-01-01",
                "to": "2026-12-31",
                "zone": "Zone 1",
                "format": "pdf",
            }
            res = self.client.post("/api/reports.php?action=generate", json=payload)
            self.assertEqual(res.status_code, 200, f"Failed for report type {rt}")
            data = res.get_json()
            self.assertTrue(data.get("ok"))
            dl = self.client.get(f"/api/reports.php?action=download&file={data['file']}")
            self.assertEqual(dl.status_code, 200)
            self.assertTrue(len(dl.data) > 1000)
            self.assertTrue(dl.data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
